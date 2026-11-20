"""
Semantic Feature Extractor using Sentence-BERT (all-MiniLM-L6-v2).

Features:
- 384-dimensional dense semantic representations.
- Chunking & mean-pooling for long statements without loss of constraints/I/O.
- Memory & persistent disk caching.
- Graceful offline / fallback support.
"""
from __future__ import annotations

import hashlib
import os
import pickle
import re
from typing import Dict, List, Optional, Tuple, Union
import numpy as np


class SemanticEmbedder:
    """
    Sentence-BERT embedding extractor with chunking, pooling, and multi-tier caching.
    """

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384
    CHUNK_SIZE_WORDS = 200
    CHUNK_OVERLAP_WORDS = 50

    def __init__(self, cache_dir: Optional[str] = None):
        self._model = None
        self._model_load_attempted = False
        self._memory_cache: Dict[str, np.ndarray] = {}
        self._cache_dir = cache_dir or os.path.join(
            os.path.dirname(__file__), "artifacts"
        )
        self._disk_cache_file = os.path.join(self._cache_dir, "embedding_cache.pkl")
        self._load_disk_cache()

    def _load_disk_cache(self):
        """Loads cached embeddings from disk if available."""
        if os.path.exists(self._disk_cache_file):
            try:
                with open(self._disk_cache_file, "rb") as f:
                    data = pickle.load(f)
                    if isinstance(data, dict):
                        self._memory_cache.update(data)
            except Exception:
                pass

    def save_disk_cache(self):
        """Persists the in-memory cache to disk."""
        try:
            os.makedirs(self._cache_dir, exist_ok=True)
            with open(self._disk_cache_file, "wb") as f:
                pickle.dump(self._memory_cache, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception:
            pass

    def _get_model(self):
        """Lazy loads the SentenceTransformer model."""
        if self._model is not None:
            return self._model
        if self._model_load_attempted:
            return None

        self._model_load_attempted = True
        try:
            from sentence_transformers import SentenceTransformer
            # Load with local_files_only if possible, or download once
            self._model = SentenceTransformer(self.MODEL_NAME)
            return self._model
        except Exception as e:
            # If offline or downloading failed, we will fall back to deterministic projection
            return None

    def _hash_text(self, text: str) -> str:
        """Returns SHA-256 hash of cleaned text."""
        cleaned = " ".join(text.split()).strip()
        return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

    def _chunk_text(self, text: str) -> List[str]:
        """
        Splits text into overlapping sliding-window word chunks to ensure long
        statements with input/output and constraints fit within the transformer's
        maximum context without truncation.
        """
        words = text.split()
        if len(words) <= self.CHUNK_SIZE_WORDS:
            return [text]

        chunks = []
        step = self.CHUNK_SIZE_WORDS - self.CHUNK_OVERLAP_WORDS
        for i in range(0, len(words), step):
            chunk_words = words[i : i + self.CHUNK_SIZE_WORDS]
            chunks.append(" ".join(chunk_words))
            if i + self.CHUNK_SIZE_WORDS >= len(words):
                break
        return chunks

    def _deterministic_fallback_embed(self, text: str) -> np.ndarray:
        """
        Deterministic, seed-based projection fallback when PyTorch/Transformers
        is offline or model files are unavailable. Produces consistent 384-dim unit vector.
        """
        words = re.findall(r"\w+", text.lower())
        vec = np.zeros(self.EMBEDDING_DIM, dtype=np.float32)
        if not words:
            vec[0] = 1.0
            return vec

        for word in words:
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.EMBEDDING_DIM
            sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
            vec[idx] += sign

        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec = vec / norm
        else:
            vec[0] = 1.0
        return vec

    def embed_text(self, text: str) -> np.ndarray:
        """
        Embeds a single problem text into a normalized 384-dimensional vector.
        Applies chunking and mean-pooling for long statements.
        """
        text = text.strip()
        if not text:
            zero_vec = np.zeros(self.EMBEDDING_DIM, dtype=np.float32)
            zero_vec[0] = 1.0
            return zero_vec

        cache_key = self._hash_text(text)
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key].copy()

        model = self._get_model()
        if model is None:
            # Use deterministic projection fallback
            emb = self._deterministic_fallback_embed(text)
            self._memory_cache[cache_key] = emb
            return emb.copy()

        # Split into chunks if long
        chunks = self._chunk_text(text)
        try:
            chunk_embeddings = model.encode(
                chunks,
                batch_size=min(len(chunks), 8),
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            if len(chunks) == 1:
                pooled = chunk_embeddings[0]
            else:
                # Mean pool across chunks
                pooled = np.mean(chunk_embeddings, axis=0)
                norm = np.linalg.norm(pooled)
                if norm > 1e-6:
                    pooled = pooled / norm
        except Exception:
            pooled = self._deterministic_fallback_embed(text)

        pooled = pooled.astype(np.float32)
        self._memory_cache[cache_key] = pooled
        return pooled.copy()

    def embed_problem(
        self,
        title: str,
        statement: str,
        constraints: Optional[str] = "",
        input_format: Optional[str] = "",
        output_format: Optional[str] = "",
    ) -> np.ndarray:
        """
        Assembles all problem sections into structured semantic input and returns
        the 384-dim normalized embedding.
        """
        sections = [f"Title: {title.strip()}"]
        if statement:
            sections.append(f"Statement: {statement.strip()}")
        if input_format:
            sections.append(f"Input: {input_format.strip()}")
        if output_format:
            sections.append(f"Output: {output_format.strip()}")
        if constraints:
            sections.append(f"Constraints: {constraints.strip()}")

        full_text = "\n\n".join(sections)
        return self.embed_text(full_text)

    def batch_embed(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Batch embeds multiple texts efficiently.
        """
        embeddings = []
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            key = self._hash_text(text)
            if key in self._memory_cache:
                embeddings.append(self._memory_cache[key].copy())
            else:
                embeddings.append(None)
                uncached_indices.append(i)
                uncached_texts.append(text)

        if uncached_texts:
            model = self._get_model()
            if model is not None:
                try:
                    computed = model.encode(
                        uncached_texts,
                        batch_size=batch_size,
                        show_progress_bar=False,
                        convert_to_numpy=True,
                        normalize_embeddings=True,
                    )
                    for idx, emb in zip(uncached_indices, computed):
                        emb = emb.astype(np.float32)
                        key = self._hash_text(texts[idx])
                        self._memory_cache[key] = emb
                        embeddings[idx] = emb
                except Exception:
                    for idx in uncached_indices:
                        emb = self.embed_text(texts[idx])
                        embeddings[idx] = emb
            else:
                for idx in uncached_indices:
                    emb = self._deterministic_fallback_embed(texts[idx])
                    key = self._hash_text(texts[idx])
                    self._memory_cache[key] = emb
                    embeddings[idx] = emb

        return np.vstack(embeddings)


semantic_embedder = SemanticEmbedder()
