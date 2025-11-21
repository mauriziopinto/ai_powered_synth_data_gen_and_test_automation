"""Demo of Jira integration for test execution results."""

import asyncio
from datetime import datetime
from agents.test_execution.agent import (
    JiraIntegration,
    JiraUpdateConfig,
    JiraUpdatePolicy,
    TestResult,
    TestStatus,
    TestExecutionReport
)
from shared.utils.jira_client import MockJiraClient


async def demo_jira_integration():
    """Demo Jira integration with test results."""
    print("=" * 80)
    print("JIRA INTEGRATION DEMO")
    print("=" * 80)
    print("This demo shows automatic Jira updates for test execution results")
    print("=" * 80)
    print()
    
    # Create mock Jira client
    jira_client = MockJiraClient()
    
    # Configure Jira integration
    config = JiraUpdateConfig(
        enabled=True,
        create_issues_for_failures=True,
        update_test_scenarios=True,
        policy=JiraUpdatePolicy.FAILURES_ONLY,
        failure_priority="High",
        failure_labels=["automated-test", "test-failure"],
        link_to_scenarios=True
    )
    
    print("📋 Jira Integration Configuration:")
    print(f"   Enabled: {config.enabled}")
    print(f"   Create issues for failures: {config.create_issues_for_failures}")
    print(f"   Update test scenarios: {config.update_test_scenarios}")
    print(f"   Policy: {config.policy.value}")
    print(f"   Failure priority: {config.failure_priority}")
    print(f"   Link to scenarios: {config.link_to_scenarios}")
    print()
    
    # Create Jira integration
    integration = JiraIntegration(jira_client, config)
    
    # Create mock test results
    results = [
        TestResult(
            test_id="test_login",
            test_name="test_user_login_valid_credentials.robot",
            framework="robot",
            status=TestStatus.PASSED,
            duration=2.5,
            start_time=datetime.now()
        ),
        TestResult(
            test_id="test_data_submission",
            test_name="test_data_submission_synthetic.robot",
            framework="robot",
            status=TestStatus.FAILED,
            duration=5.2,
            error_message="AssertionError: Expected status code 200, got 500",
            output="Test output showing server error...",
            start_time=datetime.now()
        ),
        TestResult(
            test_id="test_edge_case",
            test_name="test_invalid_email_validation.py",
            framework="selenium",
            status=TestStatus.ERROR,
            duration=1.8,
            error_message="WebDriverException: Unable to locate element",
            output="Selenium error trace...",
            start_time=datetime.now()
        ),
        TestResult(
            test_id="test_performance",
            test_name="test_page_load_time.py",
            framework="playwright",
            status=TestStatus.PASSED,
            duration=3.1,
            start_time=datetime.now()
        )
    ]
    
    # Create test execution report
    report = TestExecutionReport.from_results(results)
    
    print("📊 Test Execution Results:")
    print(f"   Total tests: {report.total_tests}")
    print(f"   Passed: {report.passed_tests}")
    print(f"   Failed: {report.failed_tests}")
    print(f"   Errors: {report.error_tests}")
    print(f"   Pass rate: {report.pass_rate:.1f}%")
    print()
    
    # Map test IDs to Jira scenario keys
    test_scenarios = {
        "test_login": "TEST-1",
        "test_data_submission": "TEST-2",
        "test_edge_case": "TEST-3"
    }
    
    print("🔗 Test Scenario Mapping:")
    for test_id, scenario_key in test_scenarios.items():
        print(f"   {test_id} → {scenario_key}")
    print()
    
    # Process test results
    print("🔄 Processing test results for Jira updates...")
    summary = await integration.process_test_results(report, test_scenarios)
    print()
    
    print("✅ Jira Updates Complete!")
    print()
    print("📈 Update Summary:")
    print(f"   Issues created: {summary['issues_created']}")
    print(f"   Scenarios updated: {summary['scenarios_updated']}")
    print(f"   Errors: {len(summary['errors'])}")
    print()
    
    # Show created issues
    created_issues = integration.get_created_issues()
    if created_issues:
        print("🐛 Created Jira Issues:")
        for issue in created_issues:
            print(f"   • {issue.get('key')}: {issue.get('self', 'N/A')}")
        print()
    
    # Generate summary report
    print("📄 Jira Integration Report:")
    print(integration.generate_summary_report())
    print()


