# =============================================================================
# SecureFlow Analytics - Data Generation for Google Colab
# =============================================================================
# Copy this entire script into a Colab notebook cell and run it.
# Data will be saved to: /content/drive/MyDrive/secureflow_analytics/data/raw/
# =============================================================================

# Mount Google Drive first (run this in a separate cell):
# from google.colab import drive
# drive.mount('/content/drive')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================
PROJECT_ROOT = Path("/content/drive/MyDrive/secureflow_analytics")
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 42
DATE_START = "2024-01-01"
DATE_END = "2025-06-30"
N_USERS = 50_000

np.random.seed(RANDOM_SEED)
START_DATE = datetime.strptime(DATE_START, "%Y-%m-%d")
END_DATE = datetime.strptime(DATE_END, "%Y-%m-%d")

# Categorical values
ACQUISITION_CHANNELS = {"organic_search": 0.25, "paid_search": 0.20, "social_media": 0.15, "referral": 0.12, "affiliate": 0.10, "direct": 0.10, "app_store": 0.08}
COUNTRIES = {"US": 0.35, "CA": 0.08, "UK": 0.12, "DE": 0.08, "FR": 0.06, "AU": 0.05, "IN": 0.10, "BR": 0.06, "JP": 0.05, "MX": 0.05}
DEVICE_OS = {"windows": 0.45, "macos": 0.25, "android": 0.18, "ios": 0.12}
EVENT_TYPES = ["app_open", "scan_started", "scan_completed", "threat_detected", "threat_resolved", "settings_changed", "upgrade_clicked", "help_viewed", "notification_clicked", "share_clicked", "feature_discovered", "onboarding_step_completed"]
FEATURES = ["real_time_protection", "scheduled_scans", "vpn_feature", "password_manager", "safe_browsing", "firewall", "identity_monitoring", "parental_controls"]
PREMIUM_ONLY_FEATURES = ["vpn_feature", "identity_monitoring", "parental_controls"]
THREAT_TYPES = ["malware", "pup", "adware", "phishing", "tracking_cookie"]
THREAT_SEVERITIES = ["low", "medium", "high", "critical"]
SCAN_TYPES = ["quick", "full", "custom"]
TICKET_CATEGORIES = ["technical", "billing", "feature_request", "threat_help", "account"]

# Modifiers
CHANNEL_CONVERSION_MODIFIER = {"referral": 1.5, "organic_search": 1.1, "paid_search": 1.2, "social_media": 0.9, "affiliate": 0.8, "direct": 1.0, "app_store": 1.1}
CHANNEL_CHURN_MODIFIER = {"referral": 0.75, "organic_search": 0.9, "paid_search": 1.0, "social_media": 1.1, "affiliate": 1.2, "direct": 0.95, "app_store": 1.0}
PLAN_CHURN_RATES = {"free": 0.15, "premium_monthly": 0.08, "premium_annual": 0.03}
PLAN_MRR = {"free": 0, "premium_monthly": 9.99, "premium_annual": 7.99}
FEATURE_ADOPTION_RATES = {"real_time_protection": 0.65, "scheduled_scans": 0.40, "vpn_feature": 0.15, "password_manager": 0.25, "safe_browsing": 0.45, "firewall": 0.35, "identity_monitoring": 0.20, "parental_controls": 0.10}

# Experiments
EXPERIMENTS = {
    "exp_001": {"name": "new_onboarding_flow", "start_date": "2024-03-01", "end_date": "2024-05-31", "variants": ["control", "treatment"], "allocation": [0.5, 0.5], "primary_metric": "activated", "targeting": "all_new_users", "expected_lift": 0.15},
    "exp_002": {"name": "threat_explainer_v2", "start_date": "2024-06-01", "end_date": "2024-08-31", "variants": ["control", "treatment"], "allocation": [0.5, 0.5], "primary_metric": "viewed_help", "targeting": "all_users", "expected_lift": -0.20},
    "exp_003": {"name": "premium_upsell_timing", "start_date": "2024-09-01", "end_date": "2024-11-30", "variants": ["day_7_upsell", "day_3_upsell"], "allocation": [0.5, 0.5], "primary_metric": "converted_to_premium", "targeting": "free_users", "expected_lift": -0.25},
    "exp_004": {"name": "real_time_protection_default", "start_date": "2024-11-01", "end_date": "2025-02-28", "variants": ["rollout_group", "control_group"], "allocation": [0.5, 0.5], "primary_metric": "threat_resolved", "targeting": "geo_based", "expected_lift": 0.10}
}

