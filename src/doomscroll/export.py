"""Export the vault as one denormalized JSON file for the web app (vault/app.json).

The web app is read-only and loads this single file, so everything a screen needs is
precomputed here: groups in display order, nuance/conflict text inline, and reverse indexes
from reels to their insights and tools. Bump SCHEMA when the shape changes.
"""

import json
from collections import defaultdict
from datetime import date

from . import config
from .render import related_groups, title_case
from .store import Insight, Vault

SCHEMA = 1


def _insight(vault: Vault, ins: Insight, children: dict[str, list[Insight]]) -> dict:
    return {
        "id": ins.id,
        "text": ins.text,
        "kind": ins.kind,
        "count": len(ins.sources),
        "sources": ins.sources,
        "created": ins.created,
        "nuances": [{"text": c.text, "count": len(c.sources)}
                    for c in sorted(children[ins.id], key=lambda c: -len(c.sources))],
        "conflicts": [vault.insights[c].text for c in ins.contradicts if c in vault.insights],
    }


def _topic(vault: Vault, path: str, insights: list[Insight], children: dict[str, list[Insight]]) -> dict:
    top = [i for i in insights if i.parent is None]
    groups: dict[str | None, list[Insight]] = defaultdict(list)
    for i in top:
        groups[i.group].append(i)
    related = related_groups(vault, groups)
    order = sorted(groups, key=lambda g: (g is None, -sum(len(i.sources) for i in groups[g])))
    area, _, leaf = path.partition("/")
    return {
        "path": path,
        "title": title_case(leaf or area),
        "area": title_case(area),
        "insightCount": len(insights),
        "reelCount": len({r for i in insights for r in i.sources}),
        "ungroupedCount": len(groups.get(None, [])),
        "groups": [
            {
                "name": g,
                "pinned": bool(g and vault.groups.get((path, g)) and vault.groups[(path, g)].pinned),
                "related": related.get(g, []) if g else [],
                "insights": [_insight(vault, i, children) for i in sorted(groups[g], key=lambda i: -len(i.sources))],
            }
            for g in order
        ],
    }


def build(vault: Vault) -> dict:
    children: dict[str, list[Insight]] = defaultdict(list)
    for i in vault.insights.values():
        if i.parent:
            children[i.parent].append(i)

    by_topic: dict[str, list[Insight]] = defaultdict(list)
    for i in vault.insights.values():
        by_topic[i.topic].append(i)

    reel_insights: dict[str, list[str]] = defaultdict(list)
    for i in vault.insights.values():
        for r in i.sources:
            reel_insights[r].append(i.id)
    reel_tools: dict[str, list[str]] = defaultdict(list)
    for t in vault.tools.values():
        for r in t.sources:
            reel_tools[r].append(t.id)

    return {
        "schema": SCHEMA,
        "generated": date.today().isoformat(),
        "stats": {
            "reels": len(vault.reels),
            "insights": len(vault.insights),
            "tools": len(vault.tools),
            "ungrouped": sum(1 for i in vault.insights.values() if i.parent is None and i.group is None),
        },
        "topics": [_topic(vault, p, ins, children) for p, ins in sorted(by_topic.items())],
        "tools": [
            {
                "id": t.id,
                "name": t.name,
                "whatItIs": t.what_it_is,
                "category": t.category,
                "link": t.link,
                "status": t.status,
                "notes": t.notes,
                "firstSeen": t.first_seen,
                "mentions": [{"reel": r, "claim": c} for r, c in zip(t.sources, t.mentions)],
            }
            for t in sorted(vault.tools.values(), key=lambda t: (-len(t.sources), t.name.lower()))
        ],
        "reels": [
            {
                "id": r.id,
                "url": r.url,
                "author": r.author,
                "title": r.title,
                "summary": r.summary,
                "transcript": r.transcript,
                "note": r.note,
                "saved": r.processed,
                "insights": reel_insights.get(r.id, []),
                "tools": reel_tools.get(r.id, []),
            }
            for r in sorted(vault.reels.values(), key=lambda r: r.processed, reverse=True)
        ],
    }


def write(vault: Vault) -> None:
    (config.VAULT / "app.json").write_text(json.dumps(build(vault), ensure_ascii=False, indent=1) + "\n")
