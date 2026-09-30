"""One test per regroup case: same, grew, split, merge, fold by meaning, new, singletons, pinned."""

import numpy as np
import pytest

from doomscroll.regroup import STICKINESS, regroup
from doomscroll.store import Group, Insight, Vault

DIM = 8
T = "system-design/caching"


def near(axis: int, j: int = 0) -> np.ndarray:
    """A unit vector close to `axis`; j nudges it slightly so members aren't identical."""
    v = np.zeros(DIM, dtype=np.float32)
    v[axis] = 1.0
    v[DIM - 1] += 0.05 * j
    return v / np.linalg.norm(v)


def build(spec, pinned=()):
    """spec: [(id, axis, group)]; returns a Vault with those top-level insights in topic T."""
    insights = [Insight(i, f"text {i}", "pattern", T, ["r"], group=g) for i, _, g in spec]
    vectors = {i: near(axis, n) for n, (i, axis, _) in enumerate(spec)}
    groups = [Group(T, g, pinned=g in pinned) for g in {g for _, _, g in spec if g}]
    return Vault([], insights, [], vectors, groups)


class Namer:
    def __init__(self, names=None):
        self.calls, self.names = [], names or {}

    def __call__(self, topic, groups, avoid):
        self.calls.append((groups, avoid))
        return {label: self.names.get(len(self.calls), f"New {label}") for label in groups}


def group_of(v, *ids):
    return [v.insights[i].group for i in ids]


def test_same_group_keeps_its_name_without_naming_calls():
    v = build([("a1", 0, "A"), ("a2", 0, "A"), ("a3", 0, "A")])
    namer = Namer()
    s = regroup(v, namer, threshold=0.8)[T]
    assert group_of(v, "a1", "a2", "a3") == ["A"] * 3
    assert namer.calls == [] and s.kept == 1


def test_grown_group_absorbs_new_insights():
    v = build([("a1", 0, "A"), ("a2", 0, "A"), ("n1", 0, None)])
    regroup(v, Namer(), threshold=0.8)
    assert group_of(v, "n1") == ["A"]


def test_split_larger_part_keeps_name_smaller_part_named_distinctly():
    v = build([("a1", 0, "A"), ("a2", 0, "A"), ("a3", 0, "A"), ("a4", 1, "A"),
               ("n1", 1, None), ("n2", 1, None)])
    namer = Namer()
    regroup(v, namer, threshold=0.8)
    assert group_of(v, "a1", "a2", "a3") == ["A"] * 3
    split = group_of(v, "a4", "n1", "n2")
    assert len(set(split)) == 1 and split[0] != "A"
    (groups, avoid), = namer.calls
    assert list(avoid.values()) == [["A"]]  # asked to stay distinct from A


def test_merge_takes_larger_name_and_drops_the_other():
    v = build([("a1", 0, "A"), ("a2", 0, "A"), ("a3", 0, "A"), ("b1", 0, "B"), ("b2", 0, "B")])
    regroup(v, Namer(), threshold=0.8)
    assert set(group_of(v, "a1", "a2", "a3", "b1", "b2")) == {"A"}
    assert (T, "B") not in v.groups


def test_new_cluster_similar_to_existing_group_folds_in():
    # P is pinned, so it's outside the clustering pool; the new pair must fold in by meaning.
    v = build([("p1", 0, "P"), ("p2", 0, "P"), ("n1", 0, None), ("n2", 0, None)], pinned={"P"})
    namer = Namer()
    s = regroup(v, namer, threshold=0.8)[T]
    assert group_of(v, "n1", "n2") == ["P", "P"]
    assert namer.calls == [] and s.folded == 1


def test_genuinely_new_cluster_gets_named_with_neighbours_as_context():
    v = build([("a1", 0, "A"), ("a2", 0, "A"), ("n1", 2, None), ("n2", 2, None)])
    namer = Namer()
    s = regroup(v, namer, threshold=0.8)[T]
    assert group_of(v, "n1", "n2")[0].startswith("New")
    assert s.new == 1 and namer.calls[0][1] == {next(iter(namer.calls[0][0])): ["A"]}


def test_name_collisions_get_a_suffix():
    v = build([("a1", 0, "A"), ("a2", 0, "A"), ("n1", 2, None), ("n2", 2, None)])
    regroup(v, Namer({1: "A"}), threshold=0.8)
    assert group_of(v, "n1") == ["A (2)"]


def test_singletons_join_a_close_group_or_stay_ungrouped():
    v = build([("a1", 0, "A"), ("a2", 0, "A"), ("close", 0, None), ("far", 3, None)])
    # "close" clusters with A directly; add a lone far one too.
    s = regroup(v, Namer(), threshold=0.8)[T]
    assert group_of(v, "close", "far") == ["A", None]
    assert s.ungrouped == 1


def test_lone_singleton_near_pinned_group_joins_it():
    v = build([("p1", 0, "P"), ("p2", 0, "P"), ("n1", 0, None)], pinned={"P"})
    regroup(v, Namer(), threshold=0.8)
    assert group_of(v, "n1") == ["P"]


def test_pinned_groups_are_never_reclustered_or_renamed():
    # Claude deliberately grouped two dissimilar insights; the regroup must respect that.
    v = build([("p1", 0, "Picked by Claude"), ("p2", 3, "Picked by Claude")], pinned={"Picked by Claude"})
    namer = Namer()
    regroup(v, namer, threshold=0.8)
    assert group_of(v, "p1", "p2") == ["Picked by Claude"] * 2
    assert v.groups[(T, "Picked by Claude")].pinned
    assert namer.calls == []


def unit(v):
    v = np.asarray(v, dtype=np.float32)
    return v / np.linalg.norm(v)


def test_stickiness_keeps_borderline_insight_in_its_old_group():
    # A sits on axis 0; a new pair sits on u, 53 degrees away. "edge" is between them, only
    # slightly closer to u, by less than STICKINESS, so it stays in A.
    u = unit([0.6, 0, 0.8, 0, 0, 0, 0, 0])
    v = build([("a1", 0, "A"), ("a2", 0, "A"), ("a3", 0, "A")])
    for k, jitter in enumerate((0.02, -0.02)):
        v.insights[f"n{k}"] = Insight(f"n{k}", "n", "pattern", T, ["r"])
        v.vectors[f"n{k}"] = unit(u + np.eye(DIM, dtype=np.float32)[3] * jitter)
    v.insights["edge"] = Insight("edge", "edge", "pattern", T, ["r"], group="A")
    v.vectors["edge"] = unit(0.95 * near(0) + 1.05 * u)
    to_a, to_u = float(v.vectors["edge"] @ near(0)), float(v.vectors["edge"] @ u)
    assert 0.8 < to_a < to_u < to_a + STICKINESS

    regroup(v, Namer(), threshold=0.8)
    assert group_of(v, "edge") == ["A"]


def test_insight_clearly_closer_to_new_group_moves():
    v = build([("a1", 0, "A"), ("a2", 0, "A"), ("a3", 0, "A"), ("mover", 2, "A"),
               ("n1", 2, None), ("n2", 2, None)])
    regroup(v, Namer(), threshold=0.8)
    assert group_of(v, "mover")[0] != "A"


def test_nuances_follow_parent_and_registry_tracks_groups():
    v = build([("a1", 0, "A"), ("a2", 0, "A")])
    v.insights["kid"] = Insight("kid", "nuance", "pitfall", T, ["r"], parent="a1")
    regroup(v, Namer(), threshold=0.8)
    assert group_of(v, "kid") == ["A"]
    assert set(v.groups) == {(T, "A")}
