/* Marks outside scenes: the titles, cards and running heads a composition draws around its scenes.
 *
 * The motion audit follows the marks of scenes, and the pace limit a film declares holds for their glides and flows.
 * A text drawn outside every scene was followed by nothing: the DDWG film's review round 41 (finding EN41-11) judged
 * chapter titles that travelled from their card to the running head at 1,137 to 1,198 px/s a racing mark, on films
 * whose every scene kept 450 px/s.
 *
 * Each text outside a scene, a caption apart, is followed from frame to frame by its words: the same words nearest
 * to where they stood, within SAME px. A stretch is two or more consecutive steps in which the text's centre moves
 * over the pace line, named by its fastest step. */
import { overPace, PACE } from "../motion-audit/pace.mjs";

/** A text below the opacity SEEN is not followed, and the same words more than SAME px from where they stood one
 * frame before are another mark (at 60 fps, 3,600 px/s: four times the pace at which a mark races). */
export const OUTSIDE = Object.freeze({ SEEN: 0.2, SAME: 60 });

/** The texts of a frame's layout that stand outside every scene and are no caption, each with its words and centre. */
export function outsideTexts(texts) {
  return texts
    .filter((v) => !v.scene && v.role !== "caption" && v.alpha > OUTSIDE.SEEN)
    .map((v) => ({
      text: v.text,
      x: (v.bounds[0] + v.bounds[2]) / 2,
      y: (v.bounds[1] + v.bounds[3]) / 2,
    }));
}

/** Follows the texts outside scenes through consecutive frames `dt` seconds apart. `frame(t, marks)` takes the
 * frame's `outsideTexts`; `finish()` returns the stretches over the pace line, in the order they began: each with its
 * `text`, its `start` and `end`, its `frames`, its fastest `speed` in px/s, the time `at` of that step and the `way`
 * in px its centre covered in the stretch. */
export function outsideRuns(dt) {
  let last = [];
  const open = new Map(),
    closed = [];
  const close = (text) => {
    const run = open.get(text);
    if (run && run.frames >= 2) closed.push(run);
    open.delete(text);
  };
  return {
    frame(t, marks) {
      const taken = new Set(),
        moving = new Set();
      for (const mark of marks) {
        let best = null;
        last.forEach((was, index) => {
          if (was.text !== mark.text || taken.has(index)) return;
          const step = Math.hypot(mark.x - was.x, mark.y - was.y);
          if (step <= OUTSIDE.SAME && !(best?.step <= step)) best = { index, step };
        });
        if (!best) continue;
        taken.add(best.index);
        const speed = best.step / dt;
        if (!overPace(speed)) continue;
        moving.add(mark.text);
        const run = open.get(mark.text);
        if (run) {
          run.end = t;
          run.frames++;
          run.way += best.step;
          // A step faster by more than rounding noise: equal steps keep the first as the fastest.
          if (speed > run.speed + 1e-6) Object.assign(run, { speed, at: t });
        } else
          open.set(mark.text, {
            text: mark.text,
            start: t,
            end: t,
            frames: 1,
            speed,
            at: t,
            way: best.step,
          });
      }
      for (const text of [...open.keys()]) if (!moving.has(text)) close(text);
      last = marks;
    },
    finish() {
      for (const text of [...open.keys()]) close(text);
      return closed
        .map((run) => ({ ...run, speed: Math.round(run.speed), way: Math.round(run.way) }))
        .sort((a, b) => a.start - b.start);
    },
  };
}

export { PACE };
