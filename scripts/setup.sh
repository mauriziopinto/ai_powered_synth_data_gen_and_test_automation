#!/bin/bash
# Setup script for Synthetic Data Generator

set -e

echo "==================================="
echo "Synthetic Data Generator Setup"
echo "==================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created. Please edit it with your configuration."
else
    echo "✓ .env file already exists"
fi

# Check PostgreSQL connection
echo ""
echo "Checking PostgreSQL connection..."
if command -v psql &> /dev/null; then
    echo "✓ PostgreSQL client found"
    echo "  Please ensure PostgreSQL server is running"
else
    echo "⚠ PostgreSQL client not found"
    echo "  Please install PostgreSQL to use the database features"
fi

# Check AWS CLI
echo ""
echo "Checking AWS CLI..."
if command -v aws &> /dev/null; then
    echo "✓ AWS CLI found"
    aws_version=$(aws --version 2>&1)
    echo "  $aws_version"
else
    echo "⚠ AWS CLI not found"
    echo "  Please install AWS CLI and configure credentials"
fi

echo ""
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Configure AWS credentials: aws configure"
echo "3. Set up database: python scripts/setup_database.py create"
echo "4. Run tests: pytest"
echo ""
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo ""
