"""Jira API client for retrieving test scenarios and managing test results."""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    JIRA_AVAILABLE = True
except ImportError:
    JIRA_AVAILABLE = False

logger = logging.getLogger(__name__)


class IssueType(Enum):
    """Jira issue types."""
    TEST = "Test"
    BUG = "Bug"
    STORY = "Story"
    TASK = "Task"


@dataclass
class JiraConfig:
    """Jira connection configuration."""
    url: str
    username: str
    api_token: str
    project_key: str
    
    @property
    def base_url(self) -> str:
        """Get base API URL."""
        return f"{self.url}/rest/api/3"


@dataclass
class TestScenario:
    """Represents a Jira test scenario."""
    id: str
    key: str
    summary: str
    description: str
    tags: List[str]
    preconditions: Optional[str] = None
    expected_outcome: Optional[str] = None
    test_steps: Optional[List[Dict[str, str]]] = None
    priority: str = "Medium"
    status: str = "To Do"
    
    def __post_init__(self):
        if self.test_steps is None:
            self.test_steps = []


class JiraClient:
    """Client for Jira REST API."""
    
    def __init__(self, config: JiraConfig):
        """Initialize Jira client.
        
        Args:
            config: Jira configuration
        """
        if not JIRA_AVAILABLE:
            raise ImportError(
                "Jira client requires 'requests'. "
                "Install with: pip install requests"
            )
        
        self.config = config
        
        # Create session with retry logic
        self.session = requests.Session()
        self.session.auth = (config.username, config.api_token)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
    
    def search_issues(
        self,
        jql: str,
        max_results: int = 50,
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for issues using JQL.
        
        Args:
            jql: JQL query string
            max_results: Maximum number of results
            fields: List of fields to return
        
        Returns:
            List of issue dictionaries
        """
        url = f"{self.config.base_url}/search"
        
        params = {
            'jql': jql,
            'maxResults': max_results,
            'fields': ','.join(fields) if fields else '*all'
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data.get('issues', [])
    
    def get_test_scenarios_by_tag(
        self,
        tag: str,
        project_key: Optional[str] = None
    ) -> List[TestScenario]:
        """Retrieve test scenarios by tag.
        
        Args:
            tag: Tag to filter by
            project_key: Project key (uses config default if not provided)
        
        Returns:
            List of test scenarios
        """
        project = project_key or self.config.project_key
        
        # Build JQL query
        jql = f'project = "{project}" AND labels = "{tag}" AND type = Test'
        
        logger.info(f"Searching for test scenarios with tag '{tag}' in project '{project}'")
        
        issues = self.search_issues(jql, max_results=100)
        
        scenarios = []
        for issue in issues:
            scenario = self._parse_test_scenario(issue)
            scenarios.append(scenario)
        
        logger.info(f"Found {len(scenarios)} test scenarios")
        return scenarios
    
    def _parse_test_scenario(self, issue: Dict[str, Any]) -> TestScenario:
        """Parse Jira issue into test scenario.
        
        Args:
            issue: Jira issue dictionary
        
        Returns:
            TestScenario object
        """
        fields = issue.get('fields', {})
        
        # Extract basic fields
        scenario = TestScenario(
            id=issue.get('id', ''),
            key=issue.get('key', ''),
            summary=fields.get('summary', ''),
            description=fields.get('description', ''),
            tags=fields.get('labels', []),
            priority=fields.get('priority', {}).get('name', 'Medium'),
            status=fields.get('status', {}).get('name', 'To Do')
        )
        
        # Parse description for structured content
        description = fields.get('description', '')
        if description:
            parsed = self._parse_description(description)
            scenario.preconditions = parsed.get('preconditions')
            scenario.expected_outcome = parsed.get('expected_outcome')
            scenario.test_steps = parsed.get('test_steps', [])
        
        return scenario
    
    def _parse_description(self, description: str) -> Dict[str, Any]:
        """Parse test scenario description for structured content.
        
        Args:
            description: Test scenario description
        
        Returns:
            Dictionary with parsed content
        """
        result = {
            'preconditions': None,
            'expected_outcome': None,
            'test_steps': []
        }
        
        # Simple parsing logic - look for common patterns
        lines = description.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Detect sections
            if line.lower().startswith('precondition'):
                current_section = 'preconditions'
                continue
            elif line.lower().startswith('expected'):
                current_section = 'expected_outcome'
                continue
            elif line.lower().startswith('steps') or line.lower().startswith('test steps'):
                current_section = 'test_steps'
                continue
            
            # Add content to current section
            if line and current_section:
                if current_section == 'test_steps':
                    # Parse step (e.g., "1. Do something")
                    if line[0].isdigit():
                        step_text = line.split('.', 1)[1].strip() if '.' in line else line
                        result['test_steps'].append({
                            'action': step_text,
                            'expected': ''
                        })
                else:
                    if result[current_section]:
                        result[current_section] += '\n' + line
                    else:
                        result[current_section] = line
        
        return result
    
    def create_issue(
        self,
        summary: str,
        description: str,
        issue_type: str = "Bug",
        priority: str = "Medium",
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new Jira issue.
        
        Args:
            summary: Issue summary
            description: Issue description
            issue_type: Issue type (Bug, Task, etc.)
            priority: Issue priority
            labels: Issue labels
        
        Returns:
            Created issue data
        """
        url = f"{self.config.base_url}/issue"
        
        payload = {
            'fields': {
                'project': {'key': self.config.project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
                'priority': {'name': priority}
            }
        }
        
        if labels:
            payload['fields']['labels'] = labels
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Created issue {data.get('key')}")
        return data
    
    def update_issue_status(
        self,
        issue_key: str,
        status: str,
        comment: Optional[str] = None
    ) -> None:
        """Update issue status.
        
        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            status: New status
            comment: Optional comment
        """
        # Get available transitions
        url = f"{self.config.base_url}/issue/{issue_key}/transitions"
        response = self.session.get(url)
        response.raise_for_status()
        
        transitions = response.json().get('transitions', [])
        
        # Find transition to desired status
        transition_id = None
        for transition in transitions:
            if transition['to']['name'].lower() == status.lower():
                transition_id = transition['id']
                break
        
        if not transition_id:
            logger.warning(f"No transition found to status '{status}' for {issue_key}")
            return
        
        # Execute transition
        payload = {'transition': {'id': transition_id}}
        
        if comment:
            payload['update'] = {
                'comment': [{'add': {'body': comment}}]
            }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        logger.info(f"Updated {issue_key} status to '{status}'")
    
    def add_comment(self, issue_key: str, comment: str) -> None:
        """Add comment to issue.
        
        Args:
            issue_key: Issue key
            comment: Comment text
        """
        url = f"{self.config.base_url}/issue/{issue_key}/comment"
        
        payload = {'body': comment}
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        logger.info(f"Added comment to {issue_key}")
    
    def close(self) -> None:
        """Close the client session."""
        if self.session:
            self.session.close()
            logger.info("Jira client session closed")


class MockJiraClient:
    """Mock Jira client for demo mode."""
    
    def __init__(self, config: Optional[JiraConfig] = None):
        """Initialize mock Jira client.
        
        Args:
            config: Optional Jira configuration (ignored in mock)
        """
        self.config = config
        self._mock_scenarios = self._create_mock_scenarios()
        logger.info("Initialized mock Jira client")
    
    def _create_mock_scenarios(self) -> List[TestScenario]:
        """Create mock test scenarios."""
        return [
            TestScenario(
                id="10001",
                key="TEST-1",
                summary="Verify user login with valid credentials",
                description="""
Preconditions:
- User account exists in the system
- User has valid credentials

Test Steps:
1. Navigate to login page
2. Enter valid username
3. Enter valid password
4. Click login button

Expected Outcome:
- User is successfully logged in
- User is redirected to dashboard
- Welcome message is displayed
                """,
                tags=["login", "authentication", "smoke"],
                priority="High",
                status="To Do"
            ),
            TestScenario(
                id="10002",
                key="TEST-2",
                summary="Verify data submission with synthetic records",
                description="""
Preconditions:
- Synthetic data has been generated
- Target system is accessible

Test Steps:
1. Select synthetic data record
2. Fill form with data values
3. Submit form
4. Verify submission success

Expected Outcome:
- Form submission succeeds
- Data is stored in target system
- Confirmation message is displayed
                """,
                tags=["data-submission", "integration", "regression"],
                priority="Medium",
                status="To Do"
            ),
            TestScenario(
                id="10003",
                key="TEST-3",
                summary="Verify edge case handling for invalid email",
                description="""
Preconditions:
- Email validation is enabled
- Edge case data is available

Test Steps:
1. Navigate to registration form
2. Enter invalid email format
3. Submit form
4. Verify error message

Expected Outcome:
- Form validation fails
- Appropriate error message is shown
- Form is not submitted
                """,
                tags=["edge-cases", "validation", "negative-testing"],
                priority="Medium",
                status="To Do"
            )
        ]
    
    def search_issues(
        self,
        jql: str,
        max_results: int = 50,
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Mock search for issues.
        
        Args:
            jql: JQL query string (ignored in mock)
            max_results: Maximum number of results
            fields: List of fields to return (ignored in mock)
        
        Returns:
            List of mock issue dictionaries
        """
        logger.info(f"Mock Jira search: {jql}")
        
        # Return mock issues
        issues = []
        for scenario in self._mock_scenarios[:max_results]:
            issues.append({
                'id': scenario.id,
                'key': scenario.key,
                'fields': {
                    'summary': scenario.summary,
                    'description': scenario.description,
                    'labels': scenario.tags,
                    'priority': {'name': scenario.priority},
                    'status': {'name': scenario.status}
                }
            })
        
        return issues
    
    def get_test_scenarios_by_tag(
        self,
        tag: str,
        project_key: Optional[str] = None
    ) -> List[TestScenario]:
        """Retrieve mock test scenarios by tag.
        
        Args:
            tag: Tag to filter by
            project_key: Project key (ignored in mock)
        
        Returns:
            List of mock test scenarios
        """
        logger.info(f"Mock Jira: Getting test scenarios with tag '{tag}'")
        
        # Filter scenarios by tag
        filtered = [s for s in self._mock_scenarios if tag in s.tags]
        
        if not filtered:
            # If no exact match, return all scenarios
            logger.info(f"No scenarios found with tag '{tag}', returning all mock scenarios")
            return self._mock_scenarios.copy()
        
        return filtered
    
    def create_issue(
        self,
        summary: str,
        description: str,
        issue_type: str = "Bug",
        priority: str = "Medium",
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Mock create issue.
        
        Args:
            summary: Issue summary
            description: Issue description
            issue_type: Issue type
            priority: Issue priority
            labels: Issue labels
        
        Returns:
            Mock created issue data
        """
        issue_key = f"MOCK-{len(self._mock_scenarios) + 1}"
        logger.info(f"Mock Jira: Created issue {issue_key}")
        
        return {
            'id': str(10000 + len(self._mock_scenarios)),
            'key': issue_key,
            'self': f'https://mock-jira.example.com/rest/api/3/issue/{issue_key}'
        }
    
    def update_issue_status(
        self,
        issue_key: str,
        status: str,
        comment: Optional[str] = None
    ) -> None:
        """Mock update issue status.
        
        Args:
            issue_key: Issue key
            status: New status
            comment: Optional comment
        """
        logger.info(f"Mock Jira: Updated {issue_key} status to '{status}'")
        if comment:
            logger.info(f"Mock Jira: Added comment to {issue_key}")
    
    def add_comment(self, issue_key: str, comment: str) -> None:
        """Mock add comment to issue.
        
        Args:
            issue_key: Issue key
            comment: Comment text
        """
        logger.info(f"Mock Jira: Added comment to {issue_key}")
    
    def close(self) -> None:
        """Mock close session."""
        logger.info("Mock Jira client closed")
