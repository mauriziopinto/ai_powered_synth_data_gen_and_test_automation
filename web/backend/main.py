"""FastAPI backend for Synthetic Data Generator web application.

This module provides REST API endpoints and WebSocket support for:
- Configuration management
- Workflow execution control
- Real-time monitoring
- Results retrieval
- Audit logging

Validates Requirements 11.1, 11.2, 11.3
"""

import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
logging.info(f"Loaded environment variables from {env_path}")

from web.backend.routers import (
    configuration,
    workflow,
    monitoring,
    results,
    audit,
    demo,
    csv_enhanced,
    cost_estimation,
    targets,
    mock_targets,
    mcp_config,
    mcp_distribution
)
from web.backend.websocket_manager import WebSocketManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# WebSocket manager for real-time updates
ws_manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Synthetic Data Generator API")
    yield
    logger.info("Shutting down Synthetic Data Generator API")
    await ws_manager.disconnect_all()


# Create FastAPI application
app = FastAPI(
    title="Synthetic Data Generator API",
    description="REST API for synthetic data generation, workflow management, and monitoring",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set WebSocket manager in workflow router for agent logging
workflow.set_websocket_manager(ws_manager)

# Include routers
app.include_router(
    configuration.router,
    prefix="/api/v1/config",
    tags=["configuration"]
)
app.include_router(
    workflow.router,
    prefix="/api/v1/workflow",
    tags=["workflow"]
)
app.include_router(
    monitoring.router,
    prefix="/api/v1/monitoring",
    tags=["monitoring"]
)
app.include_router(
    results.router,
    prefix="/api/v1/results",
    tags=["results"]
)
app.include_router(
    audit.router,
    prefix="/api/v1/audit",
    tags=["audit"]
)
app.include_router(
    demo.router,
    prefix="/api/v1",
    tags=["demo"]
)
app.include_router(
    csv_enhanced.router,
    tags=["csv"]
)
app.include_router(
    cost_estimation.router,
    tags=["cost-estimation"]
)
app.include_router(
    targets.router,
    prefix="/api/v1",
    tags=["targets"]
)
app.include_router(
    mock_targets.router,
    prefix="/api/v1",
    tags=["mock-targets"]
)
app.include_router(
    mcp_config.router,
    prefix="/api/v1",
    tags=["mcp"]
)
app.include_router(
    mcp_distribution.router,
    tags=["mcp-distribution"]
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Synthetic Data Generator API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates.
    
    Validates Requirement 11.3: Real-time monitoring and updates.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            logger.debug(f"Received WebSocket message: {data}")
            
            # Echo back for now (can be extended for client commands)
            await websocket.send_json({
                "type": "ack",
                "message": "Message received"
            })
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        ws_manager.disconnect(websocket)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
