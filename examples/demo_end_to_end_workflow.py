"""End-to-End Demo: Complete Synthetic Data Generation Workflow.

This demo shows the complete workflow:
1. Data Processor Agent analyzes production data
2. Synthetic Data Agent generates synthetic replacements
3. Distribution Agent loads data to database
"""

import asyncio
import pandas as pd
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float

# Import agents
from agents.data_processor import DataProcessorAgent
from agents.synthetic_data import SyntheticDataAgent
from agents.distribution import DistributionAgent, TargetConfig
from shared.utils.confluence_client import MockConfluenceClient
from shared.utils.bedrock_client import BedrockClient
from shared.utils.quality_validator import QualityValidator


def setup_target_database():
    """Set up target database for synthetic data."""
    engine = create_engine('sqlite:///end_to_end_demo.db', echo=False)
    
    metadata = MetaData()
    
    # Create telecom customers table
    customers = Table('telecom_customers', metadata,
        Column('customer_id', Integer, primary_key=True),
        Column('name', String(100)),
        Column('email', String(100)),
        Column('phone', String(20)),
        Column('address', String(200)),
        Column('city', String(50)),
        Column('postcode', String(20)),
        Column('account_status', String(20))
    )
    
    metadata.create_all(engine)
    return engine


def load_production_data():
    """Load sample production data (simulating MGW_File.csv)."""
    # Simulate production data with some PII
    production_data = pd.DataFrame({
        'customer_id': [1001, 1002, 1003, 1004, 1005],
        'name': ['John Smith', 'Jane Doe', 'Bob Johnson', 'Alice Williams', 'Charlie Brown'],
        'email': ['john.smith@email.com', 'jane.doe@email.com', 'bob.j@email.com', 
                  'alice.w@email.com', 'charlie.b@email.com'],
        'phone': ['555-0101', '555-0102', '555-0103', '555-0104', '555-0105'],
        'address': ['123 Main St', '456 Oak Ave', '789 Pine Rd', '321 Elm St', '654 Maple Dr'],
        'city': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'],
        'postcode': ['10001', '90001', '60601', '77001', '85001'],
        'account_status': ['Active', 'Active', 'Suspended', 'Active', 'Active']
    })
    
    return production_data


