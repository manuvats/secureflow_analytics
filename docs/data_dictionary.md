# SecureFlow Analytics - Data Dictionary

## Overview

This document describes all tables and columns in the SecureFlow Analytics dataset. The data simulates 18 months of product telemetry for a security software application.

**Time Range:** January 1, 2024 - June 30, 2025  
**Scale:** ~50,000 users, ~7.5M events

---

## Tables

### 1. users.csv

User profile information captured at signup.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| user_id | string | Unique user identifier | `user_000001` |
| signup_date | date | Date user registered | `2024-03-15` |
| plan_type | string | Subscription tier at signup | `free`, `premium_monthly`, `premium_annual` |
| country | string | User's country (ISO 2-letter) | `US`, `CA`, `UK`, `DE` |
| device_os | string | Primary device operating system | `windows`, `macos`, `android`, `ios` |
| acquisition_channel | string | How user discovered the product | See below |
| email_domain | string | Domain of user's email | `gmail.com`, `yahoo.com` |

**Acquisition Channels:**
- `organic_search` - Found via search engine
- `paid_search` - Clicked paid ad
- `social_media` - Social media referral
- `referral` - Referred by existing user
- `affiliate` - Affiliate partner
- `direct` - Direct to website
- `app_store` - Found in app store

**Key Relationships:**
- `acquisition_channel` correlates with conversion rates and LTV
- `country` determines experiment eligibility (exp_004 is geo-based)
- `device_os` affects engagement patterns (desktop vs mobile)

---

### 2. subscriptions.csv

Subscription lifecycle records. One user may have multiple records (renewals, plan changes).

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| subscription_id | string | Unique subscription record ID | `user_000001_sub_01` |
| user_id | string | Foreign key to users | `user_000001` |
| plan | string | Plan type for this period | `premium_monthly` |
| start_date | date | Subscription period start | `2024-03-15` |
| end_date | date | Subscription period end | `2024-04-15` |
| status | string | Current status | `active`, `renewed`, `cancelled` |
| mrr | float | Monthly recurring revenue | `9.99`, `7.99`, `0` |
| cancellation_reason | string | Why user cancelled (if applicable) | `price`, `not_using`, `switched_competitor` |

**Status Values:**
- `active` - Currently active subscription
- `renewed` - Period ended, user renewed
- `cancelled` - User cancelled during this period

**Key Patterns:**
- Referral users have ~25% lower churn rate
- Q4 cohorts have better retention (holiday promotions)
- Annual plans have much lower churn than monthly

---

### 3. events.csv

Product telemetry events capturing user interactions.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| event_id | string | Unique event identifier | `evt_0000000001` |
| user_id | string | Foreign key to users | `user_000001` |
| timestamp | datetime | When event occurred | `2024-03-15 14:32:45` |
| event_type | string | Type of event | See below |
| properties | json | Event-specific metadata | `{"scan_type": "quick"}` |
| session_id | string | Session identifier | `sess_user_000001_20240315_01` |
| device_os | string | Device used for this event | `windows` |
| app_version | string | App version at event time | `4.1.0` |

**Event Types:**

| Event | Description | Key Properties |
|-------|-------------|----------------|
| `app_open` | User opened the application | - |
| `scan_started` | User initiated a scan | `scan_type` |
| `scan_completed` | Scan finished | `scan_type`, `duration_seconds`, `files_scanned`, `threats_found` |
| `threat_detected` | Security threat found | `threat_type`, `severity` |
| `threat_resolved` | User addressed a threat | `action` (quarantined/deleted/allowed) |
| `settings_changed` | User modified settings | `setting` |
| `upgrade_clicked` | User clicked upgrade CTA | `source`, `plan_shown` |
| `help_viewed` | User accessed help content | `article_id`, `category` |
| `notification_clicked` | User clicked notification | - |
| `share_clicked` | User shared the product | - |
| `feature_discovered` | User found a new feature | - |
| `onboarding_step_completed` | Onboarding progress | `step`, `step_name` |

**Key Patterns:**
- Users with 3+ `scan_completed` events in week 1 have much better retention
- `threat_detected` without subsequent `threat_resolved` correlates with churn
- High `help_viewed` frequency indicates user confusion

---

### 4. experiments.csv

Metadata for A/B tests and experiments.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| experiment_id | string | Unique experiment ID | `exp_001` |
| experiment_name | string | Human-readable name | `new_onboarding_flow` |
| start_date | date | Experiment start | `2024-03-01` |
| end_date | date | Experiment end | `2024-05-31` |
| status | string | Current status | `completed` |
| variants | list | Variant names | `['control', 'treatment']` |
| allocation | list | Traffic allocation | `[0.5, 0.5]` |
| primary_metric | string | Main success metric | `activation_rate` |
| targeting | string | Who's eligible | `all_new_users`, `free_users`, `geo_based` |

