"""
models.slugs - Structured URL Intent Classifier for slug detection.

Modules
-------
constants   : Vocabulary, stopwords, and hyperparameters.
features    : Feature extraction from URL path tokens.
labeling    : Heuristic auto-labeling for self-supervised training.
classifier  : Logistic-classifier model (train / predict / save / load).
pipeline    : End-to-end training, classification, and slug export.

Usage
-----
    from models.slugs import URLIntentModel
    from models.slugs.pipeline import run

    # Quick pipeline
    model = run("data/paths.txt", "output/slugs.txt", "output/slugs_review.txt")

    # Manual
    model = URLIntentModel()
    model.train("/artikel/panduan-belajar-online", "slug")
    result = model.predict("/artikel/panduan-belajar-online")
"""

from .classifier import URLIntentModel
from .features import extract
from .labeling import auto_label
from .pipeline import run

__all__ = [
    "URLIntentModel",
    "auto_label",
    "extract",
    "run",
]
