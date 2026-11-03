/* What the frame audit reports of the frames it measured, and the files its measures are asked to write. */
import { writeFileSync } from "node:fs";

import { BALANCE_LIMITS, COVER_LIMITS } from "../rules/balance.mjs";

/* A chapter's first word needs 90 levels. */
const FIRST_WORD = 90;
/* Each thought's picture, the union of its firm marks and legible names, is balanced on the content centre (within 8%
 * of the safe width and height) and fills at least half the safe width or two fifths of its height. */
const CENTRE = [960, 500],
  OFF = [0.08 * 1728, 0.08 * 972],
  FILL = [0.5 * 1728, 0.4 * 972];
/* The smallest share of the frame a thought's picture may cover two seconds in and 70% through. */
const AREA = 0.1;

/* Runs per scene, each as its span and its worst share in percent. */
const runsByScene = (runs) =>
  Object.fromEntries(
    Object.entries(Object.groupBy(runs, (v) => v.scene)).map(([id, list]) => [
      id,
      list.map((v) => `${v.start.toFixed(2)}-${v.end.toFixed(2)} ${(v.worst * 100).toFixed(1)}%`),
    ]),
  );

export function frameReport({
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
  sparseRuns,
  offCentreRuns,
  thinRuns,
  underfilled,
}) {
  const listsLeft = Object.groupBy(lists.findings(), (v) =>
    v.kind === "list_leaving_early" ? "early" : "dimmed",
  );
  return {
    frames_checked: Math.ceil((to - from) / step),
    errors: [...errors].map(([message, t]) => ({ message, t: +t.toFixed(2) })),
    overlaps: [...overlaps].map(([pair, t]) => ({ pair, t })),
    outside_safe_area: [...outside].map(([text, v]) => ({ text, ...v })),
    graphic_collisions: [...collisions].map(([pair, v]) => ({ pair, ...v })),
    empty_during_speech: Object.fromEntries(
      [...empty]
        .map(([id, runs]) => [id, runs.filter(([a, b]) => b - a > 0.5)])
        .filter(([, runs]) => runs.length),
    ),
    /* Near-empty frames longer than 0.15 s around a cut within a chapter, keyed by the incoming scene. */
    blank_between_scenes: Object.fromEntries(
      [...blank]
        .map(([id, runs]) => [id, runs.filter(([a, b]) => b - a > 0.15)])
        .filter(([, runs]) => runs.length),
    ),
    /* Every frame of bare ground (no scene paint above 4%) within the voiced film, keyed by the speaking or incoming scene;
     * the real-browser gate refuses even one. */
    bare_frames: Object.fromEntries([...bare].filter(([, runs]) => runs.length)),
    /* Every voiced frame, or frame in a pause within a chapter, whose brightest scene mark rises less than 30 levels
     * above the ground, keyed by the speaking or incoming scene. */
    dim_frames: Object.fromEntries([...dim].filter(([, runs]) => runs.length)),
    /* Chapter openers whose first scene shows less than 90 levels on the first word. */
    faint_first_words: Object.fromEntries(
      Object.entries(firstWords).filter(([, v]) => v < FIRST_WORD),
    ),
    /* Voiced runs longer than 0.1 s with fewer than three firm marks from all scenes, keyed by the speaking scene. */
    thin_during_speech: Object.fromEntries(
      [...thin]
        .map(([id, runs]) => [id, runs.filter(([a, b]) => b - a > 0.1)])
        .filter(([, runs]) => runs.length),
    ),
    shapes_outside_action_safe: [...shapesOutside].map(([key, v]) => ({ key, ...v })),
    /* Voiced frames with more than twelve names of at least 3:1 contrast, a wrapped or growing name counted once; none
     * may exceed it. DENSITY_ALL=1 lists every scene's peak. */
    name_load: Object.fromEntries(
      [...density]
        .map(([id, v]) => [id, { crowded: +(v.crowded / v.frames).toFixed(2), peak: v.peak }])
        .filter(([, v]) => process.env.DENSITY_ALL || v.crowded > 0),
    ),
    /* Legible names that no layout primitive placed, per scene. */
    unplaced_labels: Object.fromEntries(
      [...unplaced].map(([id, set]) => [id, [...set].slice(0, 12)]),
    ),
    /* Scenes showing more than two text sizes at once, with the sizes seen. */
    type_sizes: Object.fromEntries(
      [...sizes].map(([id, set]) => [id, [...set].sort((a, b) => a - b)]),
    ),
    /* Names that join items with a middle dot instead of a structure. */
    dot_joins: Object.fromEntries([...dotJoins].map(([id, set]) => [id, [...set]])),
    /* Lists whose names do not leave together: names that stop being legible more than 0.6 s before the last of their set. */
    lists_leaving_early: Object.fromEntries(
      Object.entries(Object.groupBy(listsLeft.early ?? [], (v) => `${v.scene}:${v.set}`)).map(
        ([key, names]) => [key, names.map((v) => `${v.name}@${v.at.toFixed(1)}`)],
      ),
    ),
    /* Lists that leave with part of the set dimmed: in the last frame the list is seen, a name below 90% of the
     * brightest name of its set in the same colour (a refused name is muted by design). A list leaves whole. */
    lists_leaving_dimmed: Object.fromEntries(
      Object.entries(Object.groupBy(listsLeft.dimmed ?? [], (v) => `${v.scene}:${v.set}`)).map(
        ([key, names]) => [
          key,
          `${names[0].at.toFixed(2)}: ${names.map((v) => `${v.name} ${v.share.toFixed(2)}`).join(", ")}`,
        ],
      ),
    ),
    /* Thoughts whose picture stands off the content centre or fills too little of the frame, with its centre and size. */
    off_balance: Object.fromEntries(
      Object.entries(
        Object.groupBy(
          thoughts
            .filter((v) => v.box)
            .map((v) => {
              const [x0, y0, x1, y1] = v.box,
                cx = (x0 + x1) / 2,
                cy = (y0 + y1) / 2,
                w = x1 - x0,
                h = y1 - y0;
              const off = Math.abs(cx - CENTRE[0]) > OFF[0] || Math.abs(cy - CENTRE[1]) > OFF[1],
                small = w < FILL[0] && h < FILL[1];
              return off || small
                ? {
                    scene: v.scene,
                    at: `${v.scene}.${v.index}`,
                    centre: [Math.round(cx), Math.round(cy)],
                    size: [Math.round(w), Math.round(h)],
                  }
                : null;
            })
            .filter(Boolean),
          (v) => v.scene,
        ),
      ).map(([id, list]) => [id, list.map((v) => `${v.at}@${v.centre}:${v.size.join("x")}`)]),
    ),
    /* Thoughts whose picture stands beyond the reviewers' limit off the content centre at one of their instants, with the
     * instant and the offsets as percentages of the frame's width and height. */
    off_centre: Object.fromEntries(
      Object.entries(
        Object.groupBy(
          thoughts.flatMap((v) =>
            Object.entries(v.offsets ?? {})
              .filter(
                ([name, [dx, dy]]) => Math.max(Math.abs(dx), Math.abs(dy)) > BALANCE_LIMITS[name],
              )
              .map(([name, [dx, dy]]) => ({
                scene: v.scene,
                row: `${v.scene}.${v.index} ${name} ${Math.round(dx * 100)}%/${Math.round(dy * 100)}%`,
              })),
          ),
          (v) => v.scene,
        ),
      ).map(([id, list]) => [id, list.map((v) => v.row)]),
    ),
    /* Names equal to the caption standing with them, or sentence-long names it contains, per scene, with when each was
     * first seen; and names set on more than two lines. */
    caption_echoes: Object.fromEntries(
      Object.entries(Object.groupBy([...echoes], ([key]) => key.split("\u0000")[0])).map(
        ([id, list]) => [id, list.map(([key, t]) => `${key.split("\u0000")[1]}@${t}`)],
      ),
    ),
    long_names: Object.fromEntries(
      Object.entries(Object.groupBy([...longNames], ([key]) => key.split("\u0000")[0])).map(
        ([id, list]) => [id, list.map(([key, t]) => `${key.split("\u0000")[1]}@${t}`)],
      ),
    ),
    /* Runs of 1.5 s or more of speech whose visible marks cover under 4% of the content band, per scene. */
    sparse_runs: Object.fromEntries(
      Object.entries(Object.groupBy(sparseRuns, (v) => v.scene)).map(([id, runs]) => [
        id,
        runs.map((v) => `${v.start.toFixed(2)}-${v.end.toFixed(2)} ${(v.least * 100).toFixed(1)}%`),
      ]),
    ),
    /* Runs of 2 s or more of speech whose lit picture stands more than 12% off the content centre, or covers less than
     * a tenth of the band, per scene, with their span and the largest offset or the least cover. */
    off_centre_runs: runsByScene(offCentreRuns),
    thin_runs: runsByScene(thinRuns),
    /* Thoughts whose lit picture covers less than the reviewers' share of the band at one of their instants, with the
     * instant and the share. */
    thin_lit: Object.fromEntries(
      Object.entries(
        Object.groupBy(
          thoughts.flatMap((v) =>
            Object.entries(v.covers ?? {})
              .filter(([name, cover]) => cover < COVER_LIMITS[name])
              .map(([name, cover]) => ({
                scene: v.scene,
                row: `${v.scene}.${v.index} ${name} ${(cover * 100).toFixed(1)}%`,
              })),
          ),
          (v) => v.scene,
        ),
      ).map(([id, list]) => [id, list.map((v) => v.row)]),
    ),
    /* Containers that stood less than half filled through more than a second of speech, per scene: the kind, the box, the
     * run and its least fill. */
    underfilled_containers: Object.fromEntries(
      Object.entries(Object.groupBy(underfilled, (v) => v.scene)).map(([id, runs]) => [
        id,
        runs.map(
          (v) =>
            `${v.kind} ${v.box.join(",")} ${v.start.toFixed(2)}-${v.end.toFixed(2)} ${Math.round(v.least * 100)}%`,
        ),
      ]),
    ),
    /* Thoughts whose picture covers less than a tenth of the frame two seconds in or 70% through, with both shares, and
     * the median shares over all thoughts. */
    sparse_beats: (() => {
      const rows = thoughts.filter((v) => v.areas),
        med = (k) => {
          const a = rows
            .map((v) => v.areas[k])
            .filter((v) => v !== undefined)
            .sort((p, q) => p - q);
          return a.length ? +a[a.length >> 1].toFixed(3) : null;
        };
      return {
        median_two: med("two"),
        median_late: med("late"),
        thoughts: rows
          .filter((v) => (v.areas.two ?? 1) < AREA || (v.areas.late ?? 1) < AREA)
          .map(
            (v) =>
              `${v.scene}.${v.index}@${(v.areas.two ?? NaN).toFixed(3)}/${(v.areas.late ?? NaN).toFixed(3)}`,
          ),
      };
    })(),
    /* Labels held between 1.8:1 and 3:1 for more than a second, per scene: total seconds and the longest runs. */
    faint_clutter: Object.fromEntries(
      Object.entries(Object.groupBy(clutter, (v) => v.key.split("|")[0])).map(([id, runs]) => [
        id,
        {
          seconds: +runs.reduce((n, v) => n + v.end - v.start, 0).toFixed(1),
          longest: runs.sort((a, b) => b.end - b.start - (a.end - a.start)).slice(0, 3),
        },
      ]),
    ),
  };
}

