"""
SecureFlow Analytics - Configuration Settings
"""
from pathlib import Path
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"

# Database
DUCKDB_PATH = DATA_DIR / "secureflow.duckdb"

# Data generation parameters
DATA_CONFIG = {
    "start_date": datetime(2024, 1, 1),
    "end_date": datetime(2025, 6, 30),
    "n_users": 50_000,
    "random_seed": 42,
}

# Experiment configurations
EXPERIMENTS = {
    "exp_001": {
        "name": "new_onboarding_flow",
        "expected_lift": 0.15,  # 15% lift in activation
        "primary_metric": "activated",
    },
    "exp_002": {
        "name": "threat_explainer_v2",
        "expected_lift": -0.20,  # 20% reduction in help views
        "primary_metric": "viewed_help",
    },
    "exp_003": {
        "name": "premium_upsell_timing",
        "expected_lift": -0.25,  # 25% DECREASE (negative result)
        "primary_metric": "converted_to_premium",
    },
    "exp_004": {
        "name": "real_time_protection_default",
        "expected_lift": 0.10,  # But confounded by country
        "primary_metric": "threat_resolved",
        "analysis_method": "difference_in_differences",
    },
}

# Feature importance for churn (ground truth for validation)
CHURN_DRIVERS = {
    "onboarding_incomplete": 2.5,  # 2.5x more likely to churn
    "unresolved_threats": 2.0,     # 2x more likely to churn
    "no_real_time_protection": 1.7, # 1.7x more likely to churn
    "low_engagement": 1.5,          # 1.5x more likely to churn
}

# MLflow settings
MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"
MLFLOW_EXPERIMENT_NAME = "secureflow_models"

# Dashboard settings
DASHBOARD_CONFIG = {
    "refresh_interval": 3600,  # 1 hour
    "default_date_range": 90,  # days
}
