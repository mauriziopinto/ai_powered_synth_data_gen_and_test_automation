"""Unit tests for Distribution Agent."""

import pytest
import pandas as pd
import asyncio
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, ForeignKey, inspect
from sqlalchemy.orm import sessionmaker

from agents.distribution import (
    DistributionAgent,
    DatabaseLoader,
    DatabaseConnectionManager,
    TopologicalSorter,
    TargetConfig,
    LoadResult,
    DistributionReport,
    LoadStrategy,
    DatabaseType
)


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com'],
        'age': [25, 30, 35]
    })


@pytest.fixture
def sqlite_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine('sqlite:///:memory:', echo=False)
    
    # Create test tables
    metadata = MetaData()
    
    # Parent table
    users = Table('users', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(100)),
        Column('email', String(100))
    )
    
    # Child table with FK
    orders = Table('orders', metadata,
        Column('id', Integer, primary_key=True),
        Column('user_id', Integer, ForeignKey('users.id')),
        Column('amount', Integer)
    )
    
    metadata.create_all(engine)
    
    yield engine
    
    engine.dispose()


@pytest.fixture
def postgres_connection_string():
    """PostgreSQL connection string for testing."""
    # This would be a test database in real scenarios
    return "postgresql://test:test@localhost:5432/test_db"


@pytest.fixture
def mysql_connection_string():
    """MySQL connection string for testing."""
    # This would be a test database in real scenarios
    return "mysql://test:test@localhost:3306/test_db"


class TestTopologicalSorter:
    """Test topological sorting for FK dependencies."""
    
    def test_simple_dependency_chain(self):
        """Test sorting with simple A -> B -> C chain."""
        fk_map = {
            'table_a': [],  # No dependencies
            'table_b': [('table_a', 'a_id')],  # Depends on A
            'table_c': [('table_b', 'b_id')]   # Depends on B
        }
        
        sorter = TopologicalSorter()
        result = sorter.sort_tables(fk_map)
        
        # A should come before B, B before C
        assert result.index('table_a') < result.index('table_b')
        assert result.index('table_b') < result.index('table_c')
    
    def test_multiple_dependencies(self):
        """Test sorting with multiple dependencies."""
        fk_map = {
            'users': [],
            'products': [],
            'orders': [('users', 'user_id'), ('products', 'product_id')]
        }
        
        sorter = TopologicalSorter()
        result = sorter.sort_tables(fk_map)
        
        # Both users and products should come before orders
        assert result.index('users') < result.index('orders')
        assert result.index('products') < result.index('orders')
    
    def test_no_dependencies(self):
        """Test sorting with no dependencies."""
        fk_map = {
            'table_a': [],
            'table_b': [],
            'table_c': []
        }
        
        sorter = TopologicalSorter()
        result = sorter.sort_tables(fk_map)
        
        # Should return all tables (order doesn't matter)
        assert set(result) == {'table_a', 'table_b', 'table_c'}
        assert len(result) == 3
    
    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        fk_map = {
            'table_a': [('table_b', 'b_id')],
            'table_b': [('table_a', 'a_id')]
        }
        
        sorter = TopologicalSorter()
        
        with pytest.raises(ValueError, match="Circular dependency"):
            sorter.sort_tables(fk_map)
    
    def test_complex_dependency_graph(self):
        """Test sorting with complex dependency graph."""
        fk_map = {
            'countries': [],
            'states': [('countries', 'country_id')],
            'cities': [('states', 'state_id')],
            'users': [('cities', 'city_id')],
            'orders': [('users', 'user_id')],
            'order_items': [('orders', 'order_id')]
        }
        
        sorter = TopologicalSorter()
        result = sorter.sort_tables(fk_map)
        
        # Verify dependency order
        assert result.index('countries') < result.index('states')
        assert result.index('states') < result.index('cities')
        assert result.index('cities') < result.index('users')
        assert result.index('users') < result.index('orders')
        assert result.index('orders') < result.index('order_items')


