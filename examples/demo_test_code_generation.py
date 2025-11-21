"""Demo of Test Case Agent with Bedrock-powered test code generation."""

import asyncio
from pathlib import Path
from agents.test_case import TestCaseAgent, TestCaseConfig


async def demo_template_based_generation():
    """Demo template-based test generation."""
    print("=" * 80)
    print("TEMPLATE-BASED TEST GENERATION")
    print("=" * 80)
    print("This demo shows traditional template-based test generation")
    print("=" * 80)
    print()
    
    config = TestCaseConfig(
        jira_url="https://mock-jira.example.com",
        jira_username="demo@example.com",
        jira_api_token="mock_token",
        jira_project_key="TEST",
        test_tag="smoke",
        framework="robot",
        output_dir="tests/generated/template",
        use_mock=True,
        use_bedrock=False  # Template-based
    )
    
    agent = TestCaseAgent(config)
    
    print("📊 Generating tests using templates...")
    print(f"   Framework: {config.framework}")
    print(f"   Method: Template-based")
    print()
    
    test_cases = await agent.process()
    
    print(f"✅ Generated {len(test_cases)} test cases")
    print()
    
    if test_cases:
        print("📄 Sample Generated Code (Template):")
        print("-" * 80)
        print(test_cases[0].code)
        print("-" * 80)
        print()
    
    agent.close()


async def demo_bedrock_generation():
    """Demo Bedrock-powered test generation."""
    print("=" * 80)
    print("BEDROCK-POWERED TEST GENERATION")
    print("=" * 80)
    print("This demo shows AI-powered test generation using Amazon Bedrock")
    print("⚠️  Note: Requires AWS credentials and Bedrock access")
    print("=" * 80)
    print()
    
    config = TestCaseConfig(
        jira_url="https://mock-jira.example.com",
        jira_username="demo@example.com",
        jira_api_token="mock_token",
        jira_project_key="TEST",
        test_tag="integration",
        framework="playwright",
        output_dir="tests/generated/bedrock",
        use_mock=True,
        use_bedrock=True  # Bedrock-powered
    )
    
    agent = TestCaseAgent(config)
    
    print("📊 Generating tests using Bedrock AI...")
    print(f"   Framework: {config.framework}")
    print(f"   Method: Bedrock AI")
    print(f"   Model: {config.bedrock_model}")
    print()
    
    try:
        test_cases = await agent.process()
        
        print(f"✅ Generated {len(test_cases)} test cases")
        print()
        
        if test_cases:
            print("📄 Sample Generated Code (Bedrock AI):")
            print("-" * 80)
            print(test_cases[0].code[:800] + "..." if len(test_cases[0].code) > 800 else test_cases[0].code)
            print("-" * 80)
            print()
            
            print("💡 AI-Generated Features:")
            print("   • Complete, executable test code")
            print("   • Intelligent step implementation")
            print("   • Proper assertions and error handling")
            print("   • Best practices for the framework")
            print("   • Context-aware test logic")
            print()
    
    except Exception as e:
        print(f"❌ Bedrock generation failed: {str(e)}")
        print("   This is expected without AWS credentials")
        print("   Falling back to template-based generation...")
        print()
    
    agent.close()


async def demo_data_reference_mapping():
    """Demo data reference extraction and mapping."""
    print("=" * 80)
    print("DATA REFERENCE MAPPING")
    print("=" * 80)
    print("This demo shows extracting and mapping synthetic data to tests")
    print("=" * 80)
    print()
    
    config = TestCaseConfig(
        jira_url="https://mock-jira.example.com",
        jira_username="demo@example.com",
        jira_api_token="mock_token",
        jira_project_key="TEST",
        test_tag="data-submission",
        framework="selenium",
        output_dir="tests/generated/data_mapping",
        use_mock=True,
        use_bedrock=False
    )
    
    agent = TestCaseAgent(config)
    
    print("📊 Generating test with data references...")
    test_cases = await agent.process()
    
    if test_cases:
        test_case = test_cases[0]
        
        print(f"✅ Generated test: {test_case.name}")
        print(f"   Data References: {test_case.data_references}")
        print()
        
        # Simulate synthetic data
        synthetic_data = {
            'username': 'john.doe@example.com',
            'password': 'SecurePass123!',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '+1-555-0123'
        }
        
        print("📦 Synthetic Data:")
        for key, value in synthetic_data.items():
            print(f"   {key}: {value}")
        print()
        
        # Map data to test
        print("🔗 Mapping data to test code...")
        mapped_code = agent.map_data_to_test(test_case, synthetic_data)
        
        print("✅ Data mapping complete")
        print()
        
        print("📄 Test Code with Mapped Data:")
        print("-" * 80)
        print(mapped_code[:500] + "..." if len(mapped_code) > 500 else mapped_code)
        print("-" * 80)
        print()
    
    agent.close()


