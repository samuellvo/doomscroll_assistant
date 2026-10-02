// "Ask Claude" deep links: open claude.ai (or the Claude app) with a prefilled prompt that
// carries the relevant vault context. Uses the viewer's own Claude plan; no API key involved.

import { postNoun, type Vault } from "./data";
import type { Insight, LocatedInsight, Reel, Tool, Topic } from "./types";

const REPO = "https://github.com/samuellvo/doomscroll_assistant";
// Prefilled prompts travel in the URL, so keep them well under typical URL limits.
const MAX_PROMPT_CHARS = 3500;

function link(prompt: string): string {
  return "https://claude.ai/new?q=" + encodeURIComponent(prompt);
}

/** Trim a long block to fit the remaining budget, marking the cut. */
function fit(text: string, budget: number): string {
  if (text.length <= budget) return text;
  return text.slice(0, Math.max(0, budget - 15)).trimEnd() + " …(truncated)";
}

function assemble(head: string[], flexible: string, tail: string[]): string {
  const fixed = [...head, ...tail].join("\n\n");
  const room = MAX_PROMPT_CHARS - fixed.length - 4;
  const middle = flexible && room > 200 ? fit(flexible, room) : "";
  return [...head, ...(middle ? [middle] : []), ...tail].join("\n\n");
}

function bullets(items: string[], limit: number): string {
  const shown = items.slice(0, limit).map((t) => `- ${t}`);
  if (items.length > limit) shown.push(`- …and ${items.length - limit} more`);
  return shown.join("\n");
}

const count = (i: Insight) => (i.count > 1 ? ` (said in ${i.count} reels)` : "");

export function askAboutInsight(vault: Vault, insight: LocatedInsight): string {
  const group = insight.topic.groups.find((g) => g.name === insight.group);
  const siblings = (group?.insights ?? []).filter((i) => i.id !== insight.id).map((i) => i.text + count(i));
  const reel = vault.reelsById.get(insight.sources[0]);
  const head = [
    `I keep a knowledge vault of insights from Instagram reels I save (full vault: ${REPO}/tree/main/vault). Help me go deeper on this one:`,
    `"${insight.text}"${count(insight)}`,
    `Topic: ${insight.topic.area} › ${insight.topic.title}${insight.group ? ` › ${insight.group}` : ""}. Kind: ${insight.kind}.`,
    ...(insight.nuances.length ? ["Nuances I've collected:\n" + bullets(insight.nuances.map((n) => n.text), 5)] : []),
    ...(insight.conflicts.length ? ["Conflicting claims I've seen:\n" + bullets(insight.conflicts, 3)] : []),
    ...(siblings.length ? ["Related insights in the same group:\n" + bullets(siblings, 6)] : []),
  ];
  const source = reel ? `Source reel: "${reel.title}" by ${reel.author}. ${reel.summary}` : "";
  const tail = [
    "Explain why this is true, when it breaks down or is oversimplified, and give a concrete example. Then tell me what to learn next to build on it.",
  ];
  return link(assemble(head, source, tail));
}

export function askAboutReel(vault: Vault, reel: Reel): string {
  const insights = reel.insights.map((id) => vault.insightsById.get(id)?.text).filter((t): t is string => !!t);
  const tools = reel.tools.map((id) => vault.toolsById.get(id)?.name).filter((t): t is string => !!t);
  const head = [
    `I saved this Instagram ${reel.kind === "carousel" ? `carousel (${reel.items} slides)` : postNoun(reel)} to my knowledge vault (${REPO}/tree/main/vault): "${reel.title}" by ${reel.author}.`,
    ...(reel.note ? [`Why I saved it: ${reel.note}`] : []),
    `Summary: ${reel.summary}`,
    ...(insights.length ? ["Insights extracted:\n" + bullets(insights, 8)] : []),
    ...(tools.length ? [`Tools mentioned: ${tools.join(", ")}`] : []),
  ];
  const tail = [
    "Help me go deeper: what's accurate, what's oversimplified or missing, and how would I actually apply this? Suggest a small hands-on exercise.",
  ];
  const label = reel.kind === "reel" ? "Transcript" : "Text from the post";
  return link(assemble(head, reel.transcript ? `${label}:\n${reel.transcript}` : "", tail));
}

export function askAboutTool(vault: Vault, tool: Tool): string {
  const claims = tool.mentions.map((m) => {
    const reel = vault.reelsById.get(m.reel);
    return reel ? `${m.claim} (from "${reel.title}" by ${reel.author})` : m.claim;
  });
  const head = [
    `Creators I follow on Instagram recommended ${tool.name}${tool.link ? ` (${tool.link})` : ""}: ${tool.whatItIs}`,
    "What they claimed:\n" + bullets(claims, 6),
    ...(tool.notes ? [`My notes so far: ${tool.notes}`] : []),
  ];
  const tail = [
    "Is it worth my time as a software engineer? Check the claims, compare it with the main alternatives, and tell me the fastest way to try it plus any gotchas.",
  ];
  return link(assemble(head, "", tail));
}

export function askAboutTopic(topic: Topic): string {
  const lines = topic.groups.flatMap((g) =>
    g.insights.map((i) => `${g.name ? `[${g.name}] ` : ""}${i.text}${count(i)}`),
  );
  const head = [
    `Here's everything I've collected on ${topic.area} › ${topic.title} from Instagram reels (vault: ${REPO}/tree/main/vault):`,
  ];
  const tail = [
    "What am I missing? Point out the most important ideas this doesn't cover, anything here that's misleading or oversimplified, and give me a short learning path to fill the gaps.",
  ];
  return link(assemble(head, bullets(lines, 60), tail));
}
