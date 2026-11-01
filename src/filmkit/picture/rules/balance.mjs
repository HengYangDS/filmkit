/** Balance as the reviewers measure it: the content band runs from 120 to 900 px, so a picture's box stands off the
 * content centre (960, 510) by these shares of the frame's width and height. A thought's picture may stand at most 12%
 * off two seconds into the thought and at most 8% off 70% through it, and its box must cover at least 5% and 10% of
 * the band at those instants. */
export const BALANCE_BAND = [120, 900],
  BALANCE_LIMITS = { two: 0.12, late: 0.08 },
  COVER_LIMITS = { two: 0.05, late: 0.1 };
export function pictureOffset([x0, y0, x1, y1]) {
  return [((x0 + x1) / 2 - 960) / 1920, ((y0 + y1) / 2 - 510) / 1080];
}
export function bandCover([x0, y0, x1, y1]) {
  const [top, bottom] = BALANCE_BAND;
  return (
    ((x1 - x0) * Math.max(0, Math.min(y1, bottom) - Math.max(y0, top))) / (1920 * (bottom - top))
  );
}
