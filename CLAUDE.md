# Doomscroll vault — instructions for Claude

This repo turns Instagram reels I save into a deduplicated knowledge base. A GitHub Action
downloads each reel, Gemini extracts insights and tools, and the results land in `vault/`.
Your job is to **read, curate, and apply my feedback**.

## Reading the vault

Start at `vault/index.md`. Then:
- `vault/topics/**.md` — insights grouped by similarity. `(×N)` means N reels said it; higher N
  = more consensus. Nuances are nested under the idea they refine; ⚠️ marks conflicts.
  **Ungrouped** (last section) holds new arrivals; "See also" links related groups.
- `vault/queue.md` + `vault/tools/*.md` — tools to investigate, by status.
- `vault/reels/*.md` — per-reel summary and transcript; cite these when answering.
- `vault/inbox.md` — low-confidence reels, unapproved topic paths, and conflicts to resolve.

## Source of truth: edit data, not markdown

Everything under `vault/topics`, `vault/tools`, `vault/reels`, and `queue.md`/`inbox.md`/
`index.md` is **generated** and gets overwritten. To change anything, edit:
- `vault/data/insights.jsonl` — one insight per line (`topic`, `group`, `parent`, `sources`, `contradicts`)
- `vault/data/tools.jsonl` — tools (`status`: new | investigating | tried | adopted | dropped; `notes`)
- `vault/data/reels.jsonl` — reels
- `vault/data/groups.jsonl` — one line per group (`topic`, `name`, `pinned`)
- `vault/taxonomy.md` — allowed topic/category paths (Gemini reads this every run)
- `vault/feedback.md` — rules Gemini follows every run

Then run `python -m doomscroll render` and commit.

`vault/data/embeddings.npz` maps insight ids to vectors. When you merge insights, keep the
surviving id; orphaned vectors are harmless and dropped on the next save.

## Feedback workflow

When I correct something ("that's not caching", "these are the same", "split this group"):
1. Make the change in the data files.
2. If the correction could recur, add a one-line rule to `vault/feedback.md` with today's date.
3. If it's a new or renamed topic, update `vault/taxonomy.md`.
4. Render, and summarize what changed.

Merging duplicates: union `sources` into the surviving insight, repoint any `parent`/
`contradicts` references, delete the other line.

## Groups, Ungrouped, and pinning

- New insights arrive with `group: null` (Ungrouped). The weekly regroup Action
  (`python -m doomscroll regroup`) sorts them: it keeps existing group names stable, folds
  similar ones into existing groups, names genuinely new clusters, and leaves loners Ungrouped.
- **Any group you create, rename, or edit by hand must be pinned** (`"pinned": true` in
  `groups.jsonl`), or the weekly regroup may reshape it. Pinned groups are never re-clustered,
  renamed, split, or merged, though new similar insights can still join them.
- Renaming a group: update `group` on its insights and the `name` in `groups.jsonl`, and pin it.
- "Group the ungrouped insights in X": reuse existing group names where they fit, create new
  groups only for clear themes of 2+ insights, pin every group you touch, and leave true loners
  Ungrouped.

## Weekly curation (when asked to "review the vault")

- Work through `inbox.md`: approve or remap new paths, resolve conflicts (or leave both
  with a note), and double-check low-confidence reels.
- Look for near-duplicate insights the embedding thresholds missed.
- Suggest taxonomy splits for topics with over ~40 insights, and merges for tiny ones.
- For tools with status `new` and 2+ mentions, research them and write findings into `notes`;
  set status to `investigating`.

## Code

`src/doomscroll/`: `fetch` (yt-dlp) → `gemini` (analysis, embeddings, judge) → `dedup` →
`store` → `render`; `regroup` re-clusters weekly (see its module docstring). Tests: `pytest`.
