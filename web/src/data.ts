import { useEffect, useMemo, useState } from "react";
import type { LocatedInsight, Reel, Tool, Topic, VaultData } from "./types";

const LAST_VISIT_KEY = "doomscroll:lastVisit";

// Storage can throw in private mode or be cleared; it's only a convenience here.
function readLastVisit(): string | null {
  try {
    return localStorage.getItem(LAST_VISIT_KEY);
  } catch {
    return null;
  }
}

function writeLastVisit(date: string) {
  try {
    localStorage.setItem(LAST_VISIT_KEY, date);
  } catch {
    /* ignore */
  }
}

export interface Vault extends VaultData {
  insightsById: Map<string, LocatedInsight>;
  topicsByPath: Map<string, Topic>;
  toolsById: Map<string, Tool>;
  reelsById: Map<string, Reel>;
  /** The date of the previous visit, captured before this visit overwrote it. */
  previousVisit: string | null;
}

function index(data: VaultData, previousVisit: string | null): Vault {
  const insightsById = new Map<string, LocatedInsight>();
  for (const topic of data.topics)
    for (const group of topic.groups)
      for (const insight of group.insights) insightsById.set(insight.id, { ...insight, topic, group: group.name });
  return {
    ...data,
    insightsById,
    topicsByPath: new Map(data.topics.map((t) => [t.path, t])),
    toolsById: new Map(data.tools.map((t) => [t.id, t])),
    reelsById: new Map(data.reels.map((r) => [r.id, r])),
    previousVisit,
  };
}

export type LoadState = { status: "loading" } | { status: "error"; message: string } | { status: "ready"; vault: Vault };

export function useVault(): LoadState {
  const [previousVisit] = useState(readLastVisit);
  const [state, setState] = useState<{ status: "loading" } | { status: "error"; message: string } | { status: "ready"; data: VaultData }>({
    status: "loading",
  });

  useEffect(() => {
    let cancelled = false;
    fetch("./app.json", { cache: "no-cache" })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<VaultData>;
      })
      .then((data) => {
        if (cancelled) return;
        setState({ status: "ready", data });
        writeLastVisit(new Date().toISOString().slice(0, 10));
      })
      .catch((err: Error) => !cancelled && setState({ status: "error", message: err.message }));
    return () => {
      cancelled = true;
    };
  }, []);

  return useMemo<LoadState>(
    () => (state.status === "ready" ? { status: "ready", vault: index(state.data, previousVisit) } : state),
    [state, previousVisit],
  );
}

export function plural(n: number, word: string): string {
  return `${n} ${word}${n === 1 ? "" : "s"}`;
}

export function formatDate(iso: string): string {
  const d = new Date(iso + "T12:00:00");
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export function titleCase(slug: string): string {
  const acronyms: Record<string, string> = { api: "API", ai: "AI", ml: "ML", sql: "SQL", cdn: "CDN" };
  return slug
    .split("-")
    .map((w) => acronyms[w] ?? w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function categoryLabel(path: string): string {
  return path.split("/").map(titleCase).join(" · ");
}
