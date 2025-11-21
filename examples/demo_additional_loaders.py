"""Demo of additional Distribution Agent loaders: Salesforce, API, and File."""

import asyncio
import pandas as pd
from pathlib import Path
from agents.distribution import DistributionAgent, TargetConfig

# Sample synthetic data
sample_data = pd.DataFrame({
    'Name': ['Acme Corp', 'Global Inc', 'Tech Solutions', 'Data Systems', 'Cloud Services'],
    'Type': ['Customer', 'Partner', 'Customer', 'Partner', 'Customer'],
    'Industry': ['Technology', 'Manufacturing', 'Technology', 'Finance', 'Technology'],
    'External_Id__c': ['ACC001', 'ACC002', 'ACC003', 'ACC004', 'ACC005'],
    'Revenue': [1000000, 2500000, 750000, 1800000, 3200000],
    'Employees': [50, 200, 30, 150, 400]
})


async def demo_salesforce_loader():
    """Demo Salesforce Bulk API loader."""
    print("=" * 80)
    print("SALESFORCE BULK API LOADER DEMO")
    print("=" * 80)
    print("This demo shows loading data to Salesforce using Bulk API 2.0")
    print("⚠️  Note: This uses placeholder credentials and will show expected failures")
    print("=" * 80)
    print()
    
    # Configure Salesforce target
    salesforce_config = TargetConfig(
        name="salesforce_demo",
        type="salesforce",
        load_strategy="upsert",
        tables=["Account"],
        table_mappings={
            "Account": ["Name", "Type", "Industry", "External_Id__c"]
        },
        external_id_fields={
            "Account": "External_Id__c"
        },
        batch_size=100,
        salesforce_username="demo@example.com",
        salesforce_password="demo_password",
        salesforce_security_token="demo_token",
        salesforce_domain="test",  # sandbox
        salesforce_api_version="58.0"
    )
    
    # Load data
    agent = DistributionAgent()
    print(f"📊 Loading {len(sample_data)} records to Salesforce...")
    print(f"   Strategy: {salesforce_config.load_strategy}")
    print(f"   Object: Account")
    print(f"   External ID: External_Id__c")
    print()
    
    report = await agent.process(sample_data, [salesforce_config])
    
    # Display results
    print("📈 Results:")
    for result in report.results:
        if result.status == 'success':
            print(f"   ✅ {result.target}: {result.records_loaded} records loaded in {result.duration:.2f}s")
        else:
            print(f"   ❌ {result.target}: {result.error}")
            print(f"      This is expected without real Salesforce credentials")
    print()


async def demo_api_loader():
    """Demo REST API loader."""
    print("=" * 80)
    print("REST API LOADER DEMO")
    print("=" * 80)
    print("This demo shows loading data via REST API")
    print("=" * 80)
    print()
    
    # Configure API target
    api_config = TargetConfig(
        name="api_demo",
        type="api",
        api_url="https://httpbin.org/post",  # Test endpoint
        api_method="POST",
        api_headers={
            "X-Custom-Header": "SyntheticData"
        },
        batch_size=2  # Small batches for demo
    )
    
    # Load data
    agent = DistributionAgent()
    print(f"📊 Sending {len(sample_data)} records to API...")
    print(f"   URL: {api_config.api_url}")
    print(f"   Method: {api_config.api_method}")
    print(f"   Batch size: {api_config.batch_size}")
    print()
    
    report = await agent.process(sample_data, [api_config])
    
    # Display results
    print("📈 Results:")
    for result in report.results:
        if result.status == 'success':
            print(f"   ✅ {result.target}: {result.records_loaded} records sent in {result.duration:.2f}s")
        else:
            print(f"   ❌ {result.target}: {result.error}")
    print()


async def demo_file_loader_local():
    """Demo local file storage loader."""
    print("=" * 80)
    print("FILE STORAGE LOADER DEMO - Local Files")
    print("=" * 80)
    print("This demo shows saving data to local files in various formats")
    print("=" * 80)
    print()
    
    # Create output directory
    output_dir = Path("data/distribution_demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure file targets for different formats
    configs = [
        TargetConfig(
            name="csv_file",
            type="file",
            file_path=str(output_dir / "accounts.csv"),
            file_format="csv"
        ),
        TargetConfig(
            name="json_file",
            type="file",
            file_path=str(output_dir / "accounts.json"),
            file_format="json"
        ),
        TargetConfig(
            name="parquet_file",
            type="file",
            file_path=str(output_dir / "accounts.parquet"),
            file_format="parquet"
        )
    ]
    
    # Load data
    agent = DistributionAgent()
    print(f"📊 Saving {len(sample_data)} records to local files...")
    print(f"   Output directory: {output_dir}")
    print(f"   Formats: CSV, JSON, Parquet")
    print()
    
    report = await agent.process(sample_data, configs)
    
    # Display results
    print("📈 Results:")
    for result in report.results:
        if result.status == 'success':
            print(f"   ✅ {result.target}: {result.records_loaded} records saved to {result.tables_loaded[0]}")
        else:
            print(f"   ❌ {result.target}: {result.error}")
    print()
    
    # Verify files exist
    print("📁 Verifying files:")
    for config in configs:
        file_path = Path(config.file_path)
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"   ✅ {file_path.name}: {size:,} bytes")
        else:
            print(f"   ❌ {file_path.name}: Not found")
    print()


