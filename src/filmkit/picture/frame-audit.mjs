/* Exercise every frame of the composition headlessly on one timeline and report layout, legibility, how its text
 * lines up and its pacing.
 * Usage: python -m filmkit.tools frame-audit <timeline.json> [step-seconds] [--from s] [--to s] [--at s]
 * --from and --to limit the frames exercised to one stretch of the film, such as the scenes being rebuilt; --at
 * reports one frame in detail. TRACE=<file> writes the label trace that filmkit.picture.sync_audit reads; MARKS=<file> writes the
 * firm marks and repeated members of each voiced frame, with whether a legible name stands at each, for its seat
 * check (src/filmkit/picture/seat-marks.mjs); BOUNDS=<file> writes each scene's drawn extent; BALANCE=<file> writes
 * each thought's lit offsets and band cover at the reviewers' two instants. FILMKIT_TEXT_METRICS=<file> names the
 * advance widths of the film's declared faces (filmkit.picture.metrics), by which the headless canvas measures text;
 * without it the canvas estimates text metrics (headless-composition.mjs). geometry-check.mjs measures real geometry. */
import { parseArgs } from "node:util";

import { compositionMeasures } from "./frame-audit/composition.mjs";
import { inHead, spanOf, VISIBLE } from "./frame-audit/marks.mjs";
import { frameReport, writeRequestedFiles } from "./frame-audit/report.mjs";
import { textLayout } from "./frame-audit/typography/index.mjs";
import { openComposition, readTextMetrics, readTimeline } from "./headless-composition.mjs";
import { analysis } from "./rules/frame.mjs";
import { inkLevel, readingLoad } from "./rules/ink.mjs";
import { faintLabels, listTracker, nameRules } from "./rules/names.mjs";

const USAGE =
  "Usage: python -m filmkit.tools frame-audit <timeline.json> [step-seconds] [--from s] [--to s] [--at s]";
/* A malformed invocation stops before any frame is exercised, so it can never read as a clean report. */
function refuse(problem) {
  console.error(`${problem}\n${USAGE}`);
  process.exit(2);
}
const seconds = (text, name) => {
  const value = text.trim() ? Number(text) : NaN;
  if (!Number.isFinite(value)) refuse(`${name} is not a number of seconds: ${text}`);
  return value;
};
let values, positionals;
try {
  ({ values, positionals } = parseArgs({
    allowPositionals: true,
    options: { from: { type: "string" }, to: { type: "string" }, at: { type: "string" } },
  }));
} catch (error) {
  refuse(error.message);
}
if (positionals.length < 1 || positionals.length > 2)
  refuse("Expected one timeline and at most one step");
const timeline = readTimeline(positionals[0]);
const step = seconds(positionals[1] ?? "0.25", "The step");
if (step <= 0) refuse(`The step is not a positive number of seconds: ${positionals[1]}`);
const probe = values.at === undefined ? null : seconds(values.at, "--at");
if (probe !== null && (values.from !== undefined || values.to !== undefined))
  refuse("--at reports one frame and takes no --from or --to");
const from = Math.max(
    0,
    Math.floor((values.from === undefined ? 0 : seconds(values.from, "--from")) / step) * step,
  ),
  to = Math.min(
    values.to === undefined ? timeline.duration : seconds(values.to, "--to"),
    timeline.duration,
  );
if (probe === null && !(from < to)) refuse(`The range from ${from} s to ${to} s holds no frame`);

/* Any paint above 4% opacity counts as ink, so a frame without it reads as bare ground. */
const INK = 0.04,
  STRONG = 0.25;
/* A mark's level is how far its brightest channel rises above the ground at its opacity. Within the voiced film no
 * frame may fall below 30 levels (steady scenes reach 150-225). */
const LEVEL = 30;

/* A measure holds runs of frames per key: the frame at t extends the last run, or starts one after a gap. */
function extendRun(runs, key, t) {
  const list = runs.get(key) ?? [];
  const last = list.at(-1);
  if (last && Math.abs(last[1] - t) < step * 1.5) last[1] = +(t + step).toFixed(2);
  else list.push([+t.toFixed(2), +(t + step).toFixed(2)]);
  runs.set(key, list);
}

const film = openComposition(timeline, { faces: readTextMetrics() });
/* Reading load is measured as WCAG contrast against the ground: a label of at least 3:1 is legible; a label held
 * between 1.8:1 and 3:1 for more than a second is neither a usable recap nor gone, so it reads as faint clutter. The
 * ink level and the label, name and list rules are those of the real-browser check (geometry-check.mjs). */
