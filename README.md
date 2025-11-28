# Synthetic Data Generator with MCP Distribution

An agent-based system that orchestrates a complete end-to-end testing workflow from synthetic data generation through test execution and reporting.

## Workflow Overview

The system follows a 5-step workflow:

1. **Configuration** - Define data schema and generation rules
2. **Synthetic Data Generation** - AI generates realistic test data matching your schema
3. **AI Distribution** - An agent distributes data to external systems (databases, APIs, Jira, Salesforce) using natural language instructions and MCP servers
4. **Test Synthesis** - (Coming Soon) Automatic test case generation
5. **Agentic Test Execution** - (Coming Soon) Agentic test execution and validation


[![Demo Video](https://img.youtube.com/vi/UgZR5nL6mtA/0.jpg)](https://www.youtube.com/watch?v=UgZR5nL6mtA)


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

5. Run the application:
```bash
# Start backend (from project root)
uv run uvicorn web.backend.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (in another terminal)
cd web/frontend
npm install
npm run dev
```

## Workflow Persistence

✅ **Workflows are automatically saved to disk and persist across server restarts!**

All workflow executions are automatically saved to `data/workflows/` as JSON files. This means:
- No data loss on server restart or crash
- Complete workflow history preserved
- Easy debugging and audit trail
- No database setup required for basic persistence

## Requirements

- Python 3.10
- uv (Python package manager)
- PostgreSQL 13+ (optional - workflows use file-based persistence)
- Node.js 16+
- AWS Account with Bedrock access