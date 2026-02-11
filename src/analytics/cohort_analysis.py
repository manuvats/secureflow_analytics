"""
Cohort Analysis Functions - SecureFlow Analytics
DuckDB-based retention and cohort calculations
"""
import duckdb
import pandas as pd
from typing import Optional
from pathlib import Path
import sys

# Import config
sys.path.append(str(Path(__file__).parent.parent))
import config


def calculate_retention_cohorts(
    con: duckdb.DuckDBPyConnection,
    cohort_period: str = 'week',
    activity_event: str = 'scan_completed',
    max_periods: int = 12
) -> pd.DataFrame:
    """
    Calculate classic retention cohorts (Week 0, Week 1, etc.).
    
    Args:
        con: DuckDB connection
        cohort_period: 'week' or 'month'
        activity_event: Event that defines "active"
        max_periods: Number of periods to track
    
    Returns:
        DataFrame with cohort retention percentages
    """
    period_func = "DATE_TRUNC('week', CAST(signup_date AS TIMESTAMP))" if cohort_period == 'week' else "DATE_TRUNC('month', CAST(signup_date AS TIMESTAMP))"
    
    query = f"""
    WITH user_cohorts AS (
        SELECT 
            user_id,
            {period_func} as cohort_period
        FROM read_parquet('{config.USERS_FILE}')
    ),
    user_activity AS (
        SELECT 
            user_id,
            {period_func.replace('signup_date', 'timestamp')} as activity_period
        FROM read_parquet('{config.EVENTS_FILE}')
        WHERE event_type = '{activity_event}'
        GROUP BY user_id, activity_period
    ),
    cohort_activity AS (
        SELECT 
            uc.cohort_period,
            ua.activity_period,
            COUNT(DISTINCT ua.user_id) as active_users
        FROM user_cohorts uc
        INNER JOIN user_activity ua ON uc.user_id = ua.user_id
        GROUP BY uc.cohort_period, ua.activity_period
    ),
    cohort_sizes AS (
        SELECT 
            cohort_period,
            COUNT(DISTINCT user_id) as cohort_size
        FROM user_cohorts
        GROUP BY cohort_period
    )
    SELECT 
        ca.cohort_period,
        cs.cohort_size,
        ca.activity_period,
        DATEDIFF('{cohort_period}', ca.cohort_period, ca.activity_period) as periods_out,
        ca.active_users,
        ROUND(100.0 * ca.active_users / cs.cohort_size, 2) as retention_pct
    FROM cohort_activity ca
    INNER JOIN cohort_sizes cs ON ca.cohort_period = cs.cohort_period
    WHERE DATEDIFF('{cohort_period}', ca.cohort_period, ca.activity_period) <= {max_periods}
    ORDER BY ca.cohort_period, periods_out
    """
    
    return con.execute(query).df()