# Event probabilities
EVENT_PROBS_ONBOARDING = {"app_open": 0.20, "scan_started": 0.15, "scan_completed": 0.12, "threat_detected": 0.02, "threat_resolved": 0.02, "settings_changed": 0.05, "upgrade_clicked": 0.03, "help_viewed": 0.08, "notification_clicked": 0.03, "share_clicked": 0.02, "feature_discovered": 0.08, "onboarding_step_completed": 0.20}
EVENT_PROBS_THREAT = {"app_open": 0.10, "scan_started": 0.10, "scan_completed": 0.08, "threat_detected": 0.02, "threat_resolved": 0.25, "settings_changed": 0.05, "upgrade_clicked": 0.02, "help_viewed": 0.15, "notification_clicked": 0.08, "share_clicked": 0.02, "feature_discovered": 0.03, "onboarding_step_completed": 0.10}
EVENT_PROBS_NORMAL = {"app_open": 0.25, "scan_started": 0.12, "scan_completed": 0.10, "threat_detected": 0.05, "threat_resolved": 0.04, "settings_changed": 0.08, "upgrade_clicked": 0.04, "help_viewed": 0.06, "notification_clicked": 0.08, "share_clicked": 0.03, "feature_discovered": 0.05, "onboarding_step_completed": 0.10}

HOUR_WEIGHTS_DESKTOP = [0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.03, 0.05, 0.08, 0.10, 0.10, 0.08, 0.06, 0.08, 0.08, 0.06, 0.05, 0.04, 0.03, 0.03, 0.02, 0.02, 0.01, 0.01]
HOUR_WEIGHTS_MOBILE = [0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.03, 0.04, 0.05, 0.05, 0.04, 0.04, 0.04, 0.04, 0.04, 0.05, 0.06, 0.07, 0.08, 0.08, 0.07, 0.05, 0.03, 0.02]
APP_VERSIONS = [("2024-01-01", "2024-03-31", "3.0.0"), ("2024-04-01", "2024-06-30", "3.1.0"), ("2024-07-01", "2024-09-30", "3.2.0"), ("2024-10-01", "2024-12-31", "4.0.0"), ("2025-01-01", "2025-03-31", "4.1.0"), ("2025-04-01", "2025-06-30", "4.2.0")]

print(f"✓ Config loaded | Output: {RAW_DIR}")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_hour_weights(device):
    weights = HOUR_WEIGHTS_DESKTOP if device in ['windows', 'macos'] else HOUR_WEIGHTS_MOBILE
    return [w/sum(weights) for w in weights]

def get_event_probs(phase, plan, engagement):
    probs = EVENT_PROBS_ONBOARDING.copy() if phase == 'onboarding' else EVENT_PROBS_THREAT.copy() if phase == 'threat' else EVENT_PROBS_NORMAL.copy()
    if phase == 'normal':
        if plan == 'free': probs['upgrade_clicked'] = 0.08
        if engagement == 'high': probs['feature_discovered'] = 0.10
    prob_list = [probs.get(et, 0.05) for et in EVENT_TYPES]
    return [p/sum(prob_list) for p in prob_list]

def get_app_version(date):
    for start, end, version in APP_VERSIONS:
        if datetime.strptime(start, '%Y-%m-%d') <= date <= datetime.strptime(end, '%Y-%m-%d'):
            return version
    return '4.2.0'

def generate_event_properties(event_type, day_num):
    props = {}
    if event_type == 'scan_started': props['scan_type'] = np.random.choice(SCAN_TYPES, p=[0.6, 0.3, 0.1])
    elif event_type == 'scan_completed': props = {'scan_type': np.random.choice(SCAN_TYPES, p=[0.6, 0.3, 0.1]), 'duration_seconds': int(np.random.exponential(120)), 'files_scanned': int(np.random.exponential(5000)), 'threats_found': int(np.random.poisson(0.3))}
    elif event_type == 'threat_detected': props = {'threat_type': np.random.choice(THREAT_TYPES, p=[0.15, 0.25, 0.20, 0.15, 0.25]), 'severity': np.random.choice(THREAT_SEVERITIES, p=[0.3, 0.4, 0.2, 0.1])}
    elif event_type == 'threat_resolved': props['action'] = np.random.choice(['quarantined', 'deleted', 'allowed'], p=[0.5, 0.4, 0.1])
    elif event_type == 'settings_changed': props['setting'] = np.random.choice(['real_time_protection', 'scan_schedule', 'notifications', 'firewall_rules', 'exclusions'])
    elif event_type == 'upgrade_clicked': props = {'source': np.random.choice(['banner', 'feature_gate', 'settings', 'notification']), 'plan_shown': np.random.choice(['monthly', 'annual'])}
    elif event_type == 'help_viewed': props = {'article_id': f"help_{np.random.randint(1, 50):03d}", 'category': np.random.choice(['setup', 'scanning', 'threats', 'billing', 'features'])}
    elif event_type == 'onboarding_step_completed': step = min(day_num, 5); props = {'step': step, 'step_name': ['welcome', 'first_scan', 'review_results', 'configure_settings', 'complete'][step-1] if step > 0 else 'welcome'}
    return props

