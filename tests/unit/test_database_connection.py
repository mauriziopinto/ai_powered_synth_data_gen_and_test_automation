"""Unit tests for database connection management."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import OperationalError
from shared.database.connection import DatabaseManager, get_db
import os


class TestDatabaseManager:
    """Test DatabaseManager class."""
    
    def test_init_with_connection_string(self):
        """Test initialization with explicit connection string."""
        conn_str = "postgresql://user:pass@localhost:5432/testdb"
        db_manager = DatabaseManager(connection_string=conn_str)
        
        assert db_manager.connection_string == conn_str
        assert db_manager.engine is not None
        assert db_manager.SessionLocal is not None
    
    def test_init_with_env_variable(self):
        """Test initialization using DATABASE_URL environment variable."""
        test_url = "postgresql://envuser:envpass@localhost:5432/envdb"
        with patch.dict(os.environ, {'DATABASE_URL': test_url}):
            db_manager = DatabaseManager()
            assert db_manager.connection_string == test_url
    
    def test_init_with_default_connection(self):
        """Test initialization with default connection string."""
        with patch.dict(os.environ, {}, clear=True):
            db_manager = DatabaseManager()
            expected = 'postgresql://postgres:postgres@localhost:5432/synthetic_data_generator'
            assert db_manager.connection_string == expected
    
    def test_engine_configuration(self):
        """Test that engine is configured with correct pool settings."""
        db_manager = DatabaseManager()
        
        # Check pool configuration
        assert db_manager.engine.pool.size() >= 0  # Pool exists
        # Engine should have pool_pre_ping enabled for connection health checks
        assert db_manager.engine.pool._pre_ping is True
    
    @patch('shared.database.connection.sessionmaker')
    @patch('shared.database.connection.create_engine')
    def test_get_session_success(self, mock_create_engine, mock_sessionmaker):
        """Test successful session creation and cleanup."""
        # Setup mocks
        mock_session = MagicMock()
        mock_session_class = MagicMock(return_value=mock_session)
        mock_sessionmaker.return_value = mock_session_class
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        db_manager = DatabaseManager()
        
        # Use context manager
        with db_manager.get_session() as session:
            assert session == mock_session
        
        # Verify session lifecycle
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.rollback.assert_not_called()
    
    @patch('shared.database.connection.sessionmaker')
    @patch('shared.database.connection.create_engine')
    def test_get_session_with_exception(self, mock_create_engine, mock_sessionmaker):
        """Test session rollback on exception."""
        # Setup mocks
        mock_session = MagicMock()
        mock_session_class = MagicMock(return_value=mock_session)
        mock_sessionmaker.return_value = mock_session_class
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        db_manager = DatabaseManager()
        
        # Simulate exception during session use
        with pytest.raises(ValueError):
            with db_manager.get_session() as session:
                raise ValueError("Test error")
        
        # Verify rollback was called
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.commit.assert_not_called()
    
    @patch('shared.database.connection.create_engine')
    def test_close(self, mock_create_engine):
        """Test closing database connections."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        db_manager = DatabaseManager()
        db_manager.close()
        
        mock_engine.dispose.assert_called_once()
    
    def test_get_db_dependency(self):
        """Test FastAPI dependency function."""
        # Get generator
        gen = get_db()
        
        # Get session from generator
        session = next(gen)
        assert session is not None
        
        # Close generator (simulates end of request)
        try:
            next(gen)
        except StopIteration:
            pass
        
        # Session should be closed after generator exits


@pytest.mark.unit
class TestDatabaseConnectionIntegration:
    """Integration-style tests for database connection (with mocked engine)."""
    
    @patch('shared.database.connection.create_engine')
    def test_connection_string_parsing(self, mock_create_engine):
        """Test that connection strings are properly parsed."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        test_cases = [
            "postgresql://user:pass@localhost:5432/db",
            "postgresql://user@localhost/db",
            "postgresql+psycopg2://user:pass@host:5433/db"
        ]
        
        for conn_str in test_cases:
            db_manager = DatabaseManager(connection_string=conn_str)
            assert db_manager.connection_string == conn_str
            mock_create_engine.assert_called()
    
    @patch('shared.database.connection.create_engine')
    def test_invalid_connection_string_handling(self, mock_create_engine):
        """Test handling of invalid connection strings."""
        mock_create_engine.side_effect = OperationalError("Connection failed", None, None)
        
        with pytest.raises(OperationalError):
            db_manager = DatabaseManager(connection_string="invalid://connection")
