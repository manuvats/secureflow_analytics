"""
Funnel Analysis Functions - SecureFlow Analytics
DuckDB-based conversion funnel calculations
"""
import duckdb
import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path
import sys

# Import config
sys.path.append(str(Path(__file__).parent.parent))
import config


def calculate_funnel(
    con: duckdb.DuckDBPyConnection,
    funnel_steps: List[tuple],
    segment_by: Optional[str] = None,
    date_range: Optional[tuple] = None
) -> pd.DataFrame:
    """
    Calculate conversion funnel with optional segmentation.
    
    Args:
        con: DuckDB connection
        funnel_steps: List of (step_name, event_type) tuples
        segment_by: Column to segment by (e.g., 'country', 'acquisition_channel')
        date_range: Optional (start_date, end_date) tuple
    
    Returns:
        DataFrame with funnel metrics per segment
    """
    # Build WHERE clause for date filtering
    where_clause = ""
    if date_range:
        where_clause = f"AND timestamp BETWEEN '{date_range[0]}' AND '{date_range[1]}'"
    
    # Build funnel CTEs - using read_parquet with local files
    funnel_ctes = []
    for i, (step_name, event_type) in enumerate(funnel_steps):
        cte = f"""
        step_{i} AS (
            SELECT DISTINCT user_id
            FROM read_parquet('{config.EVENTS_FILE}')
            WHERE event_type = '{event_type}' {where_clause}
        )"""
        funnel_ctes.append(cte)
    
    # Build segment join if needed
    segment_join = ""
    segment_select = ""
    segment_group = ""
    
    if segment_by:
        segment_join = f"""
        LEFT JOIN read_parquet('{config.USERS_FILE}') u
            ON step_0.user_id = u.user_id
        """
        segment_select = f"u.{segment_by},"
        segment_group = f"u.{segment_by},"
    
    # Build main query
    step_selects = []
    for i in range(len(funnel_steps)):
        if i == 0:
            step_selects.append(f"COUNT(DISTINCT step_0.user_id) as step_{i}_users")
        else:
            step_selects.append(f"COUNT(DISTINCT step_{i}.user_id) as step_{i}_users")
    
    query = f"""
    WITH {','.join(funnel_ctes)}
    
    SELECT 
        {segment_select}
        {','.join(step_selects)}
    FROM step_0
    {segment_join}
    {' '.join([f'LEFT JOIN step_{i} ON step_0.user_id = step_{i}.user_id' for i in range(1, len(funnel_steps))])}
    {'GROUP BY ' + segment_group.rstrip(',') if segment_group else ''}
    """
    
    df = con.execute(query).df()
    
    # Calculate conversion rates
    for i in range(1, len(funnel_steps)):
        # Overall rate from step 0
        df[f'step_0_to_{i}_rate'] = (df[f'step_{i}_users'] / df[f'step_0_users'] * 100).round(2)
        
        # Incremental rate from previous step
        df[f'step_{i-1}_to_{i}_incremental'] = (df[f'step_{i}_users'] / df[f'step_{i-1}_users'] * 100).round(2)
    
    # Add step names
    step_mapping = {f'step_{i}_users': step_name for i, (step_name, _) in enumerate(funnel_steps)}
    
    return df, step_mapping


