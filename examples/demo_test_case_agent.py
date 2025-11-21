"""Demo of Test Case Agent with Jira integration."""

import asyncio
from pathlib import Path
from agents.test_case import TestCaseAgent, TestCaseConfig


async def demo_robot_framework():
    """Demo Robot Framework test generation."""
    print("=" * 80)
    print("TEST CASE AGENT DEMO - Robot Framework")
    print("=" * 80)
    print("This demo shows generating Robot Framework tests from Jira scenarios")
    print("=" * 80)
    print()
    
    # Configure agent with mock Jira
    config = TestCaseConfig(
        jira_url="https://mock-jira.example.com",
        jira_username="demo@example.com",
        jira_api_token="mock_token",
        jira_project_key="TEST",
        test_tag="smoke",
        framework="robot",
        output_dir="tests/generated/robot",
        use_mock=True
    )
    
    # Create agent
    agent = TestCaseAgent(config)
    
    print(f"📊 Retrieving test scenarios from Jira...")
    print(f"   Project: {config.jira_project_key}")
    print(f"   Tag: {config.test_tag}")
    print(f"   Framework: {config.framework}")
    print()
    
    # Generate test cases
    test_cases = await agent.process()
    
    print(f"✅ Generated {len(test_cases)} test cases")
    print()
    
    # Display test cases
    for tc in test_cases:
        print(f"📝 Test Case: {tc.name}")
        print(f"   ID: {tc.id}")
        print(f"   Jira Key: {tc.jira_key}")
        print(f"   Framework: {tc.framework}")
        print(f"   Data References: {tc.data_references if tc.data_references else 'None'}")
        print(f"   File: tests/generated/robot/{tc.id.lower().replace('-', '_')}.robot")
        print()
    
    # Show sample code
    if test_cases:
        print("📄 Sample Generated Code:")
        print("-" * 80)
        print(test_cases[0].code[:500] + "..." if len(test_cases[0].code) > 500 else test_cases[0].code)
        print("-" * 80)
        print()
    
    agent.close()


async def demo_selenium():
    """Demo Selenium test generation."""
    print("=" * 80)
    print("TEST CASE AGENT DEMO - Selenium")
    print("=" * 80)
    print("This demo shows generating Selenium (Python) tests from Jira scenarios")
    print("=" * 80)
    print()
    
    # Configure agent with mock Jira
    config = TestCaseConfig(
        jira_url="https://mock-jira.example.com",
        jira_username="demo@example.com",
        jira_api_token="mock_token",
        jira_project_key="TEST",
        test_tag="integration",
        framework="selenium",
        output_dir="tests/generated/selenium",
        use_mock=True
    )
    
    # Create agent
    agent = TestCaseAgent(config)
    
    print(f"📊 Retrieving test scenarios from Jira...")
    print(f"   Project: {config.jira_project_key}")
    print(f"   Tag: {config.test_tag}")
    print(f"   Framework: {config.framework}")
    print()
    
    # Generate test cases
    test_cases = await agent.process()
    
    print(f"✅ Generated {len(test_cases)} test cases")
    print()
    
    # Display test cases
    for tc in test_cases:
        print(f"📝 Test Case: {tc.name}")
        print(f"   ID: {tc.id}")
        print(f"   Framework: {tc.framework}")
        print(f"   File: tests/generated/selenium/{tc.id.lower().replace('-', '_')}.py")
        print()
    
    # Show sample code
    if test_cases:
        print("📄 Sample Generated Code:")
        print("-" * 80)
        print(test_cases[0].code[:500] + "..." if len(test_cases[0].code) > 500 else test_cases[0].code)
        print("-" * 80)
        print()
    
    agent.close()


