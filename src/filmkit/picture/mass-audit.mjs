/** The mass audit: where the weight of the lit picture lies in each frame of an edition's uncaptioned stage, as the
 * fused DDWG film's rule 3 measures it (measure-balance-on-content, design decisions 1, 4 and 5).
 *
 * Its usage is `USAGE`, which it prints when it is invoked wrongly.
 *
 * It opens the stage as the renderer opens it (native-canvas.mjs, `openPicture`), with the text renderer it is given,
 * at the composition's own frame of 1920x1080, so that each cell of the reviewers' 480x270 grey is 4x4 pixels, and
 * draws it every MASS.step seconds; it encodes nothing. A wrapper of the context's paint methods, which only this
 * audit uses, draws the ground, a `fillRect` over the whole canvas at full opacity, so that each frame stands on the
 * composition's own ground and not on the frame before it, and the paints of the scene being drawn: `stroke`, `fill`,
 * `fillText` and `fillRect` while `window.__sceneId` names a scene. A stroke painted under DECLARED_FRAME_ROLE
 * (headless-composition.mjs) is counted for its scene and not drawn. A frame that paints a scene before it lays the
 * ground is refused: the canvas would still hold the frame before. Titles, chapter cards and credits drawn outside
 * every scene are not weighed; a title drawn inside a scene is. Each frame is read by `massLit` (rules/ink.mjs) over
 * the content band, rows 120 to 919 (REVIEWED_BAND), which leaves out the head band and the chip; the stage holds no
 * caption. A frame of MASS.cells lit cells or more has a mass centre, the mean of their centres, and the frames are
 * joined per scene drawn by `massRuns` (rules/balance.mjs).
 *
 * The report states the canvas and the step; each frame, with its time, the scene drawn (its ids joined by "+" where
 * a frame draws several), its lit cells and its mass centre; `off_centre_mass`, each run per scene with its span and
 * largest signed offset in px; `mass_balance`, per scene, the frames with a mass, the frames too faint to weigh, the
 * declared frame strokes left out, the median offsets from the content centre and the share of frames within 90 px;
 * and `outside_scenes`, the frames that draw no scene. It exits 0 whatever it finds: the picture gate refuses by the
 * report (filmkit.picture.gates). */
import { realpathSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

import { DECLARED_FRAME_ROLE } from "./headless-composition.mjs";
import { openPicture } from "./native-canvas.mjs";
import { CONTENT_CENTRE, MASS, massRuns, REVIEWED_BAND } from "./rules/balance.mjs";
import { massLit } from "./rules/ink.mjs";

const SELF = fileURLToPath(import.meta.url);
const USAGE = "Usage: node mass-audit.mjs <stage> --text-renderer <name>";
// The composition's own frame width, at which every coordinate of a composition is its own.
const WIDTH = 1920;

const median = (values) => {
  if (!values.length) return null;
  const sorted = values.slice().sort((a, b) => a - b),
    middle = sorted.length >> 1;
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
};
const rounded = (value, places = 2) => (value === null ? null : +value.toFixed(places));

/* Whether a fillRect(x, y, w, h) lays the ground: it covers the whole canvas at full opacity, under a transform that
 * only scales and moves. */
function laysGround(context, [x, y, w, h]) {
  const { a, b, c, d, e, f } = context.getTransform(),
    xs = [a * x + e, a * (x + w) + e],
    ys = [d * y + f, d * (y + h) + f];
  return (
    b === 0 &&
    c === 0 &&
    context.globalAlpha === 1 &&
    Math.min(...xs) <= 0 &&
    Math.max(...xs) >= context.canvas.width &&
    Math.min(...ys) <= 0 &&
    Math.max(...ys) >= context.canvas.height
  );
}

/* Wrap the context's paint methods so that a frame draws only the ground and what the mass weighs. `take()` gives the
 * scenes the frame last drawn painted in, joined by "+", or null; the declared frame strokes it left out; and the
 * first paint of a scene it drew before laying the ground, or null. */
function weighOnly(context, window) {
  let scenes = new Set(),
    declared = 0,
    grounded = false,
    ungrounded = null;
  for (const name of ["stroke", "fill", "fillText", "fillRect"]) {
    const paint = context[name];
    context[name] = (...args) => {
      const scene = window.__sceneId ?? null,
        ground = name === "fillRect" && laysGround(context, args);
      grounded ||= ground;
      if (scene === null) return ground ? paint.apply(context, args) : undefined;
      scenes.add(scene);
      if (name === "stroke" && window.__paintRole === DECLARED_FRAME_ROLE) {
        declared++;
        return undefined;
      }
      if (!grounded) ungrounded ??= `${name} in scene ${scene}`;
      return paint.apply(context, args);
    };
  }
  return {
    take() {
      const taken = { scene: [...scenes].sort().join("+") || null, declared, ungrounded };
      scenes = new Set();
      declared = 0;
      grounded = false;
      ungrounded = null;
      return taken;
    },
  };
}

/** Measure the mass of every frame of the stage in `stage`, drawn with `textRenderer`: the report. */
export function measureMass(stage, textRenderer) {
  const picture = openPicture(stage, textRenderer, WIDTH),
    { canvas, record, window } = picture;
  // A record without a duration would give no frame and so no finding.
  if (!(Number(record.duration) > 0))
    throw Error(`The record of ${stage} names no duration; stage the picture again`);
  const weighed = weighOnly(canvas.getContext("2d", { alpha: false }), window);
  const [cx, cy] = CONTENT_CENTRE,
    runs = massRuns(MASS.step),
    frames = [],
    scenes = {};
  let outside = 0;
  for (let k = 0; k * MASS.step < record.duration - 1e-9; k++) {
    const t = k * MASS.step;
    picture.renderFrame(t);
    const { scene, declared, ungrounded } = weighed.take();
    if (ungrounded)
      throw Error(
        `The frame at ${rounded(t, 3)} s of ${stage} lays no ground over the whole canvas with fillRect before it ` +
          `paints (${ungrounded}); the mass audit cannot clear the frame before it`,
      );
    const lit = massLit(canvas.data(), canvas.width, REVIEWED_BAND);
    const centre =
      scene !== null && lit.cells >= MASS.cells ? [lit.x / lit.cells, lit.y / lit.cells] : null;
    runs.frame(t, scene, centre);
    frames.push({
      t: rounded(t, 3),
      scene,
      cells: lit.cells,
      centre: centre?.map((v) => rounded(v)) ?? null,
    });
    if (scene === null) {
      outside++;
      continue;
    }
    const seen = (scenes[scene] ??= { frames: 0, faint: 0, declared: 0, dx: [], dy: [] });
    seen.declared += declared;
    if (centre === null) seen.faint++;
    else {
      seen.frames++;
      seen.dx.push(centre[0] - cx);
      seen.dy.push(centre[1] - cy);
    }
  }
  const found = runs.finish();
  return {
    canvas: [canvas.width, canvas.height],
    step: MASS.step,
    frames,
    off_centre_mass: Object.fromEntries(
      Object.entries(Object.groupBy(found, (run) => run.scene)).map(([id, list]) => [
        id,
        list.map((v) => `${v.start.toFixed(2)}-${v.end.toFixed(2)} ${v.worst.toFixed(1)} px`),
      ]),
    ),
    mass_balance: Object.fromEntries(
      Object.entries(scenes).map(([id, v]) => [
        id,
        {
          frames: v.frames,
          faint: v.faint,
          declared: v.declared,
          median_dx: rounded(median(v.dx), 1),
          median_dy: rounded(median(v.dy), 1),
          within: v.frames
            ? rounded(v.dx.filter((dx) => Math.abs(dx) <= MASS.px).length / v.frames, 3)
            : null,
        },
      ]),
    ),
    outside_scenes: outside,
  };
}

if (process.argv[1] && realpathSync(process.argv[1]) === SELF) {
  let parsed;
  try {
    parsed = parseArgs({
      allowPositionals: true,
      options: { "text-renderer": { type: "string" } },
    });
  } catch (error) {
    console.error(`${error.message}\n${USAGE}`);
    process.exit(2);
  }
  const { values, positionals } = parsed;
  if (positionals.length !== 1 || !values["text-renderer"]) {
    console.error(USAGE);
    process.exit(2);
  }
  console.log(JSON.stringify(measureMass(positionals[0], values["text-renderer"])));
}