# =============================================================================
# GENERATE USERS
# =============================================================================
print("\n[1/7] Generating users...")
email_domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com"]
users = []
days_range = (END_DATE - START_DATE).days

for i in range(N_USERS):
    signup_date = START_DATE + timedelta(days=np.random.randint(0, days_range - 30))
    channel = np.random.choice(list(ACQUISITION_CHANNELS.keys()), p=list(ACQUISITION_CHANNELS.values()))
    premium_prob = min(0.5, 0.15 * CHANNEL_CONVERSION_MODIFIER.get(channel, 1.0) * (1.3 if signup_date.month in [10, 11, 12] else 1.0))
    users.append({
        'user_id': f"user_{i:06d}", 'signup_date': signup_date.strftime('%Y-%m-%d'),
        'plan_type': np.random.choice(['free', 'premium_monthly', 'premium_annual'], p=[1-premium_prob, premium_prob*0.6, premium_prob*0.4]),
        'country': np.random.choice(list(COUNTRIES.keys()), p=list(COUNTRIES.values())),
        'device_os': np.random.choice(list(DEVICE_OS.keys()), p=list(DEVICE_OS.values())),
        'acquisition_channel': channel, 'email_domain': np.random.choice(email_domains)
    })
users_df = pd.DataFrame(users)
print(f"    ✓ {len(users_df):,} users")

# =============================================================================
# GENERATE SUBSCRIPTIONS
# =============================================================================
print("[2/7] Generating subscriptions...")
subscriptions = []
for _, user in users_df.iterrows():
    signup_date = datetime.strptime(user['signup_date'], '%Y-%m-%d')
    plan_type, channel = user['plan_type'], user['acquisition_channel']
    final_churn = PLAN_CHURN_RATES.get(plan_type, 0.10) * CHANNEL_CHURN_MODIFIER.get(channel, 1.0) * (0.85 if signup_date.month in [10, 11, 12] else 1.0)
    current_date, sub_id = signup_date, 0
    while current_date < END_DATE:
        sub_id += 1
        period_days = 365 if plan_type == 'premium_annual' else 30
        if np.random.random() < final_churn:
            end_date, status = current_date + timedelta(days=np.random.randint(7, period_days)), 'cancelled'
        else:
            end_date = current_date + timedelta(days=period_days)
            status = 'active' if end_date >= END_DATE else 'renewed'
        subscriptions.append({'subscription_id': f"{user['user_id']}_sub_{sub_id:02d}", 'user_id': user['user_id'], 'plan': plan_type, 'start_date': current_date.strftime('%Y-%m-%d'), 'end_date': min(end_date, END_DATE).strftime('%Y-%m-%d'), 'status': status, 'mrr': PLAN_MRR.get(plan_type, 0), 'cancellation_reason': np.random.choice(['price', 'not_using', 'switched_competitor', 'technical_issues'], p=[0.30, 0.40, 0.18, 0.12]) if status == 'cancelled' else None})
        if status == 'cancelled': break
        current_date = end_date
subscriptions_df = pd.DataFrame(subscriptions)
print(f"    ✓ {len(subscriptions_df):,} subscriptions | Churn: {(subscriptions_df.groupby('user_id')['status'].last() == 'cancelled').mean()*100:.1f}%")

# =============================================================================
# GENERATE EVENTS
# =============================================================================
print("[3/7] Generating events (this takes a few minutes)...")
user_periods = subscriptions_df.groupby('user_id').agg({'start_date': 'min', 'end_date': 'max', 'status': 'last'}).reset_index()
users_merged = users_df.merge(user_periods, on='user_id')
all_events, event_counter = [], 0

