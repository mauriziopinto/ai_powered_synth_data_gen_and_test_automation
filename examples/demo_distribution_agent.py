"""Demo of Distribution Agent loading synthetic data to database."""

import asyncio
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, ForeignKey

from agents.distribution import (
    DistributionAgent,
    TargetConfig,
    LoadStrategy
)


def setup_demo_database():
    """Set up an in-memory SQLite database with sample schema."""
    engine = create_engine('sqlite:///demo_distribution.db', echo=True)
    
    metadata = MetaData()
    
    # Create customers table
    customers = Table('customers', metadata,
        Column('customer_id', Integer, primary_key=True),
        Column('name', String(100)),
        Column('email', String(100)),
        Column('phone', String(20)),
        Column('city', String(50))
    )
    
    # Create orders table with FK to customers
    orders = Table('orders', metadata,
        Column('order_id', Integer, primary_key=True),
        Column('customer_id', Integer, ForeignKey('customers.customer_id')),
        Column('order_date', String(20)),
        Column('total_amount', Float)
    )
    
    # Create order_items table with FK to orders
    order_items = Table('order_items', metadata,
        Column('item_id', Integer, primary_key=True),
        Column('order_id', Integer, ForeignKey('orders.order_id')),
        Column('product_name', String(100)),
        Column('quantity', Integer),
        Column('price', Float)
    )
    
    metadata.create_all(engine)
    
    return engine


def create_synthetic_data():
    """Create sample synthetic data."""
    # Customer data
    customers_df = pd.DataFrame({
        'customer_id': [1, 2, 3, 4, 5],
        'name': ['Alice Johnson', 'Bob Smith', 'Charlie Brown', 'Diana Prince', 'Eve Wilson'],
        'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com', 
                  'diana@example.com', 'eve@example.com'],
        'phone': ['555-0101', '555-0102', '555-0103', '555-0104', '555-0105'],
        'city': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']
    })
    
    # Orders data
    orders_df = pd.DataFrame({
        'order_id': [101, 102, 103, 104, 105, 106],
        'customer_id': [1, 1, 2, 3, 4, 5],
        'order_date': ['2024-01-15', '2024-01-20', '2024-01-18', 
                       '2024-01-22', '2024-01-25', '2024-01-28'],
        'total_amount': [150.50, 200.00, 75.25, 300.00, 125.75, 450.00]
    })
    
    # Order items data
    order_items_df = pd.DataFrame({
        'item_id': [1, 2, 3, 4, 5, 6, 7, 8],
        'order_id': [101, 101, 102, 103, 104, 105, 106, 106],
        'product_name': ['Widget A', 'Widget B', 'Gadget X', 'Tool Y', 
                        'Device Z', 'Widget A', 'Gadget X', 'Tool Y'],
        'quantity': [2, 1, 3, 1, 2, 5, 2, 1],
        'price': [50.00, 50.50, 200.00, 75.25, 150.00, 50.00, 200.00, 250.00]
    })
    
    # Combine all data into single DataFrame
    # In real scenario, this would come from Synthetic Data Agent
    all_data = pd.concat([
        customers_df,
        orders_df,
        order_items_df
    ], axis=1)
    
    return all_data, customers_df, orders_df, order_items_df


