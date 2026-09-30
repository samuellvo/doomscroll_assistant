"""Paths, model names, and tunable thresholds. Override any of these with env vars."""

import os
from pathlib import Path

ROOT = Path(os.environ.get("DOOMSCROLL_ROOT", Path(__file__).resolve().parents[2]))
VAULT = ROOT / "vault"
DATA = VAULT / "data"

REELS_FILE = DATA / "reels.jsonl"
INSIGHTS_FILE = DATA / "insights.jsonl"
TOOLS_FILE = DATA / "tools.jsonl"
GROUPS_FILE = DATA / "groups.jsonl"
EMBEDDINGS_FILE = DATA / "embeddings.npz"
TAXONOMY_FILE = VAULT / "taxonomy.md"
FEEDBACK_FILE = VAULT / "feedback.md"

# Run `python -m doomscroll models` to see what your key can use. Each list is tried in order,
# falling through on 503 (overloaded) / 429 (quota), which the free tier hits often.
def _models(var: str, default: str) -> list[str]:
    return [m.strip() for m in os.environ.get(var, default).split(",") if m.strip()]

# Video understanding: newest Flash first.
ANALYSIS_MODELS = _models("GEMINI_MODELS", "gemini-3.8-flash,gemini-3.6-flash,gemini-flash-latest")
# Cheap text-only calls (duplicate judging, group naming) use Lite to spare the main model's quota.
LIGHT_MODELS = _models("GEMINI_LIGHT_MODELS", "gemini-3.5-flash-lite,gemini-3.1-flash-lite")
EMBEDDING_MODEL = os.environ.get("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIM = 768

# Cosine-similarity bands for dedup. gemini-embedding-001 scores distinct-but-related ideas
# 0.79-0.89, so these sit above that. Recalibrate after ~20 real reels.
DUPLICATE_THRESHOLD = float(os.environ.get("DUPLICATE_THRESHOLD", 0.95))
AMBIGUOUS_THRESHOLD = float(os.environ.get("AMBIGUOUS_THRESHOLD", 0.85))
# Weekly regroup: minimum average similarity for insights to share a group, and for an
# ungrouped insight or cluster to fold into an existing group. Recalibrate with real data.
GROUP_THRESHOLD = float(os.environ.get("GROUP_THRESHOLD", 0.80))
# Groups whose centroids are at least this similar get "See also" links to each other.
RELATED_THRESHOLD = float(os.environ.get("RELATED_THRESHOLD", 0.72))

IG_COOKIES_FILE = os.environ.get("IG_COOKIES_FILE")