class TestDatabaseConnectionManager:
    """Test database connection manager."""
    
    def test_sqlite_connection(self):
        """Test SQLite connection creation."""
        conn_manager = DatabaseConnectionManager(
            'sqlite:///:memory:',
            'postgresql'  # Type doesn't matter for SQLite
        )
        
        engine = conn_manager.connect()
        assert engine is not None
        
        # Test connection works
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            assert result.fetchone()[0] == 1
        
        conn_manager.close()
    
    def test_metadata_reflection(self, sqlite_engine):
        """Test metadata reflection."""
        # Use the connection string from the fixture
        conn_manager = DatabaseConnectionManager(
            str(sqlite_engine.url),
            'postgresql'
        )
        
        metadata = conn_manager.get_metadata()
        
        # Should have reflected the tables
        assert 'users' in metadata.tables
        assert 'orders' in metadata.tables
        
        conn_manager.close()
    
    def test_foreign_key_detection(self, sqlite_engine):
        """Test foreign key relationship detection."""
        conn_manager = DatabaseConnectionManager(
            str(sqlite_engine.url),
            'postgresql'
        )
        
        fk_map = conn_manager.get_foreign_keys()
        
        # Orders table should have FK to users
        assert 'orders' in fk_map
        assert len(fk_map['orders']) > 0
        
        # Check that users is referenced
        referenced_tables = [ref[0] for ref in fk_map['orders']]
        assert 'users' in referenced_tables
        
        conn_manager.close()


class TestDatabaseLoader:
    """Test database loader functionality."""
    
    @pytest.mark.asyncio
    async def test_truncate_insert_strategy(self, sqlite_engine, sample_data):
        """Test truncate-insert loading strategy."""
        conn_manager = DatabaseConnectionManager(
            str(sqlite_engine.url),
            'postgresql'
        )
        
        config = TargetConfig(
            name='test_db',
            type='database',
            connection_string=str(sqlite_engine.url),
            database_type='postgresql',
            load_strategy='truncate_insert',
            respect_fk_order=False,
            tables=['users'],
            table_mappings={'users': ['id', 'name', 'email']},
            batch_size=100
        )
        
        loader = DatabaseLoader(conn_manager)
        result = await loader.load(sample_data, config)
        
        assert result.status == 'success'
        assert result.records_loaded == 3
        assert 'users' in result.tables_loaded
        
        # Verify data was loaded
        with sqlite_engine.connect() as conn:
            result_df = pd.read_sql('SELECT * FROM users', conn)
            assert len(result_df) == 3
            assert set(result_df['name']) == {'Alice', 'Bob', 'Charlie'}
        
        conn_manager.close()
    
    @pytest.mark.asyncio
    async def test_append_strategy(self, sqlite_engine, sample_data):
        """Test append loading strategy."""
        conn_manager = DatabaseConnectionManager(
            str(sqlite_engine.url),
            'postgresql'
        )
        
        # Insert initial data
        with sqlite_engine.begin() as conn:
            sample_data.to_sql('users', conn, if_exists='append', index=False)
        
        # Append more data
        new_data = pd.DataFrame({
            'id': [4, 5],
            'name': ['David', 'Eve'],
            'email': ['david@example.com', 'eve@example.com']
        })
        
        config = TargetConfig(
            name='test_db',
            type='database',
            connection_string=str(sqlite_engine.url),
            database_type='postgresql',
            load_strategy='append',
            respect_fk_order=False,
            tables=['users'],
            table_mappings={'users': ['id', 'name', 'email']},
            batch_size=100
        )
        
        loader = DatabaseLoader(conn_manager)
        result = await loader.load(new_data, config)
        
        assert result.status == 'success'
        assert result.records_loaded == 2
        
        # Verify both old and new data exist
        with sqlite_engine.connect() as conn:
            result_df = pd.read_sql('SELECT * FROM users', conn)
            assert len(result_df) == 5
        
        conn_manager.close()
    
    @pytest.mark.asyncio
    async def test_fk_ordered_loading(self, sqlite_engine):
        """Test FK-ordered loading."""
        conn_manager = DatabaseConnectionManager(
            str(sqlite_engine.url),
            'postgresql'
        )
        
        # Create data for both tables
        users_data = pd.DataFrame({
            'id': [1, 2],
            'name': ['Alice', 'Bob'],
            'email': ['alice@example.com', 'bob@example.com']
        })
        
        orders_data = pd.DataFrame({
            'id': [101, 102],
            'user_id': [1, 2],
            'amount': [100, 200]
        })
        
        # Combine into single dataframe
        combined_data = pd.concat([
            users_data.assign(table='users'),
            orders_data.assign(table='orders')
        ], ignore_index=True)
        
        config = TargetConfig(
            name='test_db',
            type='database',
            connection_string=str(sqlite_engine.url),
            database_type='postgresql',
            load_strategy='truncate_insert',
            respect_fk_order=True,
            tables=['users', 'orders'],
            table_mappings={
                'users': ['id', 'name', 'email'],
                'orders': ['id', 'user_id', 'amount']
            },
            batch_size=100
        )
        
        loader = DatabaseLoader(conn_manager)
        
        # Load users first
        result_users = await loader.load(users_data, TargetConfig(
            name='test_db',
            type='database',
            connection_string=str(sqlite_engine.url),
            database_type='postgresql',
            load_strategy='truncate_insert',
            respect_fk_order=False,
            tables=['users'],
            table_mappings={'users': ['id', 'name', 'email']},
            batch_size=100
        ))
        
        # Then load orders
        result_orders = await loader.load(orders_data, TargetConfig(
            name='test_db',
            type='database',
            connection_string=str(sqlite_engine.url),
            database_type='postgresql',
            load_strategy='truncate_insert',
            respect_fk_order=False,
            tables=['orders'],
            table_mappings={'orders': ['id', 'user_id', 'amount']},
            batch_size=100
        ))
        
        assert result_users.status == 'success'
        assert result_orders.status == 'success'
        
        # Verify FK relationships are intact
        with sqlite_engine.connect() as conn:
            orders_df = pd.read_sql('SELECT * FROM orders', conn)
            assert len(orders_df) == 2
            assert all(orders_df['user_id'].isin([1, 2]))
        
        conn_manager.close()