export function writeRequestedFiles({ trace, thoughts, marks, extents, drawn }) {
  if (process.env.TRACE) writeFileSync(process.env.TRACE, trace.join("\n") + "\n");
  if (process.env.BALANCE)
    writeFileSync(
      process.env.BALANCE,
      JSON.stringify(
        thoughts.flatMap((v) =>
          Object.entries(v.covers ?? {}).map(([at, cover]) => ({
            thought: `${v.scene}.${v.index}`,
            at,
            dx: v.offsets?.[at] ? +(v.offsets[at][0] * 100).toFixed(1) : null,
            dy: v.offsets?.[at] ? +(v.offsets[at][1] * 100).toFixed(1) : null,
            cover: +(cover * 100).toFixed(1),
          })),
        ),
      ) + "\n",
    );
  if (process.env.MARKS) writeFileSync(process.env.MARKS, marks.join("\n") + "\n");
  if (process.env.BOUNDS)
    writeFileSync(
      process.env.BOUNDS,
      JSON.stringify(
        Object.fromEntries(
          Object.entries(extents).map(([id, e]) => [
            id,
            {
              box: e.box.map(Math.round),
              drawn: (drawn[id] ?? []).map(Math.round),
              mean_frame_area: +(e.area / Math.max(1, e.frames)).toFixed(3),
            },
          ]),
        ),
        null,
        1,
      ) + "\n",
    );
}
