"""
Comprehensive Model Evaluation Script for Difficulty Prediction.

Evaluates:
- Central Metrics: MAE, RMSE, Spearman Rank Correlation
- Quantile Uncertainty: Coverage (target 80%), Average Interval Width
- Range Accuracy across Codeforces Tiers (Div 3, Div 2, Div 1, Master+)
- Baseline Comparisons:
  1. Training Mean Baseline
  2. Structured-Features-Only LightGBM Baseline
  3. IntelliGate Proposed System (Sentence-BERT + Structured Features + Calibrated Quantiles)
"""
from __future__ import annotations

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from scipy.stats import spearmanr


def get_tier(rating: float) -> str:
    if rating < 1400:
        return "Div 3 (Easy, <1400)"
    elif rating < 1900:
        return "Div 2 (Medium, 1400-1899)"
    elif rating < 2400:
        return "Div 1 (Hard, 1900-2399)"
    else:
        return "Master+ (Extreme, >=2400)"


def run_evaluation() -> dict:
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "data")
    artifacts_dir = os.path.join(base_dir, "artifacts")

    # Load test features
    test_feat_path = os.path.join(data_dir, "features_test.npz")
    if not os.path.exists(test_feat_path):
        raise FileNotFoundError(f"Test features not found at {test_feat_path}. Run train.py first.")

    data = np.load(test_feat_path)
    X_test = data["X_combined"]
    X_test_s = data["X_structured"]
    y_test = data["y"]

    # Load models
    lgbm_median = joblib.load(os.path.join(artifacts_dir, "lgbm_median.joblib"))
    lgbm_lower = joblib.load(os.path.join(artifacts_dir, "lgbm_lower.joblib"))
    lgbm_upper = joblib.load(os.path.join(artifacts_dir, "lgbm_upper.joblib"))
    lgbm_struct_baseline = joblib.load(os.path.join(artifacts_dir, "lgbm_struct_baseline.joblib"))

    with open(os.path.join(artifacts_dir, "calibration_meta.json"), "r") as f:
        meta = json.load(f)

    mean_baseline_val = meta["training_mean_rating"]
    delta = meta["validation_metrics"]["calibration_delta"]

    # ── 1. Baseline 1: Training Mean ──────────────────────────────────────────
    pred_mean = np.full_like(y_test, fill_value=mean_baseline_val)
    mae_mean = float(mean_absolute_error(y_test, pred_mean))
    rmse_mean = float(root_mean_squared_error(y_test, pred_mean))
    spearman_mean = 0.0  # constant predictions have 0 correlation

    # ── 2. Baseline 2: Structured-Only LightGBM ───────────────────────────────
    pred_struct = lgbm_struct_baseline.predict(X_test_s)
    mae_struct = float(mean_absolute_error(y_test, pred_struct))
    rmse_struct = float(root_mean_squared_error(y_test, pred_struct))
    spearman_struct = float(spearmanr(y_test, pred_struct).correlation)

    # ── 3. Proposed System: Full Sentence-BERT + Structured LightGBM ──────────
    pred_median = lgbm_median.predict(X_test)
    pred_lower_raw = lgbm_lower.predict(X_test)
    pred_upper_raw = lgbm_upper.predict(X_test)

    # Calibrated bounds
    pred_lower_cal = pred_lower_raw - delta
    pred_upper_cal = pred_upper_raw + delta

    mae_full = float(mean_absolute_error(y_test, pred_median))
    rmse_full = float(root_mean_squared_error(y_test, pred_median))
    spearman_full = float(spearmanr(y_test, pred_median).correlation)

    # Interval metrics
    raw_coverage = float(np.mean((y_test >= pred_lower_raw) & (y_test <= pred_upper_raw)))
    raw_width = float(np.mean(pred_upper_raw - pred_lower_raw))

    cal_coverage = float(np.mean((y_test >= pred_lower_cal) & (y_test <= pred_upper_cal)))
    cal_width = float(np.mean(pred_upper_cal - pred_lower_cal))

    # Range / Tier accuracy
    actual_tiers = [get_tier(y) for y in y_test]
    pred_tiers_full = [get_tier(p) for p in pred_median]
    pred_tiers_struct = [get_tier(p) for p in pred_struct]
    pred_tiers_mean = [get_tier(p) for p in pred_mean]

    tier_acc_full = float(np.mean([a == p for a, p in zip(actual_tiers, pred_tiers_full)]))
    tier_acc_struct = float(np.mean([a == p for a, p in zip(actual_tiers, pred_tiers_struct)]))
    tier_acc_mean = float(np.mean([a == p for a, p in zip(actual_tiers, pred_tiers_mean)]))

    # Per-tier breakdown
    tier_breakdown = {}
    for tier_name in [
        "Div 3 (Easy, <1400)",
        "Div 2 (Medium, 1400-1899)",
        "Div 1 (Hard, 1900-2399)",
        "Master+ (Extreme, >=2400)",
    ]:
        indices = [i for i, t in enumerate(actual_tiers) if t == tier_name]
        if indices:
            sub_y = y_test[indices]
            sub_pred = pred_median[indices]
            sub_low = pred_lower_cal[indices]
            sub_up = pred_upper_cal[indices]
            tier_breakdown[tier_name] = {
                "count": len(indices),
                "mae": round(float(mean_absolute_error(sub_y, sub_pred)), 2),
                "rmse": round(float(root_mean_squared_error(sub_y, sub_pred)), 2),
                "coverage_80": round(float(np.mean((sub_y >= sub_low) & (sub_y <= sub_up))), 4),
            }

    report = {
        "test_sample_count": len(y_test),
        "models_evaluated": {
            "mean_baseline": {
                "name": "Training Mean Baseline",
                "mae": round(mae_mean, 2),
                "rmse": round(rmse_mean, 2),
                "spearman_rho": 0.0,
                "tier_accuracy": round(tier_acc_mean, 4),
            },
            "structured_only_lgbm": {
                "name": "Structured Features Only LightGBM",
                "mae": round(mae_struct, 2),
                "rmse": round(rmse_struct, 2),
                "spearman_rho": round(spearman_struct, 4),
                "tier_accuracy": round(tier_acc_struct, 4),
            },
            "sentence_bert_lightgbm": {
                "name": "IntelliGate Proposed (Sentence-BERT + Structured + Calibrated Quantiles)",
                "mae": round(mae_full, 2),
                "rmse": round(rmse_full, 2),
                "spearman_rho": round(spearman_full, 4),
                "tier_accuracy": round(tier_acc_full, 4),
                "raw_interval_coverage": round(raw_coverage, 4),
                "raw_interval_width": round(raw_width, 1),
                "calibrated_interval_coverage": round(cal_coverage, 4),
                "calibrated_interval_width": round(cal_width, 1),
                "calibration_delta": round(delta, 1),
            },
        },
        "per_tier_breakdown": tier_breakdown,
    }

    report_path = os.path.join(artifacts_dir, "evaluation_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    # Print markdown table
    print("\n=================== MODEL EVALUATION RESULTS ===================")
    print(f"Test Set Size: {len(y_test)} problems (chronologically held-out recent contests)")
    print("\n| Model / Baseline | MAE | RMSE | Spearman Rho | Tier Accuracy | 80% CI Coverage |")
    print("|---|---|---|---|---|---|")
    print(f"| Training Mean Baseline | {mae_mean:.1f} | {rmse_mean:.1f} | 0.0000 | {tier_acc_mean*100:.1f}% | N/A |")
    print(f"| Structured-Only LightGBM | {mae_struct:.1f} | {rmse_struct:.1f} | {spearman_struct:.4f} | {tier_acc_struct*100:.1f}% | N/A |")
    print(f"| **IntelliGate Sentence-BERT + LightGBM** | **{mae_full:.1f}** | **{rmse_full:.1f}** | **{spearman_full:.4f}** | **{tier_acc_full*100:.1f}%** | **{cal_coverage*100:.1f}%** |")
    print("================================================================\n")

    return report


if __name__ == "__main__":
    run_evaluation()