const contrast = readingLoad(film.palette),
  levelOf = inkLevel(film.palette),
  inspectFrame = analysis(levelOf),
  nameFindings = nameRules(),
  lists = listTracker(),
  faintSeen = faintLabels();

/* Painted paths are recorded so labels crossing strokes or partly covered by fills are reported, and what the scene
 * itself paints outside the head band is counted, so speech over an empty picture is reported. Every paint is kept
 * for the frame's text layout. */
let paints;
function onPaint(paint) {
  const points = paint.subs.flat(),
    seq = ++paints.seq;
  paints.all.push(paint);
  if (paint.kind === "text") paints.texts.push(seq);
  if (paint.scene && !inHead(points)) {
    paints.level = Math.max(paints.level, levelOf(paint.color, paint.alpha));
    if (paint.alpha > INK) paints.ink++;
    if (paint.alpha > STRONG) paints.strong++;
  }
  if (paint.kind === "stroke" && paint.alpha > VISIBLE)
    paints.graphics.push({
      kind: "stroke",
      seq,
      alpha: paint.alpha,
      color: paint.color,
      width: paint.lineWidth * paint.scale,
      subs: paint.subs,
      scene: paint.scene,
    });
  else if (paint.kind === "fill" && points.length)
    paints.graphics.push({
      kind: "fill",
      seq,
      alpha: paint.alpha,
      color: paint.color,
      box: spanOf(points),
      scene: paint.scene,
    });
}
const layoutScene = (t) => timeline.segments.findLast((v) => v.start <= t)?.id;
const units = (v) => v.replace(/[^\p{L}\p{N}]/gu, "").toLowerCase();
const thoughts = timeline.segments.flatMap((seg) => {
  let k = 0;
  return seg.utterance_groups.map((group, index) => {
    const need = units(group).length,
      first = k;
    let n = 0;
    while (k < seg.words.length && n < need) n += units(seg.words[k++].text).length;
    return {
      scene: seg.id,
      index: index + 1,
      start: seg.words[first].start,
      end: seg.words[k - 1].end,
      box: null,
    };
  });
});

/* Render the frame at t and gather what the measures read: its layout and graphics, what its scene painted, where it
 * falls in the timeline and its scene words. */
function renderedFrame(t) {
  paints = { all: [], graphics: [], texts: [], seq: 0, ink: 0, strong: 0, level: 0 };
  const layout = film.render(t, onPaint);
  const segments = timeline.segments,
    at = segments.findLastIndex((v) => v.start <= t),
    seg = segments[at],
    following = segments[at + 1];
  const speaking = segments.find((v) => v.voice_start <= t && t < v.voice_end);
  // A pause within a chapter: a scene that follows another of its chapter, until half a second into its voice, or a
  // scene whose voice has ended while the next one of its chapter waits.
  const inChapter = at > 0 && segments[at - 1].chapter === seg.chapter && t < seg.voice_start + 0.5;
  const beforeNext = following && following.chapter === seg.chapter && t > seg.voice_end;
  // Words are read; marks such as "?", "≠" or a bare value are seen, so only text with letters counts.
  const labels = layout.texts.filter((v) => v.scene && v.role === "label" && /\p{L}/u.test(v.text));
  // fillText order matches registration order, so each label knows what was painted before it.
  layout.texts.forEach((v, i) => {
    v.seq = paints.texts[i];
  });
  const sceneGraphics = paints.graphics.filter((g) => g.scene);
  return {
    t,
    layout,
    paints: paints.all,
    graphics: paints.graphics,
    sceneGraphics,
    sceneMarks: sceneGraphics.filter((g) => g.alpha > 0.35).length,
    sceneTexts: layout.texts.filter((v) => v.scene && v.alpha > 0.35).length,
    ink: paints.ink,
    strong: paints.strong,
    level: paints.level,
    speaking,
    seg,
    following,
    inChapter,
    beforeNext,
    // The scene a frame that must paint answers for: the speaking scene, or in a pause within a chapter the scene
    // just begun or the one about to begin.
    mustPaint: speaking ? speaking.id : inChapter ? seg.id : beforeNext ? following.id : null,
    labels,
    legible: labels.filter((v) => contrast(v.color, v.alpha) >= 3),
  };
}

const errors = new Map(),
  overlaps = new Map(),
  outside = new Map(),
  collisions = new Map(),
  shapesOutside = new Map(),
  empty = new Map(),
  blank = new Map(),
  bare = new Map(),
  thin = new Map(),
  dim = new Map(),
  firstWords = {},
  density = new Map(),
  clutter = [],
  trace = [];
/* The visual system's positive layout measures: names placed by hand, more than two text sizes or a dot-joined name at
 * once, a list whose names do not leave together, and a stage whose content stands off the content centre. */
