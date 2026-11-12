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

/** The reviewers' limits through speech, not only at their instants: a stretch of RUN_SECONDS or more of one scene's
 * speech through which the lit box stands more than RUN_OFFSET of the frame's width or height off the content centre,
 * or covers less than RUN_COVER of the band, is a run. */
export const RUN_SECONDS = 2,
  RUN_OFFSET = BALANCE_LIMITS.two,
  RUN_COVER = COVER_LIMITS.late;

/** Joins frames sampled every `step` seconds into off-centre and thin runs. `frame(t, scene, box)` takes the speaking
 * scene's id, or null between voices, and the frame's lit box in the band, or null when nothing is lit; a frame
 * without speech or of another scene ends a run. `finish()` returns the runs, each with its scene, start, end and worst
 * value: the largest offset of an off-centre run, the least cover of a thin one. */
export function balanceRuns(step) {
  const runs = { off: [], thin: [] },
    open = { off: null, thin: null };
  const close = (kind) => {
    const run = open[kind];
    if (run && run.end - run.start >= RUN_SECONDS - 1e-9) runs[kind].push(run);
    open[kind] = null;
  };
  const extend = (kind, t, scene, value, worse) => {
    const run = open[kind];
    if (run && run.scene === scene && Math.abs(run.end - t) < step * 1.5) {
      run.end = t + step;
      run.worst = worse(run.worst, value);
    } else {
      close(kind);
      open[kind] = { scene, start: t, end: t + step, worst: value };
    }
  };
  return {
    frame(t, scene, box) {
      if (!scene) {
        close("off");
        close("thin");
        return;
      }
      const offset = box ? Math.max(...pictureOffset(box).map(Math.abs)) : 0,
        cover = box ? bandCover(box) : 0;
      if (offset > RUN_OFFSET) extend("off", t, scene, offset, Math.max);
      else close("off");
      if (cover < RUN_COVER) extend("thin", t, scene, cover, Math.min);
      else close("thin");
    },
    finish() {
      close("off");
      close("thin");
      return runs;
    },
  };
}

/** Balance as the reviews since DDWG round 29 measure it, on full-size frames: the box of every paint brighter than
 * grey 60 in rows 120-919 (rules/ink.mjs litAtFullSize) and its horizontal offset from x 960. A build-up may stand
 * more than 90 px off for less than 1.5 s; a still state, its box's left and right edges steady within 4 px, may stand
 * more than 50 px off for less than 2 s, counted from where the glide that settles into it, at 15 px/s or more, passed
 * 50 px, whether it is a settled composition or held while the next parts that grow from it are still to come. A lone
 * mark centred where it stands is within both. */
export const REVIEWED_BAND = [120, 919],
  REVIEWED_BUILD = { px: 90, seconds: 1.5 },
  REVIEWED_SETTLED = { px: 50, seconds: 2, steady: 4, glide: 15 };

/** Joins frames sampled every `step` seconds into the reviewers' off-centre runs. `frame(t, scene, box, cut)` takes
 * the scene the frame falls in, the frame's lit box in the band, or null when nothing is lit, and whether a stage cut
 * the composition declares for that scene falls since the previous sample; a frame of another scene, a frame without
 * a lit box and a gap in the samples each end a run, and a still run also ends when an edge moves more than 4 px from
 * where it stood when the run began, or at a stage cut. A still run is held when the frame that ends it, after no stage
 * cut, holds a wider box of the same scene that contains it: the picture grew from it. A still run that the next
 * frame replaces, by a stage cut of its scene or by another scene's picture, is a finished composition: no part can
 * still dock to it. Every other still run is settled. A still run is timed from the glide that settles into it: the
 * frames just before it, after its scene's last stage cut, that stand more than 50 px off on its side, each moving
 * toward its offset at 15 px/s or more without reversing; slower, the picture creeps as a build-up does. `finish()`
 * returns `builds`, `held`, `settled` and `finished`, each run with its scene, start, end and largest offset in px,
 * signed; a still run's offset is its still frames'. */
