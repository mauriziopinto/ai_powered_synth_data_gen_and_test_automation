"""Distribution Agent for loading synthetic data into target systems."""

import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import pandas as pd
from sqlalchemy import (
    create_engine, MetaData, Table, inspect, text,
    Integer, String, Float, Boolean, DateTime, Date, Text
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects import postgresql, mysql
import logging

logger = logging.getLogger(__name__)


class LoadStrategy(Enum):
    """Data loading strategies."""
    TRUNCATE_INSERT = "truncate_insert"
    UPSERT = "upsert"
    APPEND = "append"


class DatabaseType(Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


@dataclass
class TargetConfig:
    """Configuration for a target system."""
    name: str
    type: str  # 'database', 'salesforce', 'api', 'file'
    connection_string: Optional[str] = None
    database_type: Optional[str] = None  # 'postgresql', 'mysql'
    load_strategy: str = 'truncate_insert'
    respect_fk_order: bool = True
    tables: Optional[List[str]] = None
    table_mappings: Optional[Dict[str, List[str]]] = None  # table -> column list
    primary_keys: Optional[Dict[str, List[str]]] = None  # table -> pk columns
    batch_size: int = 1000
    
    # Salesforce-specific fields
    salesforce_username: Optional[str] = None
    salesforce_password: Optional[str] = None
    salesforce_security_token: Optional[str] = None
    salesforce_domain: str = 'login'  # 'login' for production, 'test' for sandbox
    salesforce_api_version: str = '58.0'
    external_id_fields: Optional[Dict[str, str]] = None  # table -> external ID field
    
    # API-specific fields
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    api_headers: Optional[Dict[str, str]] = None
    api_method: str = 'POST'
    
    # File-specific fields
    file_path: Optional[str] = None
    file_format: str = 'csv'  # 'csv', 'json', 'parquet'
    s3_bucket: Optional[str] = None
    s3_prefix: Optional[str] = None
    
    def __post_init__(self):
        if self.tables is None:
            self.tables = []
        if self.table_mappings is None:
            self.table_mappings = {}
        if self.primary_keys is None:
            self.primary_keys = {}
        if self.external_id_fields is None:
            self.external_id_fields = {}
        if self.api_headers is None:
            self.api_headers = {}


@dataclass
class LoadResult:
    """Result of loading data to a target."""
    target: str
    status: str  # 'success', 'failed', 'partial'
    records_loaded: int
    duration: float
    error: Optional[str] = None
    tables_loaded: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.tables_loaded is None:
            self.tables_loaded = []


@dataclass
class DistributionReport:
    """Report of distribution operation."""
    results: List[LoadResult]
    total_targets: int
    successful_targets: int
    failed_targets: int
    total_records: int
    total_duration: float
    timestamp: datetime
    
    @classmethod
    def from_results(cls, results: List[LoadResult]):
        """Create report from load results."""
        return cls(
            results=results,
            total_targets=len(results),
            successful_targets=sum(1 for r in results if r.status == 'success'),
            failed_targets=sum(1 for r in results if r.status == 'failed'),
            total_records=sum(r.records_loaded for r in results),
            total_duration=sum(r.duration for r in results),
            timestamp=datetime.now()
        )


class DatabaseConnectionManager:
    """Manages database connections for different database types."""
    
    def __init__(self, connection_string: str, database_type: str):
        """Initialize connection manager.
        
        Args:
            connection_string: Database connection string
            database_type: Type of database ('postgresql' or 'mysql')
        """
        self.connection_string = connection_string
        self.database_type = DatabaseType(database_type.lower())
        self.engine: Optional[Engine] = None
        self.metadata: Optional[MetaData] = None
    
    def connect(self) -> Engine:
        """Create and return database engine."""
        if self.engine is None:
            # Configure engine based on database type
            if self.database_type == DatabaseType.POSTGRESQL:
                self.engine = create_engine(
                    self.connection_string,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,
                    echo=False
                )
            elif self.database_type == DatabaseType.MYSQL:
                self.engine = create_engine(
                    self.connection_string,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,
                    pool_recycle=3600,  # Recycle connections after 1 hour
                    echo=False
                )
            else:
                raise ValueError(f"Unsupported database type: {self.database_type}")
        
        return self.engine
    
    def get_metadata(self) -> MetaData:
        """Get database metadata."""
        if self.metadata is None:
            engine = self.connect()
            self.metadata = MetaData()
            self.metadata.reflect(bind=engine)
        return self.metadata
    
    def get_foreign_keys(self) -> Dict[str, List[Tuple[str, str]]]:
        """Get foreign key relationships for all tables.
        
        Returns:
            Dict mapping table name to list of (referenced_table, fk_column) tuples
        """
        engine = self.connect()
        inspector = inspect(engine)
        fk_map = {}
        
        for table_name in inspector.get_table_names():
            fks = inspector.get_foreign_keys(table_name)
            fk_list = []
            for fk in fks:
                referenced_table = fk['referred_table']
                # Get the first column (simplified - assumes single column FKs)
                fk_column = fk['constrained_columns'][0] if fk['constrained_columns'] else None
                if fk_column:
                    fk_list.append((referenced_table, fk_column))
            fk_map[table_name] = fk_list
        
        return fk_map
    
    def close(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.metadata = None


class TopologicalSorter:
    """Sorts tables in dependency order for FK-respecting loads."""
    
    @staticmethod
    def sort_tables(fk_map: Dict[str, List[Tuple[str, str]]]) -> List[str]:
        """Sort tables in topological order based on foreign key dependencies.
        
        Args:
            fk_map: Dict mapping table name to list of (referenced_table, fk_column) tuples
        
        Returns:
            List of table names in dependency order (tables with no dependencies first)
        
        Raises:
            ValueError: If circular dependencies are detected
        """
        # Build adjacency list (table -> tables that depend on it)
        graph: Dict[str, Set[str]] = {table: set() for table in fk_map.keys()}
        in_degree: Dict[str, int] = {table: 0 for table in fk_map.keys()}
        
        for table, dependencies in fk_map.items():
            for referenced_table, _ in dependencies:
                if referenced_table in graph:
                    graph[referenced_table].add(table)
                    in_degree[table] += 1
        
        # Kahn's algorithm for topological sort
        queue = [table for table, degree in in_degree.items() if degree == 0]
        sorted_tables = []
        
        while queue:
            # Sort queue for deterministic ordering
            queue.sort()
            current = queue.pop(0)
            sorted_tables.append(current)
            
            # Reduce in-degree for dependent tables
            for dependent in graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Check for cycles
        if len(sorted_tables) != len(fk_map):
            remaining = set(fk_map.keys()) - set(sorted_tables)
            raise ValueError(f"Circular dependency detected among tables: {remaining}")
        
        return sorted_tables


class DatabaseLoader:
    """Loads data into relational databases."""
    
    def __init__(self, connection_manager: DatabaseConnectionManager):
        """Initialize database loader.
        
        Args:
            connection_manager: Database connection manager
        """
        self.conn_manager = connection_manager
        self.sorter = TopologicalSorter()
    
    async def load(
        self,
        data: pd.DataFrame,
        config: TargetConfig
    ) -> LoadResult:
        """Load data into database.
        
        Args:
            data: DataFrame containing data to load
            config: Target configuration
        
        Returns:
            LoadResult with operation details
        """
        start_time = datetime.now()
        tables_loaded = []
        total_records = 0
        
        try:
            engine = self.conn_manager.connect()
            
            # Determine table loading order
            if config.respect_fk_order and len(config.tables) > 1:
                fk_map = self.conn_manager.get_foreign_keys()
                # Filter to only requested tables
                filtered_fk_map = {
                    table: fks for table, fks in fk_map.items()
                    if table in config.tables
                }
                tables_to_load = self.sorter.sort_tables(filtered_fk_map)
            else:
                tables_to_load = config.tables
            
            # Load each table
            for table_name in tables_to_load:
                if table_name not in config.table_mappings:
                    logger.warning(f"No column mapping for table {table_name}, skipping")
                    continue
                
                # Extract columns for this table
                columns = config.table_mappings[table_name]
                table_data = data[columns].copy()
                
                # Load based on strategy
                strategy = LoadStrategy(config.load_strategy)
                
                if strategy == LoadStrategy.TRUNCATE_INSERT:
                    records = self._truncate_insert(
                        engine, table_name, table_data, config.batch_size
                    )
                elif strategy == LoadStrategy.UPSERT:
                    pk_columns = config.primary_keys.get(table_name, [])
                    if not pk_columns:
                        raise ValueError(
                            f"Primary key columns required for upsert strategy on table {table_name}"
                        )
                    records = self._upsert(
                        engine, table_name, table_data, pk_columns, config.batch_size
                    )
                elif strategy == LoadStrategy.APPEND:
                    records = self._append(
                        engine, table_name, table_data, config.batch_size
                    )
                else:
                    raise ValueError(f"Unknown load strategy: {strategy}")
                
                tables_loaded.append(table_name)
                total_records += records
                logger.info(f"Loaded {records} records into {table_name}")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return LoadResult(
                target=config.name,
                status='success',
                records_loaded=total_records,
                duration=duration,
                tables_loaded=tables_loaded
            )
        
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Failed to load data to {config.name}: {str(e)}")
            return LoadResult(
                target=config.name,
                status='failed',
                records_loaded=total_records,
                duration=duration,
                error=str(e),
                tables_loaded=tables_loaded
            )
    
    def _truncate_insert(
        self,
        engine: Engine,
        table_name: str,
        data: pd.DataFrame,
        batch_size: int
    ) -> int:
        """Truncate table and insert data.
        
        Args:
            engine: SQLAlchemy engine
            table_name: Name of table
            data: Data to insert
            batch_size: Batch size for inserts
        
        Returns:
            Number of records inserted
        """
        with engine.begin() as conn:
            # Truncate table (SQLite uses DELETE, others use TRUNCATE)
            if 'sqlite' in str(engine.url):
                conn.execute(text(f'DELETE FROM {table_name}'))
            elif self.conn_manager.database_type == DatabaseType.POSTGRESQL:
                conn.execute(text(f'TRUNCATE TABLE "{table_name}" CASCADE'))
            else:  # MySQL
                conn.execute(text(f'TRUNCATE TABLE `{table_name}`'))
            
            # Insert data in batches
            data.to_sql(
                table_name,
                conn,
                if_exists='append',
                index=False,
                chunksize=batch_size,
                method='multi'
            )
        
        return len(data)
    
    def _upsert(
        self,
        engine: Engine,
        table_name: str,
        data: pd.DataFrame,
        pk_columns: List[str],
        batch_size: int
    ) -> int:
        """Upsert data (insert or update on conflict).
        
        Args:
            engine: SQLAlchemy engine
            table_name: Name of table
            data: Data to upsert
            pk_columns: Primary key column names
            batch_size: Batch size for operations
        
        Returns:
            Number of records upserted
        """
        records_processed = 0
        
        # Get all columns except primary keys for update
        update_columns = [col for col in data.columns if col not in pk_columns]
        
        with engine.begin() as conn:
            # Process in batches
            for i in range(0, len(data), batch_size):
                batch = data.iloc[i:i + batch_size]
                
                if self.conn_manager.database_type == DatabaseType.POSTGRESQL:
                    # PostgreSQL: Use INSERT ... ON CONFLICT DO UPDATE
                    self._upsert_postgresql(conn, table_name, batch, pk_columns, update_columns)
                else:  # MySQL
                    # MySQL: Use INSERT ... ON DUPLICATE KEY UPDATE
                    self._upsert_mysql(conn, table_name, batch, pk_columns, update_columns)
                
                records_processed += len(batch)
        
        return records_processed
    
    def _upsert_postgresql(
        self,
        conn,
        table_name: str,
        data: pd.DataFrame,
        pk_columns: List[str],
        update_columns: List[str]
    ):
        """Perform upsert for PostgreSQL."""
        # Build column lists
        all_columns = list(data.columns)
        columns_str = ', '.join(f'"{col}"' for col in all_columns)
        values_placeholders = ', '.join(f':{col}' for col in all_columns)
        
        # Build conflict clause
        conflict_columns = ', '.join(f'"{col}"' for col in pk_columns)
        
        # Build update clause
        if update_columns:
            update_clause = ', '.join(
                f'"{col}" = EXCLUDED."{col}"' for col in update_columns
            )
            on_conflict = f'ON CONFLICT ({conflict_columns}) DO UPDATE SET {update_clause}'
        else:
            on_conflict = f'ON CONFLICT ({conflict_columns}) DO NOTHING'
        
        # Build and execute query
        query = text(f'''
            INSERT INTO "{table_name}" ({columns_str})
            VALUES ({values_placeholders})
            {on_conflict}
        ''')
        
        # Execute for each row
        for _, row in data.iterrows():
            conn.execute(query, row.to_dict())
    
    def _upsert_mysql(
        self,
        conn,
        table_name: str,
        data: pd.DataFrame,
        pk_columns: List[str],
        update_columns: List[str]
    ):
        """Perform upsert for MySQL."""
        # Build column lists
        all_columns = list(data.columns)
        columns_str = ', '.join(f'`{col}`' for col in all_columns)
        values_placeholders = ', '.join(f':{col}' for col in all_columns)
        
        # Build update clause
        if update_columns:
            update_clause = ', '.join(
                f'`{col}` = VALUES(`{col}`)' for col in update_columns
            )
            on_duplicate = f'ON DUPLICATE KEY UPDATE {update_clause}'
        else:
            # If no update columns, just ignore duplicates
            on_duplicate = ''
        
        # Build and execute query
        query_str = f'''
            INSERT INTO `{table_name}` ({columns_str})
            VALUES ({values_placeholders})
            {on_duplicate}
        '''
        query = text(query_str)
        
        # Execute for each row
        for _, row in data.iterrows():
            conn.execute(query, row.to_dict())
    
    def _append(
        self,
        engine: Engine,
        table_name: str,
        data: pd.DataFrame,
        batch_size: int
    ) -> int:
        """Append data to table without truncating.
        
        Args:
            engine: SQLAlchemy engine
            table_name: Name of table
            data: Data to append
            batch_size: Batch size for inserts
        
        Returns:
            Number of records inserted
        """
        with engine.begin() as conn:
            data.to_sql(
                table_name,
                conn,
                if_exists='append',
                index=False,
                chunksize=batch_size,
                method='multi'
            )
        
        return len(data)


class SalesforceLoader:
    """Salesforce Bulk API loader."""
    
    def __init__(self, config: TargetConfig):
        """Initialize Salesforce loader.
        
        Args:
            config: Target configuration with Salesforce credentials
        """
        try:
            from shared.utils.salesforce_client import SalesforceClient, SalesforceConfig, SALESFORCE_AVAILABLE
            
            if not SALESFORCE_AVAILABLE:
                raise ImportError("Salesforce client not available - install required dependencies")
            
            # Extract Salesforce configuration
            sf_config = SalesforceConfig(
                username=getattr(config, 'salesforce_username', ''),
                password=getattr(config, 'salesforce_password', ''),
                security_token=getattr(config, 'salesforce_security_token', ''),
                domain=getattr(config, 'salesforce_domain', 'login'),
                api_version=getattr(config, 'salesforce_api_version', '58.0')
            )
            
            self.client = SalesforceClient(sf_config)
            self.config = config
            
        except ImportError as e:
            logger.warning(f"Salesforce client not available: {str(e)}")
            self.client = None
            self.config = config
    
    async def load(self, data: pd.DataFrame, config: TargetConfig) -> LoadResult:
        """Load data to Salesforce using Bulk API.
        
        Args:
            data: DataFrame to load
            config: Target configuration
        
        Returns:
            LoadResult
        """
        start_time = datetime.now()
        
        try:
            if self.client is None:
                raise ImportError("Salesforce client not available - install required dependencies")
            
            if data.empty:
                raise ValueError("Cannot load empty dataset")
            
            # Validate required configuration
            if not getattr(config, 'salesforce_username', None):
                raise ValueError("Salesforce username is required")
            
            # Authenticate
            await self.client.authenticate()
            
            total_success = 0
            total_failed = 0
            tables_loaded = []
            
            # Load each table/object
            tables = config.tables or ['Account']  # Default to Account if not specified
            
            for table in tables:
                # Get columns for this table
                columns = config.table_mappings.get(table) if config.table_mappings else None
                table_data = data[columns] if columns else data
                
                # Determine operation
                if config.load_strategy == 'upsert':
                    external_id_field = config.external_id_fields.get(table) if hasattr(config, 'external_id_fields') else None
                    if not external_id_field:
                        raise ValueError(f"External ID field required for upsert on {table}")
                    
                    success, failed, errors = await self.client.bulk_upsert(
                        table,
                        table_data,
                        external_id_field,
                        batch_size=config.batch_size
                    )
                else:
                    # Default to insert
                    success, failed, errors = await self.client.bulk_insert(
                        table,
                        table_data,
                        batch_size=config.batch_size
                    )
                
                total_success += success
                total_failed += failed
                tables_loaded.append(table)
                
                if errors:
                    logger.warning(f"Errors loading {table}: {len(errors)} records failed")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Close client
            self.client.close()
            
            return LoadResult(
                target=config.name,
                status='success' if total_failed == 0 else 'partial',
                records_loaded=total_success,
                duration=duration,
                tables_loaded=tables_loaded,
                error=f"{total_failed} records failed" if total_failed > 0 else None
            )
        
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            if self.client:
                self.client.close()
            return LoadResult(
                target=config.name,
                status='failed',
                records_loaded=0,
                duration=duration,
                error=str(e)
            )


class APILoader:
    """REST API loader."""
    
    async def load(self, data: pd.DataFrame, config: TargetConfig) -> LoadResult:
        """Load data via REST API.
        
        Args:
            data: DataFrame to load
            config: Target configuration
        
        Returns:
            LoadResult
        """
        start_time = datetime.now()
        
        try:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            if not config.api_url:
                raise ValueError("API URL is required")
            
            if data.empty:
                raise ValueError("Cannot load empty dataset")
            
            # Convert to JSON
            json_data = data.to_dict(orient='records')
            
            # Setup session with retry logic
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["POST", "PUT", "PATCH"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            
            # Prepare headers
            headers = config.api_headers.copy() if config.api_headers else {}
            headers['Content-Type'] = 'application/json'
            
            if config.api_key:
                headers['Authorization'] = f'Bearer {config.api_key}'
            
            # Send data in batches
            total_success = 0
            total_failed = 0
            
            for i in range(0, len(json_data), config.batch_size):
                batch = json_data[i:i + config.batch_size]
                
                # Make API request
                if config.api_method.upper() == 'POST':
                    response = session.post(config.api_url, json=batch, headers=headers)
                elif config.api_method.upper() == 'PUT':
                    response = session.put(config.api_url, json=batch, headers=headers)
                elif config.api_method.upper() == 'PATCH':
                    response = session.patch(config.api_url, json=batch, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {config.api_method}")
                
                response.raise_for_status()
                total_success += len(batch)
            
            duration = (datetime.now() - start_time).total_seconds()
            session.close()
            
            return LoadResult(
                target=config.name,
                status='success',
                records_loaded=total_success,
                duration=duration,
                tables_loaded=['API_Endpoint']
            )
        
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return LoadResult(
                target=config.name,
                status='failed',
                records_loaded=0,
                duration=duration,
                error=str(e)
            )


class FileLoader:
    """File storage loader (S3, local)."""
    
    async def load(self, data: pd.DataFrame, config: TargetConfig) -> LoadResult:
        """Load data to file storage (local or S3).
        
        Args:
            data: DataFrame to load
            config: Target configuration
        
        Returns:
            LoadResult
        """
        start_time = datetime.now()
        
        try:
            if data.empty:
                raise ValueError("Cannot load empty dataset")
            
            # Determine if S3 or local
            if config.s3_bucket:
                # S3 upload
                output_path = await self._upload_to_s3(data, config)
            else:
                # Local file
                output_path = await self._save_to_local(data, config)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return LoadResult(
                target=config.name,
                status='success',
                records_loaded=len(data),
                duration=duration,
                tables_loaded=[output_path]
            )
        
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return LoadResult(
                target=config.name,
                status='failed',
                records_loaded=0,
                duration=duration,
                error=str(e)
            )
    
    async def _save_to_local(self, data: pd.DataFrame, config: TargetConfig) -> str:
        """Save data to local file.
        
        Args:
            data: DataFrame to save
            config: Target configuration
        
        Returns:
            Path to saved file
        """
        output_path = config.file_path or f'output_data.{config.file_format}'
        
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Write based on format
        if config.file_format == 'csv':
            data.to_csv(output_path, index=False)
        elif config.file_format == 'json':
            data.to_json(output_path, orient='records', indent=2)
        elif config.file_format == 'parquet':
            data.to_parquet(output_path, index=False)
        else:
            raise ValueError(f"Unsupported file format: {config.file_format}")
        
        logger.info(f"Saved {len(data)} records to {output_path}")
        return output_path
    
    async def _upload_to_s3(self, data: pd.DataFrame, config: TargetConfig) -> str:
        """Upload data to S3.
        
        Args:
            data: DataFrame to upload
            config: Target configuration
        
        Returns:
            S3 path
        """
        try:
            import boto3
            from io import BytesIO
            
            s3_client = boto3.client('s3')
            
            # Generate S3 key
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            prefix = config.s3_prefix or 'synthetic_data'
            s3_key = f"{prefix}/{timestamp}.{config.file_format}"
            
            # Convert to bytes based on format
            buffer = BytesIO()
            
            if config.file_format == 'csv':
                data.to_csv(buffer, index=False)
            elif config.file_format == 'json':
                data.to_json(buffer, orient='records', indent=2)
            elif config.file_format == 'parquet':
                data.to_parquet(buffer, index=False)
            else:
                raise ValueError(f"Unsupported file format: {config.file_format}")
            
            # Upload to S3
            buffer.seek(0)
            s3_client.put_object(
                Bucket=config.s3_bucket,
                Key=s3_key,
                Body=buffer.getvalue()
            )
            
            s3_path = f"s3://{config.s3_bucket}/{s3_key}"
            logger.info(f"Uploaded {len(data)} records to {s3_path}")
            return s3_path
            
        except ImportError:
            raise ImportError("boto3 is required for S3 uploads. Install with: pip install boto3")
        except Exception as e:
            raise Exception(f"Failed to upload to S3: {str(e)}")


class DistributionAgent:
    """Agent for distributing synthetic data to target systems."""
    
    def __init__(self):
        """Initialize distribution agent."""
        self.loaders = {
            'database': self._load_to_database,
            'salesforce': self._load_to_salesforce,
            'api': self._load_to_api,
            'file': self._load_to_file,
        }
    
    async def process(
        self,
        synthetic_data: pd.DataFrame,
        targets: List[TargetConfig]
    ) -> DistributionReport:
        """Process data distribution to all targets.
        
        Args:
            synthetic_data: DataFrame with synthetic data
            targets: List of target configurations
        
        Returns:
            DistributionReport with results for all targets
        """
        results = []
        
        for target in targets:
            try:
                loader = self.loaders.get(target.type)
                if not loader:
                    results.append(LoadResult(
                        target=target.name,
                        status='failed',
                        records_loaded=0,
                        duration=0.0,
                        error=f"Unsupported target type: {target.type}"
                    ))
                    continue
                
                result = await loader(synthetic_data, target)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error loading to {target.name}: {str(e)}")
                results.append(LoadResult(
                    target=target.name,
                    status='failed',
                    records_loaded=0,
                    duration=0.0,
                    error=str(e)
                ))
        
        return DistributionReport.from_results(results)
    
    async def _load_to_database(
        self,
        data: pd.DataFrame,
        config: TargetConfig
    ) -> LoadResult:
        """Load data to database target.
        
        Args:
            data: DataFrame to load
            config: Target configuration
        
        Returns:
            LoadResult
        """
        if not config.connection_string:
            raise ValueError("Database connection string is required")
        
        if not config.database_type:
            raise ValueError("Database type is required")
        
        conn_manager = DatabaseConnectionManager(
            config.connection_string,
            config.database_type
        )
        
        try:
            loader = DatabaseLoader(conn_manager)
            result = await loader.load(data, config)
            return result
        finally:
            conn_manager.close()
    
    async def _load_to_salesforce(
        self,
        data: pd.DataFrame,
        config: TargetConfig
    ) -> LoadResult:
        """Load data to Salesforce target.
        
        Args:
            data: DataFrame to load
            config: Target configuration
        
        Returns:
            LoadResult
        """
        loader = SalesforceLoader(config)
        return await loader.load(data, config)
    
    async def _load_to_api(
        self,
        data: pd.DataFrame,
        config: TargetConfig
    ) -> LoadResult:
        """Load data to REST API target.
        
        Args:
            data: DataFrame to load
            config: Target configuration
        
        Returns:
            LoadResult
        """
        loader = APILoader()
        return await loader.load(data, config)
    
    async def _load_to_file(
        self,
        data: pd.DataFrame,
        config: TargetConfig
    ) -> LoadResult:
        """Load data to file storage target.
        
        Args:
            data: DataFrame to load
            config: Target configuration
        
        Returns:
            LoadResult
        """
        loader = FileLoader()
        return await loader.load(data, config)
