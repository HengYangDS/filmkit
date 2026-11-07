/** Prove at the composition that an edition's uncaptioned picture differs from its captioned one only by its captions.
 *
 * The composition runs headlessly (headless-composition.mjs) twice in one process: on the edition's timeline, as the
 * captioned picture's stage holds it, and on the same timeline with no captions, as the uncaptioned picture's stage
 * holds it. Both render the same instants in the same order: every caption's start, middle and end and every `step`
 * seconds of the film. At each instant the uncaptioned frame's paints must equal the captioned frame's, in order, once
 * the captioned frame's caption paints are taken out. A caption paint is a text painted outside every scene whose
 * letters and digits are those of the display text of a cue in force: the cue that started last at the instant, which
 * the painter may hold through a gap, or the next one, which it may lead into; and the frame's layout must name such a
 * text in the caption role. Every other difference is a finding, at its instant: a captioned paint that the
 * uncaptioned frame lacks or changes, or a paint only the uncaptioned frame holds. So a film that paints anything else
 * from its captions is found out.
 *
 * The report, printed as JSON, gives the instants, the counts of paints compared and of caption paints, the cues whose
 * middle shows a caption paint, the band the caption paints cover in the composition's 1920x1080 frame, and the
 * findings, the first FINDINGS of them in full.
 * Usage: python -m filmkit.tools caption-equivalence <timeline.json> [<step>] */
import { isDeepStrictEqual, parseArgs } from "node:util";

import { openComposition, readTextMetrics, readTimeline } from "./headless-composition.mjs";

const USAGE = "Usage: python -m filmkit.tools caption-equivalence <timeline.json> [<step>]";
/* How many findings the report holds in full; it counts them all. */
const FINDINGS = 20;

/** The letters and digits of a text, by which a caption paint is matched to its cue. */
export const letters = (text) => String(text ?? "").replace(/[^\p{L}\p{N}]/gu, "");

/** The instants both compositions render, in order: every `step` seconds from the start, and every caption's start,
 * middle and end, each once and before the film's end. */
export function instants(timeline, step) {
  const times = new Set();
  for (let k = 0; k * step < timeline.duration; k++) times.add(k * step);
  for (const cue of timeline.captions ?? [])
    for (const t of [cue.start, (cue.start + cue.end) / 2, cue.end])
      if (t >= 0 && t < timeline.duration) times.add(t);
  return [...times].sort((a, b) => a - b);
}

/** The cues a caption painter may show at `t`: the one that started last at or before it, and the next one. */
export function cuesInForce(captions, t) {
  const last = captions.findLastIndex((cue) => cue.start <= t);
  return [captions[last], captions[last + 1]].filter(Boolean);
}

/* A paint as two frames are compared by it: everything it carries but its transform function. */
const comparable = (paint) =>
  Object.fromEntries(Object.entries(paint).filter(([, value]) => typeof value !== "function"));

/* Where a paint stands on the screen: a text's box, or the span of its subpaths. */
function screenBox(paint) {
  const points =
    paint.kind === "text" && paint.points?.length === 2
      ? paint.points.map(paint.toScreen)
      : (paint.subs ?? []).flat();
  if (!points.length) return null;
  const xs = points.map(([x]) => x),
    ys = points.map(([, y]) => y);
  return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
}

/* A paint as a finding names it. */
function described(paint) {
  if (!paint) return null;
  const box = screenBox(paint);
  return {
    kind: paint.kind,
    scene: paint.scene,
    ...(paint.kind === "text" ? { text: paint.text } : {}),
    color: paint.color,
    alpha: paint.alpha,
    box: box && box.map((v) => Math.round(v * 10) / 10),
  };
}

/** Whether a paint of the captioned frame at `t` is one of its caption paints. */
export function isCaptionPaint(paint, t, captions, layout) {
  if (paint.kind !== "text" || paint.scene !== null) return false;
  const painted = letters(paint.text);
  if (!painted) return false;
  const named = (layout?.texts ?? []).some(
    (record) => record.role === "caption" && letters(record.text) === painted,
  );
  return (
    named &&
    cuesInForce(captions, t).some((cue) => letters(cue.display_text ?? cue.text) === painted)
  );
}