async def demo_playwright():
    """Demo Playwright test generation."""
    print("=" * 80)
    print("TEST CASE AGENT DEMO - Playwright")
    print("=" * 80)
    print("This demo shows generating Playwright (Python) tests from Jira scenarios")
    print("=" * 80)
    print()
    
    # Configure agent with mock Jira
    config = TestCaseConfig(
        jira_url="https://mock-jira.example.com",
        jira_username="demo@example.com",
        jira_api_token="mock_token",
        jira_project_key="TEST",
        test_tag="regression",
        framework="playwright",
        output_dir="tests/generated/playwright",
        use_mock=True
    )
    
    # Create agent
    agent = TestCaseAgent(config)
    
    print(f"📊 Retrieving test scenarios from Jira...")
    print(f"   Project: {config.jira_project_key}")
    print(f"   Tag: {config.test_tag}")
    print(f"   Framework: {config.framework}")
    print()
    
    # Generate test cases
    test_cases = await agent.process()
    
    print(f"✅ Generated {len(test_cases)} test cases")
    print()
    
    # Display test cases
    for tc in test_cases:
        print(f"📝 Test Case: {tc.name}")
        print(f"   ID: {tc.id}")
        print(f"   Framework: {tc.framework}")
        print(f"   File: tests/generated/playwright/{tc.id.lower().replace('-', '_')}.py")
        print()
    
    # Show sample code
    if test_cases:
        print("📄 Sample Generated Code:")
        print("-" * 80)
        print(test_cases[0].code[:500] + "..." if len(test_cases[0].code) > 500 else test_cases[0].code)
        print("-" * 80)
        print()
    
    agent.close()


async def demo_test_case_retrieval():
    """Demo test case retrieval."""
    print("=" * 80)
    print("TEST CASE RETRIEVAL DEMO")
    print("=" * 80)
    print("This demo shows retrieving and listing generated test cases")
    print("=" * 80)
    print()
    
    # Configure agent
    config = TestCaseConfig(
        jira_url="https://mock-jira.example.com",
        jira_username="demo@example.com",
        jira_api_token="mock_token",
        jira_project_key="TEST",
        test_tag="smoke",
        framework="robot",
        output_dir="tests/generated/robot",
        use_mock=True
    )
    
    agent = TestCaseAgent(config)
    
    # List test cases
    print("📋 Listing generated test cases...")
    test_ids = agent.list_test_cases()
    
    if test_ids:
        print(f"   Found {len(test_ids)} test cases:")
        for test_id in test_ids:
            print(f"   • {test_id}")
        print()
        
        # Retrieve a specific test case
        print(f"📖 Retrieving test case: {test_ids[0]}")
        test_case = agent.get_test_case(test_ids[0])
        
        if test_case:
            print(f"   Name: {test_case.name}")
            print(f"   Framework: {test_case.framework}")
            print(f"   Created: {test_case.created_at}")
            print(f"   Data References: {test_case.data_references if test_case.data_references else 'None'}")
            print()
    else:
        print("   No test cases found. Run generation demos first.")
        print()
    
    agent.close()


async def main():
    """Run all demos."""
    print("\n")
    print("=" * 80)
    print("TEST CASE AGENT DEMO")
    print("=" * 80)
    print("This demo showcases the Test Case Agent:")
    print("  • Jira integration for test scenario retrieval")
    print("  • Test code generation for multiple frameworks")
    print("  • Data reference extraction")
    print("  • Test case storage and retrieval")
    print("=" * 80)
    print("\n")
    
    # Run demos
    await demo_robot_framework()
    await demo_selenium()
    await demo_playwright()
    await demo_test_case_retrieval()
    
    print("=" * 80)
    print("✅ All demos completed!")
    print("=" * 80)
    print()
    print("💡 Key Features Demonstrated:")
    print("   • Mock Jira client for demo without real Jira access")
    print("   • Test scenario retrieval by tag")
    print("   • Robot Framework test generation")
    print("   • Selenium (Python) test generation")
    print("   • Playwright (Python) test generation")
    print("   • Data reference extraction from scenarios")
    print("   • Test case storage and retrieval")
    print()
    print("🔧 Setup for Real Usage:")
    print("   1. Install: pip install requests")
    print("   2. Set Jira credentials in TestCaseConfig")
    print("   3. Set use_mock=False")
    print("   4. Tag test scenarios in Jira")
    print()
    print("📁 Generated Files:")
    print("   • tests/generated/robot/*.robot")
    print("   • tests/generated/selenium/*.py")
    print("   • tests/generated/playwright/*.py")
    print("   • tests/generated/*/*.json (metadata)")
    print()


if __name__ == "__main__":
    asyncio.run(main())
