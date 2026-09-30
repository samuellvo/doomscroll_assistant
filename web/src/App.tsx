import { useEffect } from "react";
import { Empty } from "./components";
import { useVault, type Vault } from "./data";
import { href, useRoute } from "./router";
import { Reel } from "./screens/Reel";
import { Search } from "./screens/Search";
import { Today } from "./screens/Today";
import { Tool } from "./screens/Tool";
import { Tools } from "./screens/Tools";
import { Topic } from "./screens/Topic";
import { Topics } from "./screens/Topics";

const TABS = [
  { id: "", label: "Today", icon: "M4 11.5 12 5l8 6.5V20a1 1 0 0 1-1 1h-5v-6h-4v6H5a1 1 0 0 1-1-1z" },
  { id: "topics", label: "Topics", icon: "M4 6h16M4 12h16M4 18h10" },
  { id: "tools", label: "Tools", icon: "M14.5 5.5a4 4 0 0 0-5.3 5.3L4 16v4h4l5.2-5.2a4 4 0 0 0 5.3-5.3l-2.6 2.6-2.6-.6-.6-2.6z" },
  { id: "search", label: "Search", icon: "M11 18a7 7 0 1 1 0-14 7 7 0 0 1 0 14zm5-2 4 4" },
];

function Screen({ vault }: { vault: Vault }) {
  const { path, query } = useRoute();
  const [section, ...rest] = path;
  switch (section) {
    case undefined:
      return <Today vault={vault} />;
    case "topics":
      return rest.length ? <Topic vault={vault} path={rest.join("/")} /> : <Topics vault={vault} />;
    case "tools":
      return rest.length ? <Tool vault={vault} id={rest[0]} /> : <Tools vault={vault} />;
    case "reels":
      return <Reel vault={vault} id={rest[0] ?? ""} />;
    case "search":
      return <Search vault={vault} q={query.get("q") ?? ""} />;
    default:
      return <Empty>Page not found.</Empty>;
  }
}

export function App() {
  const state = useVault();
  const { path } = useRoute();
  const section = path[0] ?? "";

  // New screen: start at the top. Search keystrokes change only the query, so they don't jump.
  const screenKey = path.join("/");
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [screenKey]);

  return (
    <div className="app">
      <main>
        {state.status === "loading" && <p className="empty">Loading vault…</p>}
        {state.status === "error" && (
          <Empty>
            Couldn't load the vault ({state.message}). If you're offline, open the app once while online so it can save a
            copy.
          </Empty>
        )}
        {state.status === "ready" && <Screen vault={state.vault} />}
      </main>
      <nav className="tabs" aria-label="Sections">
        {TABS.map((t) => (
          <a key={t.id} href={href(...(t.id ? [t.id] : []))} className={section === t.id || (t.id === "" && section === "reels") ? "active" : ""}>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d={t.icon} />
            </svg>
            <span>{t.label}</span>
          </a>
        ))}
      </nav>
    </div>
  );
}
