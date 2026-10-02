// Mirrors src/doomscroll/export.py (schema 1). Keep the two in sync.

export interface Nuance {
  text: string;
  count: number;
}

export interface Insight {
  id: string;
  text: string;
  kind: string;
  count: number;
  sources: string[];
  created: string;
  nuances: Nuance[];
  conflicts: string[];
}

export interface Group {
  name: string | null; // null = Ungrouped
  pinned: boolean;
  related: string[];
  insights: Insight[];
}

export interface Topic {
  path: string;
  title: string;
  area: string;
  insightCount: number;
  reelCount: number;
  ungroupedCount: number;
  groups: Group[];
}

export interface Tool {
  id: string;
  name: string;
  whatItIs: string;
  category: string;
  link: string;
  status: string;
  notes: string;
  firstSeen: string;
  mentions: { reel: string; claim: string }[];
}

export interface Reel {
  id: string;
  url: string;
  author: string;
  title: string;
  summary: string;
  transcript: string;
  note: string;
  saved: string;
  kind: "reel" | "image" | "carousel";
  items: number; // slides in a carousel
  insights: string[];
  tools: string[];
}

export interface VaultData {
  schema: number;
  generated: string;
  stats: { reels: number; insights: number; tools: number; ungrouped: number };
  topics: Topic[];
  tools: Tool[];
  reels: Reel[];
}

/** An insight plus where it lives, for cross-screen links. */
export interface LocatedInsight extends Insight {
  topic: Topic;
  group: string | null;
}
