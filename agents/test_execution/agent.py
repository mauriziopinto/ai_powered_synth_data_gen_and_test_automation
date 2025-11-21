"""Test Execution Agent for running generated test cases with Jira integration."""

import asyncio
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Test execution status."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestFramework(Enum):
    """Supported test frameworks."""
    ROBOT = "robot"
    SELENIUM = "selenium"
    PLAYWRIGHT = "playwright"


class JiraUpdatePolicy(Enum):
    """Policy for when to update Jira."""
    ALWAYS = "always"  # Update for all test results
    FAILURES_ONLY = "failures_only"  # Only update for failures
    NEVER = "never"  # Never update Jira


@dataclass
class TestExecutionConfig:
    """Configuration for test execution."""
    test_directory: str
    framework: str = "robot"  # robot, selenium, playwright
    output_directory: str = "test_results"
    parallel_execution: bool = False
    max_workers: int = 4
    timeout: int = 300  # seconds
    retry_failed: bool = False
    retry_count: int = 1
    generate_reports: bool = True

    def __post_init__(self):
        # Validate framework
        if self.framework not in ['robot', 'selenium', 'playwright']:
            raise ValueError(f"Unsupported framework: {self.framework}")


@dataclass
class JiraUpdateConfig:
    """Configuration for Jira updates."""
    enabled: bool = False
    create_issues_for_failures: bool = True
    update_test_scenarios: bool = True
    policy: JiraUpdatePolicy = JiraUpdatePolicy.FAILURES_ONLY
    auto_assign: bool = False
    default_assignee: Optional[str] = None
    failure_priority: str = "Medium"
    failure_labels: List[str] = field(default_factory=lambda: ["test-failure", "automated"])
    link_to_scenarios: bool = True


@dataclass
class TestResult:
    """Represents a single test execution result."""
    test_id: str
    test_name: str
    framework: str
    status: TestStatus
    duration: float
    error_message: Optional[str] = None
    output: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'test_id': self.test_id,
            'test_name': self.test_name,
            'framework': self.framework,
            'status': self.status.value,
            'duration': self.duration,
            'error_message': self.error_message,
            'output': self.output,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None
        }


@dataclass
class TestExecutionReport:
    """Comprehensive test execution report."""
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    total_duration: float
    pass_rate: float
    results: List[TestResult]
    execution_time: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_results(cls, results: List[TestResult]):
        """Create report from test results."""
        total = len(results)
        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)
        error = sum(1 for r in results if r.status == TestStatus.ERROR)
        duration = sum(r.duration for r in results)
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        return cls(
            total_tests=total,
            passed_tests=passed,
            failed_tests=failed,
            skipped_tests=skipped,
            error_tests=error,
            total_duration=duration,
            pass_rate=pass_rate,
            results=results
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'skipped_tests': self.skipped_tests,
            'error_tests': self.error_tests,
            'total_duration': self.total_duration,
            'pass_rate': self.pass_rate,
            'execution_time': self.execution_time.isoformat(),
            'results': [r.to_dict() for r in self.results]
        }



