import type { ReactNode } from "react";
import { askAboutInsight } from "./ask";
import { categoryLabel, plural, type Vault } from "./data";
import { href, topicHref } from "./router";
import type { Insight, LocatedInsight } from "./types";

/** `back.to` omitted means "go back in history" (a reel can be opened from any screen). */
export function PageHeader({ title, subtitle, back }: { title: string; subtitle?: ReactNode; back?: { to?: string; label: string } }) {
  return (
    <header className="page-header">
      {back?.to && (
        <a className="back" href={back.to}>
          <span aria-hidden="true">‹</span> {back.label}
        </a>
      )}
      {back && !back.to && (
        <button type="button" className="back" onClick={() => history.back()}>
          <span aria-hidden="true">‹</span> {back.label}
        </button>
      )}
      <h1>{title}</h1>
      {subtitle && <p className="subtitle">{subtitle}</p>}
    </header>
  );
}

export function Section({ title, aside, children }: { title: string; aside?: ReactNode; children: ReactNode }) {
  return (
    <section className="section">
      <div className="section-title">
        <h2>{title}</h2>
        {aside}
      </div>
      {children}
    </section>
  );
}

export function Chip({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "accent" | "warn" | "muted" }) {
  return <span className={`chip chip-${tone}`}>{children}</span>;
}

/** "×3" consensus badge: how many reels said the same thing. Hidden for single mentions. */
export function Consensus({ count }: { count: number }) {
  if (count < 2) return null;
  return (
    <span className="consensus" title={`Said in ${count} reels`}>
      ×{count}
    </span>
  );
}

export function InsightItem({ insight, vault, showTopic = false }: { insight: Insight | LocatedInsight; vault: Vault; showTopic?: boolean }) {
  const located = "topic" in insight ? insight : null;
  const forAsk = located ?? vault.insightsById.get(insight.id);
  return (
    <li className="insight">
      <p className="insight-text">
        {insight.text} <Consensus count={insight.count} />
      </p>
      <div className="insight-meta">
        <Chip tone="muted">{insight.kind}</Chip>
        {showTopic && located && <a href={topicHref(located.topic.path)}>{located.topic.title}</a>}
        {insight.sources.map((id) => (
          <a key={id} href={href("reels", id)} className="source">
            {vault.reelsById.get(id)?.author ?? id}
          </a>
        ))}
        {forAsk && <AskClaude compact href={askAboutInsight(vault, forAsk)} />}
      </div>
      {insight.nuances.length > 0 && (
        <ul className="nuances">
          {insight.nuances.map((n) => (
            <li key={n.text}>
              <span className="label">Nuance</span> {n.text} <Consensus count={n.count} />
            </li>
          ))}
        </ul>
      )}
      {insight.conflicts.map((c) => (
        <p key={c} className="conflict">
          <span className="label">Conflicts with</span> {c}
        </p>
      ))}
    </li>
  );
}

export function ToolRow({ id, vault }: { id: string; vault: Vault }) {
  const tool = vault.toolsById.get(id);
  if (!tool) return null;
  return (
    <a className="row" href={href("tools", tool.id)}>
      <div className="row-main">
        <span className="row-title">{tool.name}</span>
        <span className="row-sub">{tool.whatItIs}</span>
      </div>
      <div className="row-aside">
        <Chip>{categoryLabel(tool.category)}</Chip>
        {tool.mentions.length > 1 && <span className="muted">{plural(tool.mentions.length, "mention")}</span>}
      </div>
    </a>
  );
}

/** Opens Claude (app or claude.ai) with a prefilled prompt; uses the viewer's own plan. */
export function AskClaude({ href, label = "Ask Claude", compact = false }: { href: string; label?: string; compact?: boolean }) {
  return (
    <a className={compact ? "ask-link" : "button button-secondary"} href={href} target="_blank" rel="noreferrer">
      {label}
      <span aria-hidden="true"> ↗</span>
    </a>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="empty">{children}</p>;
}
