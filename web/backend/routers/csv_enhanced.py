"""
Enhanced CSV upload router with parameter configuration support.
"""
import os
import csv
import tempfile
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import pandas as pd

router = APIRouter(prefix="/api/v1/csv", tags=["csv"])


def map_pandas_dtype_to_friendly_name(dtype_str: str) -> str:
    """Map pandas dtype to user-friendly type name.
    
    Args:
        dtype_str: String representation of pandas dtype
        
    Returns:
        User-friendly type name: 'string', 'integer', 'float', 'boolean', 'date', 'datetime'
    """
    dtype_lower = dtype_str.lower()
    
    # Integer types
    if 'int' in dtype_lower:
        return 'integer'
    
    # Float types
    if 'float' in dtype_lower or 'double' in dtype_lower:
        return 'float'
    
    # Boolean types
    if 'bool' in dtype_lower:
        return 'boolean'
    
    # Date/datetime types
    if 'datetime' in dtype_lower or 'timestamp' in dtype_lower:
        return 'datetime'
    if 'date' in dtype_lower:
        return 'date'
    
    # String/object types (default for text data)
    if 'object' in dtype_lower or 'string' in dtype_lower or 'str' in dtype_lower:
        return 'string'
    
    # Default to string for unknown types
    return 'string'


@router.post("/analyze")
async def analyze_csv(file: UploadFile = File(...)):
    """
    Analyze uploaded CSV file and return metadata.
    
    Returns:
        - row_count: Number of rows
        - column_count: Number of columns
        - columns: List of column info (name, type, sample values)
        - file_size: File size in bytes
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Analyze with pandas
        df = pd.read_csv(tmp_path)
        
        # Get column information
        columns = []
        for col in df.columns:
            pandas_dtype = str(df[col].dtype)
            friendly_dtype = map_pandas_dtype_to_friendly_name(pandas_dtype)
            
            col_info = {
                "name": col,
                "type": friendly_dtype,
                "null_count": int(df[col].isnull().sum()),
                "unique_count": int(df[col].nunique()),
                "sample_values": df[col].dropna().head(3).tolist() if not df[col].empty else []
            }
            
            # Add statistics for numeric columns
            if pd.api.types.is_numeric_dtype(df[col]):
                # Handle NaN/Inf values that aren't JSON serializable
                def safe_float(val):
                    if pd.isna(val) or val == float('inf') or val == float('-inf'):
                        return None
                    return float(val)
                
                col_info["statistics"] = {
                    "min": safe_float(df[col].min()) if not df[col].empty else None,
                    "max": safe_float(df[col].max()) if not df[col].empty else None,
                    "mean": safe_float(df[col].mean()) if not df[col].empty else None,
                    "median": safe_float(df[col].median()) if not df[col].empty else None,
                }
            
            columns.append(col_info)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": columns,
            "file_size": len(content),
            "has_header": True,  # Pandas assumes header by default
        }
        
    except Exception as e:
        # Clean up temp file if it exists
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to analyze CSV: {str(e)}")


@router.post("/upload-csv-enhanced")
async def upload_csv_enhanced(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    workflow_name: str = Form(...),
    sdv_model: str = Form("gaussian_copula"),
    bedrock_model: str = Form("anthropic.claude-3-sonnet-20240229-v1:0"),
    num_records: int = Form(100),
    edge_case_frequency: float = Form(0.1),
    preserve_edge_cases: bool = Form(True),
    random_seed: Optional[int] = Form(None),
    temperature: float = Form(0.7),
    max_tokens: int = Form(2000),
):
    """
    Upload CSV with full parameter configuration and start workflow.
    
    This endpoint accepts all the same parameters as manual configuration,
    allowing users to fully customize the synthetic data generation process.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Import here to avoid circular dependencies
        from shared.config.manager import ConfigurationManager, WorkflowConfiguration, ConfigurationMetadata
        from datetime import datetime
        from pathlib import Path
        import json
        
        # Save uploaded file with timestamp to avoid conflicts
        from datetime import datetime
        upload_dir = "data/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Add timestamp to filename to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = file.filename.rsplit('.', 1)[0]
        extension = file.filename.rsplit('.', 1)[1] if '.' in file.filename else 'csv'
        timestamped_filename = f"{base_name}_{timestamp}.{extension}"
        
        file_path = os.path.join(upload_dir, timestamped_filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Read CSV to infer schema
        df = pd.read_csv(file_path)
        
        # Build schema definition from CSV
        schema_definition = {
            "source_type": "csv",
            "source_path": file_path,
            "fields": []
        }
        
        for col in df.columns:
            field_def = {
                "name": col,
                "type": str(df[col].dtype),
                "nullable": bool(df[col].isnull().any()),
            }
            schema_definition["fields"].append(field_def)
        
        # Create configuration manager and generate ID
        config_manager = ConfigurationManager()
        config_id = config_manager.generate_config_id()
        
        # Create metadata
        metadata = ConfigurationMetadata(
            config_id=config_id,
            name=workflow_name,
            description=f"CSV upload workflow for {file.filename}",
            tags=["csv", "upload"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # Create full configuration
        config = WorkflowConfiguration(
            metadata=metadata,
            schema_definition=schema_definition,
            generation_parameters={
                "num_records": num_records,
                "sdv_model": sdv_model,
                "random_seed": random_seed,
            },
            edge_case_rules={
                "edge_case_frequency": edge_case_frequency,
                "preserve_edge_cases": preserve_edge_cases,
            },
            target_system_settings={
                "type": "synthetic_data",
                "bedrock_model": bedrock_model,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        
        # Save configuration
        config_manager.save(config)
        
        # Create workflow state (following the pattern from workflow.py)
        workflow_id = f"wf_csv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workflow_state = {
            'workflow_id': workflow_id,
            'status': 'running',
            'config_id': config_id,
            'num_records': num_records,
            'started_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'progress': 0.0,
            'current_stage': 'initializing',
            'stages_completed': [],
            'workflow_name': workflow_name,
            'source_file': file_path,  # Store full path, not just filename
            'original_filename': file.filename,  # Keep original name for display
            'configuration': {
                "sdv_model": sdv_model,
                "bedrock_model": bedrock_model,
                "num_records": num_records,
                "edge_case_frequency": edge_case_frequency,
                "preserve_edge_cases": preserve_edge_cases,
            },
            'agent_logs': []  # Store agent activity logs
        }
        
        # Save workflow state to disk and add to cache
        workflow_dir = Path("data/workflows")
        workflow_dir.mkdir(parents=True, exist_ok=True)
        workflow_file = workflow_dir / f"{workflow_id}.json"
        with open(workflow_file, 'w') as f:
            json.dump(workflow_state, f, indent=2)
        
        # Add to workflow cache so execute_csv_workflow can find it
        from web.backend.routers.workflow import workflow_states, execute_csv_workflow
        workflow_states[workflow_id] = workflow_state
        
        # Start background workflow execution
        background_tasks.add_task(execute_csv_workflow, workflow_id, Path(file_path), num_records)
        
        return {
            "workflow_id": workflow_id,
            "config_id": config_id,
            "status": "running",
            "message": "Workflow started successfully",
            "configuration": {
                "sdv_model": sdv_model,
                "bedrock_model": bedrock_model,
                "num_records": num_records,
                "edge_case_frequency": edge_case_frequency,
                "preserve_edge_cases": preserve_edge_cases,
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")
