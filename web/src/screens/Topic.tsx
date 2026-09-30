import { Chip, Empty, InsightItem, PageHeader } from "../components";
import { plural, type Vault } from "../data";
import { href } from "../router";

const anchor = (name: string) => "group-" + name.toLowerCase().replace(/[^a-z0-9]+/g, "-");

export function Topic({ vault, path }: { vault: Vault; path: string }) {
  const topic = vault.topicsByPath.get(path);
  if (!topic) return <Empty>That topic doesn't exist anymore.</Empty>;

  const jump = (name: string) => document.getElementById(anchor(name))?.scrollIntoView({ behavior: "smooth", block: "start" });

  return (
    <>
      <PageHeader
        title={topic.title}
        subtitle={`${topic.area} · ${plural(topic.insightCount, "insight")} from ${plural(topic.reelCount, "reel")}`}
        back={{ to: href("topics"), label: "Topics" }}
      />
      {topic.groups.map((g) => {
        const name = g.name ?? "Ungrouped";
        return (
          <details key={name} id={anchor(name)} className={`group${g.name === null ? " ungrouped" : ""}`} open>
            <summary>
              <span className="group-name">{name}</span>
              {g.pinned && <Chip tone="accent">pinned</Chip>}
              <span className="muted">{g.insights.length}</span>
            </summary>
            {g.name === null && <p className="hint">New arrivals. Sorted into groups every Monday, or when you ask Claude.</p>}
            {g.related.length > 0 && (
              <p className="see-also">
                See also{" "}
                {g.related.map((r) => (
                  <button key={r} type="button" className="link" onClick={() => jump(r)}>
                    {r}
                  </button>
                ))}
              </p>
            )}
            <ul className="list">
              {g.insights.map((i) => (
                <InsightItem key={i.id} insight={i} vault={vault} />
              ))}
            </ul>
          </details>
        );
      })}
    </>
  );
}
