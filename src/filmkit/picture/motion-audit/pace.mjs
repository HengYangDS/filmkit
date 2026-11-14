/* The pace of a scene's glides and flows (follow.mjs): the stretches in which a followed mark moves faster than the
 * line the reviews hold a calm picture to.
 *
 * A mark's speed is the one a viewer sees on the screen, so a mark that moves inside a gliding stage carries the
 * stage's motion with its own. One stretch therefore joins every mark of one scene that moves above the line in
 * consecutive frames: a stage that glides with the marks it carries, and the marks that move within it, are one
 * stretch, named by its fastest mark, and are not counted once for each mark or once as a glide and once as a flow. */

/** The viewer's pace line, in 1080p pixels per second: the film reviews read each scene's fastest glide and flow from
 * the motion report as whole numbers and pass a picture whose every glide and flow is at or under 450 px/s, so a speed
 * is over the line when it rounds to more than PACE. */
export const PACE = 450;

/** Whether a speed, as the report states it to the whole pixel per second, is over the pace line. */
export const overPace = (speed, line = PACE) => Math.round(speed) > line;

/** Joins the marks that move over the pace line into stretches, frame by frame, dt seconds apart.
 * `frame(t, fast)` takes one frame's marks over the line, each a row with its scene, its `speed` and its `move`, a
 * glide or a flow; `finish()` returns one row for each stretch, in the order of their fastest frames: the row of its
 * fastest mark, at the time it was fastest, with the stretch's `start` and `end`, its `frames` and `marks`, the most
 * marks over the line in one of its frames. */
export function paceRuns(dt) {
  const open = new Map(),
    closed = [];
  function frame(t, fast) {
    const scenes = new Map();
    for (const e of fast) scenes.set(e.scene, [...(scenes.get(e.scene) ?? []), e]);
    for (const [scene, events] of scenes) {
      const peak = events.reduce((a, e) => (e.speed > a.speed ? e : a)),
        run = open.get(scene);
      if (run && t - run.end <= 1.5 * dt) {
        run.end = t;
        run.frames++;
        run.marks = Math.max(run.marks, events.length);
        if (peak.speed > run.peak.speed) run.peak = peak;
        continue;
      }
      if (run) closed.push(run);
      open.set(scene, { start: t, end: t, frames: 1, marks: events.length, peak });
    }
  }
  function finish() {
    return [...closed, ...open.values()]
      .map(({ peak, ...run }) => ({ ...peak, ...run }))
      .sort((a, b) => a.t - b.t);
  }
  return { frame, finish };
}
