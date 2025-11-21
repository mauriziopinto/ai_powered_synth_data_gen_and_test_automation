# Synthetic Data Generator

An intelligent, agent-based system that orchestrates a complete end-to-end testing workflow from production data ingestion through test execution and reporting.

## Project Structure

```
synthetic-data-generator/
├── agents/                 # Strands-based AI agents
│   ├── data_processor/    # Identifies sensitive data
│   ├── synthetic_data/    # Generates synthetic data
│   ├── distribution/      # Distributes data to targets
│   ├── test_case/         # Creates test cases
│   └── test_execution/    # Executes tests
├── web/                   # React web application
│   ├── frontend/          # React UI
│   └── backend/           # FastAPI backend
├── shared/                # Shared libraries and utilities
│   ├── models/            # Data models
│   ├── database/          # Database utilities
│   └── utils/             # Common utilities
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   └── property/          # Property-based tests
├── data/                  # Data storage
│   ├── production/        # Production data samples
│   └── synthetic/         # Generated synthetic data
├── results/               # Execution results
└── config/                # Configuration files
```

## Setup

1. Install uv (Python package manager):
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

2. Create and activate virtual environment with Python 3.10:
```bash
# Create venv with uv (automatically uses Python 3.10)
uv venv --python 3.10

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
uv pip install -r requirements.txt
```

4. Configure environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your configuration:
# - AWS credentials (AWS_REGION, AWS_PROFILE or AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY)
# - Bedrock model settings (BEDROCK_MODEL_ID, BEDROCK_TEMPERATURE)
# - Database URL (if using PostgreSQL)
# - Optional: Confluence/Jira credentials for demo mode
```

5. Set up database (optional):
```bash
python scripts/setup_database.py
```

6. Run the application:
```bash
# Start backend (from project root)
uv run uvicorn web.backend.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (in another terminal)
cd web/frontend
npm install
npm start
```

## Workflow Persistence

✅ **Workflows are automatically saved to disk and persist across server restarts!**

All workflow executions are automatically saved to `data/workflows/` as JSON files. This means:
- No data loss on server restart or crash
- Complete workflow history preserved
- Easy debugging and audit trail
- No database setup required for basic persistence

For more information:
- Quick Start: See `WORKFLOW_PERSISTENCE_QUICKSTART.md`
- User Guide: See `WORKFLOW_PERSISTENCE_USER_GUIDE.md`
- Technical Details: See `WORKFLOW_PERSISTENCE_COMPLETE.md`

## Requirements

- Python 3.10
- uv (Python package manager)
- PostgreSQL 13+ (optional - workflows use file-based persistence)
- Node.js 16+
- AWS Account with Bedrock access
