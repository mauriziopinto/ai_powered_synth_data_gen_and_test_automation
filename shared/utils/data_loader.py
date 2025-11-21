"""Utility functions for loading data from various file formats."""

from pathlib import Path
from typing import Union, Optional, Dict, Any
import pandas as pd
import json


class DataLoader:
    """Utility class for loading data from various file formats."""
    
    @staticmethod
    def load_csv(
        file_path: Union[str, Path],
        encoding: str = 'utf-8',
        **kwargs
    ) -> pd.DataFrame:
        """Load data from CSV file.
        
        Args:
            file_path: Path to CSV file
            encoding: File encoding (default: utf-8)
            **kwargs: Additional arguments passed to pd.read_csv
            
        Returns:
            DataFrame containing the loaded data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be parsed
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        try:
            # Default parameters for robust CSV parsing
            default_params = {
                'encoding': encoding,
                'low_memory': False,
                'na_values': ['', 'NA', 'N/A', 'null', 'NULL', 'None'],
                'keep_default_na': True
            }
            
            # Merge with user-provided kwargs
            params = {**default_params, **kwargs}
            
            df = pd.read_csv(file_path, **params)
            
            return df
            
        except Exception as e:
            raise ValueError(f"Failed to parse CSV file {file_path}: {str(e)}")
    
    @staticmethod
    def load_json(
        file_path: Union[str, Path],
        orient: str = 'records',
        **kwargs
    ) -> pd.DataFrame:
        """Load data from JSON file.
        
        Args:
            file_path: Path to JSON file
            orient: JSON orientation ('records', 'index', 'columns', 'values', 'split', 'table')
            **kwargs: Additional arguments passed to pd.read_json
            
        Returns:
            DataFrame containing the loaded data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be parsed
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        
        try:
            df = pd.read_json(file_path, orient=orient, **kwargs)
            return df
            
        except Exception as e:
            raise ValueError(f"Failed to parse JSON file {file_path}: {str(e)}")
    
    @staticmethod
    def load_parquet(
        file_path: Union[str, Path],
        **kwargs
    ) -> pd.DataFrame:
        """Load data from Parquet file.
        
        Args:
            file_path: Path to Parquet file
            **kwargs: Additional arguments passed to pd.read_parquet
            
        Returns:
            DataFrame containing the loaded data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be parsed
            ImportError: If pyarrow or fastparquet not installed
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Parquet file not found: {file_path}")
        
        try:
            df = pd.read_parquet(file_path, **kwargs)
            return df
            
        except ImportError as e:
            raise ImportError(
                "Parquet support requires pyarrow or fastparquet. "
                "Install with: pip install pyarrow"
            ) from e
        except Exception as e:
            raise ValueError(f"Failed to parse Parquet file {file_path}: {str(e)}")
    
    @staticmethod
    def load_data(
        file_path: Union[str, Path],
        file_format: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """Load data from file, auto-detecting format if not specified.
        
        Args:
            file_path: Path to data file
            file_format: File format ('csv', 'json', 'parquet'). If None, auto-detect from extension
            **kwargs: Additional arguments passed to format-specific loader
            
        Returns:
            DataFrame containing the loaded data
            
        Raises:
            ValueError: If format cannot be determined or is unsupported
        """
        file_path = Path(file_path)
        
        # Auto-detect format from extension if not specified
        if file_format is None:
            extension = file_path.suffix.lower()
            format_map = {
                '.csv': 'csv',
                '.json': 'json',
                '.jsonl': 'json',
                '.parquet': 'parquet',
                '.pq': 'parquet'
            }
            file_format = format_map.get(extension)
            
            if file_format is None:
                raise ValueError(
                    f"Cannot determine file format from extension: {extension}. "
                    f"Supported formats: {list(format_map.values())}"
                )
        
        # Load using appropriate method
        loaders = {
            'csv': DataLoader.load_csv,
            'json': DataLoader.load_json,
            'parquet': DataLoader.load_parquet
        }
        
        loader = loaders.get(file_format.lower())
        if loader is None:
            raise ValueError(
                f"Unsupported file format: {file_format}. "
                f"Supported formats: {list(loaders.keys())}"
            )
        
        return loader(file_path, **kwargs)
    
    @staticmethod
    def save_csv(
        df: pd.DataFrame,
        file_path: Union[str, Path],
        encoding: str = 'utf-8',
        **kwargs
    ) -> None:
        """Save DataFrame to CSV file.
        
        Args:
            df: DataFrame to save
            file_path: Output file path
            encoding: File encoding (default: utf-8)
            **kwargs: Additional arguments passed to df.to_csv
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_params = {
            'index': False,
            'encoding': encoding
        }
        params = {**default_params, **kwargs}
        
        df.to_csv(file_path, **params)
    
    @staticmethod
    def save_json(
        df: pd.DataFrame,
        file_path: Union[str, Path],
        orient: str = 'records',
        **kwargs
    ) -> None:
        """Save DataFrame to JSON file.
        
        Args:
            df: DataFrame to save
            file_path: Output file path
            orient: JSON orientation
            **kwargs: Additional arguments passed to df.to_json
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_params = {
            'orient': orient,
            'indent': 2
        }
        params = {**default_params, **kwargs}
        
        df.to_json(file_path, **params)
    
    @staticmethod
    def save_parquet(
        df: pd.DataFrame,
        file_path: Union[str, Path],
        **kwargs
    ) -> None:
        """Save DataFrame to Parquet file.
        
        Args:
            df: DataFrame to save
            file_path: Output file path
            **kwargs: Additional arguments passed to df.to_parquet
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_parquet(file_path, **kwargs)
    
    @staticmethod
    def get_data_profile(df: pd.DataFrame) -> Dict[str, Any]:
        """Generate a statistical profile of the DataFrame.
        
        Args:
            df: DataFrame to profile
            
        Returns:
            Dictionary containing profile information for each column
        """
        profile = {}
        
        for column in df.columns:
            col_data = df[column]
            
            col_profile = {
                'dtype': str(col_data.dtype),
                'count': int(col_data.count()),
                'null_count': int(col_data.isna().sum()),
                'null_percentage': float(col_data.isna().sum() / len(col_data) * 100),
                'unique_count': int(col_data.nunique()),
                'sample_values': col_data.dropna().head(10).tolist()
            }
            
            # Add numeric statistics if applicable
            if pd.api.types.is_numeric_dtype(col_data):
                col_profile.update({
                    'mean': float(col_data.mean()) if not col_data.isna().all() else None,
                    'std': float(col_data.std()) if not col_data.isna().all() else None,
                    'min': float(col_data.min()) if not col_data.isna().all() else None,
                    'max': float(col_data.max()) if not col_data.isna().all() else None,
                    'median': float(col_data.median()) if not col_data.isna().all() else None
                })
            
            # Add string statistics if applicable
            elif pd.api.types.is_string_dtype(col_data) or col_data.dtype == 'object':
                non_null = col_data.dropna()
                if len(non_null) > 0:
                    col_profile.update({
                        'avg_length': float(non_null.astype(str).str.len().mean()),
                        'min_length': int(non_null.astype(str).str.len().min()),
                        'max_length': int(non_null.astype(str).str.len().max())
                    })
            
            profile[column] = col_profile
        
        return profile