class TestDistributionAgent:
    """Test distribution agent."""
    
    @pytest.mark.asyncio
    async def test_successful_distribution(self, sqlite_engine, sample_data):
        """Test successful data distribution."""
        agent = DistributionAgent()
        
        config = TargetConfig(
            name='test_db',
            type='database',
            connection_string=str(sqlite_engine.url),
            database_type='postgresql',
            load_strategy='truncate_insert',
            respect_fk_order=False,
            tables=['users'],
            table_mappings={'users': ['id', 'name', 'email']},
            batch_size=100
        )
        
        report = await agent.process(sample_data, [config])
        
        assert report.total_targets == 1
        assert report.successful_targets == 1
        assert report.failed_targets == 0
        assert report.total_records == 3
        assert len(report.results) == 1
        assert report.results[0].status == 'success'
    
    @pytest.mark.asyncio
    async def test_failed_distribution(self, sample_data):
        """Test failed data distribution."""
        agent = DistributionAgent()
        
        # Invalid connection string
        config = TargetConfig(
            name='test_db',
            type='database',
            connection_string='invalid://connection',
            database_type='postgresql',
            load_strategy='truncate_insert',
            respect_fk_order=False,
            tables=['users'],
            table_mappings={'users': ['id', 'name', 'email']},
            batch_size=100
        )
        
        report = await agent.process(sample_data, [config])
        
        assert report.total_targets == 1
        assert report.successful_targets == 0
        assert report.failed_targets == 1
        assert report.results[0].status == 'failed'
        assert report.results[0].error is not None
    
    @pytest.mark.asyncio
    async def test_unsupported_target_type(self, sample_data):
        """Test unsupported target type."""
        agent = DistributionAgent()
        
        config = TargetConfig(
            name='test_target',
            type='unsupported_type',
            batch_size=100
        )
        
        report = await agent.process(sample_data, [config])
        
        assert report.total_targets == 1
        assert report.failed_targets == 1
        assert 'Unsupported target type' in report.results[0].error


class TestLoadResult:
    """Test LoadResult dataclass."""
    
    def test_load_result_creation(self):
        """Test creating a LoadResult."""
        result = LoadResult(
            target='test_db',
            status='success',
            records_loaded=100,
            duration=1.5,
            tables_loaded=['users', 'orders']
        )
        
        assert result.target == 'test_db'
        assert result.status == 'success'
        assert result.records_loaded == 100
        assert result.duration == 1.5
        assert result.error is None
        assert len(result.tables_loaded) == 2


class TestDistributionReport:
    """Test DistributionReport dataclass."""
    
    def test_report_from_results(self):
        """Test creating report from results."""
        results = [
            LoadResult('db1', 'success', 100, 1.0),
            LoadResult('db2', 'success', 200, 2.0),
            LoadResult('db3', 'failed', 0, 0.5, error='Connection failed')
        ]
        
        report = DistributionReport.from_results(results)
        
        assert report.total_targets == 3
        assert report.successful_targets == 2
        assert report.failed_targets == 1
        assert report.total_records == 300
        assert len(report.results) == 3
