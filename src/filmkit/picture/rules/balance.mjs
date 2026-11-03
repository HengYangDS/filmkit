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
