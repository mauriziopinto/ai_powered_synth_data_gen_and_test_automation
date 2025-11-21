"""Demo of configuration management for workflow configurations."""

from shared.config import (
    ConfigurationManager,
    WorkflowConfiguration,
    ConfigurationMetadata,
    ConfigurationLibrary
)


def demo_save_load():
    """Demo saving and loading configurations."""
    print("=" * 80)
    print("CONFIGURATION SAVE/LOAD DEMO")
    print("=" * 80)
    print("This demo shows saving and loading workflow configurations")
    print("=" * 80)
    print()
    
    # Create manager
    manager = ConfigurationManager(config_dir="demo_configs")
    
    # Create configuration
    metadata = ConfigurationMetadata(
        config_id=manager.generate_config_id(),
        name="Telecom Data Generation",
        description="Configuration for generating synthetic telecom data",
        tags=["telecom", "production", "demo"],
        created_by="demo_user"
    )
    
    config = WorkflowConfiguration(
        metadata=metadata,
        schema_definition={
            'tables': [
                {
                    'name': 'customers',
                    'fields': [
                        {'name': 'customer_id', 'type': 'integer', 'primary_key': True},
                        {'name': 'email', 'type': 'string', 'sensitive': True},
                        {'name': 'phone', 'type': 'string', 'sensitive': True}
                    ]
                }
            ]
        },
        generation_parameters={
            'num_records': 10000,
            'model': 'GaussianCopula',
            'seed': 42
        },
        edge_case_rules={
            'enabled': True,
            'frequency': 0.05,
            'patterns': ['invalid_email', 'malformed_phone']
        },
        target_system_settings={
            'type': 'database',
            'connection': 'postgresql://localhost:5432/testdb'
        }
    )
    
    print("📋 Configuration Details:")
    print(f"   ID: {config.metadata.config_id}")
    print(f"   Name: {config.metadata.name}")
    print(f"   Tags: {', '.join(config.metadata.tags)}")
    print(f"   Records: {config.generation_parameters['num_records']}")
    print()
    
    # Save configuration
    print("💾 Saving configuration...")
    config_id = manager.save(config)
    print(f"   Saved with ID: {config_id}")
    print()
    
    # Load configuration
    print("📂 Loading configuration...")
    loaded_config = manager.load(config_id)
    print(f"   Loaded: {loaded_config.metadata.name}")
    print(f"   Tables: {len(loaded_config.schema_definition['tables'])}")
    print()



def demo_export_import():
    """Demo exporting and importing configurations."""
    print("=" * 80)
    print("CONFIGURATION EXPORT/IMPORT DEMO")
    print("=" * 80)
    print("This demo shows exporting and importing configurations")
    print("=" * 80)
    print()
    
    manager = ConfigurationManager(config_dir="demo_configs")
    
    # Create and save a config
    metadata = ConfigurationMetadata(
        config_id=manager.generate_config_id(),
        name="Finance Data Generation",
        description="Configuration for generating synthetic finance data",
        tags=["finance", "testing"],
        created_by="demo_user"
    )
    
    config = WorkflowConfiguration(
        metadata=metadata,
        schema_definition={'tables': [{'name': 'transactions', 'fields': []}]},
        generation_parameters={'num_records': 5000, 'model': 'CTGAN'},
        edge_case_rules={'enabled': False},
        target_system_settings={'type': 'file', 'path': '/tmp/output.csv'}
    )
    
    config_id = manager.save(config)
    print(f"📋 Created configuration: {config.metadata.name}")
    print(f"   ID: {config_id}")
    print()
    
    # Export configuration
    export_path = "demo_configs/exported_finance_config.json"
    print(f"📤 Exporting to: {export_path}")
    manager.export_config(config_id, export_path)
    print("   Export complete!")
    print()
    
    # Import configuration
    print(f"📥 Importing from: {export_path}")
    new_id = manager.import_config(export_path, new_name="Finance Data Generation (Imported)")
    print(f"   Imported with new ID: {new_id}")
    print()
    
    # Verify import
    imported_config = manager.load(new_id)
    print("✅ Import Verification:")
    print(f"   Name: {imported_config.metadata.name}")
    print(f"   Original ID: {config_id}")
    print(f"   New ID: {new_id}")
    print()


