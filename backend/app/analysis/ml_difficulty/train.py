"""
LightGBM Quantile Regression Training Pipeline for Difficulty Prediction.

Features:
- Combined 408-dimensional feature representation (384-dim Sentence-BERT + 24-dim structured features).
- Trains 3 LightGBM models:
  1. Central median rating estimator (alpha = 0.50)
  2. Lower uncertainty bound (alpha = 0.10)
  3. Upper uncertainty bound (alpha = 0.90)
- Trains baseline structured-only model for benchmark comparison.
- Conformal calibration of prediction intervals using the calibration split.
- Exports trained model artifacts and calibration metadata.
"""
from __future__ import annotations

import os
import time
import json
import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from scipy.stats import spearmanr

from app.analysis.ml_difficulty.structured_features import structured_feature_extractor
from app.analysis.ml_difficulty.semantic_embedder import semantic_embedder


def extract_split_features(
    df: pd.DataFrame,
    cache_path: str,
    desc: str = "split",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Extracts or loads cached features:
    returns (X_combined, X_structured, y)
    """
    if os.path.exists(cache_path):
        print(f"Loading cached features from {cache_path}...")
        data = np.load(cache_path)
        return data["X_combined"], data["X_structured"], data["y"]

    print(f"Extracting features for {desc} ({len(df)} samples)...")
    t0 = time.time()

    # 1. Structured features
    struct_list = []
    texts_to_embed = []

    for _, row in df.iterrows():
        stmt = str(row.get("problem_statement", ""))
        inp = str(row.get("input", ""))
        out = str(row.get("output", ""))
        tl = str(row.get("time_limit", ""))
        ml = str(row.get("memory_limit", ""))

        s_vec = structured_feature_extractor.extract_vector(
            statement=stmt,
            input_format=inp,
            output_format=out,
        )
        struct_list.append(s_vec)

        # Assemble semantic text
        combined_text = f"{stmt}\n\nInput:\n{inp}\n\nOutput:\n{out}".strip()
        texts_to_embed.append(combined_text)

    X_structured = np.array(struct_list, dtype=np.float32)

    # 2. Semantic embeddings
    print(f"  Encoding {len(texts_to_embed)} semantic texts with Sentence-BERT...")
    X_semantic = semantic_embedder.batch_embed(texts_to_embed, batch_size=64)

    # 3. Concatenate
    X_combined = np.hstack([X_semantic, X_structured])
    y = df["rating"].values.astype(np.float32)

    # Save cache
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    np.savez_compressed(
        cache_path,
        X_combined=X_combined,
        X_structured=X_structured,
        y=y,
    )
    print(f"  Done in {time.time() - t0:.2f}s. Saved to {cache_path}.")
    return X_combined, X_structured, y


def train_models():
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "data")
    artifacts_dir = os.path.join(base_dir, "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    train_df = pd.read_csv(os.path.join(data_dir, "train.csv"))
    val_df = pd.read_csv(os.path.join(data_dir, "val.csv"))
    test_df = pd.read_csv(os.path.join(data_dir, "test.csv"))

    # Extract or load features
    X_train, X_train_s, y_train = extract_split_features(
        train_df, os.path.join(data_dir, "features_train.npz"), "Train"
    )
    X_val, X_val_s, y_val = extract_split_features(
        val_df, os.path.join(data_dir, "features_val.npz"), "Val/Calibration"
    )
    X_test, X_test_s, y_test = extract_split_features(
        test_df, os.path.join(data_dir, "features_test.npz"), "Test"
    )

    print("\n--- Training LightGBM Models ---")
    common_params = {
        "n_estimators": 450,
        "learning_rate": 0.04,
        "num_leaves": 31,
        "min_child_samples": 25,
        "subsample": 0.85,
        "colsample_bytree": 0.80,
        "random_state": 42,
        "n_jobs": -1,
    }

    # 1. Central Median Model (alpha = 0.5)
    print("Training Central Median Model (alpha=0.50)...")
    lgbm_median = LGBMRegressor(objective="quantile", alpha=0.5, **common_params)
    lgbm_median.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
    )

    # 2. Lower Quantile Model (alpha = 0.10)
    print("Training Lower Quantile Model (alpha=0.10)...")
    lgbm_lower = LGBMRegressor(objective="quantile", alpha=0.10, **common_params)
    lgbm_lower.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
    )

    # 3. Upper Quantile Model (alpha = 0.90)
    print("Training Upper Quantile Model (alpha=0.90)...")
    lgbm_upper = LGBMRegressor(objective="quantile", alpha=0.90, **common_params)
    lgbm_upper.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
    )

    # 4. Structured-Only Baseline Model
    print("Training Structured-Only Baseline Model...")
    lgbm_struct_baseline = LGBMRegressor(objective="regression", **common_params)
    lgbm_struct_baseline.fit(
        X_train_s, y_train,
        eval_set=[(X_val_s, y_val)],
    )

    # ── Conformal Quantile Calibration ─────────────────────────────────────────
    print("\n--- Calibrating Uncertainty Bounds on Calibration Split ---")
    val_pred_median = lgbm_median.predict(X_val)
    val_pred_lower = lgbm_lower.predict(X_val)
    val_pred_upper = lgbm_upper.predict(X_val)

    # Raw coverage:
    raw_in_interval = (y_val >= val_pred_lower) & (y_val <= val_pred_upper)
    raw_coverage = float(np.mean(raw_in_interval))
    raw_width = float(np.mean(val_pred_upper - val_pred_lower))
    print(f"Validation Raw Coverage (alpha=0.1 to 0.9): {raw_coverage*100:.2f}%, Avg Width: {raw_width:.1f}")

    # Compute conformal margin offset delta to guarantee >= 80% coverage
    target_coverage = 0.80
    if raw_coverage < target_coverage:
        # Compute non-conformity scores: distance outside the raw interval
        lower_violations = np.maximum(0, val_pred_lower - y_val)
        upper_violations = np.maximum(0, y_val - val_pred_upper)
        violations = np.maximum(lower_violations, upper_violations)
        # 80th percentile of violations
        delta = float(np.percentile(violations, target_coverage * 100))
    else:
        delta = 0.0

    calibrated_lower = val_pred_lower - delta
    calibrated_upper = val_pred_upper + delta
    calibrated_coverage = float(np.mean((y_val >= calibrated_lower) & (y_val <= calibrated_upper)))
    calibrated_width = float(np.mean(calibrated_upper - calibrated_lower))
    print(f"Calibration Offset (delta): +-{delta:.1f}")
    print(f"Calibrated Coverage on Val: {calibrated_coverage*100:.2f}%, Calibrated Avg Width: {calibrated_width:.1f}")

    # ── Validation Metrics for Central Predictor ──────────────────────────────
    val_mae = float(mean_absolute_error(y_val, val_pred_median))
    val_rmse = float(root_mean_squared_error(y_val, val_pred_median))
    val_spearman = float(spearmanr(y_val, val_pred_median).correlation)
    print(f"Validation MAE: {val_mae:.2f}, RMSE: {val_rmse:.2f}, Spearman Rho: {val_spearman:.4f}")

    # Save artifacts
    print("\n--- Saving Artifacts ---")
    joblib.dump(lgbm_median, os.path.join(artifacts_dir, "lgbm_median.joblib"))
    joblib.dump(lgbm_lower, os.path.join(artifacts_dir, "lgbm_lower.joblib"))
    joblib.dump(lgbm_upper, os.path.join(artifacts_dir, "lgbm_upper.joblib"))
    joblib.dump(lgbm_struct_baseline, os.path.join(artifacts_dir, "lgbm_struct_baseline.joblib"))

    # Also export LightGBM native text models for portable C++/fast deployment
    lgbm_median.booster_.save_model(os.path.join(artifacts_dir, "lgbm_median.txt"))
    lgbm_lower.booster_.save_model(os.path.join(artifacts_dir, "lgbm_lower.txt"))
    lgbm_upper.booster_.save_model(os.path.join(artifacts_dir, "lgbm_upper.txt"))

    # Persist embedding disk cache
    semantic_embedder.save_disk_cache()

    metadata = {
        "train_samples": len(train_df),
        "val_samples": len(val_df),
        "test_samples": len(test_df),
        "feature_dim": X_train.shape[1],
        "semantic_dim": 384,
        "structured_dim": X_train_s.shape[1],
        "training_mean_rating": float(round(np.mean(y_train), 2)),
        "training_median_rating": float(round(np.median(y_train), 2)),
        "validation_metrics": {
            "mae": round(val_mae, 2),
            "rmse": round(val_rmse, 2),
            "spearman_rho": round(val_spearman, 4),
            "raw_interval_coverage": round(raw_coverage, 4),
            "raw_interval_width": round(raw_width, 1),
            "calibration_delta": round(delta, 1),
            "calibrated_coverage": round(calibrated_coverage, 4),
            "calibrated_width": round(calibrated_width, 1),
        },
        "structured_feature_names": structured_feature_extractor.FEATURE_NAMES,
    }

    with open(os.path.join(artifacts_dir, "calibration_meta.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print("All models and metadata saved successfully to:", artifacts_dir)
    return metadata


if __name__ == "__main__":
    train_models()
