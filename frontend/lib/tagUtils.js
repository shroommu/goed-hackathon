/** Unicode vertical-bar variants treated like ASCII "|" before splitting */
const PIPE_ALIASES = /\uFF5C|\u2502/g;

/**
 * Split a resource tag field (comma / semicolon / ASCII or Unicode pipe separated) into trimmed tokens.
 * Dedupes case-insensitively while preserving first-seen casing.
 * @param {unknown} value - Raw string from API or empty
 * @returns {string[]}
 */
export function splitResourceTags(value) {
  if (value == null || value === "") {
    return [];
  }
  let str = typeof value === "string" ? value : String(value);
  // Normalize fullwidth/box-drawing bars so "|tag1｜tag2|" splits reliably
  str = str.replace(PIPE_ALIASES, "|");
  const parts = str.split(/[,;|]/);
  const seen = new Set();
  const out = [];
  for (const part of parts) {
    const t = part.trim();
    if (!t) continue;
    const key = t.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(t);
  }
  return out;
}