for idx, user in users_merged.iterrows():
    if idx % 10000 == 0: print(f"    Processing {idx:,}/{len(users_merged):,}...")
    start, end = datetime.strptime(user['start_date'], '%Y-%m-%d'), datetime.strptime(user['end_date'], '%Y-%m-%d')
    is_churned, plan, device = user['status'] == 'cancelled', user['plan_type'], user['device_os']
    engagement = np.random.choice(['low', 'medium'], p=[0.7, 0.3]) if is_churned else np.random.choice(['low', 'medium', 'high'], p=[0.2, 0.5, 0.3])
    events_per_day = {'low': 0.5, 'medium': 2, 'high': 5}[engagement]
    current, day_num, onboarding_complete, scans_week1, unresolved_threats = start, 0, False, 0, 0
    
    while current <= end:
        day_num += 1
        for _ in range(np.random.poisson(events_per_day)):
            timestamp = current + timedelta(hours=int(np.random.choice(range(24), p=get_hour_weights(device))), minutes=int(np.random.randint(0, 60)))
            phase = 'onboarding' if day_num <= 3 and not onboarding_complete else 'threat' if unresolved_threats > 0 else 'normal'
            event_type = np.random.choice(EVENT_TYPES, p=get_event_probs(phase, plan, engagement))
            if event_type == 'scan_completed' and day_num <= 7: scans_week1 += 1; onboarding_complete = scans_week1 >= 3
            if event_type == 'threat_detected': unresolved_threats += 1
            elif event_type == 'threat_resolved': unresolved_threats = max(0, unresolved_threats - 1)
            all_events.append({'event_id': f"evt_{event_counter:010d}", 'user_id': user['user_id'], 'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'), 'event_type': event_type, 'properties': json.dumps(generate_event_properties(event_type, day_num)), 'session_id': f"sess_{user['user_id']}_{current.strftime('%Y%m%d')}_{np.random.randint(1,5):02d}", 'device_os': device, 'app_version': get_app_version(current)})
            event_counter += 1
        current += timedelta(days=1)

events_df = pd.DataFrame(all_events)
print(f"    ✓ {len(events_df):,} events")

# =============================================================================
# GENERATE EXPERIMENTS
# =============================================================================
print("[4/7] Generating experiments...")
experiments_list, assignments, metrics = [], [], []
for exp_id, cfg in EXPERIMENTS.items():
    experiments_list.append({'experiment_id': exp_id, 'experiment_name': cfg['name'], 'start_date': cfg['start_date'], 'end_date': cfg['end_date'], 'status': 'completed', 'variants': str(cfg['variants']), 'allocation': str(cfg['allocation']), 'primary_metric': cfg['primary_metric'], 'targeting': cfg['targeting']})
    start, end = datetime.strptime(cfg['start_date'], '%Y-%m-%d'), datetime.strptime(cfg['end_date'], '%Y-%m-%d')
    eligible = users_df[(pd.to_datetime(users_df['signup_date']) >= start) & (pd.to_datetime(users_df['signup_date']) <= end)]
    if cfg['targeting'] == 'free_users': eligible = eligible[eligible['plan_type'] == 'free']
    
    for _, user in eligible.iterrows():
        variant = 'rollout_group' if exp_id == 'exp_004' and user['country'] in ['US', 'CA'] else 'control_group' if exp_id == 'exp_004' else np.random.choice(cfg['variants'], p=cfg['allocation'])
        assignments.append({'experiment_id': exp_id, 'user_id': user['user_id'], 'variant': variant, 'assigned_at': user['signup_date']})
        
        if exp_id == 'exp_001': base_rate, metric_name = 0.45, 'activated'; rate = base_rate * (1 + cfg['expected_lift']) if variant == 'treatment' else base_rate
        elif exp_id == 'exp_002': base_rate, metric_name = 0.35, 'viewed_help'; rate = base_rate * (1 + cfg['expected_lift']) if variant == 'treatment' else base_rate
        elif exp_id == 'exp_003': base_rate, metric_name = 0.12, 'converted_to_premium'; rate = base_rate * (1 + cfg['expected_lift']) if variant == 'day_3_upsell' else base_rate
        else: base_rate, metric_name = 0.70, 'threat_resolved'; rate = base_rate + (0.05 if user['country'] in ['US', 'CA'] else 0) + (0.10 if variant == 'rollout_group' else 0)
        metrics.append({'experiment_id': exp_id, 'user_id': user['user_id'], 'metric_name': metric_name, 'metric_value': 1 if np.random.random() < rate else 0, 'recorded_at': user['signup_date']})

experiments_df, exp_assignments_df, exp_metrics_df = pd.DataFrame(experiments_list), pd.DataFrame(assignments), pd.DataFrame(metrics)
print(f"    ✓ {len(experiments_df)} experiments, {len(exp_assignments_df):,} assignments")

