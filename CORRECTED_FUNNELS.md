# Corrected Funnel Definitions for SecureFlow Analytics

## ✅ VALID FUNNELS (Events happen in logical order)

### 1. Onboarding Funnel - KEEP THIS
```python
onboarding_funnel = [
    ('App Open', 'app_open'),
    ('Onboarding Started', 'onboarding_step_completed'),
    ('First Scan', 'scan_completed'),
    ('Settings Changed', 'settings_changed'),
    ('Upgrade Clicked', 'upgrade_clicked'),
]
```
**Why it works**: Each step logically follows the previous one.

### 2. Scan-to-Action Funnel - NEW
```python
scan_to_action_funnel = [
    ('App Open', 'app_open'),
    ('Scan Started', 'scan_started'),
    ('Scan Completed', 'scan_completed'),
    ('Threat Detected', 'threat_detected'),
    ('Threat Resolved', 'threat_resolved'),
]
```
**Why it works**: Natural security workflow progression.

### 3. Engagement-to-Share Funnel - FIXED
```python
engagement_funnel = [
    ('App Open', 'app_open'),
    ('First Scan', 'scan_completed'),
    ('Feature Discovered', 'feature_discovered'),
    ('Settings Changed', 'settings_changed'),
    ('Share Clicked', 'share_clicked'),
]
```
**Why it works**: Engagement progression without circular dependencies.

### 4. Upgrade Journey Funnel - NEW
```python
upgrade_funnel = [
    ('App Open', 'app_open'),
    ('First Scan', 'scan_completed'),
    ('Notification Clicked', 'notification_clicked'),
    ('Upgrade Clicked', 'upgrade_clicked'),
]
```
**Why it works**: Clear path to monetization.

## ❌ INVALID FUNNELS (Don't use these)

### ❌ Conversion Funnel - REMOVE
```python
# DON'T USE - Help is not sequential
conversion_funnel = [
    ('App Open', 'app_open'),
    ('Scan Completed', 'scan_completed'),
    ('Threat Detected', 'threat_detected'),
    ('Help Viewed', 'help_viewed'),  # ← Users can view help anytime!
    ('Upgrade Clicked', 'upgrade_clicked'),
]
```
**Why it fails**: Help viewed can happen independently of threat detection.

### ❌ Security Workflow (as defined) - FIX IT
```python
# PROBLEM VERSION
security_workflow_funnel = [
    ('Scan Started', 'scan_started'),
    ('Scan Completed', 'scan_completed'),
    ('Threat Detected', 'threat_detected'),
    ('Threat Resolved', 'threat_resolved'),  # ← May resolve old threats!
]
```
**Why it fails**: Users might resolve threats from previous scans.

## 🔍 How to Verify Your Funnel is Valid

A funnel is valid if:
1. **Numbers always decrease** (or stay the same)
2. **Incremental % never exceeds 100%**
3. **Each step logically requires the previous one**

Run this test:
```python
# After calculating funnel
assert (df['step_1_users'] <= df['step_0_users']).all()
assert (df['step_2_users'] <= df['step_1_users']).all()
assert (df['step_3_users'] <= df['step_2_users']).all()
# etc...

# Check incrementals
incremental_cols = [col for col in df.columns if 'incremental' in col]
for col in incremental_cols:
    max_val = df[col].max()
    if max_val > 100:
        print(f"⚠️  WARNING: {col} = {max_val}% (impossible!)")
```

## 📊 Recommended Funnels for Your Notebook

Replace the problematic funnels with these:

```python
# PRIMARY FUNNEL: User Journey
user_journey_funnel = [
    ('App Open', 'app_open'),
    ('Onboarding Started', 'onboarding_step_completed'),
    ('First Scan', 'scan_completed'),
    ('Threat Detected', 'threat_detected'),
    ('Upgrade Clicked', 'upgrade_clicked'),
]

# SECURITY FUNNEL: Threat Handling
threat_handling_funnel = [
    ('Scan Started', 'scan_started'),
    ('Scan Completed', 'scan_completed'),
    ('Threat Detected', 'threat_detected'),
    ('Threat Resolved', 'threat_resolved'),
]
# NOTE: You may need to add date/session filters to ensure
# threat_resolved happens AFTER threat_detected in the SAME session

# ENGAGEMENT FUNNEL: Feature Discovery
feature_engagement_funnel = [
    ('App Open', 'app_open'),
    ('First Scan', 'scan_completed'),
    ('Notification Clicked', 'notification_clicked'),
    ('Feature Discovered', 'feature_discovered'),
    ('Settings Changed', 'settings_changed'),
]

# MONETIZATION FUNNEL: Path to Upgrade
monetization_funnel = [
    ('App Open', 'app_open'),
    ('Scan Completed', 'scan_completed'),
    ('Notification Clicked', 'notification_clicked'),
    ('Upgrade Clicked', 'upgrade_clicked'),
]
```

## 🎯 Interview Talking Points

When discussing these funnels in your interview:

**Good Answer**:
"I validated my funnels to ensure each step logically follows the previous one. I noticed that some events like 'help_viewed' can occur independently of the main user journey, so I excluded them from sequential funnels. Instead, I focused on true user journeys like onboarding, threat handling, and upgrade paths."

**What NOT to say**:
"My funnel shows 102% conversion..." ❌
