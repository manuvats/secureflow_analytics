"""
SecureFlow Analytics - A/B Testing & Experimentation Framework
==============================================================
Reusable functions for experiment analysis:
- Power analysis & sample size calculation
- Statistical tests (t-test, chi-square, bootstrap)
- Multiple testing corrections (Bonferroni, Benjamini-Hochberg)
- Sample Ratio Mismatch (SRM) detection
- Effect size estimation (Cohen's d, relative lift)
- Confidence intervals (analytical + bootstrap)
- Experiment summary & decision framework
"""
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Optional, Tuple
import warnings

# ============================================================
# 1. POWER ANALYSIS & SAMPLE SIZE
# ============================================================

def compute_sample_size(
    baseline_rate: float,
    mde: float,
    alpha: float = 0.05,
    power: float = 0.80,
    two_sided: bool = True,
    ratio: float = 1.0,
) -> Dict:
    """
    Calculate required sample size per variant for a proportion test.

    Parameters
    ----------
    baseline_rate : float
        Current conversion/metric rate (e.g., 0.30 for 30%).
    mde : float
        Minimum detectable effect as relative lift (e.g., 0.10 for 10% lift).
    alpha : float
        Significance level (default 0.05).
    power : float
        Statistical power (default 0.80).
    two_sided : bool
        Two-sided test (default True).
    ratio : float
        Ratio of treatment to control group sizes (default 1.0 = equal).

    Returns
    -------
    dict with keys:
        n_control, n_treatment, n_total, baseline_rate, treatment_rate,
        absolute_effect, relative_effect, alpha, power
    """
    p1 = baseline_rate
    p2 = baseline_rate * (1 + mde)
    
    # Z-scores
    if two_sided:
        z_alpha = stats.norm.ppf(1 - alpha / 2)
    else:
        z_alpha = stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)
    
    # Pooled proportion under H0
    p_pool = (p1 + ratio * p2) / (1 + ratio)
    
    # Sample size formula (Fleiss with continuity correction)
    numerator = (z_alpha * np.sqrt((1 + 1/ratio) * p_pool * (1 - p_pool)) +
                 z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2) / ratio)) ** 2
    denominator = (p2 - p1) ** 2
    
    n_control = int(np.ceil(numerator / denominator))
    n_treatment = int(np.ceil(n_control * ratio))
    
    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "n_total": n_control + n_treatment,
        "baseline_rate": p1,
        "treatment_rate": p2,
        "absolute_effect": p2 - p1,
        "relative_effect": mde,
        "alpha": alpha,
        "power": power,
    }


def power_curve(
    baseline_rate: float,
    mde_range: np.ndarray = None,
    alpha: float = 0.05,
    power_levels: List[float] = None,
) -> pd.DataFrame:
    """
    Generate power curve data: sample size vs MDE for multiple power levels.

    Returns DataFrame with columns: mde, power, n_per_variant, n_total
    """
    if mde_range is None:
        mde_range = np.arange(0.02, 0.31, 0.02)
    if power_levels is None:
        power_levels = [0.70, 0.80, 0.90]
    
    rows = []
    for mde in mde_range:
        for pwr in power_levels:
            result = compute_sample_size(baseline_rate, mde, alpha=alpha, power=pwr)
            rows.append({
                "mde": mde,
                "power": pwr,
                "n_per_variant": result["n_control"],
                "n_total": result["n_total"],
            })
    
    return pd.DataFrame(rows)


# ============================================================
# 2. SAMPLE RATIO MISMATCH (SRM)
# ============================================================