async def demo_truncate_insert():
    """Demo: Truncate-Insert strategy."""
    print("\n" + "="*80)
    print("DEMO 1: Truncate-Insert Strategy")
    print("="*80)
    
    # Setup
    engine = setup_demo_database()
    _, customers_df, orders_df, order_items_df = create_synthetic_data()
    
    # Create distribution agent
    agent = DistributionAgent()
    
    # Configure target with FK-ordered loading
    config = TargetConfig(
        name='demo_sqlite_db',
        type='database',
        connection_string='sqlite:///demo_distribution.db',
        database_type='postgresql',  # SQLite uses similar syntax
        load_strategy='truncate_insert',
        respect_fk_order=True,
        tables=['customers', 'orders', 'order_items'],
        table_mappings={
            'customers': ['customer_id', 'name', 'email', 'phone', 'city'],
            'orders': ['order_id', 'customer_id', 'order_date', 'total_amount'],
            'order_items': ['item_id', 'order_id', 'product_name', 'quantity', 'price']
        },
        batch_size=100
    )
    
    # Load customers first
    print("\n📊 Loading customers data...")
    result = await agent.process(customers_df, [TargetConfig(
        name='demo_sqlite_db',
        type='database',
        connection_string='sqlite:///demo_distribution.db',
        database_type='postgresql',
        load_strategy='truncate_insert',
        respect_fk_order=False,
        tables=['customers'],
        table_mappings={'customers': ['customer_id', 'name', 'email', 'phone', 'city']},
        batch_size=100
    )])
    
    print(f"✅ Customers loaded: {result.results[0].records_loaded} records")
    
    # Load orders
    print("\n📊 Loading orders data...")
    result = await agent.process(orders_df, [TargetConfig(
        name='demo_sqlite_db',
        type='database',
        connection_string='sqlite:///demo_distribution.db',
        database_type='postgresql',
        load_strategy='truncate_insert',
        respect_fk_order=False,
        tables=['orders'],
        table_mappings={'orders': ['order_id', 'customer_id', 'order_date', 'total_amount']},
        batch_size=100
    )])
    
    print(f"✅ Orders loaded: {result.results[0].records_loaded} records")
    
    # Load order items
    print("\n📊 Loading order items data...")
    result = await agent.process(order_items_df, [TargetConfig(
        name='demo_sqlite_db',
        type='database',
        connection_string='sqlite:///demo_distribution.db',
        database_type='postgresql',
        load_strategy='truncate_insert',
        respect_fk_order=False,
        tables=['order_items'],
        table_mappings={'order_items': ['item_id', 'order_id', 'product_name', 'quantity', 'price']},
        batch_size=100
    )])
    
    print(f"✅ Order items loaded: {result.results[0].records_loaded} records")
    
    # Verify data
    print("\n🔍 Verifying loaded data...")
    with engine.connect() as conn:
        customers_count = pd.read_sql('SELECT COUNT(*) as count FROM customers', conn).iloc[0]['count']
        orders_count = pd.read_sql('SELECT COUNT(*) as count FROM orders', conn).iloc[0]['count']
        items_count = pd.read_sql('SELECT COUNT(*) as count FROM order_items', conn).iloc[0]['count']
        
        print(f"   Customers: {customers_count}")
        print(f"   Orders: {orders_count}")
        print(f"   Order Items: {items_count}")
        
        # Show sample data
        print("\n📋 Sample customer data:")
        sample = pd.read_sql('SELECT * FROM customers LIMIT 3', conn)
        print(sample.to_string(index=False))
    
    engine.dispose()


