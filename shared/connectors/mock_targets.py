"""Mock target systems for testing data distribution."""

import time
import random
from typing import Dict, List, Any
from datetime import datetime


class MockDatabase:
    """Mock database that simulates INSERT operations."""
    
    def __init__(self, connection_string: str, table_name: str):
        self.connection_string = connection_string
        self.table_name = table_name
        self.records = []
        self.connected = True
    
    def insert(self, data: Dict[str, Any]) -> bool:
        """Simulate inserting a record."""
        time.sleep(random.uniform(0.01, 0.05))  # Simulate network delay
        
        # 2% failure rate for realism
        if random.random() < 0.02:
            raise Exception("Database connection timeout")
        
        self.records.append({
            **data,
            'inserted_at': datetime.utcnow().isoformat()
        })
        return True
    
    def get_records(self) -> List[Dict]:
        """Get all inserted records."""
        return self.records
    
    def clear(self):
        """Clear all records."""
        self.records = []


class MockSalesforce:
    """Mock Salesforce that simulates record creation."""
    
    def __init__(self, instance_url: str, access_token: str, object_type: str):
        self.instance_url = instance_url
        self.access_token = access_token
        self.object_type = object_type
        self.records = []
        self.connected = True
    
    def create_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate creating a Salesforce record."""
        time.sleep(random.uniform(0.02, 0.08))  # Simulate API delay
        
        # 3% failure rate for realism
        if random.random() < 0.03:
            raise Exception("Salesforce API rate limit exceeded")
        
        record_id = f"SF{random.randint(100000, 999999)}"
        record = {
            'Id': record_id,
            **data,
            'CreatedDate': datetime.utcnow().isoformat()
        }
        self.records.append(record)
        return {'id': record_id, 'success': True}
    
    def get_records(self) -> List[Dict]:
        """Get all created records."""
        return self.records
    
    def clear(self):
        """Clear all records."""
        self.records = []


class MockAPI:
    """Mock REST API that simulates POST/PUT requests."""
    
    def __init__(self, endpoint_url: str, method: str = "POST", headers: Dict = None):
        self.endpoint_url = endpoint_url
        self.method = method
        self.headers = headers or {}
        self.requests = []
        self.connected = True
    
    def send(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate sending data to API."""
        time.sleep(random.uniform(0.03, 0.1))  # Simulate API delay
        
        # 2% failure rate for realism
        if random.random() < 0.02:
            raise Exception("API endpoint returned 500 Internal Server Error")
        
        request_id = f"REQ{random.randint(100000, 999999)}"
        request = {
            'request_id': request_id,
            'method': self.method,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 200
        }
        self.requests.append(request)
        return {'request_id': request_id, 'status': 'success'}
    
    def get_requests(self) -> List[Dict]:
        """Get all sent requests."""
        return self.requests
    
    def clear(self):
        """Clear all requests."""
        self.requests = []


class MockS3:
    """Mock S3 that simulates file uploads."""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1", path_prefix: str = ""):
        self.bucket_name = bucket_name
        self.region = region
        self.path_prefix = path_prefix
        self.files = []
        self.connected = True
    
    def upload(self, data: List[Dict[str, Any]], filename: str = None) -> Dict[str, Any]:
        """Simulate uploading data to S3."""
        time.sleep(random.uniform(0.05, 0.15))  # Simulate upload delay
        
        # 1% failure rate for realism
        if random.random() < 0.01:
            raise Exception("S3 upload failed: Access Denied")
        
        if not filename:
            filename = f"data_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        full_path = f"{self.path_prefix}/{filename}" if self.path_prefix else filename
        
        file_record = {
            'key': full_path,
            'bucket': self.bucket_name,
            'size': len(str(data)),
            'records_count': len(data),
            'uploaded_at': datetime.utcnow().isoformat()
        }
        self.files.append(file_record)
        return {'key': full_path, 'success': True}
    
    def get_files(self) -> List[Dict]:
        """Get all uploaded files."""
        return self.files
    
    def clear(self):
        """Clear all files."""
        self.files = []


# Global mock instances for persistence across requests
_mock_instances = {}


def get_mock_target(target_type: str, config: Dict[str, Any], target_id: str):
    """Get or create a mock target instance."""
    
    # Use target_id to maintain state across requests
    if target_id not in _mock_instances:
        if target_type == "database":
            _mock_instances[target_id] = MockDatabase(
                config.get("connection_string", ""),
                config.get("table_name", "")
            )
        elif target_type == "salesforce":
            _mock_instances[target_id] = MockSalesforce(
                config.get("instance_url", ""),
                config.get("access_token", ""),
                config.get("object_type", "")
            )
        elif target_type == "api":
            _mock_instances[target_id] = MockAPI(
                config.get("endpoint_url", ""),
                config.get("method", "POST"),
                config.get("headers", {})
            )
        elif target_type == "s3":
            _mock_instances[target_id] = MockS3(
                config.get("bucket_name", ""),
                config.get("region", "us-east-1"),
                config.get("path_prefix", "")
            )
    
    return _mock_instances[target_id]


def clear_mock_target(target_id: str):
    """Clear data from a mock target."""
    if target_id in _mock_instances:
        _mock_instances[target_id].clear()


def get_mock_target_data(target_id: str) -> List[Dict]:
    """Get data from a mock target."""
    if target_id not in _mock_instances:
        return []
    
    instance = _mock_instances[target_id]
    
    if hasattr(instance, 'get_records'):
        return instance.get_records()
    elif hasattr(instance, 'get_requests'):
        return instance.get_requests()
    elif hasattr(instance, 'get_files'):
        return instance.get_files()
    
    return []