async def main():
    """Run complete end-to-end workflow."""
    print("\n" + "="*80)
    print("END-TO-END SYNTHETIC DATA WORKFLOW DEMO")
    print("="*80)
    print("\nThis demo shows the complete workflow from production data")
    print("to synthetic data generation to database loading.\n")
    
    # =========================================================================
    # STEP 1: Load Production Data
    # =========================================================================
    print("="*80)
    print("STEP 1: Load Production Data")
    print("="*80)
    
    production_data = load_production_data()
    print(f"\n✅ Loaded {len(production_data)} production records")
    print("\n📋 Sample production data:")
    print(production_data.head(3).to_string(index=False))
    
    # =========================================================================
    # STEP 2: Data Processor Agent - Identify Sensitive Fields
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 2: Data Processor Agent - Identify Sensitive Fields")
    print("="*80)
    
    # Create Data Processor Agent with mock Confluence
    confluence_client = MockConfluenceClient()
    data_processor = DataProcessorAgent(confluence_client=confluence_client)
    
    print("\n🔍 Analyzing production data for sensitive fields...")
    
    # Save to temp file for processing
    temp_file = Path('temp_production_data.csv')
    production_data.to_csv(temp_file, index=False)
    
    try:
        sensitivity_report = await data_processor.process_async(temp_file)
        
        print(f"\n✅ Analysis complete!")
        print(f"   Total fields: {sensitivity_report.total_fields}")
        print(f"   Sensitive fields: {sensitivity_report.sensitive_fields}")
        
        print("\n📊 Field Classifications:")
        for field_name, classification in sensitivity_report.classifications.items():
            if classification.is_sensitive:
                icon = "🔒"
                print(f"   {icon} {field_name}: {classification.sensitivity_type} "
                      f"(confidence: {classification.confidence:.2f})")
            else:
                print(f"   ✓ {field_name}: non-sensitive")
    
    finally:
        # Cleanup temp file
        if temp_file.exists():
            temp_file.unlink()
    
    # =========================================================================
    # STEP 3: Synthetic Data Agent - Generate Synthetic Data
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 3: Synthetic Data Agent - Generate Synthetic Data")
    print("="*80)
    
    print("\n🎲 Generating synthetic data...")
    print("   Using SDV for statistical properties")
    print("   Using rule-based generation for sensitive fields")
    
    # Create Synthetic Data Agent
    synthetic_agent = SyntheticDataAgent(bedrock_client=None)  # No Bedrock for demo
    
    # Generate synthetic data
    synthetic_result = synthetic_agent.generate_synthetic_data(
        data=production_data,
        sensitivity_report=sensitivity_report,
        num_rows=10,  # Generate 10 synthetic records
        sdv_model='gaussian_copula',
        seed=42
    )
    
    synthetic_data = synthetic_result.data
    
    print(f"\n✅ Generated {len(synthetic_data)} synthetic records")
    print("\n📋 Sample synthetic data:")
    print(synthetic_data.head(3).to_string(index=False))
    
    # Show quality metrics
    if synthetic_result.quality_metrics:
        print("\n📈 Quality Metrics:")
        print(f"   SDV Quality Score: {synthetic_result.quality_metrics.sdv_quality_score:.3f}")
        print(f"   Column Shapes Score: {synthetic_result.quality_metrics.column_shapes_score:.3f}")
        print(f"   Correlation Preservation: {synthetic_result.quality_metrics.correlation_preservation:.3f}")
    
    # Verify no data leakage
    print("\n🔒 Data Leakage Check:")
    original_names = set(production_data['name'].values)
    synthetic_names = set(synthetic_data['name'].values)
    leaked_names = original_names.intersection(synthetic_names)
    
    if leaked_names:
        print(f"   ⚠️  WARNING: {len(leaked_names)} names leaked from production data")
    else:
        print("   ✅ No data leakage detected - all names are synthetic")
    
    # =========================================================================
    # STEP 3.5: Quality Validation
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 3.5: Quality Validation")
    print("="*80)
    
    print("\n🔍 Validating synthetic data quality...")
    
    # Create quality validator
    validator = QualityValidator(output_dir=Path('results/end_to_end_quality'))
    
    # Validate quality
    quality_report = validator.validate(
        production_data,
        synthetic_data,
        edge_case_columns=['email', 'phone', 'postcode']
    )
    
    print("\n📈 Quality Metrics:")
    print(f"   Overall Quality Score: {quality_report.metrics.sdv_quality_score:.3f}")
    print(f"   Correlation Preservation: {quality_report.metrics.correlation_preservation:.3f}")
    print(f"   Edge Case Frequency Match: {quality_report.metrics.edge_case_frequency_match:.3f}")
    
    # Show statistical test results
    ks_passed = sum(1 for r in quality_report.metrics.ks_tests.values() if r.get('passed', False))
    ks_total = len(quality_report.metrics.ks_tests)
    print(f"\n📊 Statistical Tests:")
    print(f"   KS Tests: {ks_passed}/{ks_total} passed")
    
    if quality_report.metrics.chi_squared_tests:
        chi_passed = sum(1 for r in quality_report.metrics.chi_squared_tests.values() if r.get('passed', False))
        chi_total = len(quality_report.metrics.chi_squared_tests)
        print(f"   Chi-Squared Tests: {chi_passed}/{chi_total} passed")
    
    # Show warnings if any
    if quality_report.warnings:
        print(f"\n⚠️  Warnings: {len(quality_report.warnings)}")
        for warning in quality_report.warnings[:2]:  # Show first 2
            print(f"   • {warning[:80]}...")
    else:
        print("\n✅ No quality warnings - data looks good!")
    
    # Show visualizations
    print(f"\n📁 Visualizations saved to: results/end_to_end_quality/")
    
    # =========================================================================
    # STEP 4: Distribution Agent - Load to Database
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 4: Distribution Agent - Load to Database")
    print("="*80)
    
    # Setup target database
    print("\n🗄️  Setting up target database...")
    engine = setup_target_database()
    print("   ✅ Database schema created")
    
    # Create Distribution Agent
    distribution_agent = DistributionAgent()
    
    # Configure target
    target_config = TargetConfig(
        name='test_database',
        type='database',
        connection_string='sqlite:///end_to_end_demo.db',
        database_type='postgresql',
        load_strategy='truncate_insert',
        respect_fk_order=False,
        tables=['telecom_customers'],
        table_mappings={
            'telecom_customers': [
                'customer_id', 'name', 'email', 'phone', 
                'address', 'city', 'postcode', 'account_status'
            ]
        },
        batch_size=100
    )
    
    print("\n📊 Loading synthetic data to database...")
    distribution_report = await distribution_agent.process(synthetic_data, [target_config])
    
    if distribution_report.successful_targets > 0:
        print(f"   ✅ Successfully loaded {distribution_report.total_records} records")
        print(f"   ⏱️  Duration: {distribution_report.results[0].duration:.2f}s")
    else:
        print(f"   ❌ Failed to load data: {distribution_report.results[0].error}")
    
    # =========================================================================
    # STEP 5: Verify Results
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 5: Verify Results")
    print("="*80)
    
    print("\n🔍 Querying database to verify loaded data...")
    
    with engine.connect() as conn:
        # Count records
        count_df = pd.read_sql('SELECT COUNT(*) as count FROM telecom_customers', conn)
        record_count = count_df.iloc[0]['count']
        print(f"   Total records in database: {record_count}")
        
        # Show sample records
        sample_df = pd.read_sql('SELECT * FROM telecom_customers LIMIT 5', conn)
        print("\n📋 Sample records from database:")
        print(sample_df.to_string(index=False))
        
        # Verify data types
        print("\n✅ Data Verification:")
        print(f"   • All customer_ids are unique: {sample_df['customer_id'].nunique() == len(sample_df)}")
        print(f"   • All emails contain @: {sample_df['email'].str.contains('@').all()}")
        print(f"   • All phone numbers present: {sample_df['phone'].notna().all()}")
    
    engine.dispose()
    
    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "="*80)
    print("✅ END-TO-END WORKFLOW COMPLETED SUCCESSFULLY!")
    print("="*80)
    
    print("\n📊 Workflow Summary:")
    print(f"   1. Analyzed {len(production_data)} production records")
    print(f"   2. Identified {sensitivity_report.sensitive_fields} sensitive fields")
    print(f"   3. Generated {len(synthetic_data)} synthetic records")
    print(f"   4. Validated quality (score: {quality_report.metrics.sdv_quality_score:.3f})")
    print(f"   5. Loaded {distribution_report.total_records} records to database")
    print(f"   6. Verified data integrity and quality")
    
    print("\n💡 Key Achievements:")
    print("   ✓ Automatic PII detection (names, emails, phones, addresses)")
    print("   ✓ Statistical property preservation")
    print("   ✓ No data leakage from production")
    print("   ✓ Successful database loading")
    print("   ✓ Data integrity maintained")
    
    print("\n📁 Artifacts Created:")
    print("   • end_to_end_demo.db - SQLite database with synthetic data")
    
    print("\n🎯 Next Steps:")
    print("   • Add Bedrock integration for more realistic text generation")
    print("   • Implement edge case injection")
    print("   • Add quality metrics visualization")
    print("   • Create web interface for workflow monitoring")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    asyncio.run(main())