async def demo_append_strategy():
    """Demo: Append strategy."""
    print("\n" + "="*80)
    print("DEMO 2: Append Strategy")
    print("="*80)
    
    # Setup with existing data
    engine = setup_demo_database()
    
    # Load initial data
    initial_customers = pd.DataFrame({
        'customer_id': [10, 20],
        'name': ['Alice Johnson', 'Bob Smith'],
        'email': ['alice@example.com', 'bob@example.com'],
        'phone': ['555-0101', '555-0102'],
        'city': ['New York', 'Los Angeles']
    })
    
    with engine.begin() as conn:
        initial_customers.to_sql('customers', conn, if_exists='append', index=False)
    
    print("✅ Initial data loaded: 2 customers")
    
    # Create distribution agent
    agent = DistributionAgent()
    
    # Append new customers
    new_customers = pd.DataFrame({
        'customer_id': [30, 40, 50],
        'name': ['Charlie Brown', 'Diana Prince', 'Eve Wilson'],
        'email': ['charlie@example.com', 'diana@example.com', 'eve@example.com'],
        'phone': ['555-0103', '555-0104', '555-0105'],
        'city': ['Chicago', 'Houston', 'Phoenix']
    })
    
    config = TargetConfig(
        name='demo_sqlite_db',
        type='database',
        connection_string='sqlite:///demo_distribution.db',
        database_type='postgresql',
        load_strategy='append',
        respect_fk_order=False,
        tables=['customers'],
        table_mappings={'customers': ['customer_id', 'name', 'email', 'phone', 'city']},
        batch_size=100
    )
    
    print("\n📊 Appending new customers...")
    result = await agent.process(new_customers, [config])
    
    print(f"✅ New customers appended: {result.results[0].records_loaded} records")
    
    # Verify total count
    with engine.connect() as conn:
        total_count = pd.read_sql('SELECT COUNT(*) as count FROM customers', conn).iloc[0]['count']
        print(f"\n🔍 Total customers in database: {total_count}")
        
        print("\n📋 All customers:")
        all_customers = pd.read_sql('SELECT * FROM customers', conn)
        print(all_customers.to_string(index=False))
    
    engine.dispose()


async def demo_distribution_report():
    """Demo: Distribution report with multiple targets."""
    print("\n" + "="*80)
    print("DEMO 3: Distribution Report")
    print("="*80)
    
    # Setup
    engine = setup_demo_database()
    _, customers_df, _, _ = create_synthetic_data()
    
    # Create distribution agent
    agent = DistributionAgent()
    
    # Configure multiple targets (simulating different environments)
    targets = [
        TargetConfig(
            name='dev_database',
            type='database',
            connection_string='sqlite:///demo_distribution.db',
            database_type='postgresql',
            load_strategy='truncate_insert',
            respect_fk_order=False,
            tables=['customers'],
            table_mappings={'customers': ['customer_id', 'name', 'email', 'phone', 'city']},
            batch_size=100
        ),
        TargetConfig(
            name='invalid_database',
            type='database',
            connection_string='invalid://connection',
            database_type='postgresql',
            load_strategy='truncate_insert',
            respect_fk_order=False,
            tables=['customers'],
            table_mappings={'customers': ['customer_id', 'name', 'email', 'phone', 'city']},
            batch_size=100
        )
    ]
    
    print("\n📊 Distributing to multiple targets...")
    report = await agent.process(customers_df, targets)
    
    print("\n📈 Distribution Report:")
    print(f"   Total Targets: {report.total_targets}")
    print(f"   Successful: {report.successful_targets}")
    print(f"   Failed: {report.failed_targets}")
    print(f"   Total Records Loaded: {report.total_records}")
    
    print("\n📋 Individual Results:")
    for result in report.results:
        status_icon = "✅" if result.status == 'success' else "❌"
        print(f"\n   {status_icon} Target: {result.target}")
        print(f"      Status: {result.status}")
        print(f"      Records: {result.records_loaded}")
        print(f"      Duration: {result.duration:.2f}s")
        if result.error:
            print(f"      Error: {result.error}")
    
    engine.dispose()


async def main():
    """Run all demos."""
    print("\n" + "="*80)
    print("DISTRIBUTION AGENT DEMO")
    print("="*80)
    print("\nThis demo shows the Distribution Agent loading synthetic data")
    print("into a database with different strategies and FK ordering.")
    
    await demo_truncate_insert()
    await demo_append_strategy()
    await demo_distribution_report()
    
    print("\n" + "="*80)
    print("✅ All demos completed successfully!")
    print("="*80)
    print("\n💡 Key Features Demonstrated:")
    print("   • Truncate-Insert strategy for clean loads")
    print("   • Append strategy for incremental loads")
    print("   • FK-ordered loading to respect dependencies")
    print("   • Distribution reports with success/failure tracking")
    print("   • Multiple target support")
    print("\n📁 Database file created: demo_distribution.db")


if __name__ == '__main__':
    asyncio.run(main())
