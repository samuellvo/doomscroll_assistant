import { askAboutTool } from "../ask";
import { AskClaude, Chip, Empty, PageHeader, Section } from "../components";
import { categoryLabel, formatDate, titleCase, type Vault } from "../data";
import { href } from "../router";

export function Tool({ vault, id }: { vault: Vault; id: string }) {
  const tool = vault.toolsById.get(id);
  if (!tool) return <Empty>That tool doesn't exist anymore.</Empty>;

  return (
    <>
      <PageHeader title={tool.name} subtitle={tool.whatItIs} back={{ to: href("tools"), label: "Tools" }} />
      <div className="meta-row">
        <Chip tone="accent">{titleCase(tool.status)}</Chip>
        <Chip>{categoryLabel(tool.category)}</Chip>
        <span className="muted">First seen {formatDate(tool.firstSeen)}</span>
      </div>
      {tool.link && (
        <a className="button" href={tool.link.startsWith("http") ? tool.link : `https://${tool.link}`} target="_blank" rel="noreferrer">
          Open {tool.link.replace(/^https?:\/\//, "")}
        </a>
      )}
      <AskClaude href={askAboutTool(vault, tool)} label={`Is ${tool.name} worth trying?`} />
      <Section title="What creators claimed">
        <ul className="list">
          {tool.mentions.map((m) => (
            <li key={m.reel} className="insight">
              <p className="insight-text">{m.claim}</p>
              <div className="insight-meta">
                <a className="source" href={href("reels", m.reel)}>
                  {vault.reelsById.get(m.reel)?.title ?? m.reel}
                </a>
              </div>
            </li>
          ))}
        </ul>
      </Section>
      {tool.notes && (
        <Section title="Investigation notes">
          <p className="prose">{tool.notes}</p>
        </Section>
      )}
    </>
  );
}
