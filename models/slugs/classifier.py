"""
classifier.py - Logistic-classifier model for URL path intent classification.
"""

import json
import math
from collections import defaultdict

from .constants import (
    CLASSES,
    LEARNING_RATE,
    UNCERTAINTY_CONF_THRESHOLD,
    UNCERTAINTY_MARGIN_THRESHOLD,
)
from .features import extract


class URLIntentModel:
    """Multi-class logistic classifier for URL path token intent."""

    def __init__(self):
        self.weights: defaultdict[str, defaultdict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )
        self.bias: defaultdict[str, float] = defaultdict(float)
        self.lr = LEARNING_RATE
        self.classes = list(CLASSES)

    # ── Prediction ──────────────────────────────────────

    def predict(self, raw: str) -> dict:
        """Return scores, final class, confidence, margin, and uncertainty flag."""
        f = extract(raw)
        scores: dict[str, float] = {}
        for cls in self.classes:
            score = self.bias[cls]
            for feat, val in f.items():
                score += self.weights[cls].get(feat, 0.0) * val
            scores[cls] = 1.0 / (1.0 + math.exp(-max(min(score, 50.0), -50.0)))

        ranked = sorted(scores, key=lambda c: scores[c], reverse=True)
        best = ranked[0]
        second = ranked[1] if len(ranked) > 1 else best
        margin = scores[best] - scores[second]

        is_uncertain = (
            scores[best] < UNCERTAINTY_CONF_THRESHOLD
            or margin < UNCERTAINTY_MARGIN_THRESHOLD
        )

        return {
            "scores": scores,
            "final": best,
            "confidence": scores[best],
            "margin": margin,
            "is_uncertain": is_uncertain,
        }

    # ── Training ────────────────────────────────────────

    def train(self, raw: str, label: str, weight: float = 1.0) -> None:
        """One stochastic gradient-descent step."""
        f = extract(raw)
        pred_scores = self.predict(raw)["scores"]

        for cls in pred_scores:
            target = 1.0 if cls == label else 0.0
            error = (target - pred_scores[cls]) * weight
            for feat, val in f.items():
                self.weights[cls][feat] += self.lr * error * val
            self.bias[cls] += self.lr * error

    # ── Persistence ─────────────────────────────────────

    def save(self, path: str) -> None:
        """Save model weights to JSON."""
        data = {
            "weights": {c: dict(w) for c, w in self.weights.items()},
            "bias": dict(self.bias),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def load(self, path: str) -> None:
        """Load model weights from JSON."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for cls, w in data["weights"].items():
            self.weights[cls] = defaultdict(float, w)
        self.bias = defaultdict(float, data["bias"])
