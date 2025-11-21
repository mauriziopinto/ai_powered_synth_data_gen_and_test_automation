"""Tests for data loading utilities."""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import json

from shared.utils.data_loader import DataLoader

# Check if pyarrow is available
try:
    import pyarrow
    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False


class TestDataLoaderCSV:
    """Test CSV loading functionality."""
    
    def test_load_csv_basic(self, tmp_path):
        """Test loading a basic CSV file."""
        # Create test CSV
        csv_file = tmp_path / "test.csv"
        df_original = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        df_original.to_csv(csv_file, index=False)
        
        # Load and verify
        df_loaded = DataLoader.load_csv(csv_file)
        
        assert len(df_loaded) == 3
        assert list(df_loaded.columns) == ['col1', 'col2']
        pd.testing.assert_frame_equal(df_loaded, df_original)
    
    def test_load_csv_with_na_values(self, tmp_path):
        """Test loading CSV with NA values."""
        csv_file = tmp_path / "test_na.csv"
        with open(csv_file, 'w') as f:
            f.write('col1,col2\n1,a\n,b\n3,NA\n')
        
        df = DataLoader.load_csv(csv_file)
        
        assert df['col1'].isna().sum() == 1
        assert df['col2'].isna().sum() == 1
    
    def test_load_csv_file_not_found(self):
        """Test loading non-existent CSV file."""
        with pytest.raises(FileNotFoundError):
            DataLoader.load_csv('nonexistent.csv')
    
    def test_save_csv(self, tmp_path):
        """Test saving DataFrame to CSV."""
        df = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})
        csv_file = tmp_path / "output.csv"
        
        DataLoader.save_csv(df, csv_file)
        
        assert csv_file.exists()
        df_loaded = pd.read_csv(csv_file)
        pd.testing.assert_frame_equal(df_loaded, df)


class TestDataLoaderJSON:
    """Test JSON loading functionality."""
    
    def test_load_json_records(self, tmp_path):
        """Test loading JSON file with records orientation."""
        json_file = tmp_path / "test.json"
        data = [
            {'col1': 1, 'col2': 'a'},
            {'col1': 2, 'col2': 'b'}
        ]
        with open(json_file, 'w') as f:
            json.dump(data, f)
        
        df = DataLoader.load_json(json_file, orient='records')
        
        assert len(df) == 2
        assert list(df.columns) == ['col1', 'col2']
    
    def test_load_json_file_not_found(self):
        """Test loading non-existent JSON file."""
        with pytest.raises(FileNotFoundError):
            DataLoader.load_json('nonexistent.json')
    
    def test_save_json(self, tmp_path):
        """Test saving DataFrame to JSON."""
        df = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})
        json_file = tmp_path / "output.json"
        
        DataLoader.save_json(df, json_file)
        
        assert json_file.exists()
        df_loaded = pd.read_json(json_file, orient='records')
        pd.testing.assert_frame_equal(df_loaded, df)


class TestDataLoaderParquet:
    """Test Parquet loading functionality."""
    
    @pytest.mark.skipif(not HAS_PYARROW, reason="pyarrow not installed")
    def test_load_parquet_basic(self, tmp_path):
        """Test loading a basic Parquet file."""
        parquet_file = tmp_path / "test.parquet"
        df_original = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        df_original.to_parquet(parquet_file, index=False)
        
        df_loaded = DataLoader.load_parquet(parquet_file)
        
        assert len(df_loaded) == 3
        pd.testing.assert_frame_equal(df_loaded, df_original)
    
    def test_load_parquet_file_not_found(self):
        """Test loading non-existent Parquet file."""
        with pytest.raises(FileNotFoundError):
            DataLoader.load_parquet('nonexistent.parquet')
    
    @pytest.mark.skipif(not HAS_PYARROW, reason="pyarrow not installed")
    def test_save_parquet(self, tmp_path):
        """Test saving DataFrame to Parquet."""
        df = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})
        parquet_file = tmp_path / "output.parquet"
        
        DataLoader.save_parquet(df, parquet_file)
        
        assert parquet_file.exists()
        df_loaded = pd.read_parquet(parquet_file)
        pd.testing.assert_frame_equal(df_loaded, df)


