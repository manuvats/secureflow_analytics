# SecureFlow Analytics

**Product Analytics & Experimentation Platform for Security Software**

A portfolio project demonstrating end-to-end product analytics capabilities for a fictional cybersecurity company, designed to showcase skills relevant to **Data Scientist, Product Analytics** roles.

---

## 🎯 Business Problem

SecureFlow (fictional security software company) needs to:
1. **Improve user activation** — many users download but don't complete onboarding
2. **Reduce churn** — free trial users aren't converting; premium users are cancelling
3. **Optimize feature adoption** — key protective features have low usage
4. **Make data-driven product decisions** — through rigorous A/B testing and causal analysis

---

## 📊 Project Scope

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| **0** | Data Generation | Synthetic product telemetry with realistic patterns |
| **1** | Data Foundation + EDA | Exploratory analysis, data dictionary |
| **2** | Funnel & User Journey | Activation/retention funnels, cohort analysis |
| **3** | Experimentation Framework | A/B test design, power analysis, statistical testing |
| **4** | Causal Inference | DiD, propensity score matching, RDD |
| **5** | Predictive Models | Churn prediction, engagement scoring |
| **6** | MLOps & Deployment | MLflow, model serving, drift monitoring |
| **7** | BI Dashboards | Executive + experimentation dashboards |

---

## 🔑 Key Insights (Embedded in Data)

### 1. Churn Prediction Signals
- Users who don't complete onboarding (< 3 scans in week 1) churn **2-3x more**
- Unresolved threats correlate strongly with churn
- `real_time_protection` feature adopters have **~40% lower churn**

### 2. A/B Test Results
| Experiment | Outcome | Business Impact |
|------------|---------|-----------------|
| New Onboarding Flow | **+15% activation** | Positive — ship it |
| Threat Explainer v2 | **-20% help views** | Positive — less confusion |
| Early Upsell (Day 3) | **-25% conversion** | Negative — keep Day 7 |
| Real-time Default | Confounded | Needs DiD analysis |

### 3. Cohort Patterns
- Q4 cohorts have **higher LTV** (holiday promotions work)
- Referral users have **25% higher LTV** than paid acquisition
- Mobile users: lower engagement but comparable retention

### 4. Feature Adoption Insights
- `real_time_protection`: High adoption → strong retention signal
- `vpn_feature`: Low adoption but premium-only, high-value users
- `password_manager`: Adoption varies 40% by acquisition channel

---

## 🗃️ Data Schema

```
data/raw/
├── users.csv              # User profiles (50K users)
├── subscriptions.csv      # Subscription history
├── events.csv             # Product telemetry events (~7.5M events)
├── experiments.csv        # Experiment metadata
├── experiment_assignments.csv  # User-variant assignments
├── experiment_metrics.csv # Experiment outcome metrics
├── feature_usage.csv      # Feature adoption data
└── support_tickets.csv    # Customer support data
```

### Key Tables

**users**
| Column | Description |
|--------|-------------|
| user_id | Unique identifier |
| signup_date | Registration date |
| plan_type | free / premium_monthly / premium_annual |
| country | User location (for geo-based analysis) |
| device_os | windows / macos / android / ios |
| acquisition_channel | organic_search / paid_search / referral / etc. |

**events**
| Column | Description |
|--------|-------------|
| event_id | Unique event identifier |
| user_id | User who triggered event |
| timestamp | Event timestamp |
| event_type | app_open, scan_completed, threat_detected, etc. |
| properties | JSON with event-specific details |

**experiments**
| Column | Description |
|--------|-------------|
| experiment_id | Unique experiment identifier |
| experiment_name | Human-readable name |
| variants | Control/treatment groups |
| primary_metric | Main success metric |

---

## 🛠️ Tech Stack

| Layer | Tools |
|-------|-------|
| Data Generation | Python, Faker, NumPy |
| Storage | DuckDB, Delta Lake |
| Analysis | Pandas, SciPy, Statsmodels |
| Causal Inference | DoWhy, CausalML, EconML |
| ML | XGBoost, LightGBM, Scikit-learn, SHAP |
| MLOps | MLflow, Evidently |
| Visualization | Streamlit, Plotly, Seaborn |

---

## 🎤 Interview Talking Points

### "Walk me through an A/B test you designed"
→ Discuss `exp_001` (onboarding flow): hypothesis, power analysis, metric selection, guardrails, CUPED variance reduction, results interpretation

### "How do you handle feature rollouts without randomization?"
→ Discuss `exp_004` (real-time protection): why DiD was needed, parallel trends assumption, how to control for country-level confounders

### "How do you predict and reduce churn?"
→ Discuss churn model: feature engineering from event data, SHAP for interpretability, translating model insights to product recommendations

### "Tell me about a failed experiment"
→ Discuss `exp_003` (early upsell): hypothesis was wrong, earlier upsell hurt conversion, how we communicated results and next steps

### "How do you communicate insights to stakeholders?"
→ Walk through dashboard demos, executive summaries, data storytelling techniques

---

## 📁 Project Structure

```
secureflow_analytics/
├── config/
│   └── settings.py
├── data/
│   ├── raw/           # Generated CSVs
│   ├── bronze/        # Raw ingested (Delta)
│   ├── silver/        # Cleaned/joined
│   └── gold/          # Aggregated metrics
├── notebooks/
│   ├── 00_data_generation.py
│   ├── 01_eda.ipynb
│   ├── 02_funnel_analysis.ipynb
│   ├── 03_experimentation.ipynb
│   ├── 04_causal_inference.ipynb
│   └── 05_churn_model.ipynb
├── src/
│   ├── data_generation/
│   ├── analysis/
│   ├── experimentation/
│   └── models/
├── tests/
├── docs/
│   └── data_dictionary.md
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

```bash
# Clone and setup
cd secureflow_analytics
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Generate data
python notebooks/00_data_generation.py

# Launch Jupyter
jupyter notebook
```

---

## 📈 Progress Tracker

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 0: Data Generation | ✅ Complete | 50K users, 7.5M events |
| Phase 1: EDA | 🔲 Pending | |
| Phase 2: Funnel Analysis | 🔲 Pending | |
| Phase 3: Experimentation | 🔲 Pending | |
| Phase 4: Causal Inference | 🔲 Pending | |
| Phase 5: ML Models | 🔲 Pending | |
| Phase 6: MLOps | 🔲 Pending | |
| Phase 7: Dashboards | 🔲 Pending | |

---

## 📄 License

This is a portfolio project for educational purposes.
