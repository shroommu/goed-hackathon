/**
 * Distinct hues for company letter markers — gold-forward, aligned with dark UI family.
 */
export const COMPANY_ACCENT_COLORS = [
  "#d4af37",
  "#c9a227",
  "#eab308",
  "#b8860b",
  "#f59e0b",
  "#ca8a04",
  "#a16207",
  "#5b8bd9",
  "#64748b",
  "#78716c",
];

/** Readable letter color on arbitrary accent backgrounds (static HTML markers). */
export function letterColorOnAccent(bgHex) {
  const hex = bgHex.replace("#", "");
  const r = parseInt(hex.slice(0, 2), 16) / 255;
  const g = parseInt(hex.slice(2, 4), 16) / 255;
  const b = parseInt(hex.slice(4, 6), 16) / 255;
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return luminance > 0.55 ? "#0a0f1e" : "#f8fafc";
}
