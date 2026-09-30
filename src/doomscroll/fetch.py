"""Download a reel and its metadata with yt-dlp."""

from dataclasses import dataclass
from pathlib import Path

from yt_dlp import YoutubeDL

from . import config


@dataclass
class Reel:
    id: str
    url: str
    video_path: Path
    author: str
    caption: str
    duration: float | None


def download(url: str, dest: Path) -> Reel:
    opts = {
        "outtmpl": str(dest / "%(id)s.%(ext)s"),
        # Prefer a single muxed mp4; fall back to merging streams (needs ffmpeg).
        "format": "b[ext=mp4]/bv*+ba/b",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }
    if config.IG_COOKIES_FILE:
        opts["cookiefile"] = config.IG_COOKIES_FILE

    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = Path(ydl.prepare_filename(info)).with_suffix(".mp4")

    return Reel(
        id=info["id"],
        url=info.get("webpage_url", url),
        video_path=path,
        author=info.get("uploader") or info.get("channel") or "unknown",
        caption=info.get("description") or "",
        duration=info.get("duration"),
    )