# =============================================================================
# GENERATE FEATURE USAGE
# =============================================================================
print("[5/7] Generating feature usage...")
user_status = subscriptions_df.groupby('user_id')['status'].last().reset_index()
users_merged2 = users_df.merge(user_status, on='user_id')
usage_records = []

for _, user in users_merged2.iterrows():
    plan, channel, is_churned = user['plan_type'], user['acquisition_channel'], user['status'] == 'cancelled'
    signup = datetime.strptime(user['signup_date'], '%Y-%m-%d')
    for feature in FEATURES:
        if feature in PREMIUM_ONLY_FEATURES and plan == 'free': continue
        base_adoption = 0.80 if feature == 'real_time_protection' and not is_churned else 0.50 if feature == 'real_time_protection' else {'referral': 0.35, 'organic_search': 0.25}.get(channel, 0.20) if feature == 'password_manager' else FEATURE_ADOPTION_RATES.get(feature, 0.30)
        if np.random.random() < base_adoption:
            first_use = signup + timedelta(days=np.random.randint(0, 30))
            usage_records.append({'user_id': user['user_id'], 'feature_name': feature, 'first_used_at': first_use.strftime('%Y-%m-%d'), 'usage_count': max(1, int(np.random.exponential(5 if is_churned else 20))), 'last_used_at': min(first_use + timedelta(days=np.random.randint(0, 180)), END_DATE).strftime('%Y-%m-%d')})

feature_usage_df = pd.DataFrame(usage_records)
print(f"    ✓ {len(feature_usage_df):,} feature usage records")

# =============================================================================
# GENERATE SUPPORT TICKETS
# =============================================================================
print("[6/7] Generating support tickets...")
help_counts = events_df[events_df['event_type'] == 'help_viewed'].groupby('user_id').size()
tickets = []
for _, user in users_df.iterrows():
    signup = datetime.strptime(user['signup_date'], '%Y-%m-%d')
    if np.random.random() < min(0.5, 0.05 + help_counts.get(user['user_id'], 0) * 0.02):
        for _ in range(np.random.poisson(1) + 1):
            ticket_date = signup + timedelta(days=np.random.randint(1, 180))
            if ticket_date <= END_DATE:
                tickets.append({'ticket_id': f"ticket_{len(tickets):06d}", 'user_id': user['user_id'], 'created_at': ticket_date.strftime('%Y-%m-%d'), 'category': np.random.choice(TICKET_CATEGORIES, p=[0.35, 0.20, 0.15, 0.20, 0.10]), 'priority': np.random.choice(['low', 'medium', 'high'], p=[0.4, 0.45, 0.15]), 'resolution_hours': int(np.random.exponential(24)), 'csat_score': np.random.choice([1, 2, 3, 4, 5], p=[0.05, 0.10, 0.20, 0.35, 0.30])})

tickets_df = pd.DataFrame(tickets)
print(f"    ✓ {len(tickets_df):,} support tickets")

# =============================================================================
# SAVE TO PARQUET
# =============================================================================
print("[7/7] Saving to parquet...")
users_df.to_parquet(RAW_DIR / 'users.parquet', index=False)
subscriptions_df.to_parquet(RAW_DIR / 'subscriptions.parquet', index=False)
events_df.to_parquet(RAW_DIR / 'events.parquet', index=False)
experiments_df.to_parquet(RAW_DIR / 'experiments.parquet', index=False)
exp_assignments_df.to_parquet(RAW_DIR / 'experiment_assignments.parquet', index=False)
exp_metrics_df.to_parquet(RAW_DIR / 'experiment_metrics.parquet', index=False)
feature_usage_df.to_parquet(RAW_DIR / 'feature_usage.parquet', index=False)
tickets_df.to_parquet(RAW_DIR / 'support_tickets.parquet', index=False)

print(f"\n{'='*60}")
print("✅ DATA GENERATION COMPLETE")
print(f"{'='*60}")
print(f"Output: {RAW_DIR}")
for f in RAW_DIR.glob("*.parquet"):
    print(f"  {f.name}: {f.stat().st_size / 1024 / 1024:.2f} MB")

print(f"\n📊 Summary:")
print(f"  Users: {len(users_df):,}")
print(f"  Events: {len(events_df):,}")
print(f"  Churn rate: {(subscriptions_df.groupby('user_id')['status'].last() == 'cancelled').mean()*100:.1f}%")