/** Compare one instant's frames: walk the captioned paints in order, matching each to the next uncaptioned paint and
 * setting aside a caption paint that has none; the first other difference is the frame's finding. Returns the caption
 * paints set aside, how many paints matched and the finding, or null. */
export function compareFrame(captioned, uncaptioned, isCaption) {
  const removed = [];
  let next = 0;
  for (const paint of captioned) {
    if (
      next < uncaptioned.length &&
      isDeepStrictEqual(comparable(paint), comparable(uncaptioned[next]))
    ) {
      next++;
      continue;
    }
    if (isCaption(paint)) {
      removed.push(paint);
      continue;
    }
    return {
      removed,
      matched: next,
      finding: { captioned: described(paint), uncaptioned: described(uncaptioned[next]) },
    };
  }
  const extra = uncaptioned[next];
  return {
    removed,
    matched: next,
    finding: extra ? { captioned: null, uncaptioned: described(extra) } : null,
  };
}

/** Run both compositions on `timeline` at its instants and report how their frames differ. */
export function equivalence(timeline, { step = 0.5, faces = null } = {}) {
  const captions = timeline.captions ?? [];
  const captioned = openComposition(timeline, { faces }),
    uncaptioned = openComposition({ ...timeline, captions: [] }, { faces });
  const times = instants(timeline, step),
    middles = new Set(captions.map((cue) => (cue.start + cue.end) / 2));
  const findings = [],
    shownCues = new Set();
  let paints = 0,
    removedPaints = 0,
    framesWithCaptions = 0,
    band = null;
  for (const t of times) {
    const ours = [],
      theirs = [];
    const layout = captioned.render(t, (paint) => ours.push(paint));
    uncaptioned.render(t, (paint) => theirs.push(paint));
    const frame = compareFrame(ours, theirs, (paint) => isCaptionPaint(paint, t, captions, layout));
    paints += ours.length;
    removedPaints += frame.removed.length;
    if (frame.removed.length) framesWithCaptions++;
    for (const paint of frame.removed) {
      const box = screenBox(paint);
      if (box)
        band = band
          ? [
              Math.min(band[0], box[0]),
              Math.min(band[1], box[1]),
              Math.max(band[2], box[2]),
              Math.max(band[3], box[3]),
            ]
          : box;
      if (middles.has(t))
        for (const cue of cuesInForce(captions, t))
          if (letters(cue.display_text ?? cue.text) === letters(paint.text)) shownCues.add(cue);
    }
    if (frame.finding) findings.push({ time: t, ...frame.finding });
  }
  return {
    format: "caption-equivalence",
    duration: timeline.duration,
    step,
    instants: times.length,
    cues: captions.length,
    cues_shown_at_their_middle: shownCues.size,
    paints_compared: paints,
    caption_paints: removedPaints,
    frames_with_captions: framesWithCaptions,
    band: band && {
      left: Math.floor(band[0]),
      top: Math.floor(band[1]),
      right: Math.ceil(band[2]),
      bottom: Math.ceil(band[3]),
    },
    differing_instants: findings.length,
    findings: findings.slice(0, FINDINGS),
    verdict: findings.length ? "differs" : "equivalent",
  };
}

if (import.meta.main) {
  let positionals = [];
  try {
    ({ positionals } = parseArgs({ allowPositionals: true }));
  } catch (error) {
    console.error(error.message);
  }
  const step = positionals.length === 2 ? Number(positionals[1]) : 0.5;
  if (!positionals.length || positionals.length > 2 || !(step > 0)) {
    console.error(USAGE);
    process.exitCode = 2;
  } else {
    const report = equivalence(readTimeline(positionals[0]), { step, faces: readTextMetrics() });
    console.log(JSON.stringify(report));
  }
}
