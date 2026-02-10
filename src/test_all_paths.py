"""
Test script to verify all paths are correct
Run this before using the notebooks
"""
import sys
from pathlib import Path

# Update this to your actual project location
sys.path.append(r'H:\My Drive\SecureFlow_Analytics\src')

try:
    import config
    
    print("=" * 70)
    print("SecureFlow Analytics - Path Verification")
    print("=" * 70)
    
    # Test 1: Check path construction
    print("\n1️⃣  Path Construction Test:")
    print(f"   EVENTS_FILE (Windows): {config.EVENTS_FILE}")
    print(f"   EVENTS_FILE (DuckDB):  {str(config.EVENTS_FILE).replace(chr(92), '/')}")
    
    expected_windows = r"H:\My Drive\SecureFlow_Analytics\data\raw\events.parquet"
    expected_duckdb = "H:/My Drive/SecureFlow_Analytics/data/raw/events.parquet"
    
    windows_path = str(config.EVENTS_FILE)
    duckdb_path = str(config.EVENTS_FILE).replace('\\', '/')
    
    if windows_path == expected_windows:
        print("   ✅ Windows path format correct")
    else:
        print(f"   ❌ Windows path incorrect")
        print(f"      Expected: {expected_windows}")
        print(f"      Got:      {windows_path}")
    
    if duckdb_path == expected_duckdb:
        print("   ✅ DuckDB path format correct")
    else:
        print(f"   ❌ DuckDB path incorrect")
        print(f"      Expected: {expected_duckdb}")
        print(f"      Got:      {duckdb_path}")
    
    # Test 2: Check files exist
    print("\n2️⃣  File Existence Test:")
    test_files = {
        'users.parquet': config.USERS_FILE,
        'events.parquet': config.EVENTS_FILE,
        'subscriptions.parquet': config.SUBSCRIPTIONS_FILE,
    }
    
    all_exist = True
    for name, path in test_files.items():
        exists = path.exists()
        status = "✅" if exists else "❌"
        print(f"   {status} {name}: {exists}")
        if not exists:
            all_exist = False
            print(f"      Path: {path}")
    
    # Test 3: DuckDB query test
    print("\n3️⃣  DuckDB Query Test:")
    try:
        import duckdb
        con = duckdb.connect()
        
        # Test with properly formatted path
        test_path = str(config.EVENTS_FILE).replace('\\', '/')
        query = f"SELECT COUNT(*) as count FROM read_parquet('{test_path}')"
        
        print(f"   Query: {query[:80]}...")
        result = con.execute(query).fetchone()
        
        print(f"   ✅ Query successful!")
        print(f"   📊 Events count: {result[0]:,}")
        
        con.close()
    except Exception as e:
        print(f"   ❌ DuckDB query failed: {e}")
    
    # Test 4: Import analytics modules
    print("\n4️⃣  Module Import Test:")
    try:
        from analytics.funnel_analysis import calculate_funnel
        from analytics.cohort_analysis import calculate_retention_cohorts
        print("   ✅ Successfully imported analytics modules")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    if all_exist:
        print("✅ All tests passed! You're ready to run the notebooks.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    print("=" * 70)
    
except ImportError as e:
    print(f"❌ Failed to import config: {e}")
    print("\nMake sure:")
    print("1. You're running from the correct directory")
    print("2. config.py exists in H:/My Drive/SecureFlow_Analytics/src/")
    print("3. The path in sys.path.append() is correct")
