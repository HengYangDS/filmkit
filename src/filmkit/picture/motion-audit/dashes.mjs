/* A stroke's dashes as a viewer sees them change: the share of its dash pattern that is gap, and the dash snap of a
 * followed stroke whose gaps open or close by a large share of its pattern within one frame (follow.mjs). A stroke
 * drawn on keeps its pattern, and gaps that open over a third of a second change by a few hundredths of it a frame. */

/** The share of a dash pattern that is gap: the sum of its gaps over its period, 0 for a solid stroke, whose pattern is
 * empty or sums to nothing. An odd pattern repeats, as a canvas repeats it. */
export function gapShare(dash = []) {
  const pattern = dash.length % 2 ? [...dash, ...dash] : dash;
  const period = pattern.reduce((n, v) => n + v, 0);
  return period > 0 ? pattern.reduce((n, v, i) => n + (i % 2 ? v : 0), 0) / period : 0;
}

/** The dash snap of a followed pair of marks, the previous `p` and the current `c`, each with its gap share in `gaps`:
 * a stroke whose gap share steps by `step` or more within one frame snaps, from the first share to the second, each to
 * two places; any other pair is null. */
export function dashSnap(p, c, step) {
  if (c.kind !== "stroke" || Math.abs(c.gaps - p.gaps) < step) return null;
  return [p.gaps, c.gaps].map((v) => Math.round(v * 100) / 100);
}
