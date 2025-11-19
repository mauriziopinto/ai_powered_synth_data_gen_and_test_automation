# Setup Instructions

## Quick Start

Run the automated setup script:

```bash
./scripts/setup.sh
```

This will:
1. Create a Python virtual environment
2. Install all dependencies
3. Create a .env configuration file
4. Verify PostgreSQL and AWS CLI installation

## Manual Setup

If you prefer to set up manually:

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Configure AWS Credentials

```bash
aws configure
```

Or set environment variables:
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

### 5. Set Up Database

Ensure PostgreSQL is running, then:

```bash
# Create database
createdb synthetic_data_generator

# Create tables
python scripts/setup_database.py create

# Verify setup
python scripts/setup_database.py verify
```

### 6. Verify Setup

```bash
python scripts/verify_setup.py
```

## Database Commands

```bash
# Create tables
python scripts/setup_database.py create

# Drop and recreate tables
python scripts/setup_database.py create --drop

# Drop all tables
python scripts/setup_database.py drop-all

# Verify database connection
python scripts/setup_database.py verify
```

## Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit -m unit

# Run property-based tests only
pytest tests/property -m property

# Run with coverage
pytest --cov=agents --cov=shared --cov-report=html
```

## Project Structure

```
synthetic-data-generator/
├── agents/                 # Strands-based AI agents
│   ├── data_processor/    # Identifies sensitive data
│   ├── synthetic_data/    # Generates synthetic data
│   ├── distribution/      # Distributes data to targets
│   ├── test_case/         # Creates test cases
│   └── test_execution/    # Executes tests
├── web/                   # Web application
│   ├── frontend/          # React UI
│   └── backend/           # FastAPI backend
├── shared/                # Shared libraries
│   ├── models/            # Data models
│   ├── database/          # Database utilities
│   └── utils/             # Common utilities
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   └── property/          # Property-based tests
├── data/                  # Data storage
├── results/               # Execution results
├── config/                # Configuration files
└── scripts/               # Setup and utility scripts
```

## Troubleshooting

### PostgreSQL Connection Issues

If you get database connection errors:

1. Ensure PostgreSQL is running:
   ```bash
   # macOS
   brew services start postgresql
   
   # Linux
   sudo systemctl start postgresql
   ```

2. Check connection string in .env:
   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/synthetic_data_generator
   ```

3. Create database if it doesn't exist:
   ```bash
   createdb synthetic_data_generator
   ```

### AWS Credentials Issues

If you get AWS credential errors:

1. Verify credentials are configured:
   ```bash
   aws sts get-caller-identity
   ```

2. Check Bedrock access:
   ```bash
   aws bedrock list-foundation-models --region us-east-1
   ```

3. Ensure your AWS account has Bedrock access enabled

### Import Errors

If you get module import errors:

1. Ensure virtual environment is activated:
   ```bash
   source venv/bin/activate
   ```

2. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Verify Python path includes project root

## Next Steps

After setup is complete:

1. Review the requirements document: `.kiro/specs/synthetic-data-generator/requirements.md`
2. Review the design document: `.kiro/specs/synthetic-data-generator/design.md`
3. Start implementing tasks from: `.kiro/specs/synthetic-data-generator/tasks.md`
4. Begin with task 2: "Implement core data models and utilities"