def pivot_retention_table(retention_df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot retention data into classic cohort table format.
    
    Returns:
        Pivoted DataFrame (cohorts as rows, periods as columns)
    """
    pivot = retention_df.pivot_table(
        index='cohort_period',
        columns='periods_out',
        values='retention_pct',
        aggfunc='first'
    )
    
    # Add cohort size column
    cohort_sizes = retention_df.groupby('cohort_period')['cohort_size'].first()
    pivot.insert(0, 'Cohort Size', cohort_sizes)
    
    # Rename columns
    pivot.columns = ['Cohort Size'] + [f'Week {i}' if i > 0 else 'Week 0' for i in range(len(pivot.columns) - 1)]
    
    return pivot


def compare_feature_adoption_retention(
    con: duckdb.DuckDBPyConnection,
    feature_name: str,
    cohort_period: str = 'week',
    max_periods: int = 12
) -> pd.DataFrame:
    """
    Compare retention between users who adopted a feature vs those who didn't.
    
    Args:
        feature_name: Feature to analyze (e.g., 'real_time_protection')
    
    Returns:
        DataFrame with retention comparison
    """
    period_func = "DATE_TRUNC('week', CAST(signup_date AS TIMESTAMP))" if cohort_period == 'week' else "DATE_TRUNC('month', CAST(signup_date AS TIMESTAMP))"
    
    query = f"""
    WITH user_cohorts AS (
        SELECT 
            user_id,
            {period_func} as cohort_period
        FROM read_parquet('{config.USERS_FILE}')
    ),
    feature_adopters AS (
        SELECT DISTINCT user_id
        FROM read_parquet('{config.FEATURE_USAGE_FILE}')
        WHERE feature_name = '{feature_name}'
    ),
    user_activity AS (
        SELECT 
            user_id,
            {period_func.replace('signup_date', 'timestamp')} as activity_period
        FROM read_parquet('{config.EVENTS_FILE}')
        WHERE event_type = 'scan_completed'
        GROUP BY user_id, activity_period
    ),
    cohort_activity AS (
        SELECT 
            uc.cohort_period,
            ua.activity_period,
            CASE WHEN fa.user_id IS NOT NULL THEN 'Adopted' ELSE 'Not Adopted' END as adoption_status,
            COUNT(DISTINCT ua.user_id) as active_users
        FROM user_cohorts uc
        INNER JOIN user_activity ua ON uc.user_id = ua.user_id
        LEFT JOIN feature_adopters fa ON uc.user_id = fa.user_id
        GROUP BY uc.cohort_period, ua.activity_period, adoption_status
    ),
    cohort_sizes AS (
        SELECT 
            cohort_period,
            CASE WHEN fa.user_id IS NOT NULL THEN 'Adopted' ELSE 'Not Adopted' END as adoption_status,
            COUNT(DISTINCT uc.user_id) as cohort_size
        FROM user_cohorts uc
        LEFT JOIN feature_adopters fa ON uc.user_id = fa.user_id
        GROUP BY cohort_period, adoption_status
    )
    SELECT 
        ca.cohort_period,
        ca.adoption_status,
        cs.cohort_size,
        DATEDIFF('{cohort_period}', ca.cohort_period, ca.activity_period) as periods_out,
        ca.active_users,
        ROUND(100.0 * ca.active_users / cs.cohort_size, 2) as retention_pct
    FROM cohort_activity ca
    INNER JOIN cohort_sizes cs 
        ON ca.cohort_period = cs.cohort_period 
        AND ca.adoption_status = cs.adoption_status
    WHERE DATEDIFF('{cohort_period}', ca.cohort_period, ca.activity_period) <= {max_periods}
    ORDER BY ca.cohort_period, ca.adoption_status, periods_out
    """
    
    return con.execute(query).df()


def calculate_ltv_by_cohort(
    con: duckdb.DuckDBPyConnection,
    cohort_period: str = 'month'
) -> pd.DataFrame:
    """
    Calculate cumulative revenue (LTV proxy) by cohort.
    
    Returns:
        DataFrame with cumulative revenue per cohort
    """
    period_func = "DATE_TRUNC('month', CAST(signup_date AS TIMESTAMP))"
    
    query = f"""
    WITH user_cohorts AS (
        SELECT 
            user_id,
            {period_func} as cohort_period
        FROM read_parquet('{config.USERS_FILE}')
    ),
    subscription_revenue AS (
        SELECT 
            s.user_id,
            COALESCE(SUM(
                CASE s.plan
                    WHEN 'free' THEN 0
                    WHEN 'premium_monthly' THEN 9.99
                    WHEN 'premium_annual' THEN 99.99
                    ELSE 0
                END * GREATEST(DATEDIFF('month', 
                    CAST(s.start_date AS TIMESTAMP), 
                    COALESCE(CAST(s.end_date AS TIMESTAMP), CURRENT_DATE)
                ), 1)
            ), 0) as total_revenue
        FROM read_parquet('{config.SUBSCRIPTIONS_FILE}') s
        GROUP BY s.user_id
    )
    SELECT 
        uc.cohort_period,
        COUNT(DISTINCT uc.user_id) as cohort_size,
        COUNT(DISTINCT CASE WHEN sr.total_revenue > 0 THEN sr.user_id END) as paying_users,
        ROUND(AVG(COALESCE(sr.total_revenue, 0)), 2) as avg_ltv,
        ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY COALESCE(sr.total_revenue, 0)), 2) as median_ltv_all,
        ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sr.total_revenue) 
              FILTER (WHERE sr.total_revenue > 0), 2) as median_ltv_paying,
        ROUND(SUM(COALESCE(sr.total_revenue, 0)), 2) as total_revenue
    FROM user_cohorts uc
    LEFT JOIN subscription_revenue sr ON uc.user_id = sr.user_id
    GROUP BY uc.cohort_period
    ORDER BY uc.cohort_period
    """
    
    return con.execute(query).df()


def compare_channel_cohorts(
    con: duckdb.DuckDBPyConnection,
    cohort_period: str = 'week',
    max_periods: int = 8
) -> pd.DataFrame:
    """
    Compare retention across acquisition channels.
    
    Returns:
        DataFrame with retention by channel
    """
    period_func = "DATE_TRUNC('week', CAST(signup_date AS TIMESTAMP))"
    
    query = f"""
    WITH user_cohorts AS (
        SELECT 
            user_id,
            acquisition_channel,
            {period_func} as cohort_period
        FROM read_parquet('{config.USERS_FILE}')
    ),
    user_activity AS (
        SELECT 
            user_id,
            {period_func.replace('signup_date', 'timestamp')} as activity_period
        FROM read_parquet('{config.EVENTS_FILE}')
        WHERE event_type = 'scan_completed'
        GROUP BY user_id, activity_period
    ),
    cohort_activity AS (
        SELECT 
            uc.acquisition_channel,
            uc.cohort_period,
            ua.activity_period,
            COUNT(DISTINCT ua.user_id) as active_users
        FROM user_cohorts uc
        INNER JOIN user_activity ua ON uc.user_id = ua.user_id
        GROUP BY uc.acquisition_channel, uc.cohort_period, ua.activity_period
    ),
    cohort_sizes AS (
        SELECT 
            acquisition_channel,
            cohort_period,
            COUNT(DISTINCT user_id) as cohort_size
        FROM user_cohorts
        GROUP BY acquisition_channel, cohort_period
    )
    SELECT 
        ca.acquisition_channel,
        ca.cohort_period,
        DATEDIFF('week', ca.cohort_period, ca.activity_period) as weeks_out,
        cs.cohort_size,
        ca.active_users,
        ROUND(100.0 * ca.active_users / cs.cohort_size, 2) as retention_pct
    FROM cohort_activity ca
    INNER JOIN cohort_sizes cs 
        ON ca.acquisition_channel = cs.acquisition_channel 
        AND ca.cohort_period = cs.cohort_period
    WHERE DATEDIFF('week', ca.cohort_period, ca.activity_period) <= {max_periods}
    ORDER BY ca.acquisition_channel, ca.cohort_period, weeks_out
    """
    
    return con.execute(query).df()
