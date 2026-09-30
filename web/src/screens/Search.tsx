import { useEffect, useRef } from "react";
import { Empty, InsightItem, PageHeader, Section, ToolRow } from "../components";
import { type Vault } from "../data";
import { href, navigate } from "../router";

export function Search({ vault, q }: { vault: Vault; q: string }) {
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    input.current?.focus();
  }, []);

  const needle = q.trim().toLowerCase();
  const has = (...fields: string[]) => fields.some((f) => f.toLowerCase().includes(needle));
  const insights = needle ? [...vault.insightsById.values()].filter((i) => has(i.text, ...i.nuances.map((n) => n.text))) : [];
  const tools = needle ? vault.tools.filter((t) => has(t.name, t.whatItIs, t.category, ...t.mentions.map((m) => m.claim))) : [];
  const reels = needle ? vault.reels.filter((r) => has(r.title, r.summary, r.author, r.note, r.transcript)) : [];

  return (
    <>
      <PageHeader title="Search" />
      <input
        ref={input}
        className="search"
        type="search"
        placeholder="Insights, tools, reels…"
        defaultValue={q}
        onChange={(e) => navigate(href("search") + "?q=" + encodeURIComponent(e.target.value), true)}
      />
      {needle && insights.length + tools.length + reels.length === 0 && <Empty>No matches for “{q}”.</Empty>}
      {insights.length > 0 && (
        <Section title="Insights" aside={<span className="muted">{insights.length}</span>}>
          <ul className="list">
            {insights.slice(0, 30).map((i) => (
              <InsightItem key={i.id} insight={i} vault={vault} showTopic />
            ))}
          </ul>
        </Section>
      )}
      {tools.length > 0 && (
        <Section title="Tools" aside={<span className="muted">{tools.length}</span>}>
          <div className="rows">
            {tools.map((t) => (
              <ToolRow key={t.id} id={t.id} vault={vault} />
            ))}
          </div>
        </Section>
      )}
      {reels.length > 0 && (
        <Section title="Reels" aside={<span className="muted">{reels.length}</span>}>
          <div className="rows">
            {reels.map((r) => (
              <a key={r.id} className="row" href={href("reels", r.id)}>
                <div className="row-main">
                  <span className="row-title">{r.title}</span>
                  <span className="row-sub">{r.author}</span>
                </div>
              </a>
            ))}
          </div>
        </Section>
      )}
    </>
  );
}
