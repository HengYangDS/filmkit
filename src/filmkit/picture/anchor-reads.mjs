/* Draw the composition headlessly over a timeline, every frame from 0 at a step, and report what it reads of each
 * segment's anchors, for narration's check before any speech model loads (filmkit.picture.anchor_reads).
 * Its usage is `USAGE`, which it prints when it is invoked wrongly. The report states whether the composition drew and
 * why not; every id it read, with its segment, whether the timeline marks it there and the scene that read it
 * (headless-composition.mjs); and each scene that threw, with the segment the frame stands in, its error, the first
 * time it threw and the ids it read in a frame that threw; a composition that throws outside a scene it publishes, as
 * while it times a stage, is named by that segment alone. A composition that does not load is reported as not drawn
 * and not loaded, with its error, and exits 1, which filmkit.picture.anchor_reads names as not judged. */
import { openComposition, readTimeline } from "./headless-composition.mjs";

/* The step is the caller's (filmkit.picture.anchor_reads.STEP); the tool keeps no default of its own. */
const USAGE = "Usage: python -m filmkit.tools anchor-reads <timeline.json> <step-seconds>";
const [path, written, ...rest] = process.argv.slice(2);
const step = Number(written);
if (!path || rest.length || !(step > 0)) {
  console.error(`${path ? `Not a positive step: ${written}` : "No timeline"}\n${USAGE}`);
  process.exit(2);
}
const timeline = readTimeline(path);
let film;
try {
  film = openComposition(timeline);
} catch (error) {
  const reason = `The composition does not load: ${error.message}`;
  console.log(
    JSON.stringify({ drawn: false, loads: false, error: reason, reads: [], unjudged: [] }),
  );
  process.exit(1);
}
const unjudged = new Map();
for (let frame = 0; frame * step < timeline.duration; frame++) {
  try {
    film.render(frame * step);
  } catch (error) {
    const at = frame * step,
      scene = film.scene(),
      segment = timeline.segments?.find((s) => s.start <= at && at < s.end)?.id ?? null,
      key = `${scene}\u0000${segment}\u0000${error.message}`;
    if (!unjudged.has(key))
      unjudged.set(key, { scene, segment, error: String(error.message), from: at, reads: [] });
    const entry = unjudged.get(key);
    for (const read of film.drawn())
      if (read.scene === scene && !entry.reads.includes(read.id)) entry.reads.push(read.id);
  }
}
const report = {
  drawn: true,
  loads: true,
  error: null,
  reads: film.anchorReads(),
  unjudged: [...unjudged.values()],
};
console.log(JSON.stringify(report));
