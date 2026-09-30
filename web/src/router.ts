import { useSyncExternalStore } from "react";

// Hash routing (#/topics/...) because GitHub Pages can't rewrite deep links to index.html.

function subscribe(onChange: () => void) {
  window.addEventListener("hashchange", onChange);
  return () => window.removeEventListener("hashchange", onChange);
}

export function useRoute(): { path: string[]; query: URLSearchParams } {
  const hash = useSyncExternalStore(subscribe, () => window.location.hash);
  const [path, query = ""] = hash.replace(/^#\/?/, "").split("?");
  return { path: path.split("/").filter(Boolean).map(decodeURIComponent), query: new URLSearchParams(query) };
}

export function href(...segments: string[]): string {
  return "#/" + segments.map(encodeURIComponent).join("/");
}

/** Topic paths contain a slash, so they're encoded segment by segment. */
export function topicHref(path: string): string {
  return "#/topics/" + path.split("/").map(encodeURIComponent).join("/");
}

export function navigate(to: string, replace = false) {
  if (replace) window.location.replace(to);
  else window.location.hash = to.slice(1);
}
