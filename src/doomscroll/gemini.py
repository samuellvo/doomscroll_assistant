"""All Gemini calls: video analysis, embeddings, duplicate judging, group naming."""

import time
from enum import Enum
from pathlib import Path

import numpy as np
from google import genai
from google.genai import errors
from google.genai import types
from pydantic import BaseModel, Field

from . import config

_client: genai.Client | None = None


def client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client()  # reads GEMINI_API_KEY
    return _client


RETRYABLE = {429, 500, 503}


def generate(models: list[str], contents, schema) -> object:
    """generate_content with structured output, falling back across models when overloaded."""
    cfg = types.GenerateContentConfig(response_mime_type="application/json", response_schema=schema)
    last: Exception | None = None
    for attempt in range(2):
        for model in models:
            try:
                return client().models.generate_content(model=model, contents=contents, config=cfg).parsed
            except errors.APIError as e:
                if e.code not in RETRYABLE:
                    raise
                print(f"  {model}: {e.code}, trying next model")
                last = e
        time.sleep(15)
    raise RuntimeError("All Gemini models are unavailable right now") from last


# ---------- structured output schemas ----------

class InsightKind(str, Enum):
    principle = "principle"
    pattern = "pattern"
    pitfall = "pitfall"
    tradeoff = "tradeoff"
    benchmark = "benchmark"
    example = "example"


class ExtractedInsight(BaseModel):
    text: str = Field(description="One self-contained idea, reworded neutrally in one sentence.")
    kind: InsightKind
    topic: str = Field(description="Topic path from the taxonomy, e.g. 'system-design/caching'.")


class ExtractedTool(BaseModel):
    name: str
    what_it_is: str = Field(description="One sentence.")
    category: str = Field(description="Tool category path from the taxonomy, e.g. 'dev-tools/databases'.")
    link: str = Field(description="Official URL or handle if shown or said; empty string if unknown.")
    why_mentioned: str = Field(description="The claim or pitch the creator made about it.")


class ReelAnalysis(BaseModel):
    title: str
    summary: str = Field(description="2-3 sentences.")
    transcript: str = Field(description="Verbatim speech plus any important on-screen text.")
    insights: list[ExtractedInsight]
    tools: list[ExtractedTool]
    confidence: float = Field(description="0-1: how confident you are in the topic/category choices.")


class Relation(str, Enum):
    same = "same"
    nuance = "nuance"
    contradicts = "contradicts"
    different = "different"


class PairJudgement(BaseModel):
    pair: int
    relation: Relation


class GroupName(BaseModel):
    group: int
    name: str


# ---------- calls ----------

ANALYZE_PROMPT = """You are cataloguing short-form videos for a software engineer's knowledge base.

Watch the video (frames and audio) and use the caption for context.
- Break the teaching content into atomic insights: one idea each, reworded neutrally so that
  the same tip from two creators would read almost identically. Skip filler and hype.
- List every concrete tool, library, product, or service recommended or demoed.
- Choose topics/categories from the taxonomy below. Only invent a new path if nothing fits;
  keep new paths short, lowercase, and hyphenated.
- Follow the user's feedback rules; they override your defaults.

## Taxonomy
{taxonomy}

## Feedback rules
{feedback}

## Caption
{caption}
"""


def analyze_video(video_path: Path, caption: str, taxonomy: str, feedback: str) -> ReelAnalysis:
    c = client()
    f = c.files.upload(file=video_path)
    while f.state and f.state.name == "PROCESSING":
        time.sleep(2)
        f = c.files.get(name=f.name)
    if f.state and f.state.name == "FAILED":
        raise RuntimeError(f"Gemini could not process {video_path.name}")

    try:
        prompt = ANALYZE_PROMPT.format(taxonomy=taxonomy, feedback=feedback, caption=caption or "(none)")
        return generate(config.ANALYSIS_MODELS, [f, prompt], ReelAnalysis)
    finally:
        c.files.delete(name=f.name)


def embed(texts: list[str]) -> np.ndarray:
    """Unit-normalized embeddings, shape (len(texts), EMBEDDING_DIM)."""
    if not texts:
        return np.zeros((0, config.EMBEDDING_DIM), dtype=np.float32)
    resp = client().models.embed_content(
        model=config.EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(
            task_type="SEMANTIC_SIMILARITY",
            output_dimensionality=config.EMBEDDING_DIM,
        ),
    )
    vecs = np.array([e.values for e in resp.embeddings], dtype=np.float32)
    # Truncated-dimension embeddings aren't normalized, so do it ourselves.
    return vecs / np.linalg.norm(vecs, axis=1, keepdims=True)


JUDGE_PROMPT = """For each numbered pair, decide how NEW relates to EXISTING:
- same: the same idea, just worded differently
- nuance: NEW refines, qualifies, or adds a condition to EXISTING
- contradicts: NEW disagrees with EXISTING
- different: related topic but a distinct idea

{pairs}
"""


def judge_pairs(pairs: list[tuple[str, str]]) -> list[Relation]:
    """Batch all ambiguous pairs from one reel into a single call to save free-tier quota."""
    if not pairs:
        return []
    listing = "\n".join(f"{i}. NEW: {new}\n   EXISTING: {old}" for i, (new, old) in enumerate(pairs))
    judgements = generate(config.LIGHT_MODELS, JUDGE_PROMPT.format(pairs=listing), list[PairJudgement])
    by_index = {j.pair: j.relation for j in judgements}
    # If the model skips a pair, treat it as distinct rather than silently merging.
    return [by_index.get(i, Relation.different) for i in range(len(pairs))]


def name_groups(topic: str, groups: dict[int, list[str]], avoid: dict[int, list[str]]) -> dict[int, str]:
    def block(g: int, texts: list[str]) -> str:
        lines = [f"Group {g}:"] + [f"- {t}" for t in texts[:8]]
        if avoid.get(g):
            lines.append("Must be clearly distinct from existing groups: " + ", ".join(avoid[g]))
        return "\n".join(lines)

    listing = "\n\n".join(block(g, texts) for g, texts in groups.items())
    prompt = (
        f"These are clusters of insights under the topic '{topic}'. Give each group a short "
        f"(2-5 word) section heading that describes what its insights have in common. "
        f"Where existing group names are listed, choose a heading that reads as a different "
        f"subject from them, not a synonym.\n\n{listing}"
    )
    return {g.group: g.name for g in generate(config.LIGHT_MODELS, prompt, list[GroupName])}


def list_models() -> list[str]:
    return [m.name for m in client().models.list()]
