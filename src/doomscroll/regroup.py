"""Periodically re-cluster each topic's insights by similarity and name the clusters.

New insights are attached to their nearest group as they arrive (see dedup.py); this pass
fixes drift, splits groups that got too broad, and names groups that are still unnamed.
"""

from collections import defaultdict

import numpy as np

from . import config
from .store import Vault

OTHER = "Other"


def cluster(vectors: np.ndarray, threshold: float) -> list[int]:
    """Average-linkage agglomerative clustering on cosine similarity.

    O(n^3) in the worst case, which is fine for the few hundred insights a topic will hold.
    """
    n = len(vectors)
    clusters = [[i] for i in range(n)]
    sim = vectors @ vectors.T
    while len(clusters) > 1:
        best, pair = -1.0, None
        for a in range(len(clusters)):
            for b in range(a + 1, len(clusters)):
                s = sim[np.ix_(clusters[a], clusters[b])].mean()
                if s > best:
                    best, pair = s, (a, b)
        if best < threshold:
            break
        a, b = pair
        clusters[a] += clusters.pop(b)
    labels = [0] * n
    for label, members in enumerate(clusters):
        for i in members:
            labels[i] = label
    return labels


def regroup(vault: Vault, namer, threshold: float = config.GROUP_THRESHOLD) -> dict[str, int]:
    """Returns {topic: number of named groups}. `namer(topic, {label: [texts]}) -> {label: name}`."""
    by_topic: dict[str, list[str]] = defaultdict(list)
    for ins in vault.insights.values():
        if ins.parent is None and ins.id in vault.vectors:
            by_topic[ins.topic].append(ins.id)

    summary = {}
    for topic, ids in by_topic.items():
        labels = cluster(vault.matrix(ids), threshold)
        members: dict[int, list[str]] = defaultdict(list)
        for i, label in zip(ids, labels):
            members[label].append(i)

        # Singletons go under "Other" rather than getting a one-item heading.
        real = {label: m for label, m in members.items() if len(m) > 1}
        names = namer(topic, {label: [vault.insights[i].text for i in m] for label, m in real.items()}) if real else {}

        for label, m in members.items():
            name = names.get(label, OTHER) if label in real else OTHER
            for i in m:
                vault.insights[i].group = name
        summary[topic] = len(real)

    # Nuances follow their parent.
    for ins in vault.insights.values():
        if ins.parent and ins.parent in vault.insights:
            ins.group = vault.insights[ins.parent].group
    return summary
