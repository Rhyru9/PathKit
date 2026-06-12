"""
constants.py - Dictionaries, stopwords, and configuration for slug classification.
"""

VOWELS = set("aeiou")

# ── Stopwords: common words that signal natural-language slugs ──
COMMON_WORDS = {
    # Indonesian
    "dan",
    "di",
    "ke",
    "dari",
    "yang",
    "untuk",
    "dengan",
    "pada",
    "atau",
    "ini",
    "itu",
    "adalah",
    "tidak",
    "ada",
    "akan",
    "juga",
    "sudah",
    "bisa",
    "oleh",
    "cara",
    "data",
    "guru",
    "sekolah",
    "belajar",
    "siswa",
    "modul",
    "buku",
    "panduan",
    "login",
    "admin",
    "user",
    "home",
    "about",
    "contact",
    "help",
    # English
    "the",
    "and",
    "for",
    "how",
    "what",
    "new",
    "get",
    "api",
    "app",
    "web",
    "page",
    "post",
    "blog",
    "news",
    "info",
    "test",
    "demo",
    "docs",
}

# ── Anti-slug: tokens that push classification away from "slug" ──
ANTI_SLUG_WORDS = {
    "wp-content",
    "wp-includes",
    "wp-json",
    "wp-admin",
    "assets",
    "static",
    "uploads",
    "cache",
    "tmp",
    "temp",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "bin",
    "lib",
    "includes",
    "themes",
    "plugins",
    "storage",
    "media",
    "files",
    "images",
    "img",
    "css",
    "js",
    "fonts",
    "backup",
    "config",
    "log",
    "logs",
}

# ── Class labels ──
CLASSES = [
    "slug",
    "api",
    "asset",
    "search",
    "random_id",
    "file",
    "encoded",
]

# ── Hyperparameters ──
LEARNING_RATE = 0.03
UNCERTAINTY_CONF_THRESHOLD = 0.55
UNCERTAINTY_MARGIN_THRESHOLD = 0.08

# ── Normalization constants ──
MAX_LEN_NORM = 200.0
MAX_TOKEN_COUNT = 20.0
MAX_AVG_TOKEN_LEN = 30.0
MAX_READABLE_COUNT = 10
MAX_COMMON_HITS = 5
MAX_ANTI_HITS = 3
MAX_ENTROPY = 8.0
