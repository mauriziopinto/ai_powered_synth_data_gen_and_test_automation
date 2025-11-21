"""Test execution result models."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import json
import base64


@dataclass
class TestResult:
    """Individual test execution result."""
    test_id: str
    test_name: str
    status: str  # 'passed', 'failed', 'error', 'skipped'
    duration: float
    logs: str
    screenshots: List[bytes] = field(default_factory=list)
    error: Optional[str] = None
    jira_issue_created: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'test_id': self.test_id,
            'test_name': self.test_name,
            'status': self.status,
            'duration': self.duration,
            'logs': self.logs,
            'screenshots': [base64.b64encode(s).decode('utf-8') for s in self.screenshots],
            'error': self.error,
            'jira_issue_created': self.jira_issue_created
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestResult':
        """Create from dictionary."""
        # Decode base64 screenshots
        screenshots = [
            base64.b64decode(s.encode('utf-8')) if isinstance(s, str) else s
            for s in data.get('screenshots', [])
        ]
        
        return cls(
            test_id=data['test_id'],
            test_name=data['test_name'],
            status=data['status'],
            duration=data['duration'],
            logs=data['logs'],
            screenshots=screenshots,
            error=data.get('error'),
            jira_issue_created=data.get('jira_issue_created')
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TestResult':
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class TestResults:
    """Aggregated test execution results."""
    total: int
    passed: int
    failed: int
    errors: int = 0
    skipped: int = 0
    results: List[TestResult] = field(default_factory=list)
    total_duration: float = 0.0
    
    def __post_init__(self):
        """Calculate derived fields."""
        if self.total_duration == 0.0:
            self.total_duration = sum(r.duration for r in self.results)
    
    @property
    def pass_rate(self) -> float:
        """Calculate pass rate percentage."""
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'total': self.total,
            'passed': self.passed,
            'failed': self.failed,
            'errors': self.errors,
            'skipped': self.skipped,
            'results': [r.to_dict() for r in self.results],
            'total_duration': self.total_duration,
            'pass_rate': self.pass_rate
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestResults':
        """Create from dictionary."""
        results = [TestResult.from_dict(r) for r in data.get('results', [])]
        
        return cls(
            total=data['total'],
            passed=data['passed'],
            failed=data['failed'],
            errors=data.get('errors', 0),
            skipped=data.get('skipped', 0),
            results=results,
            total_duration=data.get('total_duration', 0.0)
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TestResults':
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
