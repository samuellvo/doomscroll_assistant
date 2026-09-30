import numpy as np
import pytest

from doomscroll import config, render
from doomscroll.pipeline import shortcode
from doomscroll.regroup import cluster, regroup
from doomscroll.store import Insight, ReelRecord, Tool, Vault


def unit(*xs):
    v = np.array(xs, dtype=np.float32)
    return v / np.linalg.norm(v)


def test_cluster_separates_distinct_directions():
    vecs = np.stack([unit(1, 0.1, 0), unit(1, 0, 0.1), unit(0, 1, 0.1), unit(0.1, 1, 0), unit(0, 0, 1)])
    labels = cluster(vecs, threshold=0.7)
    assert labels[0] == labels[1]
    assert labels[2] == labels[3]
    assert len(set(labels)) == 3


def make_vault():
    ins = [
        Insight("a", "Invalidate on write", "tradeoff", "system-design/caching", ["r1", "r2"]),
        Insight("b", "Delete the key on update", "tradeoff", "system-design/caching", ["r3"]),
        Insight("c", "Coalesce concurrent misses", "pattern", "system-design/caching", ["r1"]),
        Insight("d", "Breaks with many writers", "pitfall", "system-design/caching", ["r2"], parent="a"),
    ]
    vecs = {"a": unit(1, 0.05, 0), "b": unit(1, 0, 0.05), "c": unit(0, 1, 0), "d": unit(1, 0.2, 0)}
    reels = [ReelRecord(r, f"https://instagram.com/reel/{r}", "someone", f"Title {r}", "s", "t", "", 0.9)
             for r in ("r1", "r2", "r3")]
    tools = [Tool("bun", "Bun", "Fast JS runtime", "dev-tools/runtimes-and-languages", "", ["r1"], ["fast"])]
    return Vault(reels, ins, tools, vecs)


def test_regroup_names_multi_member_groups_and_moves_nuances():
    v = make_vault()
    calls = []

    def namer(topic, groups):
        calls.append((topic, groups))
        return {label: "Invalidation" for label in groups}

    regroup(v, namer, threshold=0.7)
    assert v.insights["a"].group == v.insights["b"].group == "Invalidation"
    assert v.insights["c"].group == "Other"  # singleton
    assert v.insights["d"].group == "Invalidation"  # follows parent
    assert len(calls) == 1 and len(calls[0][1]) == 1


@pytest.fixture
def tmp_vault(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "VAULT", tmp_path)
    monkeypatch.setattr(config, "TAXONOMY_FILE", tmp_path / "taxonomy.md")
    (tmp_path / "taxonomy.md").write_text("- `system-design/caching` — caches\n")
    return tmp_path


def test_render_all(tmp_vault):
    v = make_vault()
    v.insights["a"].group = v.insights["b"].group = v.insights["d"].group = "Invalidation"
    render.render_all(v)

    topic = (tmp_vault / "topics/system-design/caching.md").read_text()
    assert "## Invalidation" in topic
    assert "**Invalidate on write** (×2)" in topic
    assert "  - Nuance: Breaks with many writers" in topic
    assert "(../../reels/r1.md)" in topic
    # Most-repeated insight is listed first within its group.
    assert topic.index("Invalidate on write") < topic.index("Delete the key on update")

    assert "[Bun](tools/bun.md)" in (tmp_vault / "queue.md").read_text()
    inbox = (tmp_vault / "inbox.md").read_text()
    assert "`dev-tools/runtimes-and-languages`" in inbox  # not in taxonomy
    assert "`system-design/caching`" not in inbox


@pytest.mark.parametrize("url,code", [
    ("https://www.instagram.com/reel/DAbC_12-x/?igsh=abc", "DAbC_12-x"),
    ("https://instagram.com/reels/XYZ123/", "XYZ123"),
    ("https://www.instagram.com/someuser/reel/XYZ123/", "XYZ123"),
    ("https://www.instagram.com/p/POST1/", "POST1"),
    ("https://example.com/video", None),
])
def test_shortcode(url, code):
    assert shortcode(url) == code
