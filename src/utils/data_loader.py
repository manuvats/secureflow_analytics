"""
Data Loader Utility - SecureFlow Analytics
DuckDB utilities for loading local parquet files
"""
import duckdb
import pandas as pd
from pathlib import Path
import sys

# Import config (go up two levels: utils -> src -> project_root)
sys.path.append(str(Path(__file__).parent.parent))
import config


def get_connection(memory_only: bool = False) -> duckdb.DuckDBPyConnection:
    """
    Get DuckDB connection.
    
    Args:
        memory_only: If True, use in-memory database. Otherwise use persistent DB.
    
    Returns:
        DuckDB connection
    """
    if memory_only:
        return duckdb.connect(':memory:')
    else:
        # Use persistent database if it exists
        if config.DB_PATH.exists():
            print(f"📊 Connected to: {config.DB_PATH}")
            return duckdb.connect(str(config.DB_PATH))
        else:
            print(f"📊 Using in-memory database (no persistent DB found)")
            return duckdb.connect(':memory:')


def load_table(con: duckdb.DuckDBPyConnection, table_name: str) -> pd.DataFrame:
    """
    Load a table from parquet file using DuckDB.
    
    Args:
        con: DuckDB connection
        table_name: Name of table to load (e.g., 'users', 'events')
    
    Returns:
        DataFrame with the data
    """
    file_mapping = {
        'users': config.USERS_FILE,
        'subscriptions': config.SUBSCRIPTIONS_FILE,
        'events': config.EVENTS_FILE,
        'experiments': config.EXPERIMENTS_FILE,
        'experiment_assignments': config.EXPERIMENT_ASSIGNMENTS_FILE,
        'experiment_metrics': config.EXPERIMENT_METRICS_FILE,
        'feature_usage': config.FEATURE_USAGE_FILE,
        'support_tickets': config.SUPPORT_TICKETS_FILE,
    }
    
    if table_name not in file_mapping:
        raise ValueError(f"Unknown table: {table_name}")
    
    file_path = file_mapping[table_name]
    
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    # Read using DuckDB for efficient querying
    query = f"SELECT * FROM read_parquet('{file_path}')"
    return con.execute(query).df()


def query_events(
    con: duckdb.DuckDBPyConnection,
    event_types: list = None,
    user_ids: list = None,
    date_range: tuple = None,
    limit: int = None
) -> pd.DataFrame:
    """
    Query events table with filters.
    
    Args:
        con: DuckDB connection
        event_types: Filter by event types
        user_ids: Filter by user IDs
        date_range: Tuple of (start_date, end_date)
        limit: Max rows to return
    
    Returns:
        Filtered events DataFrame
    """
    where_clauses = []
    
    if event_types:
        types_str = "', '".join(event_types)
        where_clauses.append(f"event_type IN ('{types_str}')")
    
    if user_ids:
        ids_str = "', '".join(user_ids)
        where_clauses.append(f"user_id IN ('{ids_str}')")
    
    if date_range:
        where_clauses.append(f"CAST(timestamp AS TIMESTAMP) BETWEEN '{date_range[0]}' AND '{date_range[1]}'")
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    limit_sql = f"LIMIT {limit}" if limit else ""
    
    query = f"""
    SELECT * 
    FROM read_parquet('{config.EVENTS_FILE}')
    WHERE {where_sql}
    {limit_sql}
    """
    
    return con.execute(query).df()


def query_raw_table(
    con: duckdb.DuckDBPyConnection,
    table_name: str,
    limit: int = None
) -> pd.DataFrame:
    """
    Query any table by name.
    
    Args:
        con: DuckDB connection
        table_name: Name of table to query
        limit: Max rows to return
    
    Returns:
        DataFrame with results
    """
    file_mapping = {
        'users': config.USERS_FILE,
        'subscriptions': config.SUBSCRIPTIONS_FILE,
        'events': config.EVENTS_FILE,
        'experiments': config.EXPERIMENTS_FILE,
        'experiment_assignments': config.EXPERIMENT_ASSIGNMENTS_FILE,
        'experiment_metrics': config.EXPERIMENT_METRICS_FILE,
        'feature_usage': config.FEATURE_USAGE_FILE,
        'support_tickets': config.SUPPORT_TICKETS_FILE,
    }
    
    if table_name not in file_mapping:
        raise ValueError(f"Unknown table: {table_name}")
    
    file_path = file_mapping[table_name]
    limit_sql = f"LIMIT {limit}" if limit else ""
    
    query = f"""
    SELECT * 
    FROM read_parquet('{file_path}')
    {limit_sql}
    """
    
    return con.execute(query).df()


def execute_query(
    con: duckdb.DuckDBPyConnection,
    query: str
) -> pd.DataFrame:
    """
    Execute a custom SQL query.
    
    Args:
        con: DuckDB connection
        query: SQL query string
    
    Returns:
        DataFrame with results
    """
    return con.execute(query).df()


def get_table_info(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Get information about available tables.
    
    Returns:
        DataFrame with table names and row counts
    """
    tables = ['users', 'subscriptions', 'events', 'experiments', 
              'experiment_assignments', 'experiment_metrics', 
              'feature_usage', 'support_tickets']
    
    info = []
    for table in tables:
        try:
            file_path = getattr(config, f"{table.upper()}_FILE")
            if file_path.exists():
                count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{file_path}')").fetchone()[0]
                size_mb = file_path.stat().st_size / 1e6
                info.append({
                    'table': table,
                    'rows': count,
                    'size_mb': round(size_mb, 1)
                })
        except:
            pass
    
    return pd.DataFrame(info)


def load_all_tables(con: duckdb.DuckDBPyConnection, exclude_events: bool = True) -> dict:
    """
    Load all tables into a dictionary.
    
    Args:
        con: DuckDB connection
        exclude_events: If True, don't load events table (too large for memory)
    
    Returns:
        Dictionary with table names as keys and DataFrames as values
    """
    tables = ['users', 'subscriptions', 'experiments', 
              'experiment_assignments', 'experiment_metrics', 
              'feature_usage', 'support_tickets']
    
    if not exclude_events:
        tables.append('events')
    
    data = {}
    for table in tables:
        try:
            data[table] = load_table(con, table)
            print(f"  ✓ Loaded {table}: {len(data[table]):,} rows")
        except Exception as e:
            print(f"  ✗ Failed to load {table}: {e}")
    
    return data
