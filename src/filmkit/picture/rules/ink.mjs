/* How strongly a mark reads over the film's ground. inkLevel and readingLoad are serialised into the page: each is
 * self-contained, takes the film's palette and runs both in the real browser (geometry-check.mjs) and in the
 * headless audits. */

/** Ink level: how far a mark rises above the film's ground, its brightest channel's lift over the ground times its
 * opacity (0-255). A style other than a #rrggbb colour lifts nothing. */
export function inkLevel(palette) {
  const channels = (color) => [1, 3, 5].map((i) => parseInt(color.slice(i, i + 2), 16));
  const ground = channels(palette.ground);
  return function level(color, alpha) {
    return /^#[0-9a-f]{6}$/i.test(color ?? "")
      ? alpha * Math.max(...channels(color).map((v, k) => v - ground[k]))
      : 0;
  };
}

/** Reading load: the WCAG contrast of a mark's ink over the film's ground. A word of at least 3:1 is legible; a word
 * held between 1.8:1 and 3:1 is neither legible nor gone, so it reads as faint clutter. A style other than a #rrggbb
 * colour reads as the film's ink. */
export function readingLoad(palette) {
  const luminance = (rgb) => {
    const [r, g, b] = rgb.map((c) => {
      c /= 255;
      return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const channels = (color) => [1, 3, 5].map((i) => parseInt(color.slice(i, i + 2), 16));
  const ground = channels(palette.ground),
    ink = channels(palette.ink),
    base = luminance(ground) + 0.05;
  return function contrast(color, alpha) {
    const rgb = /^#[0-9a-f]{6}$/i.test(color ?? "") ? channels(color) : ink;
    const blended = rgb.map((v, i) => alpha * v + (1 - alpha) * ground[i]);
    return (luminance(blended) + 0.05) / base;
  };
}

/** Lit marks, as the reviewers see them: each frame scaled to 480x270 gray, where a mark is lit if its pixels rise
 * above gray 48. A mark lifts a cell's gray by its luma over the ground's, times its opacity and its share of the
 * 4 px cell. A thin stroke can straddle two cells, so it is counted at its worst share: a 2 px line in the line colour
 * stays below gray 48 there (round 16's 30.5 rail measured 44-46), and a picture balanced only by such a line is not
 * balanced. A style other than a #rrggbb colour is never lit. With `lift`, a mark counts when it rises that many
 * levels above the ground instead. */
export const LIT_GRAY = 48;
export function litLevel(palette, { lift = null } = {}) {
  const luma = (color) => {
    const [r, g, b] = [1, 3, 5].map((i) => parseInt(color.slice(i, i + 2), 16));
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const ground = luma(palette.ground),
    threshold = lift === null ? LIT_GRAY : ground + lift;
  return function lit(color, alpha, share = 1) {
    return (
      /^#[0-9a-f]{6}$/i.test(color ?? "") &&
      ground + (luma(color) - ground) * alpha * share > threshold
    );
  };
}
/* A stroke's worst share of a cell, and a fill's: thin marks fall short of a whole cell. */
export const strokeShare = (width) => Math.min(1, width / 7),
  fillShare = ([x0, y0, x1, y1]) => Math.min(1, (x1 - x0) / 7) * Math.min(1, (y1 - y0) / 7);

/** Lit at full size, as the reviews since DDWG round 29 measure a frame: a mark whose colour, mixed over the ground at
 * its opacity, is brighter than grey 60 by BT.601 luma, the grey of the reviewers' PIL measure. A style other than a
 * #rrggbb colour is never lit. */
export const FULL_SIZE_LIT_GRAY = 60;
export function litAtFullSize(palette) {
  const luma = (color) => {
    const [r, g, b] = [1, 3, 5].map((i) => parseInt(color.slice(i, i + 2), 16));
    return 0.299 * r + 0.587 * g + 0.114 * b;
  };
  const ground = luma(palette.ground);
  return function lit(color, alpha) {
    return (
      /^#[0-9a-f]{6}$/i.test(color ?? "") &&
      ground + (luma(color) - ground) * alpha > FULL_SIZE_LIT_GRAY
    );
  };
}
