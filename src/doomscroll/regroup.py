"""Weekly regroup that keeps group identity stable across runs.

New insights arrive Ungrouped (dedup.py). Each week, per topic:
1. Insights in pinned groups are left alone.
2. Everything else is clustered by similarity (average linkage on cosine distance).
3. Check 1, shared members: a cluster inherits the name of the old group it mostly came from.
4. Check 2, similar meaning: an unmatched cluster folds into an existing group with a similar
   centroid, or becomes a new group, named with its nearest neighbours as "be distinct" context.
5. Singletons join the closest group if similar enough; otherwise they stay Ungrouped.
6. Stickiness: an insight only leaves its old group if it's clearly closer to its new one.
"""

from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage

from . import config
from .store import Group, Vault

# Check 1: a cluster inherits an old name if at least this share of the cluster came from that
# group AND at least this share of that group landed in the cluster.
MATCH_SHARE = 0.5
# An insight stays in its old group unless the new group's centroid is this much closer.
STICKINESS = 0.05
NEIGHBOURS = 3

# namer(topic, {label: [insight texts]}, {label: [neighbour group names to stay distinct from]})
Namer = Callable[[str, dict[int, list[str]], dict[int, list[str]]], dict[int, str]]


@dataclass
class TopicSummary:
    kept: int = 0  # clusters that inherited an existing name
    folded: int = 0  # clusters merged into an existing group by meaning
    new: int = 0  # newly named groups
    ungrouped: int = 0  # insights left Ungrouped


def cluster(vectors: np.ndarray, threshold: float) -> list[int]:
    """Labels from average-linkage clustering; groups have mean pairwise similarity >= threshold."""
    if len(vectors) < 2:
        return list(range(len(vectors)))
    labels = fcluster(linkage(vectors, method="average", metric="cosine"), t=1 - threshold, criterion="distance")
    return [int(label) - 1 for label in labels]


def _regroup_topic(vault: Vault, topic: str, ids: list[str], namer: Namer, threshold: float) -> TopicSummary:
    summary = TopicSummary()
    old = {i: vault.insights[i].group for i in ids}
    pinned = vault.pinned(topic)
    fixed = [i for i in ids if old[i] in pinned]
    pool = [i for i in ids if old[i] not in pinned]

    clusters: dict[int, list[str]] = defaultdict(list)
    for i, label in zip(pool, cluster(vault.matrix(pool), threshold)):
        clusters[label].append(i)
    multi = {label: m for label, m in clusters.items() if len(m) > 1}
    singles = [m[0] for m in clusters.values() if len(m) == 1]

    # Check 1: shared members. Biggest overlaps claim names first; each name is used once.
    old_sizes = Counter(old[i] for i in pool if old[i])
    candidates = []
    for label, members in multi.items():
        for name, n in Counter(old[i] for i in members if old[i]).items():
            if n / len(members) >= MATCH_SHARE and n / old_sizes[name] >= MATCH_SHARE:
                candidates.append((n, label, name))
    names: dict[int, str] = {}
    for _, label, name in sorted(candidates, reverse=True):
        if label not in names and name not in names.values():
            names[label] = name
            summary.kept += 1

    # Check 2: similar meaning, against pinned groups and the names kept above.
    def group_members() -> dict[str, list[str]]:
        members: dict[str, list[str]] = defaultdict(list)
        for i in fixed:
            members[old[i]].append(i)
        for label, name in names.items():
            members[name].extend(multi[label])
        return members

    centroids = {name: vault.centroid(m) for name, m in group_members().items()}
    to_name: dict[int, list[str]] = {}
    avoid: dict[int, list[str]] = {}
    for label, members in multi.items():
        if label in names:
            continue
        c = vault.centroid(members)
        ranked = sorted(((float(c @ v), name) for name, v in centroids.items()), reverse=True)
        if ranked and ranked[0][0] >= threshold:
            names[label] = ranked[0][1]
            summary.folded += 1
        else:
            to_name[label] = [vault.insights[i].text for i in members]
            avoid[label] = [name for _, name in ranked[:NEIGHBOURS]]

    if to_name:
        proposed = namer(topic, to_name, avoid)
        used = set(names.values()) | pinned
        for label in to_name:
            base = name = (proposed.get(label) or "Unnamed group").strip()
            k = 2
            while name in used:
                name, k = f"{base} ({k})", k + 1
            names[label] = name
            used.add(name)
            summary.new += 1

    new_group: dict[str, str | None] = {i: names[label] for label, m in multi.items() for i in m}

    # Singletons join the closest group if it's similar enough; otherwise stay Ungrouped.
    centroids = {name: vault.centroid(m) for name, m in group_members().items()}
    for i in singles:
        v = vault.vectors[i]
        best = max(centroids, key=lambda name: float(v @ centroids[name]), default=None)
        new_group[i] = best if best and float(v @ centroids[best]) >= threshold else None

    # Stickiness: don't move an insight out of a surviving group unless the new home is clearly
    # closer. Centroids exclude the insight itself, or it would always look closest to where it is.
    final: dict[str, list[str]] = defaultdict(list)
    for i in fixed:
        final[old[i]].append(i)
    for i, name in new_group.items():
        if name:
            final[name].append(i)

    def similarity(i: str, name: str | None) -> float | None:
        others = [j for j in final.get(name, []) if j != i]
        return float(vault.vectors[i] @ vault.centroid(others)) if others else None

    for i in pool:
        before, after = old[i], new_group[i]
        if not before or before == after:
            continue
        stay = similarity(i, before)
        if stay is None:  # the old group didn't survive
            continue
        move = similarity(i, after) if after else None
        if stay >= (move if move is not None else threshold) - STICKINESS:
            new_group[i] = before

    for i, name in new_group.items():
        vault.insights[i].group = name
    summary.ungrouped = sum(1 for name in new_group.values() if name is None)
    return summary


def regroup(vault: Vault, namer: Namer, threshold: float = config.GROUP_THRESHOLD) -> dict[str, TopicSummary]:
    by_topic: dict[str, list[str]] = defaultdict(list)
    for ins in vault.insights.values():
        if ins.parent is None and ins.id in vault.vectors:
            by_topic[ins.topic].append(ins.id)

    summaries = {topic: _regroup_topic(vault, topic, ids, namer, threshold) for topic, ids in by_topic.items()}

    # Nuances follow their parent.
    for ins in vault.insights.values():
        if ins.parent and ins.parent in vault.insights:
            ins.group = vault.insights[ins.parent].group

    # Keep the registry in sync: one entry per group in use, preserving pinned flags.
    in_use = {(i.topic, i.group) for i in vault.insights.values() if i.group}
    vault.groups = {key: vault.groups.get(key) or Group(*key) for key in in_use}
    return summaries