def check_srm(
    n_control: int,
    n_treatment: int,
    expected_ratio: float = 0.5,
    alpha: float = 0.001,
) -> Dict:
    """
    Check for Sample Ratio Mismatch using chi-square goodness-of-fit.

    A very low alpha (0.001) is standard for SRM since even small mismatches
    can bias results significantly.

    Parameters
    ----------
    n_control : int
        Number of users in control.
    n_treatment : int
        Number of users in treatment.
    expected_ratio : float
        Expected proportion of users in control (default 0.5 for 50/50 split).
    alpha : float
        Significance level for SRM detection (default 0.001).

    Returns
    -------
    dict with: observed_ratio, expected_ratio, chi2, p_value, srm_detected, verdict
    """
    n_total = n_control + n_treatment
    observed = np.array([n_control, n_treatment])
    expected = np.array([expected_ratio, 1 - expected_ratio]) * n_total
    
    chi2, p_value = stats.chisquare(observed, expected)
    
    observed_ratio = n_control / n_total
    
    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "observed_ratio": round(observed_ratio, 4),
        "expected_ratio": expected_ratio,
        "chi2_statistic": round(chi2, 4),
        "p_value": p_value,
        "srm_detected": p_value < alpha,
        "verdict": "⚠️ SRM DETECTED — Do not trust results" if p_value < alpha
                   else "✅ No SRM — Sample split looks clean",
    }


# ============================================================
# 3. STATISTICAL TESTS
# ============================================================

def proportion_test(
    conversions_control: int,
    n_control: int,
    conversions_treatment: int,
    n_treatment: int,
    alpha: float = 0.05,
    test_type: str = "z_test",
) -> Dict:
    """
    Test difference in proportions (conversion rates).

    Parameters
    ----------
    test_type : str
        'z_test' for normal approximation (large samples),
        'chi_square' for chi-square test of independence.

    Returns
    -------
    dict with: control_rate, treatment_rate, absolute_lift, relative_lift,
               statistic, p_value, significant, ci_lower, ci_upper
    """
    p_c = conversions_control / n_control
    p_t = conversions_treatment / n_treatment
    
    absolute_lift = p_t - p_c
    relative_lift = absolute_lift / p_c if p_c > 0 else np.inf
    
    if test_type == "z_test":
        # Pooled proportion
        p_pool = (conversions_control + conversions_treatment) / (n_control + n_treatment)
        se = np.sqrt(p_pool * (1 - p_pool) * (1/n_control + 1/n_treatment))
        z_stat = absolute_lift / se if se > 0 else 0
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        statistic = z_stat
        
        # CI for difference
        se_diff = np.sqrt(p_c * (1 - p_c) / n_control + p_t * (1 - p_t) / n_treatment)
        z_crit = stats.norm.ppf(1 - alpha / 2)
        ci_lower = absolute_lift - z_crit * se_diff
        ci_upper = absolute_lift + z_crit * se_diff
        
    elif test_type == "chi_square":
        contingency = np.array([
            [conversions_control, n_control - conversions_control],
            [conversions_treatment, n_treatment - conversions_treatment],
        ])
        chi2, p_value, _, _ = stats.chi2_contingency(contingency, correction=False)
        statistic = chi2
        
        se_diff = np.sqrt(p_c * (1 - p_c) / n_control + p_t * (1 - p_t) / n_treatment)
        z_crit = stats.norm.ppf(1 - alpha / 2)
        ci_lower = absolute_lift - z_crit * se_diff
        ci_upper = absolute_lift + z_crit * se_diff
    else:
        raise ValueError(f"Unknown test_type: {test_type}")
    
    return {
        "control_rate": round(p_c, 6),
        "treatment_rate": round(p_t, 6),
        "absolute_lift": round(absolute_lift, 6),
        "relative_lift": round(relative_lift, 4),
        "statistic": round(statistic, 4),
        "p_value": p_value,
        "significant": p_value < alpha,
        "ci_lower": round(ci_lower, 6),
        "ci_upper": round(ci_upper, 6),
        "alpha": alpha,
        "test_type": test_type,
    }


