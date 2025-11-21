"""Salesforce Bulk API client for loading synthetic data."""
import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from io import StringIO
import csv

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    import pandas as pd
    SALESFORCE_AVAILABLE = True
except ImportError:
    SALESFORCE_AVAILABLE = False

logger = logging.getLogger(__name__)


class SalesforceOperation(Enum):
    """Salesforce bulk operations."""
    INSERT = "insert"
    UPSERT = "upsert"
    UPDATE = "update"
    DELETE = "delete"


class JobState(Enum):
    """Salesforce job states."""
    OPEN = "Open"
    IN_PROGRESS = "InProgress"
    JOB_COMPLETE = "JobComplete"
    FAILED = "Failed"
    ABORTED = "Aborted"


@dataclass
class SalesforceConfig:
    """Salesforce connection configuration."""
    username: str
    password: str
    security_token: str
    domain: str = "login"  # or "test" for sandbox
    api_version: str = "58.0"
    
    @property
    def login_url(self) -> str:
        """Get login URL based on domain."""
        return f"https://{self.domain}.salesforce.com/services/oauth2/token"
    
    @property
    def base_url(self) -> str:
        """Get base API URL."""
        return f"https://{self.domain}.salesforce.com/services/data/v{self.api_version}"


@dataclass
class BulkJob:
    """Represents a Salesforce bulk job."""
    id: str
    object_name: str
    operation: str
    state: str
    created_date: str
    system_modstamp: str
    api_version: str


