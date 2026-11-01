/* The rules on a frame's names are serialised into the page: each is self-contained and runs both in the real browser
 * (geometry-check.mjs) and headlessly (frame-audit.mjs). */

/** Names: a voiced frame may show at most twelve legible names, the lines of a wrapped or growing name, or a term
 * with its qualifier, counting once; every legible name is placed by a layout primitive, names use at most two text
 * sizes, and no name joins items with a middle dot instead of a structure. The findings carry how many names are
 * legible, and a type-size finding the sizes shown. */
export function nameRules() {
  const LIMIT = 12;
  return function nameFindings(words, contrast) {
    const legible = words.filter((v) => contrast(v.color, v.alpha) >= 3),
      findings = [],
      scene = legible[0]?.scene ?? null;
    findings.names = new Set(legible.map((v) => `${v.scene}|${v.whole ?? v.text}`)).size;
    if (findings.names > LIMIT) findings.push({ kind: "name_load", scene, text: "" });
    for (const v of legible) {
      if (!v.placed) findings.push({ kind: "unplaced_label", scene: v.scene, text: v.text });
      if (/·/u.test(v.text)) findings.push({ kind: "dot_join", scene: v.scene, text: v.text });
    }
    const sizes = [...new Set(legible.map((v) => v.size))].sort((a, b) => a - b);
    if (sizes.length > 2)
      findings.push({ kind: "type_sizes", scene, text: sizes.join(","), sizes });
    return findings;
  };
}

/** Lists: the names of one list build and leave as a whole, so each stops being legible within 0.6 s of the last of
 * its list, and in the last frame the list is seen every name stands at no less than 90% of the brightest name of its
 * set in the same colour (a refused name is muted by design). Each finding names its list's set and the name, with
 * when it was last seen and, for a dimmed name, its share of that brightest name. */
export function listTracker() {
  const lists = new Map(),
    last = new Map();
  return {
    see(words, t, contrast) {
      const levels = new Map();
      for (const v of words) {
        if (!v.set || contrast(v.color, v.alpha) < 3) continue;
        const key = `${v.scene}\u0000${v.set}`,
          seen = lists.get(key) ?? new Map();
        seen.set(v.whole ?? v.text, t);
        lists.set(key, seen);
        const level = levels.get(key) ?? new Map(),
          name = `${v.color}\u0001${v.whole ?? v.text}`;
        level.set(name, Math.max(level.get(name) ?? 0, v.alpha));
        levels.set(key, level);
      }
      for (const [key, level] of levels) last.set(key, { t, level });
    },
    findings() {
      const early = [...lists].flatMap(([key, seen]) => {
        const end = Math.max(...seen.values()),
          [scene, set] = key.split("\u0000");
        return [...seen]
          .filter(([, at]) => at < end - 0.6)
          .map(([name, at]) => ({
            kind: "list_leaving_early",
            scene,
            text: `${set}: ${name}`,
            set,
            name,
            at,
          }));
      });
      const dimmed = [...last].flatMap(([key, { t, level }]) => {
        const [scene, set] = key.split("\u0000"),
          peak = new Map(),
          colour = (name) => name.split("\u0001")[0];
        for (const [name, alpha] of level)
          peak.set(colour(name), Math.max(peak.get(colour(name)) ?? 0, alpha));
        return [...level]
          .filter(([name, alpha]) => alpha < 0.9 * peak.get(colour(name)))
          .map(([name, alpha]) => ({
            kind: "list_leaving_dimmed",
            scene,
            text: `${set}: ${name.split("\u0001")[1]}`,
            set,
            name: name.split("\u0001")[1],
            at: t,
            share: alpha / peak.get(colour(name)),
          }));
      });
      return [...early, ...dimmed];
    },
  };
}

/** Faint labels: a word held between 1.8:1 and 3:1 for more than a second is neither a usable recap nor gone, so it
 * reads as faint clutter. Each frame's words are seen in turn; the faint runs that ended in it are returned, each with
 * its scene and text and the times it began and ended. */
export function faintLabels() {
  const faint = new Map();
  return function see(words, t, contrast) {
    const inBand = new Set(),
      ended = [];
    for (const v of words) {
      const c = contrast(v.color, v.alpha),
        key = `${v.scene}\u0000${v.text}`;
      if (c >= 1.8 && c < 3) {
        inBand.add(key);
        if (!faint.has(key)) faint.set(key, { scene: v.scene, text: v.text, start: t });
      }
    }
    for (const [key, run] of faint) {
      if (inBand.has(key)) continue;
      if (t - run.start > 1) ended.push({ ...run, end: t });
      faint.delete(key);
    }
    return ended;
  };
}
