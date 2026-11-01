export interface Segment {
  text: string;
  match: boolean;
}

function escapeRegExp(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Splits text into matching and non-matching parts, ignoring case. The query is literal. */
export function splitMatches(text: string, query: string): Segment[] {
  const needle = query.trim();
  if (needle === "") return [{ text, match: false }];

  const pattern = new RegExp(escapeRegExp(needle), "giu");
  const segments: Segment[] = [];
  let last = 0;
  for (const found of text.matchAll(pattern)) {
    if (found.index > last) segments.push({ text: text.slice(last, found.index), match: false });
    segments.push({ text: found[0], match: true });
    last = found.index + found[0].length;
  }
  if (last < text.length) segments.push({ text: text.slice(last), match: false });
  return segments.length > 0 ? segments : [{ text, match: false }];
}

export function countMatches(lines: string[], query: string): number {
  if (query.trim() === "") return 0;
  return lines.reduce(
    (total, line) => total + splitMatches(line, query).filter((s) => s.match).length,
    0,
  );
}