def calculate_time_to_convert(
    con: duckdb.DuckDBPyConnection,
    start_event: str,
    end_event: str,
    segment_by: Optional[str] = None
) -> pd.DataFrame:
    """
    Calculate time between two events (e.g., app_open to upgrade_clicked).
    
    Args:
        con: DuckDB connection
        start_event: Starting event type
        end_event: Ending event type
        segment_by: Optional column to segment by (e.g., 'country', 'acquisition_channel')
    
    Returns:
        DataFrame with median/percentile time to convert
    """
    # Build segment join within the time_diffs CTE
    segment_join = ""
    segment_select_in_cte = ""
    segment_select_final = ""
    segment_group = ""
    
    if segment_by:
        segment_join = f"""
        LEFT JOIN read_parquet('{config.USERS_FILE}') u
            ON start_events.user_id = u.user_id
        """
        segment_select_in_cte = f"u.{segment_by},"  # In CTE, reference as u.column
        segment_select_final = f"{segment_by},"      # In final SELECT, just column name
        segment_group = f"{segment_by},"             # In GROUP BY, just column name
    
    query = f"""
    WITH start_events AS (
        SELECT 
            user_id,
            MIN(CAST(timestamp AS TIMESTAMP)) as start_time
        FROM read_parquet('{config.EVENTS_FILE}')
        WHERE event_type = '{start_event}'
        GROUP BY user_id
    ),
    end_events AS (
        SELECT 
            user_id,
            MIN(CAST(timestamp AS TIMESTAMP)) as end_time
        FROM read_parquet('{config.EVENTS_FILE}')
        WHERE event_type = '{end_event}'
        GROUP BY user_id
    ),
    time_diffs AS (
        SELECT 
            start_events.user_id,
            {segment_select_in_cte}
            EXTRACT(EPOCH FROM (end_events.end_time - start_events.start_time)) / 86400.0 as days_to_convert
        FROM start_events
        INNER JOIN end_events 
            ON start_events.user_id = end_events.user_id
        {segment_join}
        WHERE end_events.end_time > start_events.start_time
    )
    SELECT 
        {segment_select_final}
        COUNT(*) as converted_users,
        ROUND(MEDIAN(days_to_convert), 2) as median_days,
        ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY days_to_convert), 2) as p25_days,
        ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY days_to_convert), 2) as p75_days,
        ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY days_to_convert), 2) as p90_days
    FROM time_diffs
    {'GROUP BY ' + segment_group.rstrip(',') if segment_group else ''}
    """
    
    return con.execute(query).df()


def calculate_drop_off_reasons(
    con: duckdb.DuckDBPyConnection,
    funnel_steps: List[tuple]
) -> pd.DataFrame:
    """
    Identify users who dropped off at each stage and analyze characteristics.
    
    Returns:
        DataFrame with drop-off counts, segment totals, and drop-off rates
    """
    results = []
    
    for i in range(len(funnel_steps) - 1):
        current_step = funnel_steps[i][1]
        next_step = funnel_steps[i + 1][1]
        
        query = f"""
        WITH completed_current AS (
            SELECT DISTINCT user_id
            FROM read_parquet('{config.EVENTS_FILE}')
            WHERE event_type = '{current_step}'
        ),
        completed_next AS (
            SELECT DISTINCT user_id
            FROM read_parquet('{config.EVENTS_FILE}')
            WHERE event_type = '{next_step}'
        ),
        dropped_users AS (
            SELECT user_id
            FROM completed_current
            WHERE user_id NOT IN (SELECT user_id FROM completed_next)
        ),
        current_with_segment AS (
            SELECT 
                cc.user_id,
                u.country,
                u.acquisition_channel
            FROM completed_current cc
            LEFT JOIN read_parquet('{config.USERS_FILE}') u
                ON cc.user_id = u.user_id
        ),
        dropped_with_segment AS (
            SELECT 
                d.user_id,
                u.country,
                u.acquisition_channel
            FROM dropped_users d
            LEFT JOIN read_parquet('{config.USERS_FILE}') u
                ON d.user_id = u.user_id
        )
        SELECT 
            '{funnel_steps[i][0]}' as dropped_at_stage,
            COUNT(DISTINCT d.user_id) as dropped_users,
            d.country,
            d.acquisition_channel,
            COUNT(DISTINCT c.user_id) as users_in_segment,
            ROUND(COUNT(DISTINCT d.user_id) * 100.0 / COUNT(DISTINCT c.user_id), 2) as drop_off_rate
        FROM dropped_with_segment d
        LEFT JOIN current_with_segment c
            ON d.country = c.country 
            AND d.acquisition_channel = c.acquisition_channel
        GROUP BY d.country, d.acquisition_channel
        ORDER BY dropped_users DESC
        LIMIT 10
        """
        
        df = con.execute(query).df()
        results.append(df)
    
    return pd.concat(results, ignore_index=True)
        
    #results.append(con.execute(query).df())
    
    #return pd.concat(results, ignore_index=True)
