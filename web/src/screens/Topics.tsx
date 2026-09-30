import { PageHeader } from "../components";
import { plural, type Vault } from "../data";
import { topicHref } from "../router";
import type { Topic } from "../types";

function topInsight(topic: Topic) {
  return topic.groups.flatMap((g) => g.insights).sort((a, b) => b.count - a.count)[0];
}

export function Topics({ vault }: { vault: Vault }) {
  const areas = new Map<string, Topic[]>();
  for (const t of vault.topics) areas.set(t.area, [...(areas.get(t.area) ?? []), t]);

  return (
    <>
      <PageHeader title="Topics" subtitle={`${plural(vault.topics.length, "topic")} · ${plural(vault.stats.insights, "insight")}`} />
      {[...areas].map(([area, topics]) => (
        <section key={area} className="section">
          <div className="section-title">
            <h2>{area}</h2>
          </div>
          <div className="cards">
            {topics
              .sort((a, b) => b.insightCount - a.insightCount)
              .map((t) => {
                const top = topInsight(t);
                return (
                  <a key={t.path} className="card" href={topicHref(t.path)}>
                    <div className="card-head">
                      <span className="card-title">{t.title}</span>
                      <span className="muted">{t.insightCount}</span>
                    </div>
                    {top && <p className="card-preview">{top.text}</p>}
                    <span className="card-foot">
                      {plural(t.reelCount, "reel")}
                      {t.ungroupedCount > 0 && ` · ${t.ungroupedCount} ungrouped`}
                    </span>
                  </a>
                );
              })}
          </div>
        </section>
      ))}
    </>
  );
}
