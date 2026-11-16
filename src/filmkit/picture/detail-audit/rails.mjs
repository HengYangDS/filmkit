/* Rails on two baselines: names of one list that stand on alternate lines.
 *
 * Where a dense rail sets every other name a row lower, a long name reaches under its neighbour, and the row-gap
 * check, which reads one row, measures nothing between them: the DDWG film's review round 41 (note Z41-3) found such
 * names 17 to 19 px apart and asked for 48 px at 1080p.
 *
 * At the rest of a thought, each list (the names that share a `set`) whose names stand on exactly two lines of
 * tops and alternate along the rail is such a rail. Between two consecutive names the clearance is the gap across
 * when they stand side by side, the gap down when one reaches under the other, and the diagonal otherwise. */

/** A rail's names stand at least CLEAR px apart at 1080p (the review's line), are judged from the opacity SHOWN, sit
 * on lines whose tops are read to the GRID px and stand LINES px or more apart, and a list of three counts only while
 * each name is one line, at most ONE_LINE px tall. */
export const RAIL = Object.freeze({ CLEAR: 48, SHOWN: 0.5, GRID: 4, LINES: 16, ONE_LINE: 45 });

const line = (box) => Math.round(box[1] / RAIL.GRID);

/** The rails on two baselines among a frame's texts, each with its `set`, its least `clear` between two consecutive
 * names, those `names`, and that pair's gaps `across` and `down`, negative where they overlap on that axis. A name
 * of several lines is one block, its lines sharing their `whole` text. */
export function railsOf(texts) {
  const sets = new Map();
  for (const v of texts) {
    if (!v.scene || !v.set || v.alpha < RAIL.SHOWN) continue;
    const key = `${v.scene}\u0000${v.set}`,
      blocks = sets.get(key) ?? new Map(),
      name = v.whole ?? v.text,
      b = blocks.get(name) ?? [Infinity, Infinity, -Infinity, -Infinity];
    blocks.set(name, [
      Math.min(b[0], v.bounds[0]),
      Math.min(b[1], v.bounds[1]),
      Math.max(b[2], v.bounds[2]),
      Math.max(b[3], v.bounds[3]),
    ]);
    sets.set(key, blocks);
  }
  const rails = [];
  for (const [key, blocks] of sets) {
    const list = [...blocks].sort((p, q) => p[1][0] + p[1][2] - (q[1][0] + q[1][2])),
      tops = [...new Set(list.map(([, b]) => line(b)))];
    if (list.length < 3 || tops.length !== 2) continue;
    if (Math.abs(tops[0] - tops[1]) * RAIL.GRID < RAIL.LINES) continue;
    if (list.length === 3 && list.some(([, b]) => b[3] - b[1] > RAIL.ONE_LINE)) continue;
    // Every name stands on the other line than its neighbour: a list wrapped onto two rows does not.
    if (!list.every(([, b], i) => i === 0 || line(b) !== line(list[i - 1][1]))) continue;
    let least = null;
    for (let i = 0; i + 1 < list.length; i++) {
      const [na, a] = list[i],
        [nb, b] = list[i + 1];
      const across = Math.max(a[0], b[0]) - Math.min(a[2], b[2]),
        down = Math.max(a[1], b[1]) - Math.min(a[3], b[3]);
      // A name set in two places reads as overlapping its neighbour: the geometry check owns collisions.
      if (across < 0 && down < 0) continue;
      const clear = across < 0 || down < 0 ? Math.max(across, down) : Math.hypot(across, down);
      if (least === null || clear < least.clear) least = { clear, names: [na, nb], across, down };
    }
    if (least) {
      const [scene, set] = key.split("\u0000");
      rails.push({ scene, set, ...least });
    }
  }
  return rails;
}

/** Keeps each rail's least clearance over the rests of a film. `rest(thought, texts)` takes a thought's name and
 * the texts of the frame at its rest; `finish()` returns one row for each rail, by its scene and set, with the
 * thought `at` whose rest held its least clearance, tightest first. */
export function railClearances() {
  const worst = new Map();
  return {
    rest(thought, texts) {
      for (const rail of railsOf(texts)) {
        const key = `${rail.scene}\u0000${rail.set}`;
        if (!(worst.get(key)?.clear <= rail.clear)) worst.set(key, { ...rail, at: thought });
      }
    },
    finish() {
      const round = (v) => Math.round(v * 10) / 10;
      return [...worst.values()]
        .map((v) => ({
          ...v,
          clear: round(v.clear),
          across: round(v.across),
          down: round(v.down),
        }))
        .sort((a, b) => a.clear - b.clear);
    },
  };
}
