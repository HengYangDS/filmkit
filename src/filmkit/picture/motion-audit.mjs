/* Motion and transition audit of the picture: ghosts and residue, double exposure, stalls, pops and jumps, type scale
 * and camera framing, measured headlessly from the composition, and in `followed` every mark followed as a viewer sees
 * it move (motion-audit/follow.mjs) with the halts, starts, races, pops, jumps at stage cuts and dash snaps it finds
 * and each scene's fastest glide and flow (motion-audit/followed.mjs).
 * Usage: python -m filmkit.tools motion-audit <timeline.json> [fps] [--from s] [--to s] [--out report.json]
 * Every mark a scene paints is recorded with its ink level (opacity times its colour's rise above the ground), its
 * screen box, its box in its own drawing coordinates (its identity across frames), for words the size shown, and for a
 * stroke or fill its drawn pieces and its dash pattern.
 * FILMKIT_TEXT_METRICS=<file> names the advance widths of the film's declared faces, as for the frame audit. */
import { writeFileSync } from "node:fs";
import { parseArgs } from "node:util";

import { openComposition, readTextMetrics, readTimeline } from "./headless-composition.mjs";
import { follower, VIEWER } from "./motion-audit/follow.mjs";
import { followedReport } from "./motion-audit/followed.mjs";
import { motionReport, round } from "./motion-audit/report.mjs";
import { inkLevel } from "./rules/ink.mjs";

const USAGE =
  "Usage: python -m filmkit.tools motion-audit <timeline.json> [fps] [--from s] [--to s] [--out report.json]";
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
const fps = number(positionals[1] ?? "30", "The frame rate");
if (fps <= 0) refuse(`The frame rate is not positive: ${positionals[1]}`);
const dt = 1 / fps;
const from = values.from === undefined ? 0 : number(values.from, "--from"),
  to = values.to === undefined ? timeline.duration : number(values.to, "--to");
if (!(Math.round(from * fps) * dt < to))
  refuse(`The range from ${from} s to ${to} s holds no frame at ${fps} fps`);
/* Thresholds: a mark below 5 levels is not seen; 5-55 is faint (a ghost when it rests there); 25 is clearly visible;
 * 60 is firm enough that appearing within one frame reads as a pop. */
const SEEN = 5,
  FAINT = 55,
  VISIBLE = 25,
  FIRM = 60;

const film = openComposition(timeline, { faces: readTextMetrics() });
/* Ink level: how far the brightest channel rises above the ground at the mark's opacity (0-255), as the real-browser
 * check measures it (geometry-check.mjs). */
const levelOf = inkLevel(film.palette);
const bbox = (pts) => [
  Math.min(...pts.map((p) => p[0])),
  Math.min(...pts.map((p) => p[1])),
  Math.max(...pts.map((p) => p[0])),
  Math.max(...pts.map((p) => p[1])),
];
/* The mark a paint leaves, or none for a path without points. */
const markOf = (paint) =>
  paint.points.length
    ? {
        kind: paint.kind,
        scene: paint.scene,
        alpha: paint.alpha,
        level: levelOf(paint.color, paint.alpha),
        color: paint.color,
        width: paint.lineWidth,
        local: bbox(paint.points),
        screen: bbox(paint.points.map(paint.toScreen)),
        ...(paint.kind === "text"
          ? { text: paint.text, size: paint.size * paint.scale }
          : {
              // Its drawn pieces on the screen: each subpath's box and its first and last points.
              pieces: paint.subs.filter((sub) => sub.length).map(bbox),
              ends: paint.subs.filter((sub) => sub.length).map((sub) => [sub[0], sub.at(-1)]),
              dash: paint.dash,
            }),
      }
    : null;
/* The marks of the frame at t, in paint order. */
function marksAt(t) {
  const marks = [];
  const { texts } = film.render(t, (paint) => {
    const mark = markOf(paint);
    if (mark) marks.push(mark);
  });
  return { marks, texts };
}