const unplaced = new Map(),
  sizes = new Map(),
  dotJoins = new Map();

/* Within a chapter the picture should never empty between scenes, even in a pause: near-empty frames around a cut,
 * keyed by the incoming scene. */
function blankBetweenScenes(f) {
  if ((f.inChapter || f.beforeNext) && f.sceneMarks + f.sceneTexts < 2)
    extendRun(blank, f.inChapter ? f.seg.id : f.following.id, f.t);
}
/* Between the first and last voice no frame should be bare ground, in speech or in a pause within a chapter. */
function bareFrames(f) {
  if (f.mustPaint && !f.ink) extendRun(bare, f.mustPaint, f.t);
}
/* No voiced frame, and no pause within a chapter, may dim below the ground level a viewer reads as empty. */
function dimFrames(f) {
  if (f.mustPaint && f.level < LEVEL) extendRun(dim, f.mustPaint, f.t);
}
/* A chapter's first scene stands at half its contrast when the first word is spoken. */
function firstWordLevels(f) {
  const opener = timeline.segments.find(
    (v, i) =>
      i > 0 &&
      timeline.segments[i - 1].chapter !== v.chapter &&
      v.voice_start <= f.t &&
      f.t < v.voice_start + step,
  );
  if (opener) firstWords[opener.id] = Math.round(f.level);
}
/* Speech over a frame holding fewer than three firm marks (above 25%) from all scenes reads as nearly empty. */
function thinSpeech(f) {
  if (f.speaking && f.strong < 3) extendRun(thin, f.speaking.id, f.t);
}
/* Speech over fewer than two firm marks and words of its scene plays over an empty picture. */
function emptySpeech(f) {
  if (f.speaking && f.sceneMarks + f.sceneTexts < 2) extendRun(empty, f.speaking.id, f.t);
}
/* TRACE: each scene name of every frame, a placed name whole, with its contrast and opacity. */
function labelTrace(f) {
  for (const v of f.labels)
    trace.push(
      `${f.t.toFixed(2)}\t${v.scene}\t${contrast(v.color, v.alpha).toFixed(2)}\t${v.alpha.toFixed(3)}\t${v.whole ?? v.text}`,
    );
}
/* A list's names are followed in every frame of their scene, voiced or not, so a name that leaves early is seen,
 * and the last frame a list is seen keeps its levels, so a list that leaves with part of it dimmed is seen. */
function listSets(f) {
  lists.see(f.labels, f.t, contrast);
}
/* Reading load counts names: a wrapped or growing name, or a term with its qualifier, is one name. */
function nameLoad(f) {
  if (!f.speaking) return;
  const found = nameFindings(f.labels, contrast);
  const entry = density.get(f.speaking.id) ?? { frames: 0, crowded: 0, peak: 0 };
  entry.frames++;
  if (found.some((v) => v.kind === "name_load")) entry.crowded++;
  entry.peak = Math.max(entry.peak, found.names);
  density.set(f.speaking.id, entry);
  const note = (map, key, value) => map.set(key, (map.get(key) ?? new Set()).add(value));
  for (const v of found) {
    if (v.kind === "unplaced_label") note(unplaced, v.scene, v.text);
    else if (v.kind === "dot_join") note(dotJoins, v.scene, v.text);
    else if (v.kind === "type_sizes") for (const size of v.sizes) note(sizes, f.speaking.id, size);
  }
}
/* Names the eye reads while the ear hears them: a name that repeats the caption standing with it, at least three
 * quarters of the caption's letters; and names set on more than two lines. Each is kept per scene with the first time
 * it was seen. */
const echoes = new Map(),
  longNames = new Map();
function labelEchoes(f) {
  if (!f.speaking) return;
  const caption = f.layout.texts.find((v) => v.role === "caption" && v.alpha > 0.5),
    said = caption ? units(caption.text) : "",
    lines = new Map();
  for (const v of f.legible) {
    const key = `${v.scene}\u0000${v.whole ?? v.text}`,
      ys = lines.get(key) ?? new Set();
    ys.add(Math.round((v.bounds[1] + v.bounds[3]) / 2));
    lines.set(key, ys);
  }
  for (const [key, ys] of lines) {
    const whole = key.split("\u0000")[1],
      name = units(whole);
    if (ys.size > 2 && !longNames.has(key)) longNames.set(key, +f.t.toFixed(2));
    if (
      said &&
      name &&
      said.includes(name) &&
      name.length >= 0.75 * said.length &&
      !echoes.has(key)
    )
      echoes.set(key, +f.t.toFixed(2));
  }
}
/* Labels held between 1.8:1 and 3:1 for more than a second. */
function faintClutter(f) {
  for (const run of faintSeen(f.labels, f.t, contrast))
    clutter.push({
      key: `${run.scene}|${run.text}`,
      start: +run.start.toFixed(2),
      end: +run.end.toFixed(2),
    });
}
/* The label and shape rules of the real-browser check: labels apart, inside the safe area and clear of shapes, and
 * shapes inside the action-safe area, each kept with the first frame and the evidence it was seen with. */