class JiraIntegration:
    """Handles Jira integration for test execution results."""
    
    def __init__(self, jira_client, config: JiraUpdateConfig):
        """Initialize Jira integration.
        
        Args:
            jira_client: JiraClient or MockJiraClient instance
            config: Jira update configuration
        """
        self.jira_client = jira_client
        self.config = config
        self._created_issues: List[Dict[str, Any]] = []
    
    async def process_test_results(
        self,
        report: TestExecutionReport,
        test_scenarios: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Process test results and update Jira.
        
        Args:
            report: Test execution report
            test_scenarios: Optional mapping of test_id to Jira issue key
        
        Returns:
            Summary of Jira updates
        """
        if not self.config.enabled:
            logger.info("Jira integration disabled, skipping updates")
            return {'enabled': False}
        
        logger.info("Processing test results for Jira updates")
        
        summary = {
            'enabled': True,
            'issues_created': 0,
            'scenarios_updated': 0,
            'comments_added': 0,
            'errors': []
        }

        # Process each test result
        for result in report.results:
            try:
                # Check if we should process this result based on policy
                if not self._should_process_result(result):
                    continue
                
                # Create issue for failures if configured
                if (result.status == TestStatus.FAILED and 
                    self.config.create_issues_for_failures):
                    issue = await self._create_failure_issue(result)
                    if issue:
                        self._created_issues.append(issue)
                        summary['issues_created'] += 1
                        
                        # Link to test scenario if available
                        if (self.config.link_to_scenarios and 
                            test_scenarios and 
                            result.test_id in test_scenarios):
                            scenario_key = test_scenarios[result.test_id]
                            await self._link_issues(issue['key'], scenario_key)
                
                # Update test scenario status if configured
                if (self.config.update_test_scenarios and 
                    test_scenarios and 
                    result.test_id in test_scenarios):
                    scenario_key = test_scenarios[result.test_id]
                    await self._update_test_scenario(scenario_key, result)
                    summary['scenarios_updated'] += 1
                
            except Exception as e:
                logger.error(f"Error processing result for {result.test_name}: {str(e)}")
                summary['errors'].append({
                    'test': result.test_name,
                    'error': str(e)
                })
        
        logger.info(f"Jira updates complete: {summary['issues_created']} issues created, "
                   f"{summary['scenarios_updated']} scenarios updated")
        
        return summary

    def _should_process_result(self, result: TestResult) -> bool:
        """Check if result should be processed based on policy."""
        if self.config.policy == JiraUpdatePolicy.NEVER:
            return False
        elif self.config.policy == JiraUpdatePolicy.ALWAYS:
            return True
        elif self.config.policy == JiraUpdatePolicy.FAILURES_ONLY:
            return result.status in [TestStatus.FAILED, TestStatus.ERROR]
        return False
    
    async def _create_failure_issue(self, result: TestResult) -> Optional[Dict[str, Any]]:
        """Create Jira issue for test failure."""
        # Format issue summary
        summary = f"Test Failure: {result.test_name}"
        
        # Format detailed description
        description = self._format_failure_description(result)
        
        # Determine priority based on failure type
        priority = self._determine_priority(result)
        
        # Create labels
        labels = self.config.failure_labels.copy()
        labels.append(result.framework)
        if result.status == TestStatus.ERROR:
            labels.append("test-error")
        
        try:
            issue = self.jira_client.create_issue(
                summary=summary,
                description=description,
                issue_type="Bug",
                priority=priority,
                labels=labels
            )
            
            logger.info(f"Created Jira issue {issue.get('key')} for test failure: {result.test_name}")
            return issue
            
        except Exception as e:
            logger.error(f"Failed to create Jira issue for {result.test_name}: {str(e)}")
            return None

    def _format_failure_description(self, result: TestResult) -> str:
        """Format test failure description for Jira."""
        description = f"""
h2. Test Failure Details

*Test Name:* {result.test_name}
*Test ID:* {result.test_id}
*Framework:* {result.framework}
*Status:* {result.status.value.upper()}
*Duration:* {result.duration:.2f}s
*Execution Time:* {result.start_time.strftime('%Y-%m-%d %H:%M:%S')}

h3. Error Message

{{{{{result.error_message or 'No error message available'}}}}}
"""
        
        if result.output:
            # Truncate output if too long
            output = result.output[:2000] + "..." if len(result.output) > 2000 else result.output
            description += f"""

h3. Test Output

{{{{
{output}
}}}}
"""
        
        description += """

h3. Recommended Actions

# Review the error message and test output
# Check if the test data or environment has changed
# Verify the test scenario is still valid
# Re-run the test to confirm the failure is reproducible
# Update the test or fix the underlying issue
"""
        
        return description
    
    def _determine_priority(self, result: TestResult) -> str:
        """Determine issue priority based on test result."""
        # Errors are higher priority than failures
        if result.status == TestStatus.ERROR:
            return "High"
        
        # Use configured default for failures
        return self.config.failure_priority

    async def _update_test_scenario(self, scenario_key: str, result: TestResult) -> None:
        """Update test scenario with execution result."""
        # Format comment with result
        comment = self._format_result_comment(result)
        
        try:
            # Add comment with result
            self.jira_client.add_comment(scenario_key, comment)
            
            # Update status based on result
            if result.status == TestStatus.PASSED:
                # Try to transition to "Done" or "Passed"
                try:
                    self.jira_client.update_issue_status(scenario_key, "Done")
                except:
                    try:
                        self.jira_client.update_issue_status(scenario_key, "Passed")
                    except:
                        logger.warning(f"Could not update status for {scenario_key}")
            
            logger.info(f"Updated test scenario {scenario_key} with execution result")
            
        except Exception as e:
            logger.error(f"Failed to update test scenario {scenario_key}: {str(e)}")
    
    def _format_result_comment(self, result: TestResult) -> str:
        """Format test result as Jira comment."""
        status_emoji = {
            TestStatus.PASSED: "(/) ",
            TestStatus.FAILED: "(x) ",
            TestStatus.ERROR: "(!) ",
            TestStatus.SKIPPED: "(-) "
        }
        
        emoji = status_emoji.get(result.status, "")
        
        comment = f"""
{emoji}*Automated Test Execution Result*

*Status:* {result.status.value.upper()}
*Duration:* {result.duration:.2f}s
*Executed:* {result.start_time.strftime('%Y-%m-%d %H:%M:%S')}
*Framework:* {result.framework}
"""
        
        if result.error_message:
            comment += f"\n*Error:* {result.error_message}"
        
        return comment

    async def _link_issues(self, issue_key: str, scenario_key: str) -> None:
        """Link failure issue to test scenario."""
        try:
            # Add comment to failure issue referencing scenario
            comment = f"This failure is related to test scenario {scenario_key}"
            self.jira_client.add_comment(issue_key, comment)
            
            # Add comment to scenario referencing failure
            comment = f"Test failure reported in {issue_key}"
            self.jira_client.add_comment(scenario_key, comment)
            
            logger.info(f"Linked {issue_key} to test scenario {scenario_key}")
            
        except Exception as e:
            logger.error(f"Failed to link issues {issue_key} and {scenario_key}: {str(e)}")
    
    def get_created_issues(self) -> List[Dict[str, Any]]:
        """Get list of issues created during this session."""
        return self._created_issues.copy()
    
    def generate_summary_report(self) -> str:
        """Generate summary report of Jira updates."""
        if not self.config.enabled:
            return "Jira integration is disabled"
        
        report = f"""
Jira Integration Summary
========================

Configuration:
- Create issues for failures: {self.config.create_issues_for_failures}
- Update test scenarios: {self.config.update_test_scenarios}
- Update policy: {self.config.policy.value}

Results:
- Issues created: {len(self._created_issues)}
"""
        
        if self._created_issues:
            report += "\nCreated Issues:\n"
            for issue in self._created_issues:
                report += f"  - {issue.get('key')}: {issue.get('self', 'N/A')}\n"
        
        return report
