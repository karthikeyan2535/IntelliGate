"""
Unit and Integration Tests for ML Difficulty Prediction Subsystem.
Tests:
- Structured feature extractor (bounds parsing, indicators, dimension stability)
- Semantic embedder (Sentence-BERT chunking, mean-pooling, caching, normalization)
- LightGBM quantile predictor (model loading, calibration bounds, monotonicity)
- CodingProblemAnalyzer integration with ML predictions and official ratings
- CodingRouter integration with continuous success probability estimation
"""
from __future__ import annotations

import unittest
import numpy as np

from app.analysis.ml_difficulty.structured_features import structured_feature_extractor
from app.analysis.ml_difficulty.semantic_embedder import semantic_embedder
from app.analysis.ml_difficulty.predictor import difficulty_predictor, DifficultyPrediction
from app.analysis.coding_analyzer import coding_analyzer
from app.routing.coding_router import coding_router, estimate_continuous_pass_rate


class TestMLDifficultyPrediction(unittest.IsolatedAsyncioTestCase):

    def test_structured_feature_extraction(self):
        """Verify structured feature extraction and numerical bound parsing."""
        stmt = "You are given an array of n integers. Find the maximum sum subarray."
        constraints = "1 <= n <= 2 * 10^5, -10^9 <= a_i <= 10^9. Time limit: 2.0s, Memory limit: 512MB."
        feats = structured_feature_extractor.extract_features(
            statement=stmt,
            constraints=constraints,
        )

        self.assertEqual(len(feats), len(structured_feature_extractor.FEATURE_NAMES))
        self.assertAlmostEqual(feats["log_max_n"], np.log10(200000.0), places=1)
        self.assertEqual(feats["missing_max_n"], 0.0)
        self.assertAlmostEqual(feats["log_max_val"], 9.0, places=1)
        self.assertEqual(feats["missing_time_limit"], 0.0)
        self.assertEqual(feats["missing_memory_limit"], 0.0)

        vec = structured_feature_extractor.extract_vector(statement=stmt, constraints=constraints)
        self.assertEqual(len(vec), 24)
        self.assertTrue(all(isinstance(v, (int, float)) for v in vec))

    def test_structured_feature_missing_fallbacks(self):
        """Verify robust fallbacks and missing-value flags for unconstrained problems."""
        feats = structured_feature_extractor.extract_features(statement="Simple task without constraints.")
        self.assertEqual(feats["missing_max_n"], 1.0)
        self.assertEqual(feats["missing_max_val"], 1.0)
        self.assertEqual(feats["missing_time_limit"], 1.0)
        self.assertEqual(feats["missing_memory_limit"], 1.0)
        self.assertEqual(feats["has_modulo"], 0.0)
        self.assertEqual(feats["is_interactive"], 0.0)

    def test_semantic_embedder_dimension_and_norm(self):
        """Verify Sentence-BERT produces 384-dimensional unit-norm embeddings."""
        text = "Given a tree of n vertices and n-1 edges, compute the longest path between any two vertices."
        emb = semantic_embedder.embed_text(text)

        self.assertEqual(emb.shape, (384,))
        norm = np.linalg.norm(emb)
        self.assertAlmostEqual(norm, 1.0, places=4)

        # Check in-memory caching
        emb2 = semantic_embedder.embed_text(text)
        np.testing.assert_array_equal(emb, emb2)

    def test_semantic_embedder_chunking(self):
        """Verify long problem statement chunking and pooling."""
        long_text = "Competitive programming problem statement. " * 300
        emb = semantic_embedder.embed_text(long_text)
        self.assertEqual(emb.shape, (384,))
        self.assertAlmostEqual(np.linalg.norm(emb), 1.0, places=4)

    def test_difficulty_predictor_inference(self):
        """Verify LightGBM quantile regression produces valid monotonic Codeforces ratings."""
        pred = difficulty_predictor.predict(
            title="Tree Diameter",
            statement="Given a tree with n nodes, find the length of the longest path.",
            constraints="1 <= n <= 200,000",
        )

        self.assertIsInstance(pred, DifficultyPrediction)
        self.assertGreaterEqual(pred.predicted_rating, 800)
        self.assertLessEqual(pred.predicted_rating, 3500)
        # Verify calibrated uncertainty bounds monotonicity
        self.assertLessEqual(pred.lower_bound, pred.predicted_rating)
        self.assertGreaterEqual(pred.upper_bound, pred.predicted_rating)
        self.assertGreaterEqual(pred.confidence_width, 200)
        self.assertIn(pred.difficulty_tier, ["easy", "medium", "hard"])
        self.assertEqual(pred.prediction_method, "sentence_bert_lightgbm")

    def test_coding_analyzer_with_ml_prediction(self):
        """Verify CodingProblemAnalyzer integrates ML difficulty predictor."""
        analysis = coding_analyzer.analyze(
            title="Shortest Path Dijkstra",
            statement="Find shortest distance from source s to all vertices in directed weighted graph.",
            constraints="1 <= n <= 10^5, 1 <= m <= 2 * 10^5",
        )

        self.assertEqual(analysis.algorithm_family, "graphs")
        self.assertIsNotNone(analysis.predicted_rating)
        self.assertGreaterEqual(analysis.predicted_rating, 800)
        self.assertIsNotNone(analysis.lower_bound)
        self.assertIsNotNone(analysis.upper_bound)
        self.assertEqual(analysis.prediction_method, "sentence_bert_lightgbm")

    def test_coding_analyzer_with_official_rating(self):
        """Verify official Codeforces ratings are trusted and preserved directly."""
        analysis = coding_analyzer.analyze(
            title="Codeforces 1500 Problem",
            statement="Problem with official rating.",
            official_rating=1500,
        )

        self.assertEqual(analysis.predicted_rating, 1500)
        self.assertEqual(analysis.lower_bound, 1500)
        self.assertEqual(analysis.upper_bound, 1500)
        self.assertEqual(analysis.prediction_method, "official_codeforces")
        self.assertEqual(analysis.difficulty, "medium")

    def test_continuous_pass_rate_estimation(self):
        """Verify continuous pass-rate function interpolates smoothly across ratings."""
        mock_profile = {
            "easy_pass_rate": 0.95,
            "medium_pass_rate": 0.85,
            "hard_pass_rate": 0.70,
            "overall_pass_rate": 0.85,
        }

        p_easy = estimate_continuous_pass_rate(mock_profile, 1000.0)
        p_med = estimate_continuous_pass_rate(mock_profile, 1600.0)
        p_hard = estimate_continuous_pass_rate(mock_profile, 2200.0)
        p_grandmaster = estimate_continuous_pass_rate(mock_profile, 2800.0)

        # Monotonically non-increasing with difficulty
        self.assertGreater(p_easy, p_med)
        self.assertGreater(p_med, p_hard)
        self.assertGreater(p_hard, p_grandmaster)

    async def test_coding_router_with_predicted_rating(self):
        """Verify CodingRouter uses predicted rating and uncertainty range for model selection."""
        res = await coding_router.select_model(
            algorithm_category="graphs",
            difficulty="hard",
            routing_mode="intelligent",
            predicted_rating=2200,
            lower_bound=1800,
            upper_bound=2600,
            reliability_threshold=0.50,
        )

        self.assertIsNotNone(res.selected_model)
        self.assertEqual(res.predicted_rating, 2200)
        self.assertEqual(res.uncertainty_range, (1800, 2600))
        self.assertTrue(len(res.candidate_rankings) > 0)
        # Weights should emphasize quality for high-difficulty problems (R_eff >= 2000)
        self.assertGreaterEqual(res.applied_weights["quality"], 0.70)


if __name__ == "__main__":
    unittest.main()
