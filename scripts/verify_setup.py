#!/usr/bin/env python
"""Verify project setup."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_imports():
    """Check if all core modules can be imported."""
    print("Checking module imports...")
    
    try:
        from shared.models import (
            WorkflowConfig, SensitivityReport, 
            QualityMetrics, TestResults
        )
        print("✓ Shared models import successfully")
    except ImportError as e:
        print(f"✗ Failed to import shared models: {e}")
        return False
    
    try:
        from shared.database.schema import Base, WorkflowConfig as DBWorkflowConfig
        print("✓ Database schema imports successfully")
    except ImportError as e:
        print(f"✗ Failed to import database schema: {e}")
        return False
    
    try:
        from shared.database.connection import DatabaseManager
        print("✓ Database connection imports successfully")
    except ImportError as e:
        print(f"✗ Failed to import database connection: {e}")
        return False
    
    try:
        from shared.utils.aws_config import AWSConfig
        print("✓ AWS config imports successfully")
    except ImportError as e:
        print(f"✗ Failed to import AWS config: {e}")
        return False
    
    return True


def check_directory_structure():
    """Check if all required directories exist."""
    print("\nChecking directory structure...")
    
    required_dirs = [
        'agents/data_processor',
        'agents/synthetic_data',
        'agents/distribution',
        'agents/test_case',
        'agents/test_execution',
        'web/frontend',
        'web/backend',
        'shared/models',
        'shared/database',
        'shared/utils',
        'tests/unit',
        'tests/property',
        'data',
        'results',
        'config',
        'scripts'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"✓ {dir_path}")
        else:
            print(f"✗ {dir_path} - MISSING")
            all_exist = False
    
    return all_exist


def check_files():
    """Check if all required files exist."""
    print("\nChecking required files...")
    
    required_files = [
        'requirements.txt',
        'README.md',
        '.gitignore',
        '.env.example',
        'pytest.ini',
        'scripts/setup_database.py',
        'scripts/setup.sh',
        'shared/models/__init__.py',
        'shared/database/schema.py',
        'shared/database/connection.py',
        'shared/utils/aws_config.py'
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            all_exist = False
    
    return all_exist


def main():
    """Run all verification checks."""
    print("=" * 50)
    print("Project Setup Verification")
    print("=" * 50)
    print()
    
    checks = [
        ("Directory Structure", check_directory_structure),
        ("Required Files", check_files),
        ("Module Imports", check_imports),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} check failed with error: {e}")
            results.append((name, False))
        print()
    
    print("=" * 50)
    print("Verification Summary")
    print("=" * 50)
    
    all_passed = True
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    print()
    if all_passed:
        print("✓ All checks passed! Project setup is complete.")
        return 0
    else:
        print("✗ Some checks failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