class SalesforceClient:
    """Client for Salesforce Bulk API 2.0."""
    
    def __init__(self, config: SalesforceConfig):
        """Initialize Salesforce client.
        
        Args:
            config: Salesforce configuration
        """
        if not SALESFORCE_AVAILABLE:
            raise ImportError(
                "Salesforce client requires 'requests' and 'pandas'. "
                "Install with: pip install requests pandas"
            )
        
        self.config = config
        self.access_token: Optional[str] = None
        self.instance_url: Optional[str] = None
        
        # Create session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PATCH", "PUT"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
    
    async def authenticate(self) -> None:
        """Authenticate with Salesforce using OAuth 2.0 password flow."""
        logger.info("Authenticating with Salesforce...")
        
        # Note: In production, use Connected App with client_id and client_secret
        # This is a simplified version using username/password flow
        data = {
            'grant_type': 'password',
            'client_id': '3MVG9...',  # Replace with your Connected App Consumer Key
            'client_secret': 'ABC123...',  # Replace with your Connected App Consumer Secret
            'username': self.config.username,
            'password': f"{self.config.password}{self.config.security_token}"
        }
        
        try:
            response = self.session.post(self.config.login_url, data=data)
            response.raise_for_status()
            
            auth_data = response.json()
            self.access_token = auth_data['access_token']
            self.instance_url = auth_data['instance_url']
            
            # Set authorization header for future requests
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            })
            
            logger.info(f"Successfully authenticated with Salesforce instance: {self.instance_url}")
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise
    
    async def create_job(
        self,
        object_name: str,
        operation: SalesforceOperation,
        external_id_field: Optional[str] = None
    ) -> BulkJob:
        """Create a bulk job.
        
        Args:
            object_name: Salesforce object name (e.g., 'Account')
            operation: Bulk operation type
            external_id_field: External ID field for upsert operations
            
        Returns:
            Created bulk job
        """
        url = f"{self.instance_url}/services/data/v{self.config.api_version}/jobs/ingest"
        
        job_data = {
            'object': object_name,
            'operation': operation.value
        }
        
        if operation == SalesforceOperation.UPSERT and external_id_field:
            job_data['externalIdFieldName'] = external_id_field
        
        response = self.session.post(url, json=job_data)
        response.raise_for_status()
        
        job_info = response.json()
        logger.info(f"Created bulk job {job_info['id']} for {object_name}")
        
        return BulkJob(
            id=job_info['id'],
            object_name=job_info['object'],
            operation=job_info['operation'],
            state=job_info['state'],
            created_date=job_info['createdDate'],
            system_modstamp=job_info['systemModstamp'],
            api_version=job_info['apiVersion']
        )
    
    async def upload_data(self, job: BulkJob, data: pd.DataFrame) -> None:
        """Upload data to a bulk job.
        
        Args:
            job: Bulk job to upload to
            data: DataFrame containing records to upload
        """
        url = f"{self.instance_url}/services/data/v{self.config.api_version}/jobs/ingest/{job.id}/batches"
        
        # Convert DataFrame to CSV
        csv_buffer = StringIO()
        data.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'text/csv'
        }
        
        response = self.session.put(url, data=csv_data, headers=headers)
        response.raise_for_status()
        
        logger.info(f"Uploaded {len(data)} records to job {job.id}")
    
    async def close_job(self, job: BulkJob) -> BulkJob:
        """Close a bulk job to start processing.
        
        Args:
            job: Bulk job to close
            
        Returns:
            Updated bulk job
        """
        url = f"{self.instance_url}/services/data/v{self.config.api_version}/jobs/ingest/{job.id}"
        
        response = self.session.patch(url, json={'state': 'UploadComplete'})
        response.raise_for_status()
        
        job_info = response.json()
        logger.info(f"Closed job {job.id}, state: {job_info['state']}")
        
        return BulkJob(
            id=job_info['id'],
            object_name=job_info['object'],
            operation=job_info['operation'],
            state=job_info['state'],
            created_date=job_info['createdDate'],
            system_modstamp=job_info['systemModstamp'],
            api_version=job_info['apiVersion']
        )
    
    async def get_job_status(self, job_id: str) -> BulkJob:
        """Get the status of a bulk job.
        
        Args:
            job_id: Job ID to check
            
        Returns:
            Current job status
        """
        url = f"{self.instance_url}/services/data/v{self.config.api_version}/jobs/ingest/{job_id}"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        job_info = response.json()
        return BulkJob(
            id=job_info['id'],
            object_name=job_info['object'],
            operation=job_info['operation'],
            state=job_info['state'],
            created_date=job_info['createdDate'],
            system_modstamp=job_info['systemModstamp'],
            api_version=job_info['apiVersion']
        )
    
    async def wait_for_job_completion(
        self,
        job: BulkJob,
        poll_interval: int = 5,
        timeout: int = 300
    ) -> BulkJob:
        """Wait for a bulk job to complete.
        
        Args:
            job: Bulk job to wait for
            poll_interval: Seconds between status checks
            timeout: Maximum seconds to wait
            
        Returns:
            Completed bulk job
        """
        start_time = time.time()
        
        while True:
            current_job = await self.get_job_status(job.id)
            
            if current_job.state in [JobState.JOB_COMPLETE.value, JobState.FAILED.value, JobState.ABORTED.value]:
                logger.info(f"Job {job.id} completed with state: {current_job.state}")
                return current_job
            
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Job {job.id} did not complete within {timeout} seconds")
            
            logger.debug(f"Job {job.id} state: {current_job.state}, waiting...")
            await asyncio.sleep(poll_interval)
    
    async def get_job_results(self, job: BulkJob) -> Tuple[int, int, List[Dict[str, Any]]]:
        """Get the results of a completed bulk job.
        
        Args:
            job: Completed bulk job
            
        Returns:
            Tuple of (successful_records, failed_records, error_details)
        """
        # Get successful results
        success_url = f"{self.instance_url}/services/data/v{self.config.api_version}/jobs/ingest/{job.id}/successfulResults"
        success_response = self.session.get(success_url)
        success_response.raise_for_status()
        
        # Parse CSV response
        success_data = success_response.text
        success_records = len(success_data.split('\n')) - 2  # Subtract header and empty line
        
        # Get failed results
        failed_url = f"{self.instance_url}/services/data/v{self.config.api_version}/jobs/ingest/{job.id}/failedResults"
        failed_response = self.session.get(failed_url)
        failed_response.raise_for_status()
        
        failed_data = failed_response.text
        failed_records = len(failed_data.split('\n')) - 2
        
        # Parse error details
        errors = []
        if failed_records > 0:
            reader = csv.DictReader(StringIO(failed_data))
            for row in reader:
                errors.append({
                    'record': row,
                    'error': row.get('sf__Error', 'Unknown error')
                })
        
        logger.info(f"Job {job.id} results: {success_records} successful, {failed_records} failed")
        return success_records, failed_records, errors
    
    async def bulk_insert(
        self,
        object_name: str,
        data: pd.DataFrame,
        batch_size: int = 1000
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """Perform a bulk insert operation.
        
        Args:
            object_name: Salesforce object name
            data: DataFrame containing records to insert
            batch_size: Number of records per batch
            
        Returns:
            Tuple of (successful_records, failed_records, error_details)
        """
        total_success = 0
        total_failed = 0
        all_errors = []
        
        # Process in batches
        for i in range(0, len(data), batch_size):
            batch = data.iloc[i:i + batch_size]
            
            # Create job
            job = await self.create_job(object_name, SalesforceOperation.INSERT)
            
            # Upload data
            await self.upload_data(job, batch)
            
            # Close job
            job = await self.close_job(job)
            
            # Wait for completion
            job = await self.wait_for_job_completion(job)
            
            # Get results
            success, failed, errors = await self.get_job_results(job)
            total_success += success
            total_failed += failed
            all_errors.extend(errors)
        
        return total_success, total_failed, all_errors
    
    async def bulk_upsert(
        self,
        object_name: str,
        data: pd.DataFrame,
        external_id_field: str,
        batch_size: int = 1000
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """Perform a bulk upsert operation.
        
        Args:
            object_name: Salesforce object name
            data: DataFrame containing records to upsert
            external_id_field: External ID field for matching
            batch_size: Number of records per batch
            
        Returns:
            Tuple of (successful_records, failed_records, error_details)
        """
        total_success = 0
        total_failed = 0
        all_errors = []
        
        # Process in batches
        for i in range(0, len(data), batch_size):
            batch = data.iloc[i:i + batch_size]
            
            # Create job
            job = await self.create_job(object_name, SalesforceOperation.UPSERT, external_id_field)
            
            # Upload data
            await self.upload_data(job, batch)
            
            # Close job
            job = await self.close_job(job)
            
            # Wait for completion
            job = await self.wait_for_job_completion(job)
            
            # Get results
            success, failed, errors = await self.get_job_results(job)
            total_success += success
            total_failed += failed
            all_errors.extend(errors)
        
        return total_success, total_failed, all_errors
    
    def close(self) -> None:
        """Close the client session."""
        if self.session:
            self.session.close()
            logger.info("Salesforce client session closed")
