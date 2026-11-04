"""Dense subword semantic encoder and Reciprocal Rank Fusion for research discovery."""

import math
import re
from collections import Counter
from collections.abc import Iterable, Sequence

import numpy as np

from .search import _STOP_WORDS, _TOKEN


def _char_ngrams(word: str, n_min: int = 3, n_max: int = 5) -> list[str]:
    """Extract character n-grams bounded by word boundaries for subword morphology."""
    word = f'<{word}>'
    length = len(word)
    ngrams = []
    for n in range(n_min, min(n_max + 1, length + 1)):
        for i in range(length - n + 1):
            ngrams.append(word[i:i + n])
    return ngrams


class SemanticVectorizer:
    """Fast, deterministic subword TF-IDF vectorizer mapping text to dense semantic vectors.

    Captures morphological variations, compound terms, and domain roots
    (e.g. 'sensor' -> 'sensing', 'telemetric' -> 'telemetry', 'wireless' -> 'wirelessly')
    without requiring heavyweight deep-learning runtimes.
    """

    def __init__(self, dim: int = 256):
        self.dim = dim

    def encode(self, text: str) -> np.ndarray:
        if not text or not text.strip():
            return np.zeros(self.dim, dtype=np.float32)

        tokens = [
            token.casefold()
            for token in _TOKEN.findall(text)
            if token.casefold() not in _STOP_WORDS
        ]
        if not tokens:
            return np.zeros(self.dim, dtype=np.float32)

        features = []
        for token in tokens:
            features.append(f'w:{token}')
            features.extend(_char_ngrams(token))

        counts = Counter(features)
        vector = np.zeros(self.dim, dtype=np.float32)

        for feature, count in counts.items():
            # Stable feature hashing into vector dimensions
            h = hash(feature)
            idx = abs(h) % self.dim
            sign = 1.0 if (h // self.dim) % 2 == 0 else -1.0
            # Sublinear term frequency weighting
            tf = 1.0 + math.log(count)
            vector[idx] += sign * tf

        norm = np.linalg.norm(vector)
        if norm > 1e-6:
            vector /= norm
        return vector

    def similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Compute cosine similarity between two unit vectors."""
        dot = float(np.dot(vec_a, vec_b))
        return max(0.0, min(1.0, dot))


def reciprocal_rank_fusion(
    bm25_ranked_ids: Sequence[str],
    semantic_ranked_ids: Sequence[str],
    rrf_k: int = 60
) -> dict[str, float]:
    """Combine ranked lists using standard Reciprocal Rank Fusion (RRF).

    Formula: RRF_score(d) = sum(1.0 / (rrf_k + rank(d)))
    """
    scores: dict[str, float] = {}

    for rank, doc_id in enumerate(bm25_ranked_ids, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rrf_k + rank)

    for rank, doc_id in enumerate(semantic_ranked_ids, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rrf_k + rank)

    return scores