async def demo_jira_policies():
    """Demo different Jira update policies."""
    print("=" * 80)
    print("JIRA UPDATE POLICIES DEMO")
    print("=" * 80)
    print("This demo shows different Jira update policies")
    print("=" * 80)
    print()
    
    # Create mock results
    results = [
        TestResult(
            test_id="test_1",
            test_name="test_passed.robot",
            framework="robot",
            status=TestStatus.PASSED,
            duration=1.0,
            start_time=datetime.now()
        ),
        TestResult(
            test_id="test_2",
            test_name="test_failed.robot",
            framework="robot",
            status=TestStatus.FAILED,
            duration=2.0,
            error_message="Test failed",
            start_time=datetime.now()
        )
    ]
    
    report = TestExecutionReport.from_results(results)
    jira_client = MockJiraClient()
    
    # Test different policies
    policies = [
        JiraUpdatePolicy.ALWAYS,
        JiraUpdatePolicy.FAILURES_ONLY,
        JiraUpdatePolicy.NEVER
    ]
    
    for policy in policies:
        print(f"📋 Testing Policy: {policy.value}")
        print("-" * 40)
        
        config = JiraUpdateConfig(
            enabled=True,
            create_issues_for_failures=True,
            policy=policy
        )
        
        integration = JiraIntegration(jira_client, config)
        summary = await integration.process_test_results(report)
        
        print(f"   Issues created: {summary['issues_created']}")
        print(f"   Scenarios updated: {summary['scenarios_updated']}")
        print()


async def demo_jira_disabled():
    """Demo with Jira integration disabled."""
    print("=" * 80)
    print("JIRA INTEGRATION DISABLED DEMO")
    print("=" * 80)
    print("This demo shows behavior when Jira integration is disabled")
    print("=" * 80)
    print()
    
    # Create mock results
    results = [
        TestResult(
            test_id="test_1",
            test_name="test_example.robot",
            framework="robot",
            status=TestStatus.FAILED,
            duration=1.0,
            error_message="Test failed",
            start_time=datetime.now()
        )
    ]
    
    report = TestExecutionReport.from_results(results)
    jira_client = MockJiraClient()
    
    # Configure with Jira disabled
    config = JiraUpdateConfig(enabled=False)
    
    print("📋 Configuration:")
    print(f"   Jira integration enabled: {config.enabled}")
    print()
    
    integration = JiraIntegration(jira_client, config)
    summary = await integration.process_test_results(report)
    
    print("✅ Processing Complete")
    print(f"   Jira enabled: {summary['enabled']}")
    print()
    print("💡 No Jira updates were performed because integration is disabled")
    print()


async def main():
    """Run all demos."""
    print("\n")
    print("=" * 80)
    print("JIRA INTEGRATION FOR TEST EXECUTION DEMO")
    print("=" * 80)
    print("This demo showcases Jira integration features:")
    print("  • Automatic issue creation for test failures")
    print("  • Test scenario status updates")
    print("  • Issue linking and traceability")
    print("  • Configurable update policies")
    print("  • Detailed failure descriptions")
    print("  • Priority assignment based on failure type")
    print("=" * 80)
    print("\n")
    
    # Run demos
    await demo_jira_integration()
    await demo_jira_policies()
    await demo_jira_disabled()
    
    print("=" * 80)
    print("✅ All demos completed!")
    print("=" * 80)
    print()
    print("💡 Key Features Demonstrated:")
    print("   • Automatic Jira issue creation for failures")
    print("   • Test scenario updates with execution results")
    print("   • Issue linking for traceability")
    print("   • Configurable update policies (always, failures only, never)")
    print("   • Detailed failure descriptions with error messages")
    print("   • Priority assignment (errors = high, failures = configurable)")
    print("   • Label management for categorization")
    print("   • Summary reporting")
    print()
    print("🔧 Configuration Options:")
    print("   • enabled: Enable/disable Jira integration")
    print("   • create_issues_for_failures: Auto-create issues for failures")
    print("   • update_test_scenarios: Update test scenario status")
    print("   • policy: When to update (always, failures_only, never)")
    print("   • failure_priority: Priority for failure issues")
    print("   • failure_labels: Labels to apply to failure issues")
    print("   • link_to_scenarios: Link failures to test scenarios")
    print()
    print("📋 Requirements Satisfied:")
    print("   ✅ 19.1 - Update Jira test scenarios with execution results")
    print("   ✅ 19.2 - Create Jira issues for failed tests")
    print("   ✅ 19.3 - Apply appropriate labels, priorities, and assignments")
    print("   ✅ 19.4 - Link created issues to original test scenarios")
    print("   ✅ 19.5 - Support configurable Jira update policies")
    print()


if __name__ == "__main__":
    asyncio.run(main())
