# CSV Upload & Persistent Storage Guide

## ✅ Feature 1: Persistent Workflow Storage

All workflows are now automatically saved to disk using SQLite database.

### Database Location
- **File**: `workflows.db` (in project root)
- **Tables**: 
  - `workflows` - Stores workflow metadata and status
  - `agent_status` - Tracks individual agent progress

### Benefits
- ✅ Workflows survive server restarts
- ✅ Historical workflow data preserved
- ✅ Query workflows by status, date, etc.
- ✅ Agent-level tracking and monitoring

### API Endpoints
```bash
# List all workflows
GET /api/v1/workflow/

# Get specific workflow
GET /api/v1/workflow/{workflow_id}/status

# Get workflow agents
GET /api/v1/workflow/{workflow_id}/agents
```

---

## ✅ Feature 2: CSV Upload for Synthetic Data Generation

Upload a CSV file to automatically generate synthetic data matching its structure.

### How It Works

1. **Upload CSV**: Select and upload your CSV file
2. **Auto-Analysis**: System analyzes schema, data types, and patterns
3. **Workflow Creation**: Automatically creates a workflow configuration
4. **Synthetic Generation**: Generates synthetic data matching your CSV structure
5. **Results**: Download or distribute synthetic data

### Using the Web Interface

1. Navigate to **Configuration** page
2. Look for the **"Quick Start: CSV Upload"** section at the top
3. Click **"Select CSV File"** and choose your file
4. Set the number of records to generate (default: 100)
5. Optionally name your workflow
6. Click **"Upload & Start Workflow"**
7. You'll be redirected to the workflow monitoring page

### Using the API

```bash
# Upload CSV and start workflow
curl -X POST "http://localhost:8000/api/v1/workflow/upload-csv" \
  -F "file=@your_data.csv" \
  -F "num_records=500" \
  -F "workflow_name=My Synthetic Data"
```

**Response:**
```json
{
  "workflow_id": "wf_csv_20251120_072331",
  "status": "running",
  "config_id": "csv_your_data_20251120_072331",
  "num_records": 500,
  "started_at": "2025-11-20T07:23:31.890883",
  "updated_at": "2025-11-20T07:23:31.890889",
  "progress": 0.0,
  "current_stage": "analyzing_csv",
  "message": "CSV uploaded successfully. Analyzing 100 rows with 15 columns."
}
```

### What Gets Analyzed

When you upload a CSV, the system automatically:

- ✅ **Column Names**: Preserves original column names
- ✅ **Data Types**: Detects numeric, string, date, boolean types
- ✅ **Row Count**: Records original dataset size
- ✅ **Sample Data**: Captures first 3 rows for pattern analysis
- ✅ **File Storage**: Saves uploaded file to `data/uploads/`

### Example: Healthcare Data

```bash
# Upload healthcare patient data
curl -X POST "http://localhost:8000/api/v1/workflow/upload-csv" \
  -F "file=@data/demo/healthcare_patients.csv" \
  -F "num_records=1000" \
  -F "workflow_name=Synthetic Healthcare Patients"
```

This will:
1. Analyze the 23 columns in the healthcare CSV
2. Detect data types (patient_id, age, diagnosis, etc.)
3. Generate 1000 synthetic patient records
4. Maintain statistical properties of the original data

### Example: Financial Transactions

```bash
# Upload financial transaction data
curl -X POST "http://localhost:8000/api/v1/workflow/upload-csv" \
  -F "file=@data/demo/finance_transactions.csv" \
  -F "num_records=5000"
```

### Supported CSV Formats

- ✅ Standard CSV with headers
- ✅ Comma-separated values
- ✅ UTF-8 encoding
- ✅ Various data types (numeric, string, date)
- ✅ Files up to 100MB (configurable)

### File Storage

Uploaded files are saved to:
```
data/uploads/{timestamp}_{original_filename}.csv
```

Example:
```
data/uploads/20251120_072331_healthcare_patients.csv
```

### Workflow Monitoring

After upload, monitor your workflow:

1. **Web UI**: Navigate to `/workflow/{workflow_id}`
2. **API**: `GET /api/v1/workflow/{workflow_id}/status`

You'll see:
- Real-time progress updates
- Agent pipeline visualization
- Current processing stage
- Estimated completion time
- Cost tracking

### Error Handling

The system validates:
- ✅ File must be CSV format
- ✅ CSV must not be empty
- ✅ CSV must be parseable
- ✅ Reasonable file size