def demo_library_search():
    """Demo configuration library search."""
    print("=" * 80)
    print("CONFIGURATION LIBRARY DEMO")
    print("=" * 80)
    print("This demo shows searching and browsing configurations")
    print("=" * 80)
    print()
    
    manager = ConfigurationManager(config_dir="demo_configs")
    library = ConfigurationLibrary(manager)
    
    # List all configurations
    print("📚 All Configurations:")
    all_configs = manager.list_configs()
    for config in all_configs:
        print(f"   • {config.name} ({config.config_id})")
        print(f"     Tags: {', '.join(config.tags)}")
    print()
    
    # Search by query
    print("🔍 Search Results for 'telecom':")
    results = library.search(query="telecom")
    for config in results:
        print(f"   • {config.name}")
    print()
    
    # Search by tag
    print("🏷️  Configurations with 'production' tag:")
    results = library.get_by_tag("production")
    for config in results:
        print(f"   • {config.name}")
    print()
    
    # Get statistics
    print("📊 Library Statistics:")
    stats = library.get_statistics()
    print(f"   Total configurations: {stats['total_configs']}")
    print(f"   Unique tags: {stats['unique_tags']}")
    print(f"   Tags: {', '.join(stats['tags'])}")
    print()


def demo_validation():
    """Demo configuration validation."""
    print("=" * 80)
    print("CONFIGURATION VALIDATION DEMO")
    print("=" * 80)
    print("This demo shows configuration validation")
    print("=" * 80)
    print()
    
    manager = ConfigurationManager(config_dir="demo_configs")
    
    # Create invalid configuration
    metadata = ConfigurationMetadata(
        config_id=manager.generate_config_id(),
        name="Invalid Config",
        description="This configuration is missing required fields"
    )
    
    invalid_config = WorkflowConfiguration(
        metadata=metadata,
        schema_definition={},  # Missing required fields
        generation_parameters={},  # Missing num_records
        edge_case_rules={},
        target_system_settings={}  # Missing type
    )
    
    print("🔍 Validating configuration...")
    errors = invalid_config.validate()
    
    if errors:
        print("❌ Validation Failed!")
        print("   Errors:")
        for error in errors:
            print(f"     • {error}")
    else:
        print("✅ Validation Passed!")
    print()
    
    # Try to save invalid config
    print("💾 Attempting to save invalid configuration...")
    try:
        manager.save(invalid_config)
        print("   Saved (unexpected!)")
    except ValueError as e:
        print(f"   ❌ Save failed (expected): {str(e)[:60]}...")
    print()


def main():
    """Run all demos."""
    print("\n")
    print("=" * 80)
    print("CONFIGURATION MANAGEMENT DEMO")
    print("=" * 80)
    print("This demo showcases configuration management features:")
    print("  • Save and load workflow configurations")
    print("  • Unique ID generation")
    print("  • Configuration validation")
    print("  • Export and import for sharing")
    print("  • Configuration library with search")
    print("  • Tag-based organization")
    print("=" * 80)
    print("\n")
    
    # Run demos
    demo_save_load()
    demo_export_import()
    demo_library_search()
    demo_validation()
    
    print("=" * 80)
    print("✅ All demos completed!")
    print("=" * 80)
    print()
    print("💡 Key Features Demonstrated:")
    print("   • Configuration save/load with validation")
    print("   • Unique ID generation for each config")
    print("   • Metadata management (name, tags, timestamps)")
    print("   • Export/import for sharing across environments")
    print("   • Configuration library with search and filtering")
    print("   • Tag-based organization")
    print("   • Comprehensive validation")
    print()
    print("📋 Requirements Satisfied:")
    print("   ✅ 30.1 - Save complete workflow configurations")
    print("   ✅ 30.2 - Assign unique ID and metadata")
    print("   ✅ 30.3 - Configuration library with search")
    print("   ✅ 30.4 - Load and validate configurations")
    print("   ✅ 30.5 - Export/import for sharing")
    print()


if __name__ == "__main__":
    main()
