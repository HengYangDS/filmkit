/** What the rule tests share: the film's palette and the frame rule over it, and builders of the
 * labels, strokes, fills and words they measure. */
import { openComposition } from "../../../src/filmkit/picture/headless-composition.mjs";
import { analysis } from "../../../src/filmkit/picture/rules/frame.mjs";
import { inkLevel, readingLoad } from "../../../src/filmkit/picture/rules/ink.mjs";
import { nameRules } from "../../../src/filmkit/picture/rules/names.mjs";
import { authoredTimeline } from "../sample-film.mjs";

// The rules are measured against the film's own palette, as the composition defines it.
export const { palette } = openComposition(await authoredTimeline("zh"));
export const inspectFrame = analysis(inkLevel(palette));
export const contrast = readingLoad(palette);
export const label = (text, bounds, extra = {}) => ({
  text,
  bounds,
  alpha: 1,
  role: "label",
  scene: "01",
  seq: 10,
  ...extra,
});
export const stroke = (points, extra = {}) => ({
  kind: "stroke",
  seq: 1,
  alpha: 1,
  width: 2,
  subs: [points],
  ...extra,
});
export const fill = (box, extra = {}) => ({ kind: "fill", seq: 1, alpha: 1, box, ...extra });
export const kinds = (findings) => findings.map((finding) => finding.kind).sort();
export const names = nameRules();
export const word = (text, extra = {}) => ({
  text,
  bounds: [0, 0, 10, 10],
  alpha: 1,
  role: "label",
  scene: "02",
  color: "#ECE8DF",
  whole: text,
  placed: true,
  size: 38,
  set: null,
  ...extra,
});