Error responses:
```json
{
  "detail": "Only CSV files are supported"
}
```

### Integration with Existing Agents

The CSV upload integrates with:

1. **Data Processor Agent**: Analyzes CSV schema and patterns
2. **Synthetic Data Agent**: Generates matching synthetic data
3. **Distribution Agent**: Distributes to target systems
4. **Test Execution Agent**: Validates synthetic data quality

### Next Steps

After uploading a CSV:

1. ✅ Monitor workflow progress
2. ✅ View agent pipeline
3. ✅ Download synthetic results
4. ✅ Configure distribution targets
5. ✅ Run quality validation tests

### Tips for Best Results

- **Clean Data**: Remove duplicates and fix formatting issues
- **Representative Sample**: Upload a sample that represents your full dataset
- **Column Names**: Use clear, descriptive column names
- **Data Types**: Ensure consistent data types per column
- **Size**: Start with smaller files (< 10MB) for testing

### Troubleshooting

**Issue**: "CSV file is empty"
- **Solution**: Ensure CSV has headers and at least one data row

**Issue**: "Failed to parse CSV"
- **Solution**: Check for proper CSV formatting, encoding issues

**Issue**: "Upload timeout"
- **Solution**: Try smaller file or increase timeout settings

### API Reference

#### Upload CSV Endpoint

```
POST /api/v1/workflow/upload-csv
```

**Parameters:**
- `file` (required): CSV file to upload
- `num_records` (optional): Number of synthetic records (default: 100)
- `workflow_name` (optional): Custom workflow name

**Response:**
- `workflow_id`: Unique workflow identifier
- `status`: Current workflow status
- `config_id`: Generated configuration ID
- `message`: Success message with analysis details

---

## Testing the Features

### Test Persistent Storage

```bash
# Start a workflow
curl -X POST "http://localhost:8000/api/v1/workflow/start" \
  -H "Content-Type: application/json" \
  -d '{"config_id": "test-001", "num_records": 100}'

# Restart the server
# Workflows will still be available!

# List workflows
curl "http://localhost:8000/api/v1/workflow/"
```

### Test CSV Upload

```bash
# Upload demo healthcare data
curl -X POST "http://localhost:8000/api/v1/workflow/upload-csv" \
  -F "file=@data/demo/healthcare_patients.csv" \
  -F "num_records=50"

# Check workflow status
curl "http://localhost:8000/api/v1/workflow/wf_csv_TIMESTAMP/status"

# View in browser
open http://localhost:3000/workflow/wf_csv_TIMESTAMP
```

---

## Architecture

### Database Schema

```sql
-- Workflows table
CREATE TABLE workflows (
    workflow_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    config_id TEXT NOT NULL,
    num_records INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT,
    progress REAL DEFAULT 0.0,
    current_stage TEXT,
    stages_completed TEXT,
    error TEXT,
    cost_usd REAL DEFAULT 0.0
);

-- Agent status table
CREATE TABLE agent_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    status TEXT NOT NULL,
    current_operation TEXT,
    progress REAL DEFAULT 0.0,
    message TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (workflow_id) REFERENCES workflows (workflow_id)
);
```

### File Structure

```
deliverables/
├── workflows.db              # SQLite database (auto-created)
├── data/
│   └── uploads/              # Uploaded CSV files
│       └── {timestamp}_{filename}.csv
├── web/
│   ├── backend/
│   │   ├── database.py       # Database management
│   │   └── routers/
│   │       └── workflow.py   # CSV upload endpoint
│   └── frontend/
│       └── src/
│           └── components/
│               └── configuration/
│                   └── CSVUploader.tsx  # Upload UI
```

---

## Future Enhancements

Potential improvements:

- [ ] Support for Excel files (.xlsx)
- [ ] Support for JSON files
- [ ] Batch CSV upload (multiple files)
- [ ] CSV preview before upload
- [ ] Advanced schema mapping UI
- [ ] Custom data type overrides
- [ ] Statistical distribution matching
- [ ] Data quality scoring
- [ ] Export workflow configurations
- [ ] Workflow templates from CSV

---

## Summary

Both features are now fully implemented:

1. ✅ **Persistent Storage**: All workflows saved to SQLite database
2. ✅ **CSV Upload**: Upload CSV files to trigger synthetic data generation

Access the features:
- **Web UI**: http://localhost:3000/configuration
- **API Docs**: http://localhost:8000/docs
- **Database**: `workflows.db` in project root
- **Uploads**: `data/uploads/` directory