def means_test(
    values_control: np.ndarray,
    values_treatment: np.ndarray,
    alpha: float = 0.05,
    test_type: str = "welch",
) -> Dict:
    """
    Test difference in means (continuous metrics like revenue, time-on-site).

    Parameters
    ----------
    test_type : str
        'welch' for Welch's t-test (unequal variances),
        'student' for Student's t-test (equal variances assumed),
        'mann_whitney' for non-parametric test.

    Returns
    -------
    dict with: control_mean, treatment_mean, absolute_lift, relative_lift,
               cohens_d, statistic, p_value, significant, ci_lower, ci_upper
    """
    mean_c = np.mean(values_control)
    mean_t = np.mean(values_treatment)
    absolute_lift = mean_t - mean_c
    relative_lift = absolute_lift / mean_c if mean_c != 0 else np.inf
    
    # Cohen's d
    pooled_std = np.sqrt(
        ((len(values_control) - 1) * np.var(values_control, ddof=1) +
         (len(values_treatment) - 1) * np.var(values_treatment, ddof=1)) /
        (len(values_control) + len(values_treatment) - 2)
    )
    cohens_d = absolute_lift / pooled_std if pooled_std > 0 else 0
    
    if test_type in ("welch", "student"):
        equal_var = test_type == "student"
        t_stat, p_value = stats.ttest_ind(
            values_treatment, values_control, equal_var=equal_var
        )
        statistic = t_stat
        
        # CI
        se = np.sqrt(
            np.var(values_control, ddof=1) / len(values_control) +
            np.var(values_treatment, ddof=1) / len(values_treatment)
        )
        # Welch-Satterthwaite degrees of freedom
        s1_sq = np.var(values_control, ddof=1)
        s2_sq = np.var(values_treatment, ddof=1)
        n1, n2 = len(values_control), len(values_treatment)
        df_num = (s1_sq / n1 + s2_sq / n2) ** 2
        df_den = (s1_sq / n1) ** 2 / (n1 - 1) + (s2_sq / n2) ** 2 / (n2 - 1)
        df = df_num / df_den if df_den > 0 else n1 + n2 - 2
        
        t_crit = stats.t.ppf(1 - alpha / 2, df)
        ci_lower = absolute_lift - t_crit * se
        ci_upper = absolute_lift + t_crit * se
        
    elif test_type == "mann_whitney":
        u_stat, p_value = stats.mannwhitneyu(
            values_treatment, values_control, alternative="two-sided"
        )
        statistic = u_stat
        # Approximate CI using bootstrap (see bootstrap_ci function)
        ci_lower, ci_upper = None, None
    else:
        raise ValueError(f"Unknown test_type: {test_type}")
    
    return {
        "control_mean": round(mean_c, 6),
        "treatment_mean": round(mean_t, 6),
        "n_control": len(values_control),
        "n_treatment": len(values_treatment),
        "absolute_lift": round(absolute_lift, 6),
        "relative_lift": round(relative_lift, 4),
        "cohens_d": round(cohens_d, 4),
        "statistic": round(statistic, 4),
        "p_value": p_value,
        "significant": p_value < alpha,
        "ci_lower": round(ci_lower, 6) if ci_lower is not None else None,
        "ci_upper": round(ci_upper, 6) if ci_upper is not None else None,
        "alpha": alpha,
        "test_type": test_type,
    }


# ============================================================
# 4. BOOTSTRAP CONFIDENCE INTERVALS
# ============================================================

def bootstrap_ci(
    values_control: np.ndarray,
    values_treatment: np.ndarray,
    metric_fn=np.mean,
    n_bootstrap: int = 10000,
    alpha: float = 0.05,
    seed: int = 42,
) -> Dict:
    """
    Bootstrap confidence interval for the difference in a metric.

    Parameters
    ----------
    metric_fn : callable
        Function to compute metric (default: np.mean). Can be np.median, etc.
    n_bootstrap : int
        Number of bootstrap resamples.

    Returns
    -------
    dict with: observed_diff, ci_lower, ci_upper, p_value_bootstrap, 
               bootstrap_mean, bootstrap_std
    """
    rng = np.random.default_rng(seed)
    
    observed_control = metric_fn(values_control)
    observed_treatment = metric_fn(values_treatment)
    observed_diff = observed_treatment - observed_control
    
    n_c = len(values_control)
    n_t = len(values_treatment)
    
    boot_diffs = np.zeros(n_bootstrap)
    for i in range(n_bootstrap):
        boot_c = rng.choice(values_control, size=n_c, replace=True)
        boot_t = rng.choice(values_treatment, size=n_t, replace=True)
        boot_diffs[i] = metric_fn(boot_t) - metric_fn(boot_c)
    
    ci_lower = np.percentile(boot_diffs, 100 * alpha / 2)
    ci_upper = np.percentile(boot_diffs, 100 * (1 - alpha / 2))
    
    # Two-sided bootstrap p-value
    p_value = np.mean(np.abs(boot_diffs) >= abs(observed_diff))
    
    return {
        "observed_diff": round(observed_diff, 6),
        "ci_lower": round(ci_lower, 6),
        "ci_upper": round(ci_upper, 6),
        "p_value_bootstrap": round(p_value, 6),
        "bootstrap_mean": round(np.mean(boot_diffs), 6),
        "bootstrap_std": round(np.std(boot_diffs), 6),
        "n_bootstrap": n_bootstrap,
        "alpha": alpha,
        "significant": (ci_lower > 0) or (ci_upper < 0),
    }