async def demo_file_loader_s3():
    """Demo S3 file storage loader."""
    print("=" * 80)
    print("FILE STORAGE LOADER DEMO - Amazon S3")
    print("=" * 80)
    print("This demo shows uploading data to Amazon S3")
    print("⚠️  Note: Requires AWS credentials and boto3 installed")
    print("=" * 80)
    print()
    
    # Configure S3 target
    s3_config = TargetConfig(
        name="s3_demo",
        type="file",
        s3_bucket="my-synthetic-data-bucket",  # Replace with your bucket
        s3_prefix="demo/accounts",
        file_format="parquet"
    )
    
    # Load data
    agent = DistributionAgent()
    print(f"📊 Uploading {len(sample_data)} records to S3...")
    print(f"   Bucket: {s3_config.s3_bucket}")
    print(f"   Prefix: {s3_config.s3_prefix}")
    print(f"   Format: {s3_config.file_format}")
    print()
    
    try:
        report = await agent.process(sample_data, [s3_config])
        
        # Display results
        print("📈 Results:")
        for result in report.results:
            if result.status == 'success':
                print(f"   ✅ {result.target}: {result.records_loaded} records uploaded to {result.tables_loaded[0]}")
            else:
                print(f"   ❌ {result.target}: {result.error}")
    except Exception as e:
        print(f"   ❌ S3 upload failed: {str(e)}")
        print(f"      This is expected without AWS credentials or boto3")
    print()


async def demo_multi_target():
    """Demo loading to multiple targets simultaneously."""
    print("=" * 80)
    print("MULTI-TARGET DISTRIBUTION DEMO")
    print("=" * 80)
    print("This demo shows distributing data to multiple targets at once")
    print("=" * 80)
    print()
    
    # Create output directory
    output_dir = Path("data/distribution_demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure multiple targets
    configs = [
        TargetConfig(
            name="local_csv",
            type="file",
            file_path=str(output_dir / "multi_target.csv"),
            file_format="csv"
        ),
        TargetConfig(
            name="local_json",
            type="file",
            file_path=str(output_dir / "multi_target.json"),
            file_format="json"
        ),
        TargetConfig(
            name="api_endpoint",
            type="api",
            api_url="https://httpbin.org/post",
            api_method="POST",
            batch_size=5
        )
    ]
    
    # Load data
    agent = DistributionAgent()
    print(f"📊 Distributing {len(sample_data)} records to {len(configs)} targets...")
    for config in configs:
        print(f"   • {config.name} ({config.type})")
    print()
    
    report = await agent.process(sample_data, configs)
    
    # Display results
    print("📈 Results:")
    print(f"   Total targets: {report.total_targets}")
    print(f"   Successful: {report.successful_targets}")
    print(f"   Failed: {report.failed_targets}")
    print(f"   Total records: {report.total_records}")
    print(f"   Total duration: {report.total_duration:.2f}s")
    print()
    
    for result in report.results:
        status_icon = "✅" if result.status == 'success' else "❌"
        print(f"   {status_icon} {result.target}:")
        print(f"      Status: {result.status}")
        print(f"      Records: {result.records_loaded}")
        print(f"      Duration: {result.duration:.2f}s")
        if result.error:
            print(f"      Error: {result.error}")
    print()


async def main():
    """Run all demos."""
    print("\n")
    print("=" * 80)
    print("DISTRIBUTION AGENT - ADDITIONAL LOADERS DEMO")
    print("=" * 80)
    print("This demo showcases the additional loaders in the Distribution Agent:")
    print("  • Salesforce Bulk API loader")
    print("  • REST API loader")
    print("  • File storage loader (local and S3)")
    print("=" * 80)
    print("\n")
    
    # Run demos
    await demo_salesforce_loader()
    await demo_api_loader()
    await demo_file_loader_local()
    await demo_file_loader_s3()
    await demo_multi_target()
    
    print("=" * 80)
    print("✅ All demos completed!")
    print("=" * 80)
    print()
    print("💡 Key Features Demonstrated:")
    print("   • Salesforce Bulk API 2.0 integration with upsert support")
    print("   • REST API loading with retry logic and batch processing")
    print("   • Local file storage in CSV, JSON, and Parquet formats")
    print("   • Amazon S3 upload support")
    print("   • Multi-target distribution with comprehensive reporting")
    print()
    print("🔧 Setup for Real Usage:")
    print("   Salesforce:")
    print("     - Install: pip install requests pandas")
    print("     - Set credentials in TargetConfig")
    print("   API:")
    print("     - Install: pip install requests")
    print("     - Configure API URL and authentication")
    print("   S3:")
    print("     - Install: pip install boto3")
    print("     - Configure AWS credentials")
    print()


if __name__ == "__main__":
    asyncio.run(main())