export function reviewedRuns(step) {
  const runs = { builds: [], held: [], settled: [], finished: [] },
    open = { builds: null, settled: null },
    least = { builds: REVIEWED_BUILD.seconds, settled: REVIEWED_SETTLED.seconds },
    { steady: STEADY, glide: GLIDE } = REVIEWED_SETTLED;
  // Close the open run of a kind into its list when it lasted long enough, and say whether it did.
  const close = (kind, into = kind) => {
    const run = open[kind],
      kept = Boolean(run) && run.end - run.start >= least[kind] - 1e-9;
    if (kept)
      runs[into].push({ scene: run.scene, start: run.start, end: run.end, worst: run.worst });
    open[kind] = null;
    return kept;
  };
  const follows = (run, t, scene) =>
    run && run.scene === scene && Math.abs(run.end - t) < step * 1.5;
  const steady = (run, box) =>
    Math.abs(box[0] - run.left) <= STEADY && Math.abs(box[2] - run.right) <= STEADY;
  // The next frame's box grew from the still run's: it holds it and reaches further.
  const grewFrom = (run, t, scene, box) =>
    follows(run, t, scene) &&
    box !== null &&
    box[0] <= run.left + STEADY &&
    box[2] >= run.right - STEADY &&
    box[2] - box[0] > run.right - run.left + STEADY;
  // The next frame replaced the still run's picture: a stage cut of its scene, or another scene's lit picture.
  const replaced = (run, t, scene, box, cut) =>
    Math.abs(run.end - t) < step * 1.5 && box !== null && (cut || run.scene !== scene);
  // The frames more than 50 px off since the last stage cut, gap, change of scene or reported still run, each with its
  // time, scene and offset: the glide a still run may settle from.
  let trail = [];
  // Where the glide that settles into a still run opening at t, dx px off, began: the first of the frames of the trail
  // just before it on its side, each moving toward dx at GLIDE px/s or more, all one way.
  const glideStart = (t, dx) => {
    let start = t,
      way = 0;
    for (let k = trail.length - 1; k >= 0; k--) {
      const f = trail[k],
        next = trail[k + 1]?.dx ?? dx,
        toward = Math.sign(next - f.dx);
      if (Math.sign(f.dx) !== Math.sign(dx) || !toward || toward !== Math.sign(dx - f.dx)) break;
      if ((way && toward !== way) || Math.abs(next - f.dx) < GLIDE * step) break;
      way = toward;
      start = f.t;
    }
    return start;
  };
  return {
    frame(t, scene, box, cut = false) {
      const dx = box ? (box[0] + box[2]) / 2 - 960 : 0,
        far = Boolean(box) && Math.abs(dx) > REVIEWED_SETTLED.px,
        last = trail.at(-1);
      if (box && Math.abs(dx) > REVIEWED_BUILD.px) {
        const run = open.builds;
        if (follows(run, t, scene)) {
          run.end = t + step;
          if (Math.abs(dx) > Math.abs(run.worst)) run.worst = dx;
        } else {
          close("builds");
          open.builds = { scene, start: t, end: t + step, worst: dx };
        }
      } else close("builds");
      // A stage cut, a frame not far off, a gap in the samples or another scene ends the trail.
      const joined = last?.scene === scene && Math.abs(last.t + step - t) < step * 1.5;
      if (cut || !far || !joined) trail = [];
      const run = open.settled;
      if (!cut && far && follows(run, t, scene) && steady(run, box)) {
        run.end = t + step;
        if (Math.abs(dx) > Math.abs(run.worst)) run.worst = dx;
      } else {
        const into =
          run && !cut && grewFrom(run, t, scene, box)
            ? "held"
            : run && replaced(run, t, scene, box, cut)
              ? "finished"
              : "settled";
        if (close("settled", into)) trail = [];
        if (far) {
          const start = glideStart(t, dx);
          open.settled = { scene, start, end: t + step, worst: dx, left: box[0], right: box[2] };
        }
      }
      if (far) trail.push({ t, scene, dx });
    },
    finish() {
      close("builds");
      close("settled");
      return runs;
    },
  };
}
