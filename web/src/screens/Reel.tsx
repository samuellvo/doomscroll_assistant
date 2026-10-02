import { askAboutReel } from "../ask";
import { AskClaude, Empty, InsightItem, PageHeader, Section, ToolRow } from "../components";
import { formatDate, postLabel, postNoun, type Vault } from "../data";

export function Reel({ vault, id }: { vault: Vault; id: string }) {
  const reel = vault.reelsById.get(id);
  if (!reel) return <Empty>That post isn't in the vault.</Empty>;
  const insights = reel.insights.map((i) => vault.insightsById.get(i)).filter((i) => i !== undefined);

  return (
    <>
      <PageHeader
        title={reel.title}
        subtitle={`${postLabel(reel)} · ${reel.author} · saved ${formatDate(reel.saved)}`}
        back={{ label: "Back" }}
      />
      {reel.note && (
        <p className="callout">
          <span className="label">Why I saved it</span> {reel.note}
        </p>
      )}
      <a className="button" href={reel.url} target="_blank" rel="noreferrer">
        Open in Instagram
      </a>
      <AskClaude href={askAboutReel(vault, reel)} label={`Ask Claude about this ${postNoun(reel)}`} />
      <Section title="Summary">
        <p className="prose">{reel.summary}</p>
      </Section>
      {insights.length > 0 && (
        <Section title="Insights">
          <ul className="list">
            {insights.map((i) => (
              <InsightItem key={i.id} insight={i} vault={vault} showTopic />
            ))}
          </ul>
        </Section>
      )}
      {reel.tools.length > 0 && (
        <Section title="Tools mentioned">
          <div className="rows">
            {reel.tools.map((t) => (
              <ToolRow key={t} id={t} vault={vault} />
            ))}
          </div>
        </Section>
      )}
      <details className="transcript">
        <summary>{reel.kind === "reel" ? "Transcript" : "Text from the post"}</summary>
        <p className="prose">{reel.transcript}</p>
      </details>
    </>
  );
}
