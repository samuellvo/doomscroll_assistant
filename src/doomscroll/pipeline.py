"""One reel URL in, updated vault out."""

import re
import tempfile
from pathlib import Path

from . import config, fetch, gemini
from .dedup import Candidate, Outcome, place_insights
from .store import ReelRecord, Tool, Vault, slugify

SHORTCODE = re.compile(r"instagram\.com/(?:[^/]+/)?(?:reels?|p|tv)/([A-Za-z0-9_-]+)")


def shortcode(url: str) -> str | None:
    m = SHORTCODE.search(url)
    return m.group(1) if m else None


def canonical_url(post_id: str, kind: str) -> str:
    # Share links carry tokens (igsh, stkn) that can identify the sharer; never store them.
    return f"https://www.instagram.com/{'reel' if kind == 'reel' else 'p'}/{post_id}/"


def _read(path: Path) -> str:
    return path.read_text() if path.exists() else "(none)"


def process(url: str, note: str = "") -> list[Outcome] | None:
    """Returns None if the reel was already processed."""
    vault = Vault.load()
    code = shortcode(url)
    if code and code in vault.reels:
        return None

    with tempfile.TemporaryDirectory() as tmp:
        reel = fetch.download(url, Path(tmp))
        if reel.id in vault.reels:
            return None
        analysis = gemini.analyze_post(
            [item.path for item in reel.items], reel.kind, reel.caption,
            _read(config.TAXONOMY_FILE), _read(config.FEEDBACK_FILE),
        )

    candidates = [Candidate(i.text, i.kind.value, i.topic) for i in analysis.insights]
    vectors = gemini.embed([c.text for c in candidates])
    outcomes = place_insights(vault, candidates, vectors, reel.id, gemini.judge_pairs)

    for t in analysis.tools:
        slug = slugify(t.name)
        if slug in vault.tools:
            existing = vault.tools[slug]
            if reel.id not in existing.sources:
                existing.sources.append(reel.id)
                existing.mentions.append(t.why_mentioned)
            existing.link = existing.link or t.link
        else:
            vault.tools[slug] = Tool(
                id=slug, name=t.name, what_it_is=t.what_it_is, category=t.category,
                link=t.link, sources=[reel.id], mentions=[t.why_mentioned],
            )

    vault.reels[reel.id] = ReelRecord(
        id=reel.id, url=canonical_url(reel.id, reel.kind), author=reel.author, title=analysis.title,
        summary=analysis.summary, transcript=analysis.transcript, caption=reel.caption,
        confidence=analysis.confidence, note=note, kind=reel.kind, items=len(reel.items),
    )
    vault.save()
    return outcomes
