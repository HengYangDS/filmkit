/* The frame audit's case measure (mixed_case): the names of one set, and the names of one row, which begin in both
 * cases.
 *
 * A set is the list the composition gives a name (`set`); a row is the names of one scene and size whose baselines
 * stand within half their size, anywhere across the frame, since equal cards or the two sides of a mark are one row to
 * the eye whatever contains them. Each name counts once, by its whole text at its first line, so a wrapped name's
 * second line is not judged on its own. Only names the composition registers as labels are judged. */
import { sameSize } from "./layout.mjs";

/** The case of a name's first letter, "upper" or "lower", or null when the name is not judged: it opens with a
 * quotation mark, since a quotation keeps its source's case, its first letter or digit is a digit or a letter without
 * case, such as a CJK one, or its first word holds a capital after its first letter, as an acronym or a brand does. */
export function initialCase(name) {
  const at = name.search(/[\p{L}\p{N}]/u),
    first = name[at];
  if (/^\s*\p{Pi}|^\s*["']/u.test(name)) return null;
  if (at < 0 || first.toUpperCase() === first.toLowerCase()) return null;
  const word = name.slice(at).split(/\s/u)[0];
  if (/\p{Lu}/u.test(word.slice(1))) return null;
  return first === first.toUpperCase() ? "upper" : "lower";
}

/** The sets and rows of a frame's settled names (layout.mjs) whose judged names begin in both cases, each as a finding
 * with its scene, its names in reading order and which begin in each case. */
export function mixedCase({ names }) {
  const first = new Map();
  for (const line of names) {
    if ((line.role ?? "label") !== "label") continue;
    const key = `${line.scene}\u0000${line.whole}`;
    if (!first.has(key) || line.baseline < first.get(key).baseline) first.set(key, line);
  }
  const judged = [...first.values()].filter((line) => initialCase(line.whole));
  const groups = new Map();
  for (const line of judged.filter((v) => v.set)) {
    const key = `${line.scene}\u0000${line.set}`;
    groups.set(key, [...(groups.get(key) ?? []), line]);
  }
  const sets = [...groups.values()].map((group) =>
    group.sort((a, b) => a.baseline - b.baseline || a.left - b.left),
  );
  const rows = [];
  for (const line of [...judged].sort((a, b) => a.baseline - b.baseline)) {
    const row = rows.find(
      (r) =>
        r[0].scene === line.scene &&
        sameSize(r[0], line) &&
        Math.abs(r[0].baseline - line.baseline) < line.size / 2,
    );
    if (row) row.push(line);
    else rows.push([line]);
  }
  return [...sets, ...rows.map((row) => row.sort((a, b) => a.left - b.left))]
    .filter((group) => new Set(group.map((v) => initialCase(v.whole))).size > 1)
    .map((group) => ({
      kind: "mixed_case",
      scene: group[0].scene,
      texts: group.map((v) => v.whole),
      severity: 1,
      detail: {
        upper: group.filter((v) => initialCase(v.whole) === "upper").map((v) => v.whole),
        lower: group.filter((v) => initialCase(v.whole) === "lower").map((v) => v.whole),
      },
    }));
}
