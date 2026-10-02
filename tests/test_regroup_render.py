import numpy as np
import pytest

import json

from doomscroll import config, export, render
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

    assert "## Ungrouped" in topic  # "c" has no group
    assert topic.index("## Invalidation") < topic.index("## Ungrouped")

    assert "[Bun](tools/bun.md)" in (tmp_vault / "queue.md").read_text()
    inbox = (tmp_vault / "inbox.md").read_text()
    assert "`dev-tools/runtimes-and-languages`" in inbox  # not in taxonomy
    assert "`system-design/caching`" not in inbox
    assert "[system-design/caching](topics/system-design/caching.md): 1" in inbox


@pytest.mark.parametrize("url,code", [
    ("https://www.instagram.com/reel/DAbC_12-x/?igsh=abc", "DAbC_12-x"),
    ("https://instagram.com/reels/XYZ123/", "XYZ123"),
    ("https://www.instagram.com/someuser/reel/XYZ123/", "XYZ123"),
    ("https://www.instagram.com/p/POST1/", "POST1"),
    ("https://example.com/video", None),
])
def test_shortcode(url, code):
    assert shortcode(url) == code


def test_export_app_json(tmp_vault):
    v = make_vault()
    v.insights["a"].group = v.insights["b"].group = v.insights["d"].group = "Invalidation"
    render.render_all(v)
    data = json.loads((tmp_vault / "app.json").read_text())

    assert data["schema"] == export.SCHEMA
    assert data["stats"] == {"reels": 3, "insights": 4, "tools": 1, "ungrouped": 1}
    (topic,) = data["topics"]
    assert (topic["title"], topic["area"], topic["ungroupedCount"]) == ("Caching", "System Design", 1)
    assert [g["name"] for g in topic["groups"]] == ["Invalidation", None]  # Ungrouped last
    first = topic["groups"][0]["insights"][0]
    assert first["text"] == "Invalidate on write" and first["count"] == 2
    assert first["nuances"] == [{"text": "Breaks with many writers", "count": 1}]
    r1 = next(r for r in data["reels"] if r["id"] == "r1")
    assert set(r1["insights"]) == {"a", "c"} and r1["tools"] == ["bun"]


def test_post_kinds_render_and_export(tmp_vault):
    v = make_vault()
    v.reels["r2"].kind, v.reels["r2"].items = "carousel", 5
    render.render_all(v)
    assert "**Type:** Carousel · 5 slides" in (tmp_vault / "reels/r2.md").read_text()
    assert "**Type:** Reel" in (tmp_vault / "reels/r1.md").read_text()
    data = json.loads((tmp_vault / "app.json").read_text())
    r2 = next(r for r in data["reels"] if r["id"] == "r2")
    assert (r2["kind"], r2["items"]) == ("carousel", 5)


@pytest.mark.parametrize("kind,path", [("reel", "reel"), ("image", "p"), ("carousel", "p")])
def test_canonical_url_matches_post_kind(kind, path):
    from doomscroll.pipeline import canonical_url
    assert canonical_url("ABC", kind) == f"https://www.instagram.com/{path}/ABC/"