async def demo_multi_framework_generation():
    """Demo generating tests for multiple frameworks."""
    print("=" * 80)
    print("MULTI-FRAMEWORK TEST GENERATION")
    print("=" * 80)
    print("This demo shows generating the same test for different frameworks")
    print("=" * 80)
    print()
    
    frameworks = ['robot', 'selenium', 'playwright']
    
    for framework in frameworks:
        print(f"📊 Generating {framework.upper()} test...")
        
        config = TestCaseConfig(
            jira_url="https://mock-jira.example.com",
            jira_username="demo@example.com",
            jira_api_token="mock_token",
            jira_project_key="TEST",
            test_tag="smoke",
            framework=framework,
            output_dir=f"tests/generated/multi/{framework}",
            use_mock=True,
            use_bedrock=False
        )
        
        agent = TestCaseAgent(config)
        test_cases = await agent.process()
        
        if test_cases:
            print(f"   ✅ Generated {len(test_cases)} test(s)")
            print(f"   📁 Output: tests/generated/multi/{framework}/")
        
        agent.close()
        print()
    
    print("✅ Multi-framework generation complete!")
    print()


async def demo_test_case_storage_retrieval():
    """Demo test case storage and retrieval."""
    print("=" * 80)
    print("TEST CASE STORAGE & RETRIEVAL")
    print("=" * 80)
    print("This demo shows storing and retrieving generated test cases")
    print("=" * 80)
    print()
    
    config = TestCaseConfig(
        jira_url="https://mock-jira.example.com",
        jira_username="demo@example.com",
        jira_api_token="mock_token",
        jira_project_key="TEST",
        test_tag="smoke",
        framework="robot",
        output_dir="tests/generated/storage",
        use_mock=True,
        use_bedrock=False
    )
    
    agent = TestCaseAgent(config)
    
    # Generate and store
    print("📊 Generating and storing test cases...")
    test_cases = await agent.process()
    print(f"   ✅ Stored {len(test_cases)} test cases")
    print()
    
    # List stored tests
    print("📋 Listing stored test cases...")
    test_ids = agent.list_test_cases()
    print(f"   Found {len(test_ids)} test cases:")
    for test_id in test_ids:
        print(f"   • {test_id}")
    print()
    
    # Retrieve a specific test
    if test_ids:
        print(f"📖 Retrieving test case: {test_ids[0]}")
        retrieved = agent.get_test_case(test_ids[0])
        
        if retrieved:
            print(f"   Name: {retrieved.name}")
            print(f"   Framework: {retrieved.framework}")
            print(f"   Created: {retrieved.created_at}")
            print(f"   Jira Key: {retrieved.jira_key}")
            print(f"   Data Refs: {retrieved.data_references if retrieved.data_references else 'None'}")
            print()
    
    agent.close()


async def main():
    """Run all demos."""
    print("\n")
    print("=" * 80)
    print("TEST CODE GENERATION DEMO")
    print("=" * 80)
    print("This demo showcases advanced test code generation:")
    print("  • Template-based generation (fast, deterministic)")
    print("  • Bedrock AI generation (intelligent, context-aware)")
    print("  • Data reference extraction and mapping")
    print("  • Multi-framework support")
    print("  • Test case storage and retrieval")
    print("=" * 80)
    print("\n")
    
    # Run demos
    await demo_template_based_generation()
    await demo_bedrock_generation()
    await demo_data_reference_mapping()
    await demo_multi_framework_generation()
    await demo_test_case_storage_retrieval()
    
    print("=" * 80)
    print("✅ All demos completed!")
    print("=" * 80)
    print()
    print("💡 Key Features Demonstrated:")
    print("   • Template-based test generation (fast, reliable)")
    print("   • Bedrock AI-powered generation (intelligent, adaptive)")
    print("   • Automatic fallback from AI to templates")
    print("   • Data reference extraction from Jira scenarios")
    print("   • Synthetic data mapping to test code")
    print("   • Multi-framework support (Robot, Selenium, Playwright)")
    print("   • Test case persistence with metadata")
    print("   • Test case retrieval and listing")
    print()
    print("🔧 Configuration Options:")
    print("   • use_bedrock: Enable/disable AI generation")
    print("   • use_mock: Use mock Jira for demos")
    print("   • framework: Choose test framework")
    print("   • bedrock_model: Select AI model")
    print()
    print("📁 Generated Files:")
    print("   • tests/generated/template/*.robot")
    print("   • tests/generated/bedrock/*.py")
    print("   • tests/generated/data_mapping/*.py")
    print("   • tests/generated/multi/*/*.{robot,py}")
    print("   • tests/generated/*/*.json (metadata)")
    print()


if __name__ == "__main__":
    asyncio.run(main())
