"""Demo script showing Confluence integration with Data Processor Agent."""

import asyncio
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.data_processor.agent import DataProcessorAgent
from shared.utils.confluence_client import create_confluence_client


async def demo_confluence_search():
    """Demonstrate Confluence search functionality."""
    print("=" * 80)
    print("DEMO: Confluence Search")
    print("=" * 80)
    
    # Create mock Confluence client
    confluence = create_confluence_client(demo_mode=True)
    
    # Test searches
    test_queries = [
        'email field',
        'phone number',
        'customer name',
        'payment information',
    ]
    
    for query in test_queries:
        print(f"\nSearching for: '{query}'")
        print("-" * 40)
        
        results = await confluence.search(query, limit=2)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result.title}")
                print(f"   Space: {result.space}")
                print(f"   URL: {result.url}")
                print(f"   Excerpt: {result.excerpt}")
        else:
            print("   No results found")


async def demo_data_processor_with_confluence():
    """Demonstrate Data Processor Agent with Confluence integration."""
    print("\n" + "=" * 80)
    print("DEMO: Data Processor Agent with Confluence Integration")
    print("=" * 80)
    
    # Create Confluence client (demo mode)
    confluence = create_confluence_client(demo_mode=True)
    
    # Create Data Processor Agent with Confluence
    agent = DataProcessorAgent(
        confluence_client=confluence,
        bedrock_client=None  # Using mock Bedrock in Confluence classifier
    )
    
    # Process sample data
    data_file = Path(__file__).parent.parent / '.kiro' / 'specs' / 'synthetic-data-generator' / 'MGW_File.csv'
    
    if not data_file.exists():
        print(f"\nError: Sample data file not found: {data_file}")
        print("Please ensure MGW_File.csv exists in the specs directory.")
        return
    
    print(f"\nProcessing data file: {data_file.name}")
    print("This will use Confluence to enhance field classification...\n")
    
    # Process the data
    report = await agent.process_async(data_file)
    
    # Display results
    print(f"\nSensitivity Report Summary:")
    print(f"  Total fields: {report.total_fields}")
    print(f"  Sensitive fields: {report.sensitive_fields}")
    print(f"  Confidence distribution: {report.confidence_distribution}")
    
    # Show fields with Confluence references
    print(f"\nFields with Confluence Documentation:")
    print("-" * 80)
    
    confluence_enhanced = [
        (name, classification)
        for name, classification in report.classifications.items()
        if classification.confluence_references
    ]
    
    if confluence_enhanced:
        for field_name, classification in confluence_enhanced:
            print(f"\n{field_name}:")
            print(f"  Sensitive: {classification.is_sensitive}")
            print(f"  Type: {classification.sensitivity_type}")
            print(f"  Confidence: {classification.confidence:.2f}")
            print(f"  Reasoning: {classification.reasoning}")
            print(f"  Confluence References:")
            for ref in classification.confluence_references:
                print(f"    - {ref}")
    else:
        print("  No fields were enhanced with Confluence documentation")
        print("  (This may happen if field names don't match Confluence content)")
    
    # Show top 5 most sensitive fields
    print(f"\nTop 5 Most Sensitive Fields:")
    print("-" * 80)
    
    sorted_fields = sorted(
        report.classifications.items(),
        key=lambda x: x[1].confidence,
        reverse=True
    )[:5]
    
    for field_name, classification in sorted_fields:
        print(f"\n{field_name}:")
        print(f"  Confidence: {classification.confidence:.2f}")
        print(f"  Type: {classification.sensitivity_type}")
        print(f"  Strategy: {classification.recommended_strategy}")


async def demo_configuration_toggle():
    """Demonstrate configuration toggle between mock and real Confluence."""
    print("\n" + "=" * 80)
    print("DEMO: Configuration Toggle (Mock vs Real)")
    print("=" * 80)
    
    # Demo mode (mock)
    print("\n1. Creating Confluence client in DEMO mode:")
    mock_client = create_confluence_client(demo_mode=True)
    print(f"   Client type: {type(mock_client).__name__}")
    print(f"   Ready for demo presentations: ✓")
    
    # Real mode (would require credentials)
    print("\n2. Creating Confluence client in REAL mode:")
    print("   (This would require actual credentials)")
    try:
        real_client = create_confluence_client(
            demo_mode=False,
            base_url="https://company.atlassian.net/wiki",
            username="user@example.com",
            api_token="fake-token-for-demo"
        )
        print(f"   Client type: {type(real_client).__name__}")
        print(f"   Note: Real API calls would be made in production")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Show how to use in agent
    print("\n3. Using with Data Processor Agent:")
    print("   # Demo mode")
    print("   confluence = create_confluence_client(demo_mode=True)")
    print("   agent = DataProcessorAgent(confluence_client=confluence)")
    print()
    print("   # Production mode")
    print("   confluence = create_confluence_client(")
    print("       demo_mode=False,")
    print("       base_url=os.getenv('CONFLUENCE_URL'),")
    print("       username=os.getenv('CONFLUENCE_USER'),")
    print("       api_token=os.getenv('CONFLUENCE_TOKEN')")
    print("   )")
    print("   agent = DataProcessorAgent(confluence_client=confluence)")


async def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("CONFLUENCE INTEGRATION DEMO")
    print("=" * 80)
    
    # Run demos
    await demo_confluence_search()
    await demo_data_processor_with_confluence()
    await demo_configuration_toggle()
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\nKey Features Demonstrated:")
    print("  ✓ Mock Confluence client for demo mode")
    print("  ✓ Confluence search with realistic latency")
    print("  ✓ Knowledge-based field classification")
    print("  ✓ Bedrock LLM integration (mocked)")
    print("  ✓ Configuration toggle (demo vs production)")
    print("  ✓ Confluence reference tracking")
    print("  ✓ Enhanced sensitivity reporting")
    print()


if __name__ == '__main__':
    asyncio.run(main())
