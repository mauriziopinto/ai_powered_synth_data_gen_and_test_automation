"""Demo of enhanced results export and sharing functionality."""

from shared.export.exporter import (
    ComprehensiveExporter,
    ResultsArchive,
    ExportConfig,
    ExportFormat
)
from datetime import datetime, timedelta


def demo_basic_export():
    """Demo basic export functionality."""
    print("=" * 80)
    print("BASIC EXPORT DEMO")
    print("=" * 80)
    print()
    
    # Create exporter
    config = ExportConfig(
        output_directory="exports/demo",
        compression=False,
        secure_links=True,
        link_expiration_hours=24
    )
    
    exporter = ComprehensiveExporter(config)
    
    # Sample data
    data = [
        {'id': 1, 'name': 'John Doe', 'email': 'john@example.com', 'age': 30, 'city': 'New York'},
        {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com', 'age': 25, 'city': 'London'},
        {'id': 3, 'name': 'Bob Johnson', 'email': 'bob@example.com', 'age': 35, 'city': 'Tokyo'},
        {'id': 4, 'name': 'Alice Brown', 'email': 'alice@example.com', 'age': 28, 'city': 'Paris'},
        {'id': 5, 'name': 'Charlie Wilson', 'email': 'charlie@example.com', 'age': 42, 'city': 'Sydney'}
    ]
    
    print("📊 Sample Data (5 records):")
    for record in data[:3]:
        print(f"   {record}")
    print(f"   ... and {len(data) - 3} more")
    print()
    
    # Export to different formats
    formats = [ExportFormat.CSV, ExportFormat.JSON, ExportFormat.PARQUET, ExportFormat.SQL]
    
    for format in formats:
        print(f"📤 Exporting to {format.value.upper()}...")
        result = exporter.export_data(data, format)
        
        print(f"   ✅ Export ID: {result.export_id}")
        print(f"   📁 File: {result.file_path}")
        print(f"   📏 Size: {result.file_size} bytes")
        if result.download_link:
            print(f"   🔗 Download: {result.download_link}")
            print(f"   ⏰ Expires: {result.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print()


def demo_compressed_export():
    """Demo compressed export functionality."""
    print("=" * 80)
    print("COMPRESSED EXPORT DEMO")
    print("=" * 80)
    print()
    
    config = ExportConfig(
        output_directory="exports/demo",
        compression=True,
        compression_level=9
    )
    
    exporter = ComprehensiveExporter(config)
    
    # Generate larger dataset
    data = [
        {
            'id': i,
            'name': f'User {i}',
            'email': f'user{i}@example.com',
            'description': f'This is a longer description for user {i} to demonstrate compression benefits'
        }
        for i in range(1000)
    ]
    
    print(f"📊 Generated {len(data)} records for compression test")
    print()
    
    print("📤 Exporting with compression...")
    result = exporter.export_data_compressed(data, ExportFormat.JSON)
    
    print(f"   ✅ Compressed export complete")
    print(f"   📁 File: {result.file_path}")
    print(f"   📏 Compressed size: {result.file_size:,} bytes")
    print(f"   💾 Compression ratio: ~{(1 - result.file_size / (len(str(data)))) * 100:.1f}%")
    print()


def demo_html_report():
    """Demo HTML report generation."""
    print("=" * 80)
    print("HTML REPORT DEMO")
    print("=" * 80)
    print()
    
    config = ExportConfig(output_directory="exports/demo")
    exporter = ComprehensiveExporter(config)
    
    # Sample report data
    report_data = {
        'title': 'Synthetic Data Quality Report',
        'metrics': {
            'total_records': 10000,
            'quality_score': 95.5,
            'similarity_score': 92.3,
            'generation_time_seconds': 45.2,
            'data_leakage_check': 'PASSED',
            'constraint_violations': 0
        },
        'details': [
            {'field': 'name', 'quality': 98.5, 'similarity': 95.0, 'status': 'Excellent'},
            {'field': 'email', 'quality': 99.2, 'similarity': 97.5, 'status': 'Excellent'},
            {'field': 'age', 'quality': 92.1, 'similarity': 88.3, 'status': 'Good'},
            {'field': 'address', 'quality': 94.7, 'similarity': 91.2, 'status': 'Good'},
            {'field': 'phone', 'quality': 96.3, 'similarity': 93.8, 'status': 'Excellent'}
        ]
    }
    
    print("📊 Generating HTML report with embedded metrics...")
    result = exporter.generate_html_report(report_data)
    
    print(f"   ✅ Report generated")
    print(f"   📁 File: {result.file_path}")
    print(f"   📏 Size: {result.file_size} bytes")
    print(f"   🌐 Open in browser to view formatted report")
    print()


def demo_pdf_report():
    """Demo PDF report generation."""
    print("=" * 80)
    print("PDF REPORT DEMO")
    print("=" * 80)
    print()
    
    config = ExportConfig(output_directory="exports/demo")
    exporter = ComprehensiveExporter(config)
    
    report_data = {
        'title': 'Workflow Execution Summary',
        'metrics': {
            'workflow_id': 'wf_demo_001',
            'execution_time': '3m 45s',
            'agents_executed': 5,
            'success_rate': '100%',
            'total_cost': '$2.45'
        },
        'details': [
            {'agent': 'Data Processor', 'status': 'Success', 'duration': '45s'},
            {'agent': 'Synthetic Generator', 'status': 'Success', 'duration': '120s'},
            {'agent': 'Quality Validator', 'status': 'Success', 'duration': '30s'},
            {'agent': 'Distributor', 'status': 'Success', 'duration': '25s'},
            {'agent': 'Test Executor', 'status': 'Success', 'duration': '65s'}
        ]
    }
    
    print("📄 Generating PDF report...")
    result = exporter.generate_pdf_report(report_data)
    
    print(f"   ✅ PDF report generated")
    print(f"   📁 File: {result.file_path}")
    print(f"   📏 Size: {result.file_size} bytes")
    print(f"   Format: {result.format.value.upper()}")
    print()


def demo_shareable_package():
    """Demo shareable package creation."""
    print("=" * 80)
    print("SHAREABLE PACKAGE DEMO")
    print("=" * 80)
    print()
    
    config = ExportConfig(
        output_directory="exports/demo",
        secure_links=True,
        link_expiration_hours=48
    )
    exporter = ComprehensiveExporter(config)
    
    # Sample workflow data
    workflow_data = {
        'workflow_id': 'wf_12345',
        'name': 'Customer Data Synthesis Pipeline',
        'synthetic_data': [
            {'id': i, 'name': f'Synthetic User {i}', 'email': f'user{i}@synthetic.com'}
            for i in range(1, 101)
        ],
        'quality_report': {
            'overall_score': 94.5,
            'metrics': {
                'similarity': 92.0,
                'diversity': 96.5,
                'validity': 98.2
            },
            'statistical_tests': {
                'ks_test': 'PASSED',
                'chi_squared': 'PASSED',
                'correlation_preservation': 'PASSED'
            }
        },
        'test_results': {
            'total_tests': 50,
            'passed': 48,
            'failed': 2,
            'skipped': 0,
            'pass_rate': 96.0
        },
        'agent_logs': '''
[2024-01-15 10:00:00] Data Processor: Started analysis
[2024-01-15 10:00:15] Data Processor: Identified 5 sensitive fields
[2024-01-15 10:00:30] Synthetic Generator: Started generation
[2024-01-15 10:02:45] Synthetic Generator: Generated 10000 records
[2024-01-15 10:03:00] Quality Validator: Validation complete
[2024-01-15 10:03:30] Workflow: Execution complete
'''
    }
    
    print("📦 Creating shareable ZIP package...")
    result = exporter.create_shareable_package(
        workflow_data,
        include_data=True,
        include_reports=True,
        include_logs=True
    )
    
    print(f"   ✅ Package created")
    print(f"   📁 File: {result.file_path}")
    print(f"   📏 Size: {result.file_size:,} bytes ({result.file_size / 1024:.1f} KB)")
    if result.download_link:
        print(f"   🔗 Secure download link: {result.download_link}")
        print(f"   ⏰ Link expires: {result.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Demo email sharing
    print("📧 Sharing via email...")
    success = exporter.share_via_email(
        result,
        recipient_email="stakeholder@example.com",
        subject="Workflow Results Ready",
        message="Your synthetic data generation workflow has completed successfully."
    )
    
    if success:
        print("   ✅ Email notification sent")
    else:
        print("   ℹ️  Email sharing not enabled (demo mode)")
    print()


def demo_results_archive():
    """Demo results archive functionality."""
    print("=" * 80)
    print("RESULTS ARCHIVE DEMO")
    print("=" * 80)
    print()
    
    config = ExportConfig(
        output_directory="exports/demo",
        archive_enabled=True,
        archive_directory="exports/archive"
    )
    exporter = ComprehensiveExporter(config)
    
    # Archive multiple workflows
    print("📚 Archiving workflow results...")
    print()
    
    workflows = [
        {
            'workflow_id': 'wf_001',
            'name': 'Telecom Data Generation',
            'status': 'completed',
            'data': {'records': 5000, 'quality': 95.5}
        },
        {
            'workflow_id': 'wf_002',
            'name': 'Finance Data Generation',
            'status': 'completed',
            'data': {'records': 10000, 'quality': 97.2}
        },
        {
            'workflow_id': 'wf_003',
            'name': 'Healthcare Data Generation',
            'status': 'completed',
            'data': {'records': 7500, 'quality': 94.8}
        }
    ]
    
    archive_ids = []
    for workflow in workflows:
        archive_id = exporter.archive_workflow_results(
            workflow['workflow_id'],
            workflow,
            tags=['demo', workflow['name'].split()[0].lower()]
        )
        archive_ids.append(archive_id)
        print(f"   ✅ Archived: {workflow['name']}")
        print(f"      Archive ID: {archive_id}")
    print()
    
    # Search archives
    print("🔍 Searching archives...")
    results = exporter.archive.search_archives(tags=['telecom'])
    print(f"   Found {len(results)} workflows with tag 'telecom'")
    for result in results:
        print(f"      • {result.get('workflow_name')} (archived: {result.get('archived_at')})")
    print()
    
    # Get archive statistics
    print("📊 Archive Statistics:")
    stats = exporter.archive.get_archive_statistics()
    print(f"   Total workflows: {stats['total_workflows']}")
    print(f"   Total size: {stats['total_size_mb']:.2f} MB")
    print(f"   Oldest archive: {stats['oldest_archive']}")
    print(f"   Newest archive: {stats['newest_archive']}")
    print()
    
    # Retrieve an archive
    print("📥 Retrieving archived workflow...")
    retrieved = exporter.archive.retrieve_archive(archive_ids[0])
    if retrieved:
        print(f"   ✅ Retrieved: {retrieved.get('name')}")
        print(f"      Records: {retrieved.get('data', {}).get('records')}")
        print(f"      Quality: {retrieved.get('data', {}).get('quality')}")
    print()


def main():
    """Run all export demos."""
    print("\n")
    print("=" * 80)
    print("RESULTS EXPORT & SHARING DEMO")
    print("=" * 80)
    print("This demo showcases comprehensive export and sharing features:")
    print("  • Multiple export formats (CSV, JSON, Parquet, SQL)")
    print("  • Compressed exports with configurable compression levels")
    print("  • HTML and PDF report generation")
    print("  • Shareable ZIP packages with secure download links")
    print("  • Email sharing capabilities")
    print("  • Results archive for historical reference")
    print("  • Search and retrieval of archived workflows")
    print("=" * 80)
    print("\n")
    
    demo_basic_export()
    demo_compressed_export()
    demo_html_report()
    demo_pdf_report()
    demo_shareable_package()
    demo_results_archive()
    
    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
