# Distribution Agent

The Distribution Agent is responsible for loading synthetic data into target systems, with initial support for relational databases.

## Features Implemented

### ✅ Database Connection Manager
- Supports PostgreSQL and MySQL
- Connection pooling and health checks
- Metadata reflection for schema discovery
- Foreign key relationship detection

### ✅ Topological Sorter
- Sorts tables in dependency order based on foreign keys
- Uses Kahn's algorithm for topological sorting
- Detects circular dependencies
- Ensures data integrity during loading

### ✅ Loading Strategies

#### Truncate-Insert
- Clears existing data before loading
- Ensures clean state
- Respects CASCADE for foreign keys
- SQLite compatible (uses DELETE instead of TRUNCATE)

#### Upsert
- Insert or update on conflict
- PostgreSQL: `INSERT ... ON CONFLICT DO UPDATE`
- MySQL: `INSERT ... ON DUPLICATE KEY UPDATE`
- Requires primary key configuration

#### Append
- Adds new records without clearing existing data
- Useful for incremental loads
- No conflict resolution

### ✅ FK-Ordered Loading
- Automatically determines table load order
- Respects foreign key dependencies
- Prevents constraint violations
- Configurable (can be disabled)

### ✅ Batch Processing
- Configurable batch sizes
- Memory-efficient for large datasets
- Progress tracking

### ✅ Error Handling
- Detailed error reporting
- Per-target success/failure tracking
- Graceful degradation (continues with other targets on failure)
- Duration tracking

### ✅ Distribution Reports
- Comprehensive reporting of all load operations
- Success/failure counts
- Records loaded per target
- Error details
- Execution times

## Usage Example

```python
import asyncio
import pandas as pd
from agents.distribution import (
    DistributionAgent,
    TargetConfig,
    LoadStrategy
)

# Create synthetic data
data = pd.DataFrame({
    'id': [1, 2, 3],
    'name': ['Alice', 'Bob', 'Charlie'],
    'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com']
})

# Configure target
config = TargetConfig(
    name='production_db',
    type='database',
    connection_string='postgresql://user:pass@localhost:5432/mydb',
    database_type='postgresql',
    load_strategy='truncate_insert',
    respect_fk_order=True,
    tables=['users'],
    table_mappings={'users': ['id', 'name', 'email']},
    batch_size=1000
)

# Load data
agent = DistributionAgent()
report = await agent.process(data, [config])

print(f"Loaded {report.total_records} records to {report.successful_targets} targets")
```

## Demo

Run the demo to see all features in action:

```bash
source .venv/bin/activate
PYTHONPATH=. python examples/demo_distribution_agent.py
```

The demo shows:
1. **Truncate-Insert Strategy**: Loading customers, orders, and order items with FK ordering
2. **Append Strategy**: Incrementally adding new customers to existing data
3. **Distribution Report**: Loading to multiple targets with success/failure tracking

## Architecture

```
DistributionAgent
    ├── DatabaseLoader
    │   ├── _truncate_insert()
    │   ├── _upsert()
    │   └── _append()
    ├── DatabaseConnectionManager
    │   ├── connect()
    │   ├── get_metadata()
    │   └── get_foreign_keys()
    └── TopologicalSorter
        └── sort_tables()
```

## Requirements Validated

This implementation satisfies requirements 16.1-16.5:

- ✅ 16.1: Receives synthetic dataset and target configurations
- ✅ 16.2: Supports multiple target types (database implemented)
- ✅ 16.3: Executes FK-respecting INSERT/UPSERT statements
- ✅ 16.4: Uses Bulk API patterns (batch processing)
- ✅ 16.5: Logs detailed errors and continues with remaining targets

## Next Steps

Future enhancements (Tasks 12+):
- Salesforce Bulk API loader
- REST API loader
- S3/file storage loader
- Mock target systems for demo mode
