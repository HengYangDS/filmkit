/* What the frame audit's measures read of a painted mark: whether it is seen, whether it stands in the head band, and
 * the box and the points it covers. */

/* Dim marks still collide visually: anything above 15% opacity is checked. */
export const VISIBLE = 0.15;
/* Marks of the head band (the running head and the Illustrative chip) frame the picture rather than show it, so they
 * never keep a frame from reading as bare ground. */
export const HEAD = 108;
export const inHead = (points) => points.length > 0 && points.every(([, y]) => y < HEAD);

export const spanOf = (points) => [
  Math.min(...points.map((v) => v[0])),
  Math.min(...points.map((v) => v[1])),
  Math.max(...points.map((v) => v[0])),
  Math.max(...points.map((v) => v[1])),
];
/* The points a graphic covers: the corners of a fill's box, or every sampled point of a stroke. */
export const pointsOf = (g) =>
  g.kind === "fill"
    ? [
        [g.box[0], g.box[1]],
        [g.box[2], g.box[3]],
      ]
    : g.subs.flat();
export const emptyBox = () => [Infinity, Infinity, -Infinity, -Infinity];
export const growBox = (box, [x, y]) => {
  box[0] = Math.min(box[0], x);
  box[1] = Math.min(box[1], y);
  box[2] = Math.max(box[2], x);
  box[3] = Math.max(box[3], y);
};
