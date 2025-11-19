#!/usr/bin/env python
"""Database setup script."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from shared.database.schema import create_tables, drop_tables
from shared.database.connection import DatabaseManager
import click


@click.group()
def cli():
    """Database management commands."""
    pass


@cli.command()
@click.option('--drop', is_flag=True, help='Drop existing tables before creating')
def create(drop):
    """Create database tables."""
    db_manager = DatabaseManager()
    
    if drop:
        click.echo("Dropping existing tables...")
        drop_tables(db_manager.engine)
        click.echo("Tables dropped.")
    
    click.echo("Creating database tables...")
    create_tables(db_manager.engine)
    click.echo("Database tables created successfully!")
    
    # Verify tables
    with db_manager.engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        
    click.echo(f"\nCreated tables: {', '.join(tables)}")


@cli.command()
def drop_all():
    """Drop all database tables."""
    if not click.confirm('Are you sure you want to drop all tables?'):
        return
    
    db_manager = DatabaseManager()
    click.echo("Dropping all tables...")
    drop_tables(db_manager.engine)
    click.echo("All tables dropped.")


@cli.command()
def verify():
    """Verify database connection and schema."""
    try:
        db_manager = DatabaseManager()
        
        with db_manager.engine.connect() as conn:
            # Test connection
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            click.echo(f"✓ Connected to PostgreSQL: {version[:50]}...")
            
            # Check tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            if tables:
                click.echo(f"\n✓ Found {len(tables)} tables:")
                for table in tables:
                    click.echo(f"  - {table}")
            else:
                click.echo("\n⚠ No tables found. Run 'python scripts/setup_database.py create' to create them.")
        
        click.echo("\n✓ Database verification complete!")
        
    except Exception as e:
        click.echo(f"\n✗ Database verification failed: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
