/** Prove at the composition that the rows a derived uncaptioned picture paints hold caption paints and nothing else.
 *
 * The composition runs headlessly (headless-composition.mjs) on the edition's timeline at every frame of `fps`, 30
 * unless given, the frame audit's own step. `top` and `bottom` bound the painted rows in the composition's 1920x1080
 * frame. At each instant every caption paint (caption-equivalence.mjs: a text outside every scene that carries a cue's
 * display text and that the frame's layout names as a caption) must lie within those rows, and no other paint may
 * reach them: a stroke reaches as far as half its width beyond its path, and a paint drawn at no opacity reaches
 * nothing. A caption that leaves the rows is an escape and another paint that reaches them an intrusion; either makes
 * the verdict `refuse`, since painting the rows would then cut a caption or cover a mark.
 *
 * The report, printed as JSON, gives the instants, the count of instants that paint a caption, the first and the last
 * row any caption paint reached (`caption_rows`), the stretches without a caption as [first instant, last instant] in
 * seconds, in which the captioned picture's band must show the ground, and the escapes and intrusions, the first
 * FINDINGS of each in full. The stand-in reports no fillRect, so a rectangle
 * filled that way in the rows is not seen here.
 * Usage: python -m filmkit.tools band-audit <timeline.json> <top> <bottom> [<fps>] */
import { parseArgs } from "node:util";

import { isCaptionPaint, screenBox } from "./caption-equivalence.mjs";
import { openComposition, readTextMetrics, readTimeline } from "./headless-composition.mjs";

const USAGE = "Usage: python -m filmkit.tools band-audit <timeline.json> <top> <bottom> [<fps>]";
/* How many escapes and intrusions the report holds in full; it counts them all. */
const FINDINGS = 20;
/* The instants a second holds unless the caller names another count. */
export const FPS = 30;

const rounded = (box) => box.map((v) => Math.round(v * 10) / 10);

/* A paint as a finding names it, at its instant. */
function described(paint, box, time) {
  return {
    time,
    kind: paint.kind,
    scene: paint.scene,
    ...(paint.kind === "text" ? { text: paint.text } : {}),
    alpha: paint.alpha,
    box: rounded(box),
  };
}

/** Audit the rows from `top` to `bottom` of the composition's frame on `timeline` at every frame of `fps`. */
export function bandAudit(timeline, [top, bottom], { fps = FPS, faces = null } = {}) {
  const captions = timeline.captions ?? [],
    film = openComposition(timeline, { faces }),
    count = Math.ceil(timeline.duration * fps - 1e-9);
  const escapes = [],
    intrusions = [],
    free = [];
  let captionInstants = 0,
    escaping = 0,
    intruding = 0,
    paints = 0,
    captionRows = null,
    open = null;
  for (let k = 0; k < count; k++) {
    const t = k / fps,
      frame = [];
    const layout = film.render(t, (paint) => frame.push(paint));
    let captioned = false,
      escaped = false,
      intruded = false;
    paints += frame.length;
    for (const paint of frame) {
      const box = screenBox(paint);
      if (isCaptionPaint(paint, t, captions, layout)) {
        captioned = true;
        if (box)
          captionRows = captionRows
            ? [Math.min(captionRows[0], box[1]), Math.max(captionRows[1], box[3])]
            : [box[1], box[3]];
        if (box && (box[1] < top || box[3] > bottom)) {
          escaped = true;
          if (escapes.length < FINDINGS) escapes.push(described(paint, box, t));
        }
        continue;
      }
      if (!box || paint.alpha === 0) continue;
      const reach = paint.kind === "stroke" ? ((paint.lineWidth ?? 0) * (paint.scale ?? 1)) / 2 : 0;
      if (box[3] + reach > top && box[1] - reach < bottom) {
        intruded = true;
        if (intrusions.length < FINDINGS) intrusions.push(described(paint, box, t));
      }
    }
    escaping += escaped;
    intruding += intruded;
    if (captioned) {
      captionInstants++;
      open = null;
    } else if (open) open[1] = t;
    else free.push((open = [t, t]));
  }
  return {
    format: "band-audit",
    duration: timeline.duration,
    fps,
    instants: count,
    rows: [top, bottom],
    paints,
    caption_instants: captionInstants,
    caption_rows: captionRows && [Math.floor(captionRows[0]), Math.ceil(captionRows[1])],
    free,
    escaping_instants: escaping,
    intruding_instants: intruding,
    escapes,
    intrusions,
    verdict: escaping || intruding ? "refuse" : "pass",
  };
}

if (import.meta.main) {
  let positionals = [];
  try {
    ({ positionals } = parseArgs({ allowPositionals: true }));
  } catch (error) {
    console.error(error.message);
  }
  const [path, top, bottom, rate = String(FPS)] = positionals;
  const rows = [Number(top), Number(bottom)],
    fps = Number(rate);
  if (
    positionals.length < 3 ||
    positionals.length > 4 ||
    !(rows[0] >= 0 && rows[1] > rows[0]) ||
    !(fps > 0)
  ) {
    console.error(USAGE);
    process.exitCode = 2;
  } else {
    const report = bandAudit(readTimeline(path), rows, { fps, faces: readTextMetrics() });
    console.log(JSON.stringify(report));
    if (report.verdict !== "pass") process.exitCode = 1;
  }
}
