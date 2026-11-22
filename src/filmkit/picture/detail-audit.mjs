/* Detail audit of the picture: what a reviewer finds by reading single lines, strokes and names, which neither the
 * frame audit, the sync audit nor the motion audit follows. Measured headlessly from the composition:
 *   ink_drops     a line of a scene that loses part of its ink within one frame, outside a stage cut the scene
 *                 declares (detail-audit/ink.mjs);
 *   outside_runs  a text outside every scene, a caption apart, that moves over the pace line (detail-audit/outside.mjs);
 *   part_drawn    a stroke that stands part-drawn in the quiet between two thoughts, and `racing_tips`, a stroke whose
 *                 tip draws at the pace at which a mark races, both read from the `draws` the composition publishes
 *                 (detail-audit/quiets.mjs); `draws_published` says whether it publishes any;
 *   rails         each list of names on two alternate baselines with its least clearance at a thought's rest
 *                 (detail-audit/rails.mjs).
 * `lines` states the lines a reader judges them by: the `pace` over which a text outside scenes is a stretch, the
 * pace from which a mark or a tip `race`s, and the `rail_clear` px a rail's names keep.
 * The strokes and the texts outside scenes are followed through every frame at 60 frames per second, the rate of the
 * film, since a line that opens within one frame of the film may be whole again in the next.
 * Its usage is `USAGE`, which it prints when it is invoked wrongly.
 * FILMKIT_TEXT_METRICS=<file> names the advance widths of the film's declared faces, as for the frame audit. */
import { writeFileSync } from "node:fs";
import { parseArgs } from "node:util";

import { openComposition, readTextMetrics, readTimeline } from "./headless-composition.mjs";
import { inkDrops, strokePieces } from "./detail-audit/ink.mjs";
import { outsideRuns, outsideTexts, PACE } from "./detail-audit/outside.mjs";
import { partDrawn, quietsOf, racingTips, thoughtsOf, TIP_RACE } from "./detail-audit/quiets.mjs";
import { RAIL, railClearances } from "./detail-audit/rails.mjs";

const USAGE =
  "Usage: python -m filmkit.tools detail-audit <timeline.json> [fps] [--from s] [--to s] [--out report.json]";
/* A malformed invocation stops before any frame is exercised, so it can never read as a clean report. */
function refuse(problem) {
  console.error(`${problem}\n${USAGE}`);
  process.exit(2);
}
const number = (text, name) => {
  const value = text.trim() ? Number(text) : NaN;
  if (!Number.isFinite(value)) refuse(`${name} is not a number: ${text}`);
  return value;
};
let values, positionals;
try {
  ({ values, positionals } = parseArgs({
    allowPositionals: true,
    options: { from: { type: "string" }, to: { type: "string" }, out: { type: "string" } },
  }));
} catch (error) {
  refuse(error.message);
}
if (positionals.length < 1 || positionals.length > 2)
  refuse("Expected one timeline and at most one frame rate");

const timeline = readTimeline(positionals[0]);
const fps = number(positionals[1] ?? "60", "The frame rate");
if (fps <= 0) refuse(`The frame rate is not positive: ${positionals[1]}`);
const dt = 1 / fps;
const from = values.from === undefined ? 0 : number(values.from, "--from"),
  to = values.to === undefined ? timeline.duration : number(values.to, "--to");
if (!(Math.round(from * fps) * dt < to))
  refuse(`The range from ${from} s to ${to} s holds no frame at ${fps} fps`);

const film = openComposition(timeline, { faces: readTextMetrics() });
const within = (t) => t >= from && t <= to;
const sceneAt = (t) => (timeline.segments.findLast((v) => v.start <= t) ?? timeline.segments[0]).id;
const at = (t) => +t.toFixed(3);

/* Every frame: the pieces of each draw call's firm solid strokes, the texts outside scenes, the drawing tips. */
const ink = inkDrops(dt),
  outside = outsideRuns(dt),
  tips = racingTips();
let published = false;
for (let k = Math.round(from * fps); k * dt <= to + 1e-9; k++) {
  const t = k * dt,
    pieces = new Map();
  const layout = film.render(t, (paint) => {
    const found = strokePieces(paint);
    if (!found.length) return;
    const key = `${paint.scene} ${film.origin() ?? ""}`;
    pieces.set(key, [...(pieces.get(key) ?? []), ...found]);
  });
  ink.frame(t, pieces, () => film.declaredCuts());
  outside.frame(t, outsideTexts(layout.texts ?? []));
  if (layout.draws) {
    published = true;
    tips.frame(layout.draws);
  }
}

/* The quiet between two thoughts, at its middle, and the rest of each thought. */
const thoughts = thoughtsOf(timeline),
  quiets = quietsOf(thoughts).filter((q) => within(q.rest) && within(q.resume)),
  stalled = [],
  rails = railClearances();
for (const q of quiets) {
  const draws = film.render((q.rest + q.resume) / 2).draws;
  if (!draws) continue;
  published = true;
  for (const d of partDrawn(draws))
    stalled.push({
      quiet: q.id,
      rest: at(q.rest),
      resume: at(q.resume),
      scene: d.scene,
      cue: at(d.at),
      share: +d.share.toFixed(3),
    });
}
const REST = 0.02;
for (const thought of thoughts) {
  const t = thought.end + REST;
  if (within(t)) rails.rest(`${thought.scene}.${thought.index}`, film.render(t).texts ?? []);
}

const followed = ink.finish();
const report = {
  fps,
  from,
  to,
  frames: followed.frames,
  lines: { pace: PACE, race: TIP_RACE, rail_clear: RAIL.CLEAR },
  ink_drops: followed.drops.map((v) => ({ ...v, t: at(v.t), module: film.module(v.origin) })),
  ink_at_cuts: followed.at_cuts,
  outside_runs: outside
    .finish()
    .map((v) => ({ ...v, scene: sceneAt(v.at), start: at(v.start), end: at(v.end), at: at(v.at) })),
  draws_published: published,
  quiets: quiets.length,
  part_drawn: stalled,
  racing_tips: tips.finish().map((v) => ({ ...v, cue: at(v.cue) })),
  rails: rails.finish(),
};
const text = JSON.stringify(report, null, 1) + "\n";
if (values.out === undefined) process.stdout.write(text);
else {
  writeFileSync(values.out, text);
  const count = (key) => report[key].length;
  console.log(
    JSON.stringify({
      frames: report.frames,
      ink_drops: count("ink_drops"),
      outside_runs: count("outside_runs"),
      draws_published: published,
      part_drawn: count("part_drawn"),
      racing_tips: count("racing_tips"),
      rails: count("rails"),
    }),
  );
}
