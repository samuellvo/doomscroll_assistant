"""The vault's source of truth: JSONL records plus an embedding matrix.

Markdown under vault/ is generated from these files by render.py, so edits belong here.
"""

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

import numpy as np

from . import config


@dataclass
class Insight:
    id: str
    text: str
    kind: str
    topic: str
    sources: list[str]  # reel ids; len() is how many times this idea was seen
    group: str | None = None
    parent: str | None = None  # set when this insight is a nuance of another
    contradicts: list[str] = field(default_factory=list)
    created: str = field(default_factory=lambda: date.today().isoformat())


@dataclass
class Tool:
    id: str  # slug of the name
    name: str
    what_it_is: str
    category: str
    link: str
    sources: list[str]
    mentions: list[str]  # what each creator claimed about it
    status: str = "new"  # new | investigating | tried | adopted | dropped
    notes: str = ""
    first_seen: str = field(default_factory=lambda: date.today().isoformat())


@dataclass
class ReelRecord:
    id: str
    url: str
    author: str
    title: str
    summary: str
    transcript: str
    caption: str
    confidence: float
    note: str = ""
    processed: str = field(default_factory=lambda: date.today().isoformat())


def new_id() -> str:
    return uuid.uuid4().hex[:10]


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _read_jsonl(path: Path, cls):
    if not path.exists():
        return []
    return [cls(**json.loads(line)) for line in path.read_text().splitlines() if line.strip()]


def _write_jsonl(path: Path, items) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(asdict(i), ensure_ascii=False) + "\n" for i in items))


class Vault:
    def __init__(self, reels: list[ReelRecord], insights: list[Insight], tools: list[Tool],
                 vectors: dict[str, np.ndarray]):
        self.reels = {r.id: r for r in reels}
        self.insights = {i.id: i for i in insights}
        self.tools = {t.id: t for t in tools}
        self.vectors = vectors  # insight id -> unit vector

    @classmethod
    def load(cls) -> "Vault":
        vectors: dict[str, np.ndarray] = {}
        if config.EMBEDDINGS_FILE.exists():
            npz = np.load(config.EMBEDDINGS_FILE)
            vectors = dict(zip(npz["ids"].tolist(), npz["vectors"]))
        return cls(
            _read_jsonl(config.REELS_FILE, ReelRecord),
            _read_jsonl(config.INSIGHTS_FILE, Insight),
            _read_jsonl(config.TOOLS_FILE, Tool),
            vectors,
        )

    def save(self) -> None:
        _write_jsonl(config.REELS_FILE, self.reels.values())
        _write_jsonl(config.INSIGHTS_FILE, self.insights.values())
        _write_jsonl(config.TOOLS_FILE, sorted(self.tools.values(), key=lambda t: t.id))
        ids = [i for i in self.insights if i in self.vectors]
        matrix = np.stack([self.vectors[i] for i in ids]) if ids else np.zeros((0, config.EMBEDDING_DIM))
        np.savez_compressed(config.EMBEDDINGS_FILE, ids=np.array(ids), vectors=matrix.astype(np.float32))

    def matrix(self, ids: list[str]) -> np.ndarray:
        if not ids:
            return np.zeros((0, config.EMBEDDING_DIM), dtype=np.float32)
        return np.stack([self.vectors[i] for i in ids])
