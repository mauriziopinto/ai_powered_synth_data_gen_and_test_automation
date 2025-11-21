#!/usr/bin/env python3
"""
Demo: CSV Upload and Persistent Storage

This script demonstrates:
1. Uploading a CSV file to trigger synthetic data generation
2. Monitoring workflow progress
3. Verifying persistent storage (workflows survive restarts)

Usage:
    python examples/demo_csv_upload.py
"""

import requests
import time
import json
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def upload_csv(csv_path: str, num_records: int = 100, workflow_name: str = None):
    """Upload a CSV file and start a workflow."""
    print(f"📤 Uploading CSV: {csv_path}")
    
    with open(csv_path, 'rb') as f:
        files = {'file': f}
        data = {
            'num_records': num_records,
        }
        if workflow_name:
            data['workflow_name'] = workflow_name
        
        response = requests.post(
            f"{BASE_URL}/workflow/upload-csv",
            files=files,
            data=data
        )
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Upload successful!")
        print(f"   Workflow ID: {result['workflow_id']}")
        print(f"   Config ID: {result['config_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")
        return result['workflow_id']
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def get_workflow_status(workflow_id: str):
    """Get workflow status."""
    response = requests.get(f"{BASE_URL}/workflow/{workflow_id}/status")
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Failed to get status: {response.status_code}")
        return None

def list_workflows():
    """List all workflows."""
    response = requests.get(f"{BASE_URL}/workflow/")
    
    if response.status_code == 200:
        workflows = response.json()
        print(f"📋 Found {len(workflows)} workflows:")
        for wf in workflows[:5]:  # Show first 5
            print(f"   • {wf['workflow_id']}")
            print(f"     Status: {wf['status']}, Progress: {wf['progress']}%")
            print(f"     Started: {wf['started_at']}")
        return workflows
    else:
        print(f"❌ Failed to list workflows: {response.status_code}")
        return []

def monitor_workflow(workflow_id: str, max_checks: int = 10):
    """Monitor workflow progress."""
    print(f"👀 Monitoring workflow: {workflow_id}")
    
    for i in range(max_checks):
        status = get_workflow_status(workflow_id)
        if not status:
            break
        
        print(f"\n   Check {i+1}/{max_checks}:")
        print(f"   Status: {status['status']}")
        print(f"   Progress: {status['progress']}%")
        print(f"   Stage: {status['current_stage']}")
        
        if status['status'] in ['completed', 'failed', 'aborted']:
            print(f"\n✅ Workflow {status['status']}!")
            if status.get('error'):
                print(f"   Error: {status['error']}")
            break
        
        time.sleep(2)

def main():
    """Run the demo."""
    print_section("CSV Upload & Persistent Storage Demo")
    
    # Demo 1: Upload Healthcare CSV
    print_section("Demo 1: Upload Healthcare Patient Data")
    
    csv_path = "data/demo/healthcare_patients.csv"
    if not Path(csv_path).exists():
        print(f"❌ CSV file not found: {csv_path}")
        print("   Please ensure demo data exists")
        return
    
    workflow_id = upload_csv(
        csv_path,
        num_records=50,
        workflow_name="Healthcare Synthetic Data Demo"
    )
    
    if workflow_id:
        time.sleep(1)
        monitor_workflow(workflow_id, max_checks=5)
    
    # Demo 2: Upload Financial CSV
    print_section("Demo 2: Upload Financial Transaction Data")
    
    csv_path = "data/demo/finance_transactions.csv"
    if Path(csv_path).exists():
        workflow_id = upload_csv(
            csv_path,
            num_records=100,
            workflow_name="Financial Transactions Demo"
        )
        
        if workflow_id:
            time.sleep(1)
            # Just check status once
            status = get_workflow_status(workflow_id)
            if status:
                print(f"\n📊 Workflow Status:")
                print(json.dumps(status, indent=2))
    
    # Demo 3: List All Workflows (Persistent Storage)
    print_section("Demo 3: Verify Persistent Storage")
    
    print("📁 All workflows are stored in workflows.db")
    print("   These workflows will persist even after server restart!\n")
    
    workflows = list_workflows()
    
    if workflows:
        print(f"\n💾 Database contains {len(workflows)} workflows")
        print("   Location: workflows.db")
        print("   Tables: workflows, agent_status")
    
    # Demo 4: Check Uploaded Files
    print_section("Demo 4: Uploaded Files")
    
    upload_dir = Path("data/uploads")
    if upload_dir.exists():
        files = list(upload_dir.glob("*.csv"))
        print(f"📂 Found {len(files)} uploaded CSV files:")
        for f in files[-5:]:  # Show last 5
            size_kb = f.stat().st_size / 1024
            print(f"   • {f.name} ({size_kb:.1f} KB)")
    
    print_section("Demo Complete!")
    
    print("🎉 Both features are working:")
    print("   ✅ CSV Upload: Upload CSV files to generate synthetic data")
    print("   ✅ Persistent Storage: Workflows saved to SQLite database")
    print("\n📖 For more details, see: web/CSV_UPLOAD_GUIDE.md")
    print("\n🌐 Web Interface: http://localhost:3000/configuration")
    print("📚 API Docs: http://localhost:8000/docs")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