**Experiments:**

| ID | Name | Hypothesis | Result |
|----|------|-----------|--------|
| exp_001 | new_onboarding_flow | Simplified onboarding increases activation | **+15% activation** ✅ |
| exp_002 | threat_explainer_v2 | Better explanations reduce help requests | **-20% help views** ✅ |
| exp_003 | premium_upsell_timing | Earlier upsell (Day 3 vs Day 7) improves conversion | **-25% conversion** ❌ |
| exp_004 | real_time_protection_default | Enabling real-time protection by default improves threat resolution | Confounded (needs DiD) |

---

### 5. experiment_assignments.csv

User-level experiment assignments.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| experiment_id | string | Foreign key to experiments | `exp_001` |
| user_id | string | Foreign key to users | `user_000001` |
| variant | string | Assigned variant | `treatment` |
| assigned_at | date | Assignment timestamp | `2024-03-15` |

**Note:** exp_004 is non-randomized - US/CA users got `rollout_group`, others got `control_group`.

---

### 6. experiment_metrics.csv

Outcome metrics for experiment analysis.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| experiment_id | string | Foreign key to experiments | `exp_001` |
| user_id | string | Foreign key to users | `user_000001` |
| metric_name | string | Metric being measured | `activated` |
| metric_value | float | Metric value | `1` (binary) or continuous |
| recorded_at | date | When metric was recorded | `2024-03-22` |

**Metrics by Experiment:**
- exp_001: `activated` (binary)
- exp_002: `viewed_help` (binary)
- exp_003: `converted_to_premium` (binary)
- exp_004: `threat_resolved` (binary)

---

### 7. feature_usage.csv

Feature adoption and usage patterns.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| user_id | string | Foreign key to users | `user_000001` |
| feature_name | string | Feature used | `real_time_protection` |
| first_used_at | date | First usage date | `2024-03-16` |
| usage_count | int | Total times used | `47` |
| last_used_at | date | Most recent usage | `2024-06-15` |

**Features:**
| Feature | Description | Availability |
|---------|-------------|--------------|
| real_time_protection | Background threat monitoring | All |
| scheduled_scans | Automated scan scheduling | All |
| vpn_feature | VPN service | Premium only |
| password_manager | Password vault | All |
| safe_browsing | Browser protection | All |
| firewall | Network firewall | All |
| identity_monitoring | Dark web monitoring | Premium only |
| parental_controls | Child safety features | Premium only |

**Key Patterns:**
- `real_time_protection` adopters have ~40% lower churn
- `password_manager` adoption varies significantly by acquisition channel
- `vpn_feature` has low adoption but users who use it have high retention

---

### 8. support_tickets.csv

Customer support interactions.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| ticket_id | string | Unique ticket ID | `ticket_000001` |
| user_id | string | Foreign key to users | `user_000001` |
| created_at | date | Ticket creation date | `2024-04-01` |
| category | string | Issue category | `technical`, `billing`, `threat_help` |
| priority | string | Ticket priority | `low`, `medium`, `high` |
| resolution_hours | int | Time to resolve | `18` |
| csat_score | int | Customer satisfaction (1-5) | `4` |

**Key Patterns:**
- Users with high `help_viewed` events are more likely to submit tickets
- `threat_help` tickets correlate with unresolved threats in events

---

## Entity Relationships

```
users (1) ──────< (N) subscriptions
  │
  ├──────────────< (N) events
  │
  ├──────────────< (N) experiment_assignments ───> experiments
  │                         │
  │                         └──────< experiment_metrics
  │
  ├──────────────< (N) feature_usage
  │
  └──────────────< (N) support_tickets
```

---

## Data Quality Notes

1. **Synthetic Data:** All data is programmatically generated with intentional patterns
2. **No PII:** No real personal information is included
3. **Temporal Consistency:** Events respect user signup dates and subscription periods
4. **Realistic Distributions:** Channel mix, churn rates, and engagement patterns mirror industry benchmarks

---

## Suggested Analyses

1. **Cohort Retention Analysis:** Compare retention curves by signup month, channel, plan
2. **Funnel Analysis:** Measure drop-off from signup → first scan → activation → conversion
3. **A/B Test Analysis:** Calculate lift for each experiment with statistical significance
4. **Churn Prediction:** Build model using events, feature usage, and subscription data
5. **Causal Analysis:** Use DiD for exp_004 to isolate treatment effect from country effects
