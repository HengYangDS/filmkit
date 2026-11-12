/* The drawn pieces a mark the follower follows gains or loses whole (follow.mjs). A piece is one subpath of a stroke or
 * fill, known by its box and its first and last points. A piece of the previous frame continues a piece of the current
 * frame where the pair's shift puts it: drawn from the same first point, ending at the same last point or, closed, at
 * the same centre, to within 2 px or a fifth of the shift, each place of a piece continuing one piece, so a link that a
 * gap splits continues from both its ends and a link drawn on or turned keeps its first point. The shift is the first
 * of those the follower offers, the pair's motion, the shift its pieces share and none, that continues the most
 * pieces. A piece that moves on its own within its mark, as a tick slides along a span or a pan rises as its beam
 * tilts, or that is drawn on from a seed too small to place, continues a piece left over in the other frame that the
 * follower would follow as a mark of its own. Any other piece is gained or lost whole. */

const centre = (b) => [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2];
const closed = ([a, b]) => Math.abs(a[0] - b[0]) <= 0.01 && Math.abs(a[1] - b[1]) <= 0.01;
/* The places a mark's piece k is known by: its first point, its last point and, for a closed piece, its centre. */
const placesOf = (m, k) => [
  m.ends[k][0],
  m.ends[k][1],
  closed(m.ends[k]) ? centre(m.pieces[k]) : null,
];
const unset = (flags) => flags.flatMap((v, k) => (v ? [] : [k]));

/* A mark's piece k as a mark of its own, which the follower's motion rules take. */
const pieceOf = (m, k) => ({
  kind: m.kind,
  screen: m.pieces[k],
  pieces: [m.pieces[k]],
  ends: [m.ends[k]],
});

/* Which pieces of p, the previous frame's mark, and of c continue a piece of the other where the shift s puts them,
 * as flags by piece: at each place in turn, each piece's place continues at most one, nearest first, a pair already
 * continued at another place first. */
function continuedAt(p, c, s) {
  const within = Math.max(2, 0.2 * Math.hypot(...s)),
    n = p.ends.length,
    m = c.ends.length,
    a = p.ends.map((_, i) => placesOf(p, i)),
    b = c.ends.map((_, j) => placesOf(c, j));
  const miss = (x, y) => (x && y ? Math.hypot(y[0] - x[0] - s[0], y[1] - x[1] - s[1]) : Infinity);
  // Most frames hold each piece where the shift puts it, in the order it is drawn.
  if (n === m && a.every((x, i) => x.some((place, k) => miss(place, b[i][k]) <= within)))
    return [Array(n).fill(1), Array(m).fill(1)];
  const before = Array(n).fill(0),
    after = Array(m).fill(0),
    together = new Set();
  for (const k of [0, 1, 2]) {
    const options = [],
      takenP = new Set(),
      takenC = new Set();
    for (let i = 0; i < n; i++)
      for (let j = 0; j < m; j++) {
        const d = miss(a[i][k], b[j][k]);
        if (d <= within) options.push([together.has(i * m + j) ? 0 : 1, d, Math.abs(i - j), i, j]);
      }
    options.sort((x, y) => x[0] - y[0] || x[1] - y[1] || x[2] - y[2]);
    for (const [, , , i, j] of options) {
      if (takenP.has(i) || takenC.has(j)) continue;
      takenP.add(i);
      takenC.add(j);
      before[i] = after[j] = 1;
      together.add(i * m + j);
    }
  }
  return [before, after];
}

/** The pieces of a followed pair that no piece of the other frame continues: `gained`, of the current frame's mark c,
 * and `lost`, of the previous frame's mark p, by index. `shifts` are the shifts the follower offers for the pair, and
 * `follows(a, b)` the shift by which it would follow a piece a as a mark into the piece b, or null. */
export function leftPieces(p, c, shifts, follows) {
  let best = null;
  for (const [k, s] of shifts.entries()) {
    if (shifts.slice(0, k).some((r) => Math.hypot(r[0] - s[0], r[1] - s[1]) < 0.01)) continue;
    const kept = continuedAt(p, c, s),
      count = [...kept[0], ...kept[1]].reduce((n, v) => n + v, 0);
    if (!best || count > best.count) best = { s, kept, count };
    if (count === p.ends.length + c.ends.length) break;
  }
  const [before, after] = best.kept,
    options = [];
  for (const i of unset(before))
    for (const j of unset(after)) {
      const own = follows(pieceOf(p, i), pieceOf(c, j));
      if (own) options.push([Math.hypot(own[0] - best.s[0], own[1] - best.s[1]), i, j]);
    }
  options.sort((x, y) => x[0] - y[0]);
  for (const [, i, j] of options) if (!before[i] && !after[j]) before[i] = after[j] = 1;
  return { gained: unset(after), lost: unset(before) };
}
