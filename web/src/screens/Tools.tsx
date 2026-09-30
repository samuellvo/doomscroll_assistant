import { Empty, PageHeader, Section, ToolRow } from "../components";
import { plural, titleCase, type Vault } from "../data";

const STATUS_ORDER = ["investigating", "new", "tried", "adopted", "dropped"];

export function Tools({ vault }: { vault: Vault }) {
  const byStatus = new Map<string, string[]>();
  for (const t of vault.tools) byStatus.set(t.status, [...(byStatus.get(t.status) ?? []), t.id]);
  const statuses = [...STATUS_ORDER.filter((s) => byStatus.has(s)), ...[...byStatus.keys()].filter((s) => !STATUS_ORDER.includes(s))];

  return (
    <>
      <PageHeader title="Tools" subtitle={plural(vault.tools.length, "tool") + " to investigate"} />
      {statuses.length === 0 && <Empty>No tools yet.</Empty>}
      {statuses.map((s) => (
        <Section key={s} title={titleCase(s)} aside={<span className="muted">{byStatus.get(s)!.length}</span>}>
          <div className="rows">
            {byStatus.get(s)!.map((id) => (
              <ToolRow key={id} id={id} vault={vault} />
            ))}
          </div>
        </Section>
      ))}
    </>
  );
}
