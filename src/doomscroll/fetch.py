"""Download an Instagram post (reel, single image, or carousel) and its metadata with yt-dlp."""

import urllib.request
from dataclasses import dataclass
from pathlib import Path

from yt_dlp import YoutubeDL

from . import config

# yt-dlp is video-first: image posts and image slides have no formats. With this option it
# still returns their metadata, and `thumbnail` is the full uncropped image (the other
# thumbnails include square crops).
BASE_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": False,
    "ignore_no_formats_error": True,
}
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Safari/605.1.15"


@dataclass
class MediaItem:
    path: Path
    kind: str  # "video" | "image"


@dataclass
class Post:
    id: str
    url: str
    kind: str  # "reel" | "image" | "carousel"
    items: list[MediaItem]
    author: str
    caption: str


def _opts(dest: Path) -> dict:
    opts = {
        **BASE_OPTS,
        "outtmpl": str(dest / "%(id)s.%(ext)s"),
        # Prefer a single muxed mp4; fall back to merging streams (needs ffmpeg).
        "format": "b[ext=mp4]/bv*+ba/b",
        "merge_output_format": "mp4",
    }
    if config.IG_COOKIES_FILE:
        opts["cookiefile"] = config.IG_COOKIES_FILE
    return opts


def _download_image(url: str, path: Path) -> Path:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as res:
        path.write_bytes(res.read())
    return path


def _fetch_item(ydl: YoutubeDL, entry: dict, dest: Path, index: int) -> MediaItem:
    if entry.get("formats"):
        try:
            done = ydl.process_ie_result(entry, download=True)
            return MediaItem(Path(ydl.prepare_filename(done)).with_suffix(".mp4"), "video")
        except Exception:
            if not entry.get("thumbnail"):
                raise
            # Fall back to the video's cover frame rather than losing the slide.
    if not entry.get("thumbnail"):
        raise RuntimeError(f"Item {index + 1} has neither video nor image")
    return MediaItem(_download_image(entry["thumbnail"], dest / f"{index:02d}.jpg"), "image")


def download(url: str, dest: Path) -> Post:
    with YoutubeDL(_opts(dest)) as ydl:
        info = ydl.extract_info(url, download=False)
        entries = list(info.get("entries") or [])
        items = [_fetch_item(ydl, e, dest, i) for i, e in enumerate(entries or [info])]

    if entries:
        kind = "carousel"
    else:
        kind = "reel" if items[0].kind == "video" else "image"

    return Post(
        id=info["id"],
        url=info.get("webpage_url", url),
        kind=kind,
        items=items,
        author=info.get("uploader") or info.get("channel") or "unknown",
        caption=info.get("description") or "",
    )