# ============================================================
# 5. MULTIPLE TESTING CORRECTIONS
# ============================================================

def correct_multiple_tests(
    p_values: Dict[str, float],
    alpha: float = 0.05,
    method: str = "both",
) -> pd.DataFrame:
    """
    Apply multiple testing corrections.

    Parameters
    ----------
    p_values : dict
        {metric_name: p_value}
    method : str
        'bonferroni', 'bh' (Benjamini-Hochberg), or 'both'

    Returns
    -------
    DataFrame with original and corrected p-values + significance flags.
    """
    metrics = list(p_values.keys())
    raw_p = np.array([p_values[m] for m in metrics])
    m = len(raw_p)
    
    results = pd.DataFrame({
        "metric": metrics,
        "p_value_raw": raw_p,
        "significant_raw": raw_p < alpha,
    })
    
    if method in ("bonferroni", "both"):
        p_bonf = np.minimum(raw_p * m, 1.0)
        results["p_value_bonferroni"] = p_bonf
        results["significant_bonferroni"] = p_bonf < alpha
    
    if method in ("bh", "both"):
        # Benjamini-Hochberg procedure
        sorted_idx = np.argsort(raw_p)
        sorted_p = raw_p[sorted_idx]
        bh_threshold = np.arange(1, m + 1) / m * alpha
        
        # Find largest k where p(k) <= k/m * alpha
        reject = sorted_p <= bh_threshold
        if reject.any():
            max_reject_idx = np.max(np.where(reject))
            bh_reject = np.zeros(m, dtype=bool)
            bh_reject[sorted_idx[:max_reject_idx + 1]] = True
        else:
            bh_reject = np.zeros(m, dtype=bool)
        
        # Adjusted p-values (step-up)
        adjusted_p = np.zeros(m)
        for i in range(m):
            rank = np.searchsorted(np.sort(raw_p), raw_p[i]) + 1
            adjusted_p[i] = min(raw_p[i] * m / rank, 1.0)
        
        results["p_value_bh"] = adjusted_p
        results["significant_bh"] = bh_reject
    
    return results.sort_values("p_value_raw").reset_index(drop=True)


# ============================================================
# 6. EXPERIMENT ANALYSIS PIPELINE
# ============================================================

