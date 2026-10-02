from doomscroll import config
from doomscroll.store import ReelRecord, Vault


def test_jsonl_round_trip_survives_unicode_line_separators(tmp_path, monkeypatch):
    for name in ("REELS_FILE", "INSIGHTS_FILE", "TOOLS_FILE", "GROUPS_FILE", "EMBEDDINGS_FILE"):
        monkeypatch.setattr(config, name, tmp_path / getattr(config, name).name)
    caption = "line one\u2028line two\u2029para\x85next\nreal newline"
    v = Vault([ReelRecord("r1", "u", "a", "t", "s", "tr", caption, 0.9, kind="carousel", items=5)], [], [], {})
    v.save()
    loaded = Vault.load().reels["r1"]
    assert loaded.caption == caption and (loaded.kind, loaded.items) == ("carousel", 5)
