"""
Runtime Difficulty Predictor Service for Competitive Programming Problems.

Combines:
1. Sentence-BERT semantic embeddings (all-MiniLM-L6-v2, 384-dim)
2. Structured numerical feature extractor (24-dim)
3. LightGBM Quantile Regressors (alpha = 0.50, 0.10, 0.90) with conformal calibration

Outputs:
{
  "predicted_rating": 1750,
  "lower_bound": 1400,
  "upper_bound": 2100,
  "prediction_method": "sentence_bert_lightgbm"
}
"""
from __future__ import annotations

import os
import json
import logging
from typing import Dict, Any, Optional, Tuple
import joblib
import numpy as np
from pydantic import BaseModel, Field

from app.analysis.ml_difficulty.structured_features import structured_feature_extractor
from app.analysis.ml_difficulty.semantic_embedder import semantic_embedder

logger = logging.getLogger(__name__)


class DifficultyPrediction(BaseModel):
    predicted_rating: int = Field(..., description="Estimated Codeforces difficulty rating (800 - 3500)")
    lower_bound: int = Field(..., description="Calibrated lower uncertainty bound (alpha = 0.10)")
    upper_bound: int = Field(..., description="Calibrated upper uncertainty bound (alpha = 0.90)")
    confidence_width: int = Field(..., description="Uncertainty interval width (upper_bound - lower_bound)")
    difficulty_tier: str = Field("medium", description="Mapped bucket: easy, medium, hard, extreme")
    prediction_method: str = Field("sentence_bert_lightgbm", description="Algorithm identifier")


class DifficultyPredictor:
    """
    Inference service for ML-driven difficulty prediction.
    """

    def __init__(self, artifacts_dir: Optional[str] = None):
        self._artifacts_dir = artifacts_dir or os.path.join(
            os.path.dirname(__file__), "artifacts"
        )
        self._median_model = None
        self._lower_model = None
        self._upper_model = None
        self._calibration_delta = 0.0
        self._training_mean = 1850.0
        self._is_loaded = False
        self._load_attempted = False

    def _ensure_loaded(self) -> bool:
        """Lazy-loads LightGBM models and calibration metadata."""
        if self._is_loaded:
            return True
        if self._load_attempted:
            return self._is_loaded

        self._load_attempted = True
        median_path = os.path.join(self._artifacts_dir, "lgbm_median.joblib")
        lower_path = os.path.join(self._artifacts_dir, "lgbm_lower.joblib")
        upper_path = os.path.join(self._artifacts_dir, "lgbm_upper.joblib")
        meta_path = os.path.join(self._artifacts_dir, "calibration_meta.json")

        if not (os.path.exists(median_path) and os.path.exists(lower_path) and os.path.exists(upper_path)):
            logger.warning(
                f"LightGBM models not found at {self._artifacts_dir}. Fallback mode active."
            )
            return False

        try:
            self._median_model = joblib.load(median_path)
            self._lower_model = joblib.load(lower_path)
            self._upper_model = joblib.load(upper_path)

            if os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                    self._calibration_delta = float(
                        meta.get("validation_metrics", {}).get("calibration_delta", 0.0)
                    )
                    self._training_mean = float(
                        meta.get("training_mean_rating", 1850.0)
                    )

            self._is_loaded = True
            logger.info("LightGBM difficulty prediction models loaded successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to load LightGBM difficulty models: {e}")
            return False

    def _tier_from_rating(self, rating: int) -> str:
        """Maps numerical Codeforces rating to coarse string difficulty for compatibility."""
        if rating <= 1200:
            return "easy"
        elif rating <= 1800:
            return "medium"
        elif rating <= 2400:
            return "hard"
        else:
            return "hard"

    def predict(
        self,
        title: str,
        statement: str,
        constraints: Optional[str] = "",
        input_format: Optional[str] = "",
        output_format: Optional[str] = "",
        time_limit_ms: Optional[int] = None,
        memory_limit_mb: Optional[int] = None,
    ) -> DifficultyPrediction:
        """
        Predicts numerical rating and uncertainty bounds for a coding problem.
        """
        # 1. Check if models are available
        if not self._ensure_loaded():
            # Fallback estimation using structured signals if model weights missing
            s_dict = structured_feature_extractor.extract_features(
                statement=statement,
                constraints=constraints,
                time_limit_ms=time_limit_ms,
                memory_limit_mb=memory_limit_mb,
                input_format=input_format,
                output_format=output_format,
            )
            base_r = int(self._training_mean)
            if s_dict["log_max_n"] >= 8.0 or s_dict["is_interactive"] > 0:
                base_r = 2100
            elif s_dict["log_max_n"] <= 2.5:
                base_r = 1100
            elif s_dict["is_graph_problem"] > 0.3 or s_dict["has_modulo"] > 0:
                base_r = 1700
            else:
                base_r = 1400

            return DifficultyPrediction(
                predicted_rating=base_r,
                lower_bound=max(base_r - 300, 800),
                upper_bound=min(base_r + 300, 3500),
                confidence_width=600,
                difficulty_tier=self._tier_from_rating(base_r),
                prediction_method="structured_heuristic_fallback",
            )

        # 2. Extract structured numerical features (24 dims)
        s_vec = structured_feature_extractor.extract_vector(
            statement=statement,
            constraints=constraints,
            time_limit_ms=time_limit_ms,
            memory_limit_mb=memory_limit_mb,
            input_format=input_format,
            output_format=output_format,
        )

        # 3. Extract semantic embedding (384 dims)
        sem_vec = semantic_embedder.embed_problem(
            title=title,
            statement=statement,
            constraints=constraints,
            input_format=input_format,
            output_format=output_format,
        )

        # 4. Combine into 408-dimensional feature vector
        combined_feature = np.concatenate([sem_vec, np.array(s_vec, dtype=np.float32)])
        X = np.expand_dims(combined_feature, axis=0)

        # 5. Predict with LightGBM models
        pred_median = float(self._median_model.predict(X)[0])
        pred_lower_raw = float(self._lower_model.predict(X)[0])
        pred_upper_raw = float(self._upper_model.predict(X)[0])

        # Apply conformal calibration delta
        pred_lower = pred_lower_raw - self._calibration_delta
        pred_upper = pred_upper_raw + self._calibration_delta

        # Round and enforce bounds [800, 3500] and monotonicity
        rating_int = int(np.clip(round(pred_median), 800, 3500))
        lower_int = int(np.clip(round(pred_lower), 800, rating_int))
        upper_int = int(np.clip(round(pred_upper), rating_int, 3500))

        # Enforce minimum uncertainty interval width (at least 200 rating points)
        if upper_int - lower_int < 200:
            lower_int = max(800, rating_int - 100)
            upper_int = min(3500, rating_int + 100)

        tier = self._tier_from_rating(rating_int)

        return DifficultyPrediction(
            predicted_rating=rating_int,
            lower_bound=lower_int,
            upper_bound=upper_int,
            confidence_width=upper_int - lower_int,
            difficulty_tier=tier,
            prediction_method="sentence_bert_lightgbm",
        )


difficulty_predictor = DifficultyPredictor()
