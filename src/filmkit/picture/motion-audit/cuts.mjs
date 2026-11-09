/* What a stage cut excuses and what it shows (follow.mjs). A cut is the one place where marks may change at once, and
 * the marks it keeps go on as they went: the firm marks of a scene that a cut keeps but moves whole at one size by one
 * shift of JUMP px or more beyond the shift each moved by in the frame before, none for a mark at rest or newly drawn,
 * to within SHARED px, jump when together they hold HALF or more of the scene's firm ink in the frame before the cut,
 * as a viewer sees most of the picture leap. A stage gliding through the cut keeps its motion and does not jump, and a
 * heading that moves while the rest of its stage is replaced holds too little ink. A cut the composition declares that
 * changes less of its scene than a cut the follower finds excuses the marks it takes away, not the marks it brings onto
 * the stage that stands. */

const area = (b) => Math.max(1, b[2] - b[0]) * Math.max(1, b[3] - b[1]);
const centre = (b) => [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2];
/* A mark's ink, as a cut weighs its marks: its box's area times its ink level. */
const inkOf = (m) => area(m.screen) * m.level;
/* Marks of one scene that a cut may keep: their kind, words and line width. */
const likeOf = (m) => `${m.kind}|${m.text}|${m.width2}`;
/* Nearly one size, as a whole move keeps it: each side within 2 px or 5% of the other's. */
const oneSize = (p, c) =>
  [0, 1].every((k) => {
    const a = p.screen[k + 2] - p.screen[k],
      b = c.screen[k + 2] - c.screen[k];
    return Math.abs(a - b) <= Math.max(2, 0.05 * Math.abs(a));
  });

/** Whether a frame excuses a firm mark of `scene` that appears (`way` "in") or vanishes ("out") in it: a cut the
 * follower finds excuses both, and a cut the composition declares only the marks it takes away. */
export const excused = (way, scene, detected, declared) =>
  detected.has(scene) || (way === "out" && declared.has(scene));

/* Of pairs of marks, each with its shift `s` and ink, the group within `within` px of one of their shifts that holds
 * the most ink, no mark in two pairs, heaviest first; null for no pairs. */
function heaviestShift(pairs, within) {
  const cell = (s) => s.map((x) => Math.round(x / within)),
    cells = new Map(),
    tried = new Set();
  for (const pair of pairs) {
    const key = cell(pair.s).join();
    cells.set(key, [...(cells.get(key) ?? []), pair]);
  }
  let best = null;
  for (const pair of pairs) {
    const key = pair.s.map((x) => Math.round(2 * x)).join();
    if (tried.has(key)) continue;
    tried.add(key);
    const [i, j] = cell(pair.s),
      near = [];
    for (let a = -1; a <= 1; a++)
      for (let b = -1; b <= 1; b++) near.push(...(cells.get(`${i + a},${j + b}`) ?? []));
    const taken = new Set(),
      group = [];
    for (const q of near
      .filter((q) => Math.hypot(q.s[0] - pair.s[0], q.s[1] - pair.s[1]) <= within)
      .sort((a, b) => b.ink - a.ink))
      if (!taken.has(q.p) && !taken.has(q.c)) {
        taken.add(q.p).add(q.c);
        group.push(q);
      }
    const ink = group.reduce((n, q) => n + q.ink, 0);
    if (!best || ink > best.ink) best = { ink, group };
  }
  return best;
}

/** The jumps of a frame, one for each scene of `scenes`, the scenes it cuts, whose firm marks of the previous frame
 * the cut keeps in `marks` but moves whole at one size by one shift beyond the shift `d` each moved by before, holding
 * HALF or more of the scene's firm ink before the cut; a mark that stands where a like mark stood is kept in place.
 * Each jump names its scene, its heaviest mark after the cut, its shift beyond the marks' motion (weighed by ink, to
 * the pixel) and distance, how many marks moved, the share of the scene's firm ink they hold, and their kinds and
 * words. */
export function jumps(previous, marks, scenes, v) {
  const found = [];
  for (const scene of scenes) {
    const firm = (list) => list.filter((m) => m.scene === scene && m.level >= v.FIRM);
    const before = firm(previous),
      after = firm(marks),
      held = before.reduce((n, m) => n + inkOf(m), 0);
    if (!held || !after.length) continue;
    const still = new Set();
    for (const p of before) {
      const c = after.find(
        (c) =>
          !still.has(c) &&
          likeOf(c) === likeOf(p) &&
          c.screen.every((x, k) => Math.abs(x - p.screen[k]) < 0.01),
      );
      if (c) still.add(p).add(c);
    }
    const pairs = [];
    for (const p of before)
      for (const c of after) {
        if (still.has(p) || still.has(c) || likeOf(c) !== likeOf(p) || !oneSize(p, c)) continue;
        const s = [0, 1].map((k) => centre(c.screen)[k] - centre(p.screen)[k] - (p.d?.[k] ?? 0));
        if (Math.hypot(...s) >= v.JUMP) pairs.push({ p, c, s, ink: inkOf(p) });
      }
    const best = heaviestShift(pairs, v.SHARED);
    if (!best || best.ink < v.HALF * held) continue;
    const moved = best.group.map((q) => q.c),
      shift = [0, 1].map((k) =>
        Math.round(best.group.reduce((n, q) => n + q.s[k] * q.ink, 0) / best.ink),
      );
    found.push({
      scene,
      mark: moved[0],
      shift,
      distance: Math.round(Math.hypot(...shift)),
      marks: moved.length,
      share: Math.round((100 * best.ink) / held) / 100,
      paints: [...new Set(moved.map((m) => m.kind))],
      texts: [...new Set(moved.map((m) => m.text).filter(Boolean))],
    });
  }
  return found;
}