const segments = timeline.segments;
const speakingAt = (t) => segments.find((v) => v.voice_start <= t && t < v.voice_end);
const wordAt = (t) => {
  const s = speakingAt(t);
  return s?.words.find((w) => w.start - 0.05 <= t && t < w.end + 0.05);
};
const area = (b) => Math.max(0, b[2] - b[0]) * Math.max(0, b[3] - b[1]);
const centre = (b) => [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2];
const overlap = (a, b) =>
  area([Math.max(a[0], b[0]), Math.max(a[1], b[1]), Math.min(a[2], b[2]), Math.min(a[3], b[3])]);
/* A mark's identity across frames: its scene, kind, words, line width and the box in its own coordinates. Colour is
 * not part of it, so a gradual colour change keeps one identity and a sudden one is reported as a snap. */
const keyOf = (v) =>
  `${v.scene}|${v.kind}|${v.text ?? ""}|${Math.round(v.width)}|${v.local.map((c) => Math.round(c / 6)).join(",")}`;
const looksAlike = (a, b) =>
  a.scene === b.scene && a.kind === b.kind && (a.text ?? "") === (b.text ?? "");
const channels = (color) =>
  /^#[0-9a-f]{6}$/i.test(color ?? "")
    ? [1, 3, 5].map((i) => parseInt(color.slice(i, i + 2), 16))
    : null;
/* The largest change of one colour channel; a style without channels has none to measure. */
const colourStep = (a, b) => {
  const [x, y] = [channels(a), channels(b)];
  return x && y ? Math.max(...x.map((v, i) => Math.abs(v - y[i]))) : 0;
};

/* Per-key state across frames. */
const tracks = new Map();
const faintRuns = [],
  pops = [],
  jumps = [],
  doubles = [],
  snaps = [],
  frames = [];
const typeSizes = new Map(),
  cameras = new Map();
let previous = [],
  previousSeen = new Map();
