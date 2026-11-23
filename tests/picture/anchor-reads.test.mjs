/** Exercise the check before narration's tool, anchor-reads.mjs, through its interface: its arguments, the report it
 * prints and its exit status, as filmkit.picture.anchor_reads runs it. It draws a composition headlessly over a
 * timeline and reports each id the composition reads from a segment's anchors, through the runtime's recorder. */
import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { scratchFolder } from "./sample-film.mjs";

const TOOL = fileURLToPath(new URL("../../src/filmkit/picture/anchor-reads.mjs", import.meta.url));
const USAGE = "Usage: python -m filmkit.tools anchor-reads <timeline.json> <step-seconds>";

/* A composition that draws one scene a segment: 03 reads `order`, which it requires to stand at the segment's voice,
 * then `kept`; in 05 the composition throws outside any scene, as while it times a stage; 04 reads `law`, then throws
 * as a stranded cue does. */
const COMPOSITION = `var P = {};
const film = window.FILM;
const scenes = {
  "03": (s) => {
    if (s.anchors.order.start !== s.voice_start) throw Error("the stand-in is not at the voice");
    s.anchors.kept.start;
  },
  "04": (s) => {
    s.anchors.law.start;
    throw Error("Missing spoken cue 04");
  },
};
window.renderFrame = (t) => {
  const s = film.segments.find((v) => v.start <= t && t < v.end);
  if (s?.id === "05") throw Error("a stage timed outside its scene");
  if (s && scenes[s.id]) {
    window.__sceneId = s.id;
    scenes[s.id](s);
    window.__sceneId = null;
  }
  window.__filmLayout = { time: t, texts: [] };
};
`;
const KEPT = { start: 0.6, end: 0.9, units: [1, 2], thought: 1 };

/* A film folder holding `film.js` as its composition, and a timeline of three segments of 2 s each, `anchors` given
 * to segment 03 unless `marked` is false. */
async function film(composition = COMPOSITION, { marked = true } = {}) {
  const root = await scratchFolder();
  await mkdir(join(root, "picture"));
  await writeFile(join(root, "picture/film.js"), composition);
  const segment = (id, start) => ({ id, start, end: start + 2, voice_start: start + 0.5 });
  const segments = [segment("03", 0), segment("05", 2), segment("04", 4)];
  if (marked) segments.forEach((s) => (s.anchors = s.id === "03" ? { kept: KEPT } : {}));
  const timeline = join(root, "timeline.json");
  await writeFile(timeline, JSON.stringify({ language: "Chinese", duration: 6, segments }));
  return { root, timeline };
}

/* The tool run in a film folder, as the engine's tool runner runs it there. */
const run = (root, args) =>
  spawnSync(process.execPath, [TOOL, ...args], { cwd: root, encoding: "utf8" });

test("a marked id is read as the timeline holds it, and an unmarked one takes a stand-in", async () => {
  const { root, timeline } = await film();
  const result = run(root, [timeline, "0.5"]);
  assert.equal(result.status, 0, result.stderr);
  const report = JSON.parse(result.stdout);
  assert.deepEqual([report.drawn, report.loads, report.error], [true, true, null]);
  // Each id once, in the order first read; `order` is unmarked, yet the scene went on to read `kept`.
  assert.deepEqual(report.reads, [
    { segment: "03", id: "order", marked: false, scene: "03" },
    { segment: "03", id: "kept", marked: true, scene: "03" },
    { segment: "04", id: "law", marked: false, scene: "04" },
  ]);
});

test("a scene that throws is named with its segment, its error, its first time and the ids it read", async () => {
  const { root, timeline } = await film();
  const { unjudged } = JSON.parse(run(root, [timeline, "0.5"]).stdout);
  assert.deepEqual(unjudged, [
    // Thrown outside any scene the composition publishes: named by the segment alone.
    { scene: null, segment: "05", error: "a stage timed outside its scene", from: 2, reads: [] },
    { scene: "04", segment: "04", error: "Missing spoken cue 04", from: 4, reads: ["law"] },
  ]);
});

test("a segment of an edition that marks no anchor reads every id as unmarked", async () => {
  const { root, timeline } = await film(COMPOSITION, { marked: false });
  const { reads } = JSON.parse(run(root, [timeline, "0.5"]).stdout);
  assert.deepEqual(
    reads.map((read) => [read.id, read.marked]),
    [
      ["order", false],
      ["kept", false],
      ["law", false],
    ],
  );
});

test("a composition that does not load is reported as not drawn and exits 1", async () => {
  const { root, timeline } = await film('throw Error("broken");');
  const result = run(root, [timeline, "0.5"]);
  assert.equal(result.status, 1);
  assert.deepEqual(JSON.parse(result.stdout), {
    drawn: false,
    loads: false,
    error: "The composition does not load: broken",
    reads: [],
    unjudged: [],
  });
});

test("a malformed invocation exits 2 with the usage and prints no report", async () => {
  const { root, timeline } = await film();
  for (const args of [[], [timeline], [timeline, "0"], [timeline, "abc"], [timeline, "0.5", "x"]]) {
    const result = run(root, args);
    assert.equal(result.status, 2, args.join(" "));
    assert.equal(result.stdout, "", args.join(" "));
    assert.ok(result.stderr.includes(USAGE), args.join(" "));
  }
});
