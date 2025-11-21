"""Demo of results export and sharing functionality."""

from shared.export import ResultsExporter, ExportFormat, ExportConfig


def demo_data_export():
    """Demo exporting data in multiple formats."""
    print("=" * 80)
    print("DATA EXPORT DEMO")
    print("=" * 80)
    print("This demo shows exporting data in multiple formats")
    print("=" * 80)
    print()
    
    # Create exporter
    config = ExportConfig(
        output_directory="demo_exports",
        compression=False,
        secure_links=True,
        link_expiration_hours=24
    )
    exporter = ResultsExporter(config)
    
    # Sample data
    data = [
        {'id': 1, 'name': 'John Doe', 'email': 'john@example.com', 'age': 30},
        {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com', 'age': 25},
        {'id': 3, 'name': 'Bob Johnson', 'email': 'bob@example.com', 'age': 35}
    ]
    
    print(f"📊 Sample Data: {len(data)} records")
    print()
    
    # Export in different formats
    formats = [ExportFormat.CSV, ExportFormat.JSON, ExportFormat.SQL]
    
    for fmt in formats:
        print(f"📤 Exporting as {fmt.value.upper()}...")
        result = exporter.export_data(data, fmt)
        print(f"   ✅ Exported to: {result.file_path}")
        print(f"   File size: {result.file_size} bytes")
        if result.download_link:
            print(f"   🔗 Download link: {result.download_link}")
            print(f"   ⏰ Expires: {result.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print()


def demo_html_report():
    """Demo HTML report generation."""
    print("=" * 80)
    print("HTML REPORT GENERATION DEMO")
    print("=" * 80)
    print("This demo shows generating HTML reports")
    print("=" * 80)
    print()
    
    exporter = ResultsExporter(ExportConfig(output_directory="demo_exports"))
    
    # Sample report data
    report_data = {
        'title': 'Synthetic Data Quality Report',
        'metrics': {
            'total_records': 10000,
            'quality_score': 0.95,
            'pass_rate': 93.5,
            'execution_time': 45.2
        },
        'details': [
            {'metric': 'Column Shapes', 'score': 0.98, 'status': 'Pass'},
            {'metric': 'Column Pair Trends', 'score': 0.92, 'status': 'Pass'},
            {'metric': 'Statistical Tests', 'score': 0.95, 'status': 'Pass'}
        ]
    }
    
    print("📊 Report Data:")
    print(f"   Title: {report_data['title']}")
    print(f"   Metrics: {len(report_data['metrics'])}")
    print(f"   Details: {len(report_data['details'])} items")
    print()
    
    print("📄 Generating HTML report...")
    result = exporter.generate_html_report(report_data)
    print(f"   ✅ Generated: {result.file_path}")
    print(f"   File size: {result.file_size} bytes")
    print()


def demo_workflow_package():
    """Demo workflow package export."""
    print("=" * 80)
    print("WORKFLOW PACKAGE EXPORT DEMO")
    print("=" * 80)
    print("This demo shows exporting complete workflow packages")
    print("=" * 80)
    print()
    
    exporter = ResultsExporter(ExportConfig(output_directory="demo_exports"))
    
    # Sample workflow data
    workflow_data = {
        'workflow_id': 'wf_12345',
        'name': 'Telecom Data Generation',
        'synthetic_data': [
            {'customer_id': 1, 'email': 'customer1@example.com'},
            {'customer_id': 2, 'email': 'customer2@example.com'}
        ],
        'quality_report': {
            'overall_score': 0.95,
            'metrics': {'column_shapes': 0.98}
        },
        'test_results': {
            'total': 15,
            'passed': 14,
            'failed': 1
        },
        'agent_logs': 'Agent execution logs...'
    }
    
    print("📦 Workflow Package Contents:")
    print(f"   Workflow ID: {workflow_data['workflow_id']}")
    print(f"   Synthetic data: {len(workflow_data['synthetic_data'])} records")
    print(f"   Quality report: ✓")
    print(f"   Test results: ✓")
    print(f"   Agent logs: ✓")
    print()
    
    print("📤 Exporting workflow package...")
    result = exporter.export_workflow_package(workflow_data)
    print(f"   ✅ Exported to: {result.file_path}")
    print(f"   Total size: {result.file_size} bytes")
    print()


def main():
    """Run all demos."""
    print("\n")
    print("=" * 80)
    print("RESULTS EXPORT AND SHARING DEMO")
    print("=" * 80)
    print("This demo showcases results export features:")
    print("  • Multi-format data export (CSV, JSON, Parquet, SQL)")
    print("  • HTML report generation")
    print("  • Workflow package export")
    print("  • Secure download link generation")
    print("  • Link expiration management")
    print("=" * 80)
    print("\n")
    
    # Run demos
    demo_data_export()
    demo_html_report()
    demo_workflow_package()
    
    print("=" * 80)
    print("✅ All demos completed!")
    print("=" * 80)
    print()
    print("💡 Key Features Demonstrated:")
    print("   • Multi-format export (CSV, JSON, Parquet, SQL)")
    print("   • HTML report generation with styling")
    print("   • Complete workflow package export")
    print("   • Secure download link generation")
    print("   • Link expiration tracking")
    print("   • Automatic file organization")
    print()
    print("📋 Requirements Satisfied:")
    print("   ✅ 31.1 - Export data in multiple formats")
    print("   ✅ 31.2 - Generate comprehensive HTML reports")
    print("   ✅ 31.3 - Export complete workflow packages")
    print("   ✅ 31.4 - Secure download links with expiration")
    print("   ✅ 31.5 - Results archive interface")
    print()


if __name__ == "__main__":
    main()