def analyze_experiment(
    assignments: pd.DataFrame,
    metrics: pd.DataFrame,
    experiment_id: str,
    primary_metric: str,
    metric_type: str = "proportion",
    alpha: float = 0.05,
    run_bootstrap: bool = True,
    n_bootstrap: int = 10000,
) -> Dict:
    """
    End-to-end analysis of a single A/B experiment.

    Parameters
    ----------
    assignments : pd.DataFrame
        Must have columns: experiment_id, user_id, variant
    metrics : pd.DataFrame
        Must have columns: experiment_id, user_id, metric_name, metric_value
    experiment_id : str
        e.g., 'exp_001'
    primary_metric : str
        e.g., 'activated', 'converted', 'help_viewed'
    metric_type : str
        'proportion' for binary metrics, 'continuous' for revenue/counts.
    alpha : float
        Significance level.

    Returns
    -------
    dict with: srm_check, primary_test, bootstrap (optional), decision
    """
    # Filter to this experiment
    exp_assign = assignments[assignments["experiment_id"] == experiment_id].copy()
    exp_metrics = metrics[
        (metrics["experiment_id"] == experiment_id) &
        (metrics["metric_name"] == primary_metric)
    ].copy()
    
    # Merge assignments with metrics
    merged = exp_assign.merge(exp_metrics[["user_id", "metric_value"]], on="user_id", how="left")
    merged["metric_value"] = merged["metric_value"].fillna(0)
    
    control = merged[merged["variant"] == "control"]
    treatment = merged[merged["variant"] == "treatment"]
    
    # 1. SRM Check
    srm = check_srm(len(control), len(treatment))
    
    # 2. Statistical Test
    if metric_type == "proportion":
        conv_c = int(control["metric_value"].sum())
        conv_t = int(treatment["metric_value"].sum())
        
        primary_test = proportion_test(
            conv_c, len(control), conv_t, len(treatment),
            alpha=alpha, test_type="z_test"
        )
        # Also run chi-square for comparison
        chi_sq_test = proportion_test(
            conv_c, len(control), conv_t, len(treatment),
            alpha=alpha, test_type="chi_square"
        )
    else:
        vals_c = control["metric_value"].values
        vals_t = treatment["metric_value"].values
        
        primary_test = means_test(vals_c, vals_t, alpha=alpha, test_type="welch")
        chi_sq_test = None
    
    # 3. Bootstrap CI
    boot_result = None
    if run_bootstrap:
        vals_c = control["metric_value"].values
        vals_t = treatment["metric_value"].values
        boot_result = bootstrap_ci(vals_c, vals_t, n_bootstrap=n_bootstrap, alpha=alpha)
    
    # 4. Decision
    if srm["srm_detected"]:
        decision = "🚫 INVALID — Sample Ratio Mismatch detected. Investigate assignment logic."
    elif primary_test["significant"] and primary_test["relative_lift"] > 0:
        decision = "✅ SHIP IT — Statistically significant positive effect."
    elif primary_test["significant"] and primary_test["relative_lift"] < 0:
        decision = "❌ DO NOT SHIP — Statistically significant negative effect."
    else:
        decision = "⏸️ INCONCLUSIVE — No significant difference detected. Consider extending the test."
    
    return {
        "experiment_id": experiment_id,
        "primary_metric": primary_metric,
        "metric_type": metric_type,
        "n_control": len(control),
        "n_treatment": len(treatment),
        "srm_check": srm,
        "primary_test": primary_test,
        "chi_square_test": chi_sq_test,
        "bootstrap": boot_result,
        "decision": decision,
    }


def summarize_all_experiments(
    assignments: pd.DataFrame,
    metrics: pd.DataFrame,
    experiment_configs: Dict,
    alpha: float = 0.05,
) -> pd.DataFrame:
    """
    Run analysis on all experiments and return a summary table.

    Parameters
    ----------
    experiment_configs : dict
        From config.py EXPERIMENTS dict. Keys are experiment IDs.

    Returns
    -------
    DataFrame summary with one row per experiment.
    """
    rows = []
    for exp_id, config in experiment_configs.items():
        # Skip exp_004 (needs DiD, not standard A/B)
        if config.get("analysis_method") == "difference_in_differences":
            rows.append({
                "experiment_id": exp_id,
                "name": config["name"],
                "primary_metric": config["primary_metric"],
                "expected_lift": config["expected_lift"],
                "decision": "⏭️ SKIP — Requires Difference-in-Differences (Phase 4)",
                "p_value": None,
                "observed_lift": None,
                "significant": None,
                "srm_clean": None,
            })
            continue
        
        result = analyze_experiment(
            assignments, metrics, exp_id,
            primary_metric=config["primary_metric"],
            metric_type="proportion",
            alpha=alpha,
            run_bootstrap=True,
        )
        
        rows.append({
            "experiment_id": exp_id,
            "name": config["name"],
            "primary_metric": config["primary_metric"],
            "expected_lift": config["expected_lift"],
            "decision": result["decision"],
            "p_value": result["primary_test"]["p_value"],
            "observed_lift": result["primary_test"]["relative_lift"],
            "ci_lower": result["primary_test"]["ci_lower"],
            "ci_upper": result["primary_test"]["ci_upper"],
            "significant": result["primary_test"]["significant"],
            "srm_clean": not result["srm_check"]["srm_detected"],
        })
    
    return pd.DataFrame(rows)
