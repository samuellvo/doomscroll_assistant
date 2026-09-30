"""CLI: python -m doomscroll {process,render,regroup,models}"""

import argparse
import sys

from . import gemini
from .regroup import regroup
from .render import render_all
from .store import Vault


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="doomscroll")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("process", help="Download, analyze, dedup, and file one reel")
    p.add_argument("url")
    p.add_argument("--note", default="", help="Why you saved it")

    sub.add_parser("render", help="Regenerate the markdown vault from data files")
    sub.add_parser("regroup", help="Re-cluster and rename groups within each topic")
    sub.add_parser("models", help="List Gemini models available to your API key")

    args = parser.parse_args(argv)

    if args.cmd == "process":
        from .pipeline import process  # imports yt-dlp; keep other commands light

        outcomes = process(args.url, args.note)
        if outcomes is None:
            print("Already processed; skipping.")
            return 0
        for o in outcomes:
            target = f" -> {o.target}" if o.target else ""
            print(f"[{o.action:>11}] ({o.similarity:.2f}{target}) {o.text}")
        render_all(Vault.load())

    elif args.cmd == "render":
        render_all(Vault.load())

    elif args.cmd == "regroup":
        vault = Vault.load()
        for topic, s in regroup(vault, gemini.name_groups).items():
            print(f"{topic}: kept {s.kept}, folded {s.folded}, new {s.new}, ungrouped {s.ungrouped}")
        vault.save()
        render_all(vault)

    elif args.cmd == "models":
        print("\n".join(gemini.list_models()))

    return 0


if __name__ == "__main__":
    sys.exit(main())
