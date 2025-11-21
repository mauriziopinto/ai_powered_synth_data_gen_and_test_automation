# Unit Tests

This directory contains unit tests for the Synthetic Data Generator project setup.

## Test Coverage

### Completed Tests

1. **test_database_connection.py** - Tests for database connection management
   - Connection string handling
   - Environment variable configuration
   - Session management and cleanup
   - FastAPI dependency injection

2. **test_aws_config.py** - Tests for AWS configuration and credentials
   - AWS region and profile configuration
   - Client creation (Bedrock, S3, Secrets Manager)
   - Credential verification
   - Bedrock access verification

3. **test_environment_config.py** - Tests for environment variable loading
   - Database URL configuration
   - AWS configuration variables
   - Bedrock model settings
   - Application configuration
   - Boolean, numeric, and list parsing

### Schema Tests

The `test_database_schema.py` file is currently skipped because it requires PostgreSQL-specific features (JSONB and ARRAY types) that are not supported by SQLite used in unit tests.

To run schema tests, you need:
- A PostgreSQL database instance
- Update the test to use PostgreSQL instead of SQLite

## Running Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all unit tests
python -m pytest tests/unit/ -v

# Run specific test file
python -m pytest tests/unit/test_database_connection.py -v

# Run with coverage
python -m pytest tests/unit/ --cov=shared --cov-report=html
```

## Test Results

- **51 tests passing**
- **100% coverage** for database connection module
- **100% coverage** for AWS configuration module