class TestDataLoaderAutoDetect:
    """Test auto-detection of file formats."""
    
    def test_load_data_auto_detect_csv(self, tmp_path):
        """Test auto-detecting CSV format."""
        csv_file = tmp_path / "test.csv"
        df_original = pd.DataFrame({'col1': [1, 2]})
        df_original.to_csv(csv_file, index=False)
        
        df_loaded = DataLoader.load_data(csv_file)
        
        pd.testing.assert_frame_equal(df_loaded, df_original)
    
    def test_load_data_auto_detect_json(self, tmp_path):
        """Test auto-detecting JSON format."""
        json_file = tmp_path / "test.json"
        data = [{'col1': 1}, {'col1': 2}]
        with open(json_file, 'w') as f:
            json.dump(data, f)
        
        df_loaded = DataLoader.load_data(json_file)
        
        assert len(df_loaded) == 2
    
    @pytest.mark.skipif(not HAS_PYARROW, reason="pyarrow not installed")
    def test_load_data_auto_detect_parquet(self, tmp_path):
        """Test auto-detecting Parquet format."""
        parquet_file = tmp_path / "test.parquet"
        df_original = pd.DataFrame({'col1': [1, 2]})
        df_original.to_parquet(parquet_file, index=False)
        
        df_loaded = DataLoader.load_data(parquet_file)
        
        pd.testing.assert_frame_equal(df_loaded, df_original)
    
    def test_load_data_unsupported_format(self, tmp_path):
        """Test loading file with unsupported format."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("some text")
        
        with pytest.raises(ValueError, match="Cannot determine file format"):
            DataLoader.load_data(txt_file)
    
    def test_load_data_explicit_format(self, tmp_path):
        """Test loading with explicit format specification."""
        # Create CSV but specify format explicitly
        csv_file = tmp_path / "test.data"
        df_original = pd.DataFrame({'col1': [1, 2]})
        df_original.to_csv(csv_file, index=False)
        
        df_loaded = DataLoader.load_data(csv_file, file_format='csv')
        
        pd.testing.assert_frame_equal(df_loaded, df_original)


class TestDataProfile:
    """Test data profiling functionality."""
    
    def test_get_data_profile_numeric(self):
        """Test profiling numeric data."""
        df = pd.DataFrame({
            'age': [25, 30, 35, 40, None],
            'score': [85.5, 90.0, 88.5, 92.0, 87.5]
        })
        
        profile = DataLoader.get_data_profile(df)
        
        assert 'age' in profile
        assert 'score' in profile
        assert profile['age']['count'] == 4
        assert profile['age']['null_count'] == 1
        assert 'mean' in profile['age']
        assert 'std' in profile['age']
    
    def test_get_data_profile_string(self):
        """Test profiling string data."""
        df = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie', None],
            'email': ['a@test.com', 'b@test.com', 'c@test.com', 'd@test.com']
        })
        
        profile = DataLoader.get_data_profile(df)
        
        assert 'name' in profile
        assert profile['name']['count'] == 3
        assert profile['name']['null_count'] == 1
        assert 'avg_length' in profile['name']
        assert 'min_length' in profile['name']
        assert 'max_length' in profile['name']
    
    def test_get_data_profile_mixed_types(self):
        """Test profiling mixed data types."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'active': [True, False, True]
        })
        
        profile = DataLoader.get_data_profile(df)
        
        assert len(profile) == 3
        assert all(col in profile for col in df.columns)
        assert all('dtype' in profile[col] for col in df.columns)
        assert all('unique_count' in profile[col] for col in df.columns)
