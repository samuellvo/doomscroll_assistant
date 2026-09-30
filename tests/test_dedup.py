import numpy as np
import pytest

from doomscroll.dedup import Candidate, place_insights
from doomscroll.gemini import Relation
from doomscroll.store import Insight, Vault


def unit(*xs):
    v = np.array(xs, dtype=np.float32)
    return v / np.linalg.norm(v)


def vec_with_similarity(base, sim):
    """A unit vector whose cosine similarity with `base` is exactly `sim`."""
    ortho = np.zeros_like(base)
    ortho[np.argmin(np.abs(base))] = 1.0
    ortho -= ortho.dot(base) * base
    ortho /= np.linalg.norm(ortho)
    return sim * base + np.sqrt(1 - sim**2) * ortho


@pytest.fixture
def vault():
    base = unit(1, 0, 0, 0)
    existing = Insight(id="a", text="Invalidate on write", kind="tradeoff",
                       topic="system-design/caching", sources=["r1"], group="Invalidation")
    return Vault([], [existing], [], {"a": base}), base


def never_called(pairs):
    assert not pairs, "judge should not be called"
    return []


def test_high_similarity_merges_without_judge(vault):
    v, base = vault
    out = place_insights(v, [Candidate("Invalidate when writing", "tradeoff", "system-design/caching")],
                         np.stack([vec_with_similarity(base, 0.97)]), "r2", never_called)
    assert out[0].action == "merged"
    assert v.insights["a"].sources == ["r1", "r2"]
    assert len(v.insights) == 1


def test_insights_from_the_same_reel_are_never_matched(vault):
    v, base = vault
    # "a" came from r1, so a near-identical insight from r1 is a new idea, not a duplicate.
    out = place_insights(v, [Candidate("x", "tradeoff", "system-design/caching"),
                             Candidate("y", "tradeoff", "system-design/caching")],
                         np.stack([vec_with_similarity(base, 0.97), vec_with_similarity(base, 0.96)]),
                         "r1", never_called)
    assert [o.action for o in out] == ["new", "new"]
    assert v.insights["a"].sources == ["r1"]


def test_low_similarity_is_new(vault):
    v, _ = vault
    out = place_insights(v, [Candidate("Use a CDN", "pattern", "system-design/scalability")],
                         np.stack([unit(0, 1, 0, 0)]), "r2", never_called)
    assert out[0].action == "new"
    assert len(v.insights) == 2


@pytest.mark.parametrize("relation,action", [
    (Relation.same, "merged"),
    (Relation.nuance, "nuance"),
    (Relation.contradicts, "contradicts"),
    (Relation.different, "new"),
])
def test_ambiguous_band_asks_judge(vault, relation, action):
    v, base = vault
    seen = []

    def judge(pairs):
        seen.extend(pairs)
        return [relation] * len(pairs)

    out = place_insights(v, [Candidate("TTL hides bugs", "pitfall", "system-design/other")],
                         np.stack([vec_with_similarity(base, 0.90)]), "r2", judge)
    assert seen == [("TTL hides bugs", "Invalidate on write")]
    assert out[0].action == action

    if action == "nuance":
        child = next(i for i in v.insights.values() if i.id != "a")
        assert child.parent == "a"
        assert child.topic == "system-design/caching"  # inherits parent's topic
        assert child.group == "Invalidation"
    if action == "contradicts":
        other = next(i for i in v.insights.values() if i.id != "a")
        assert other.contradicts == ["a"] and v.insights["a"].contradicts == [other.id]


def test_new_insights_arrive_ungrouped(vault):
    v, base = vault
    place_insights(v, [Candidate("y", "pattern", "system-design/caching")],
                   np.stack([vec_with_similarity(base, 0.80)]), "r2", never_called)
    new = next(i for i in v.insights.values() if i.id != "a")
    assert new.group is None


def test_empty_vault():
    v = Vault([], [], [], {})
    out = place_insights(v, [Candidate("z", "principle", "t")], np.stack([unit(1, 0, 0, 0)]), "r1", never_called)
    assert out[0].action == "new"
