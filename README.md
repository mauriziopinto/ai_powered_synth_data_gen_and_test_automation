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

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure AWS credentials:
```bash
aws configure
```

4. Set up database:
```bash
python scripts/setup_database.py
```

5. Run the application:
```bash
# Start backend
cd web/backend
uvicorn main:app --reload

# Start frontend (in another terminal)
cd web/frontend
npm install
npm start
```

## Requirements

- Python 3.9+
- PostgreSQL 13+
- Node.js 16+
- AWS Account with Bedrock access

## License

Proprietary
