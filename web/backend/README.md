# Synthetic Data Generator - Backend API

FastAPI-based REST API for the Synthetic Data Generator web application.

## Features

- **Configuration Management**: Create, read, update, delete workflow configurations
- **Workflow Control**: Start, pause, resume, abort workflow executions
- **Real-time Monitoring**: WebSocket support for live workflow updates
- **Results Access**: Quality reports, test results, data export
- **Audit Logging**: Comprehensive audit trail for compliance

## Requirements

- Python 3.9+
- FastAPI
- Uvicorn
- WebSockets

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# From project root (recommended)
uv run uvicorn web.backend.main:app --reload --host 0.0.0.0 --port 8000

# Or from web/backend directory
python main.py
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Configuration
- `POST /api/v1/config/` - Create configuration
- `GET /api/v1/config/` - List configurations
- `GET /api/v1/config/{config_id}` - Get configuration
- `PUT /api/v1/config/{config_id}` - Update configuration
- `DELETE /api/v1/config/{config_id}` - Delete configuration
- `POST /api/v1/config/validate` - Validate configuration

### Workflow
- `POST /api/v1/workflow/start` - Start workflow
- `POST /api/v1/workflow/{workflow_id}/pause` - Pause workflow
- `POST /api/v1/workflow/{workflow_id}/resume` - Resume workflow
- `POST /api/v1/workflow/{workflow_id}/abort` - Abort workflow
- `GET /api/v1/workflow/{workflow_id}/status` - Get workflow status
- `GET /api/v1/workflow/` - List workflows

### Monitoring
- `GET /api/v1/monitoring/agents/{workflow_id}` - Get agent status
- `GET /api/v1/monitoring/metrics` - Get system metrics

### Results
- `GET /api/v1/results/{workflow_id}/quality` - Get quality report
- `GET /api/v1/results/{workflow_id}/samples` - Get data samples
- `POST /api/v1/results/{workflow_id}/export` - Export data
- `GET /api/v1/results/{workflow_id}/test-results` - Get test results

### Audit
- `GET /api/v1/audit/logs` - Get audit logs
- `GET /api/v1/audit/logs/{workflow_id}` - Get workflow audit logs
- `POST /api/v1/audit/logs/export` - Export audit logs

### WebSocket
- `WS /ws` - Real-time updates

## WebSocket Messages

The WebSocket endpoint sends real-time updates about workflow execution:

```json
{
  "type": "workflow_update",
  "workflow_id": "wf_20240101_120000",
  "status": "running",
  "progress": 0.65,
  "current_stage": "generating_data",
  "message": "Generated 650/1000 records"
}
```

## Architecture

```
web/backend/
├── main.py                 # FastAPI application entry point
├── websocket_manager.py    # WebSocket connection management
├── routers/
│   ├── configuration.py    # Configuration endpoints
│   ├── workflow.py         # Workflow control endpoints
│   ├── monitoring.py       # Monitoring endpoints
│   ├── results.py          # Results endpoints
│   └── audit.py            # Audit endpoints
└── requirements.txt        # Python dependencies
```

## Integration

The backend integrates with:
- `shared/config/manager.py` - Configuration management
- `shared/orchestration/workflow.py` - Workflow execution
- `shared/export/exporter.py` - Data export
- `shared/utils/cost_tracker.py` - Cost tracking

## Validation

Validates Requirements:
- 11.1: Web-based user interface for complete configuration
- 11.2: Interactive forms with real-time validation
- 11.3: Real-time monitoring and updates via WebSocket
- 11.4: Preview samples and download options
- 11.5: Visual representations and quality metrics
