"""
SecureFlow Analytics - Configuration Settings
Local configuration for running notebooks and scripts.

Data Architecture:
- Local: All data stored locally for fast access
- Database: Local DuckDB for analysis
"""
from pathlib import Path
import os

# ================== LOCAL PROJECT PATH ==================
# All data is stored locally for performance
PROJECT_ROOT = Path(r"C:\Users\Manu\secureflow_analytics")

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"

# ================== LOCAL DATABASE ==================
# Local DuckDB database (optional - can query parquet files directly)
DB_PATH = PROJECT_ROOT / "secureflow.duckdb"

# ================== DATA FILES ==================
# Local parquet files
USERS_FILE = RAW_DATA_DIR / "users.parquet"
SUBSCRIPTIONS_FILE = RAW_DATA_DIR / "subscriptions.parquet"
EVENTS_FILE = RAW_DATA_DIR / "events.parquet"
EXPERIMENTS_FILE = RAW_DATA_DIR / "experiments.parquet"
EXPERIMENT_ASSIGNMENTS_FILE = RAW_DATA_DIR / "experiment_assignments.parquet"
EXPERIMENT_METRICS_FILE = RAW_DATA_DIR / "experiment_metrics.parquet"
FEATURE_USAGE_FILE = RAW_DATA_DIR / "feature_usage.parquet"
SUPPORT_TICKETS_FILE = RAW_DATA_DIR / "support_tickets.parquet"

# ================== VALIDATION ==================
def validate_paths():
    """Check if data paths exist"""
    if not PROJECT_ROOT.exists():
        print(f"⚠️  WARNING: Project root not found at {PROJECT_ROOT}")
        return False
    
    if not RAW_DATA_DIR.exists():
        print(f"⚠️  WARNING: Raw data directory not found at {RAW_DATA_DIR}")
        print(f"   Create it with: mkdir {RAW_DATA_DIR}")
        return False
    
    required_files = [
        USERS_FILE,
        EVENTS_FILE,
        SUBSCRIPTIONS_FILE
    ]
    
    missing_files = [f for f in required_files if not f.exists()]
    if missing_files:
        print(f"⚠️  WARNING: Missing data files:")
        for f in missing_files:
            print(f"   - {f.name}")
        print(f"\n💡 Copy parquet files from Google Drive to: {RAW_DATA_DIR}")
        return False
    
    print(f"✅ All paths validated!")
    print(f"   Project: {PROJECT_ROOT}")
    print(f"   Data: {RAW_DATA_DIR}")
    
    # Show file sizes
    total_size = 0
    for f in required_files:
        if f.exists():
            size_mb = f.stat().st_size / 1e6
            total_size += size_mb
            print(f"   - {f.name}: {size_mb:.1f} MB")
    print(f"   Total: {total_size:.1f} MB")
    
    return True

# ================== DISPLAY INFO ==================
if __name__ == "__main__":
    print("=" * 60)
    print("SecureFlow Analytics - Configuration")
    print("=" * 60)
    print(f"\n📂 Project Root: {PROJECT_ROOT}")
    print(f"📊 Raw Data:     {RAW_DATA_DIR}")
    print(f"🗄️  Database:     {DB_PATH}")
    print()
    
    validate_paths()