function labelsAndShapes(f) {
  const t = +f.t.toFixed(2);
  for (const v of inspectFrame(f.layout.texts, f.graphics)) {
    if (v.kind === "outside_safe_area") {
      const key = `${v.scene}:${v.text}`;
      if (!outside.has(key)) outside.set(key, { t, bounds: v.bounds.map(Math.round) });
    } else if (v.kind === "label_overlap") {
      const key = `${v.scene}:${v.pair.join("|")}`;
      if (!overlaps.has(key)) overlaps.set(key, t);
    } else if (v.kind.endsWith("_collision")) {
      const key = `${v.scene}:${v.text}|${v.shape}`;
      if (!collisions.has(key))
        collisions.set(key, {
          t,
          text: v.bounds.map(Math.round),
          graphic: v.graphic.map(Math.round),
        });
    } else if (v.kind.endsWith("_outside_action_safe")) {
      const key = `${layoutScene(f.t)}:${v.shape}`;
      if (!shapesOutside.has(key)) shapesOutside.set(key, { t, point: v.point.map(Math.round) });
    }
  }
}

const composition = compositionMeasures({ film, step, thoughts });
/* How the settled text of each voiced frame lines up: rows, columns, leading, cards, pitch and clearance. */
const typography = textLayout(step);
/* What each frame is measured for; the trace, the marks and the bounds only when their file is asked for. */
const measures = [
  blankBetweenScenes,
  bareFrames,
  dimFrames,
  firstWordLevels,
  thinSpeech,
  emptySpeech,
  ...(process.env.TRACE ? [labelTrace] : []),
  ...(process.env.MARKS ? [composition.seats] : []),
  listSets,
  nameLoad,
  composition.pictureBalance,
  composition.balanceThroughSpeech,
  composition.reviewedBalance,
  composition.containers,
  labelEchoes,
  composition.sparseSpeech,
  faintClutter,
  ...(process.env.BOUNDS ? [composition.paintedExtent] : []),
  labelsAndShapes,
  typography.frame,
];
function* frameTimes() {
  if (probe !== null) yield probe;
  else for (let t = from; t < to; t += step) yield t;
}
let frame;
for (const t of frameTimes()) {
  try {
    frame = renderedFrame(t);
  } catch (error) {
    // The frame reported in detail must render; a stretch of the film reports each failure once.
    if (probe !== null) throw error;
    const key = String(error.message);
    if (!errors.has(key)) errors.set(key, t);
    continue;
  }
  for (const measure of measures) measure(frame);
}
composition.finish();
if (probe !== null) {
  console.log(
    JSON.stringify(
      {
        texts: frame.layout.texts.map((v) => ({
          text: v.text,
          alpha: +v.alpha.toFixed(2),
          bounds: v.bounds.map(Math.round),
          seq: v.seq,
        })),
        strokes: frame.graphics
          .filter((g) => g.kind === "stroke")
          .map((g) => ({
            seq: g.seq,
            alpha: +g.alpha.toFixed(2),
            pts: g.subs.map((v) => [v[0], v.at(-1)].map((p) => p.map(Math.round))),
          })),
      },
      null,
      0,
    ),
  );
  process.exit(0);
}
const report = frameReport({
  from,
  to,
  step,
  errors,
  overlaps,
  outside,
  collisions,
  shapesOutside,
  empty,
  blank,
  bare,
  thin,
  dim,
  firstWords,
  density,
  clutter,
  unplaced,
  sizes,
  dotJoins,
  lists,
  thoughts,
  echoes,
  longNames,
  sparseRuns: composition.sparseRuns,
  offCentreRuns: composition.offCentreRuns,
  offCentreBuilds: composition.offCentreBuilds,
  offCentreSettled: composition.offCentreSettled,
  thinRuns: composition.thinRuns,
  underfilled: composition.underfilled,
  textLayout: typography.finish(),
});
writeRequestedFiles({
  trace,
  thoughts,
  marks: composition.marks,
  extents: composition.extents,
  drawn: composition.drawn,
});
console.log(JSON.stringify(report, null, 1));
process.exitCode = report.errors.length ? 1 : 0;
