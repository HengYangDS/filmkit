/* The frame audit's text-layout measures: how the settled names and marks of each voiced frame line up.
 *
 * layout.mjs reads a frame's settled text and marks into lines, names, containers, blocks and columns, and
 * measures.mjs finds its ragged rows and columns, crammed lines, names off their card's centre, uneven pitch and
 * touching marks; case.mjs finds the sets and rows of names that begin in both cases. Each measure's findings are joined over consecutive voiced frames into runs per scene and texts, and
 * a run of 1 s or more is kept with its start, its end, its texts and the offsets of its worst frame. Every measure
 * rests on exact anchors, sizes and baselines and on the widths the canvas stand-in measures, which are the film's own
 * when the audit is given its faces; a text's height keeps the estimate. */
import { mixedCase } from "./case.mjs";
import { frameLayout } from "./layout.mjs";
import {
  crammedLines,
  offCardCentre,
  raggedColumns,
  raggedRows,
  touchingMarks,
  unevenPitch,
} from "./measures.mjs";

/* A run must last this long, so a passing build-up or a fade is not a defect. */
const RUN_SECONDS = 1;

/** The text-layout findings of one frame's paints, each with its measure, scene, texts, severity and offsets. */
export function frameFindings(paints) {
  const layout = frameLayout(paints);
  return [
    ...raggedRows(layout),
    ...raggedColumns(layout),
    ...crammedLines(layout),
    ...offCardCentre(layout),
    ...unevenPitch(layout),
    ...touchingMarks(layout),
    ...mixedCase(layout),
  ];
}

/** The measures the frame audit reports, in its order. */
export const TEXT_LAYOUT = [
  "ragged_rows",
  "ragged_columns",
  "crammed_lines",
  "off_card_centre",
  "uneven_pitch",
  "touching_marks",
  "mixed_case",
];

/** Joins each voiced frame's findings, sampled every `step` seconds, into runs. `frame(f)` reads the frame audit's
 * frame: its time, whether it is voiced and its paints; a frame without speech ends every run. `finish()` returns, for
 * each measure, its runs of 1 s or more, each with its scene, start, end, texts and the offsets of its worst frame. */
export function textLayout(step) {
  const open = new Map(),
    runs = Object.fromEntries(TEXT_LAYOUT.map((kind) => [kind, []]));
  const close = (id) => {
    const run = open.get(id);
    open.delete(id);
    // Within half a step: the gate's step, a thirtieth of a second to seven places, makes 30 frames 0.999999 s.
    if (run.end - run.start >= RUN_SECONDS - step / 2) runs[run.kind].push(run);
  };
  return {
    frame(f) {
      const seen = new Set();
      for (const v of f.speaking ? frameFindings(f.paints) : []) {
        const id = [v.kind, v.scene, v.detail.edge ?? "", ...v.texts].join("\u0000"),
          run = open.get(id);
        if (seen.has(id)) {
          if (v.severity > run.severity)
            Object.assign(run, { severity: v.severity, detail: v.detail });
          continue;
        }
        seen.add(id);
        if (run && Math.abs(run.end - f.t) < step / 2) {
          run.end = f.t + step;
          if (v.severity > run.severity)
            Object.assign(run, { severity: v.severity, detail: v.detail });
          continue;
        }
        if (run) close(id);
        open.set(id, { ...v, start: f.t, end: f.t + step });
      }
      for (const id of [...open.keys()]) if (!seen.has(id)) close(id);
    },
    finish() {
      for (const id of [...open.keys()]) close(id);
      for (const list of Object.values(runs))
        list.sort((a, b) => a.start - b.start || a.texts.join().localeCompare(b.texts.join()));
      return runs;
    },
  };
}
