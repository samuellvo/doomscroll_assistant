import { Empty, InsightItem, PageHeader, Section } from "../components";
import { formatDate, plural, type Vault } from "../data";
import { href } from "../router";

export function Today({ vault }: { vault: Vault }) {
  const all = [...vault.insightsById.values()];
  const since = vault.previousVisit;
  const fresh = since ? all.filter((i) => i.created > since) : [];
  const consensus = all.filter((i) => i.count > 1).sort((a, b) => b.count - a.count).slice(0, 3);
  const recent = vault.reels.slice(0, 5);

  return (
    <>
      <PageHeader title="Vault" subtitle={`Updated ${formatDate(vault.generated)}`} />

      <div className="stats">
        <a href={href("topics")}>
          <strong>{vault.stats.insights}</strong> insights
        </a>
        <a href={href("tools")}>
          <strong>{vault.stats.tools}</strong> tools
        </a>
        <span>
          <strong>{vault.stats.reels}</strong> reels
        </span>
      </div>

      {fresh.length > 0 && (
        <Section title="New since your last visit" aside={<span className="muted">{plural(fresh.length, "insight")}</span>}>
          <ul className="list">
            {fresh.slice(0, 8).map((i) => (
              <InsightItem key={i.id} insight={i} vault={vault} showTopic />
            ))}
          </ul>
        </Section>
      )}

      {consensus.length > 0 && (
        <Section title="Most agreed on">
          <ul className="list">
            {consensus.map((i) => (
              <InsightItem key={i.id} insight={i} vault={vault} showTopic />
            ))}
          </ul>
        </Section>
      )}

      <Section title="Recently saved">
        {recent.length === 0 ? (
          <Empty>No reels yet. Share one to the Save to Vault shortcut.</Empty>
        ) : (
          <div className="rows">
            {recent.map((r) => (
              <a key={r.id} className="row" href={href("reels", r.id)}>
                <div className="row-main">
                  <span className="row-title">{r.title}</span>
                  <span className="row-sub">
                    {r.author} · {formatDate(r.saved)}
                    {r.note && <> · “{r.note}”</>}
                  </span>
                </div>
              </a>
            ))}
          </div>
        )}
      </Section>

      {vault.stats.ungrouped > 0 && (
        <p className="callout">
          {plural(vault.stats.ungrouped, "insight")} waiting in Ungrouped. They're sorted into groups every Monday, or ask
          Claude to group them now.
        </p>
      )}
    </>
  );
}
