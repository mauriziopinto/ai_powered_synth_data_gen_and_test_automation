"""Test execution result models."""

from dataclasses import dataclass, field
from typing import List, Optional


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
