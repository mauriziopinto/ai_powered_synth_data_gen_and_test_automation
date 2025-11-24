"""Target model for data distribution."""

from enum import Enum
from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TargetType(str, Enum):
    """Supported target types."""
    DATABASE = "database"
    SALESFORCE = "salesforce"
    API = "api"
    S3 = "s3"


class DatabaseConfig(BaseModel):
    """Database target configuration."""
    connection_string: str
    table_name: str
    database_type: str = "postgresql"  # postgresql, mysql, mongodb


class SalesforceConfig(BaseModel):
    """Salesforce target configuration."""
    instance_url: str
    access_token: str
    object_type: str  # Lead, Contact, Account, etc.


class APIConfig(BaseModel):
    """API target configuration."""
    endpoint_url: str
    method: str = "POST"  # POST, PUT, PATCH
    headers: Dict[str, str] = Field(default_factory=dict)
    auth_type: Optional[str] = None  # bearer, basic, api_key
    auth_value: Optional[str] = None


class S3Config(BaseModel):
    """S3 target configuration."""
    bucket_name: str
    region: str = "us-east-1"
    path_prefix: str = ""
    file_format: str = "csv"  # csv, json, parquet


class Target(BaseModel):
    """Target for data distribution."""
    id: str
    name: str
    type: TargetType
    config: Dict  # Type-specific config
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class TargetCreate(BaseModel):
    """Request model for creating a target."""
    name: str
    type: TargetType
    config: Dict


class TargetUpdate(BaseModel):
    """Request model for updating a target."""
    name: Optional[str] = None
    config: Optional[Dict] = None
    is_active: Optional[bool] = None


class TargetTestResult(BaseModel):
    """Result of testing a target connection."""
    success: bool
    message: str
    details: Optional[Dict] = None