const viewer = follower(dt);
for (let i = Math.round(from * fps); i * dt < to; i++) {
  const t = i * dt;
  const { marks, texts } = marksAt(t);
  // Words: the role comes from the engine's own registration, in the same order as painting.
  const painted = marks.filter((v) => v.kind === "text");
  if (painted.length === texts.length)
    painted.forEach((v, k) => {
      v.role = texts[k].role;
    });
  const current = marks.filter((v) => v.scene && v.level >= SEEN && v.role !== "caption");
  // The scenes whose stage cut the composition declares between the previous frame and this one.
  const declared = [...film.declaredCuts()]
    .filter(([, at]) => [...at].some((c) => c > t - dt + 1e-9 && c <= t + 1e-9))
    .map(([scene]) => scene);
  viewer.frame(
    t,
    current.filter((v) => v.level >= VIEWER.VISIBLE),
    i === Math.round(from * fps) ? [] : declared,
  );
  const seen = new Map();
  // Two marks drawn on one geometry in the same frame are a layered crossfade (a dashed place filling, a colour
  // blending through two strokes), not one mark changing colour.
  const layered = new Set();
  for (const v of current) {
    const key = keyOf(v),
      had = seen.get(key);
    if (had) layered.add(key);
    if (!had || had.level < v.level) seen.set(key, v);
  }
  // Fade energy: how much ink changed since the last frame, weighted by mark size; motion: the fastest visible mark.
  let fade = 0,
    motion = 0;
  for (const [key, v] of seen) {
    const track = tracks.get(key);
    const size = Math.min(
      600,
      Math.max(
        4,
        Math.sqrt(
          area(v.screen) || (v.screen[2] - v.screen[0] + v.screen[3] - v.screen[1]) * v.width,
        ),
      ),
    );
    if (track && track.last === i - 1) {
      fade += Math.abs(v.level - track.level) * size;
      if (v.level >= VISIBLE && track.level >= VISIBLE) {
        const [x0, y0] = centre(track.screen),
          [x1, y1] = centre(v.screen);
        motion = Math.max(motion, Math.hypot(x1 - x0, y1 - y0) / dt);
      }
    } else fade += v.level * size;
    // A rest in the faint band: the mark stays seen but below a legible ink for a while. Dark panel fills (cards
    // and rows) are ground-like by design and are not counted.
    const faint = v.level < FAINT && !(v.kind === "fill" && v.color === film.palette.row);
    const continuing = track?.last === i - 1,
      run = continuing ? track.run : null;
    const next = faint
      ? run
        ? { ...run, end: t, low: Math.min(run.low, v.level), high: Math.max(run.high, v.level) }
        : { start: t, end: t, low: v.level, high: v.level, color: v.color }
      : null;
    if (run && !faint) faintRuns.push({ key, ...run });
    // A sudden change of colour on a visible mark (more than 60 levels in one channel within one frame) is a snap.
    if (
      continuing &&
      track.color &&
      v.level >= VISIBLE &&
      !layered.has(key) &&
      !track.layered &&
      colourStep(track.color, v.color) > 60
    )
      snaps.push({ t, scene: v.scene, kind: v.kind, text: v.text, from: track.color, to: v.color });
    tracks.set(key, {
      first: continuing ? track.first : i,
      last: i,
      level: v.level,
      screen: v.screen,
      run: next,
      color: v.color,
      layered: layered.has(key),
    });
  }
  for (const [key, track] of tracks) {
    if (track.last === i - 1 && !seen.has(key)) {
      fade += track.level * Math.min(600, Math.max(4, Math.sqrt(area(track.screen))));
      if (track.run) faintRuns.push({ key, ...track.run });
      track.run = null;
    }
  }
  // Pops and jumps: a firm mark that appears or vanishes within one frame, unless a like mark moved there.
  const before = previous.filter((v) => v.level >= VISIBLE);
  for (const v of current) {
    if (v.level < FIRM || tracks.get(keyOf(v))?.last !== i) continue;
    const track = tracks.get(keyOf(v));
    if (track.first !== i || i === Math.round(from * fps)) continue;
    const [cx, cy] = centre(v.screen);
    // A mark smaller than 12 px across is a stroke starting to grow, not a pop; a phrase that extends the words
    // standing at the same left edge (a growing label) continues them.
    if (Math.hypot(v.screen[2] - v.screen[0], v.screen[3] - v.screen[1]) < 12) continue;
    if (
      v.text &&
      before.some(
        (u) =>
          u.scene === v.scene &&
          u.text &&
          (v.text.startsWith(u.text) ||
            u.text.startsWith(v.text) ||
            v.text.endsWith(u.text.trim())) &&
          Math.abs(u.screen[1] - v.screen[1]) < 4,
      )
    )
      continue;
    const like = before.filter((u) => looksAlike(u, v));
    const nearest = like
      .map((u) => Math.hypot(centre(u.screen)[0] - cx, centre(u.screen)[1] - cy))
      .sort((a, b) => a - b)[0];
    if (nearest === undefined || nearest > 80)
      pops.push({
        t,
        scene: v.scene,
        kind: v.kind,
        text: v.text,
        level: Math.round(v.level),
        screen: v.screen.map(Math.round),
        way: "in",
      });
    else if (nearest > 40)
      jumps.push({
        t: round(t),
        scene: v.scene,
        kind: v.kind,
        text: v.text,
        distance: Math.round(nearest),
        screen: v.screen.map(Math.round),
      });
  }
  for (const [key, u] of previousSeen) {
    if (u.level < FIRM || seen.has(key)) continue;
    const [cx, cy] = centre(u.screen);
    if (
      u.text &&
      current.some(
        (v) =>
          v.scene === u.scene &&
          v.text &&
          (v.text.startsWith(u.text) ||
            u.text.startsWith(v.text) ||
            v.text.endsWith(u.text.trim())) &&
          Math.abs(u.screen[1] - v.screen[1]) < 4,
      )
    )
      continue;
    const like = current.filter(
      (v) =>
        v.scene === u.scene &&
        v.kind === u.kind &&
        (v.text ?? "") === (u.text ?? "") &&
        Math.hypot(centre(v.screen)[0] - cx, centre(v.screen)[1] - cy) <= 80,
    );
    if (!like.length)
      pops.push({
        t,
        scene: u.scene,
        kind: u.kind,
        text: u.text,
        level: Math.round(u.level),
        screen: u.screen.map(Math.round),
        way: "out",
      });
  }
  // Double exposure: a fading mark and a rising mark overlap while both are half there.
  const rising = [],
    falling = [];
  for (const [key, v] of seen) {
    const track = tracks.get(key);
    const prior = previousSeen.get(key);
    if (v.alpha < 0.12 || v.alpha > 0.88) continue;
    if (prior && v.level > prior.level + 0.3) rising.push(v);
    else if (prior && v.level < prior.level - 0.3) falling.push(v);
    // A new track beside a like mark of the previous frame is that mark moving, not a second mark arriving.
    else if (
      !prior &&
      track.first === i &&
      !previous.some(
        (u) =>
          looksAlike(u, v) &&
          Math.hypot(
            centre(u.screen)[0] - centre(v.screen)[0],
            centre(u.screen)[1] - centre(v.screen)[1],
          ) < 40,
      )
    )
      rising.push(v);
  }
  let doubled = 0;
  const pairs = [];
  const iou = (a, b) => {
    const o = overlap(a, b);
    return o / (area(a) + area(b) - o || 1);
  };
  for (const a of falling)
    for (const b of rising) {
      if (a.kind === "stroke" && b.kind === "stroke" && iou(a.screen, b.screen) > 0.85) continue;
      const o = overlap(a.screen, b.screen);
      if (o >= 150) {
        doubled += o;
        if (pairs.length < 3) pairs.push([a.text ?? a.kind, b.text ?? b.kind, a.scene, b.scene]);
      }
    }
  if (doubled)
    doubles.push({
      t,
      area: Math.round(doubled),
      pairs,
      boxes: falling.concat(rising).map((v) => ({
        scene: v.scene,
        kind: v.kind,
        text: v.text,
        screen: v.screen,
        rising: rising.includes(v),
      })),
    });
  // Type scale of words: the size at which each label is shown.
  for (const v of current) {
    if (v.kind !== "text" || v.role !== "label" || v.alpha < 0.5 || !/\p{L}/u.test(v.text))
      continue;
    const list = typeSizes.get(v.scene) ?? [];
    list.push(v.size);
    typeSizes.set(v.scene, list);
  }
  const speaking = speakingAt(t);
  const shown = segments.findLast((v) => v.start <= t);
  if (film.framed && shown && t < timeline.duration - timeline.credits_duration) {
    const c = film.camera(shown, t),
      list = cameras.get(shown.id) ?? [];
    list.push([t, c.k, c.ox - c.k * c.ax, c.oy - c.k * c.ay]);
    cameras.set(shown.id, list);
  }
  // Picture weight: how much legible content the frame holds (mark size times its ink), for emptying dips.
  const weight = current.reduce(
    (n, v) =>
      n +
      (v.level >= VISIBLE
        ? (Math.min(600, Math.max(4, Math.sqrt(area(v.screen) || 16))) * v.level) / 255
        : 0),
    0,
  );
  frames.push({
    t,
    fade,
    motion,
    weight,
    speaking: speaking?.id ?? null,
    word: Boolean(wordAt(t)),
    ink: current.reduce((n, v) => n + (v.level >= VISIBLE ? 1 : 0), 0),
  });
  previous = current;
  previousSeen = seen;
}
for (const [key, track] of tracks) if (track.run) faintRuns.push({ key, ...track.run });
const { report, summary } = motionReport({
  film,
  markOf,
  segments,
  dt,
  fps,
  from,
  to,
  SEEN,
  FAINT,
  faintRuns,
  pops,
  jumps,
  doubles,
  snaps,
  frames,
  typeSizes,
  cameras,
});
const { followed, summary: counts } = followedReport({ film, markOf, dt, found: viewer.finish() });
report.followed = followed;
summary.followed = counts;
if (values.out) writeFileSync(values.out, JSON.stringify(report, null, 1) + "\n");
console.log(JSON.stringify(summary));
