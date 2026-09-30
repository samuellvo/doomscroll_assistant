"""Decide whether each new insight is a duplicate, a nuance, a contradiction, or new.

Pure logic: embeddings and the LLM judge are passed in, so this is unit-testable offline.
"""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from . import config
from .gemini import Relation
from .store import Insight, Vault, new_id

Judge = Callable[[list[tuple[str, str]]], list[Relation]]


@dataclass
class Candidate:
    text: str
    kind: str
    topic: str


@dataclass
class Outcome:
    text: str
    action: str  # merged | nuance | contradicts | new
    target: str | None  # the existing insight id involved, if any
    similarity: float


def _best_match(vault: Vault, vec: np.ndarray, exclude: set[str]) -> tuple[str | None, float]:
    ids = [i for i in vault.insights if i in vault.vectors and i not in exclude]
    if not ids:
        return None, 0.0
    sims = vault.matrix(ids) @ vec
    j = int(np.argmax(sims))
    return ids[j], float(sims[j])


def _add(vault: Vault, c: Candidate, vec: np.ndarray, reel_id: str, exclude: set[str], **kw) -> Insight:
    ins = Insight(id=new_id(), text=c.text, kind=c.kind, topic=c.topic, sources=[reel_id], **kw)
    vault.insights[ins.id] = ins
    exclude.add(ins.id)
    vault.vectors[ins.id] = vec
    return ins


def place_insights(vault: Vault, candidates: list[Candidate], vectors: np.ndarray,
                   reel_id: str, judge: Judge) -> list[Outcome]:
    outcomes: list[Outcome] = []
    ambiguous: list[tuple[Candidate, np.ndarray, str, float]] = []
    # A reel rarely repeats itself, so its own insights are never duplicate candidates.
    same_reel = {i for i, ins in vault.insights.items() if reel_id in ins.sources}

    for c, vec in zip(candidates, vectors):
        match, sim = _best_match(vault, vec, same_reel)
        if match and sim >= config.DUPLICATE_THRESHOLD:
            existing = vault.insights[match]
            if reel_id not in existing.sources:
                existing.sources.append(reel_id)
            outcomes.append(Outcome(c.text, "merged", match, sim))
        elif match and sim >= config.AMBIGUOUS_THRESHOLD:
            ambiguous.append((c, vec, match, sim))
        else:
            _add(vault, c, vec, reel_id, same_reel)  # Ungrouped until the weekly regroup or Claude
            outcomes.append(Outcome(c.text, "new", None, sim))

    relations = judge([(c.text, vault.insights[m].text) for c, _, m, _ in ambiguous])
    for (c, vec, match, sim), rel in zip(ambiguous, relations):
        existing = vault.insights[match]
        if rel == Relation.same:
            if reel_id not in existing.sources:
                existing.sources.append(reel_id)
            outcomes.append(Outcome(c.text, "merged", match, sim))
        elif rel == Relation.nuance:
            # Nuances hang off their parent, so they inherit its topic and group.
            parent = vault.insights[existing.parent] if existing.parent else existing
            c.topic = parent.topic
            _add(vault, c, vec, reel_id, same_reel, parent=parent.id, group=parent.group)
            outcomes.append(Outcome(c.text, "nuance", parent.id, sim))
        elif rel == Relation.contradicts:
            ins = _add(vault, c, vec, reel_id, same_reel, contradicts=[match])
            existing.contradicts.append(ins.id)
            outcomes.append(Outcome(c.text, "contradicts", match, sim))
        else:
            _add(vault, c, vec, reel_id, same_reel)
            outcomes.append(Outcome(c.text, "new", None, sim))

    return outcomes
