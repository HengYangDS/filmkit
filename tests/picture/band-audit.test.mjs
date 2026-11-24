/** Exercise the band audit: the rows a derived uncaptioned picture paints, on the sample film's composition and on
 * compositions whose captions leave those rows or whose marks reach them, and the invocations the tool takes. */
import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { bandAudit } from "../../src/filmkit/picture/band-audit.mjs";
import { equivalence } from "../../src/filmkit/picture/caption-equivalence.mjs";
import { authoredTimeline, scratchFolder } from "./sample-film.mjs";

const TOOL = fileURLToPath(new URL("../../src/filmkit/picture/band-audit.mjs", import.meta.url));
/* The rows the tests paint: the caption line at y 1000, with the margin a comparison leaves around it. */
const ROWS = [928, 1056];

/* A composition that paints a label of scene 01 at `labelY`, the caption of the moment at `captionY` and `extra`. */
const composition = ({ labelY = 500, captionY = 1000, extra = "" } = {}) => `
var P = { ground: "#0F1519", ink: "#ECE8DF" };
const film = window.FILM;
const ctx = document.getElementById("picture").getContext("2d");
let texts = [];
function text(value, x, y, role, scene = null) {
  window.__sceneId = scene;
  ctx.font = "30px sans-serif";
  ctx.fillStyle = P.ink;
  ctx.fillText(value, x, y);
  texts.push({ text: value, role, scene });
  window.__sceneId = null;
}
window.renderFrame = (t) => {
  texts = [];
  text("Sources", 960, ${labelY}, "label", "01");
  const cue = film.captions.find((c) => c.start <= t && t < c.end);
  if (cue) text(cue.text, 960, ${captionY}, "caption");
  ${extra}
  window.__filmLayout = { time: t, texts };
};
`;
const TIMELINE = {
  edition: "zh",
  duration: 4,
  segments: [],
  captions: [
    { start: 1, end: 2, text: "One" },
    { start: 2.5, end: 3, text: "Two" },
  ],
};

/* Run the audit on a composition written into a film of its own. */
async function audited(source, options = {}) {
  const film = await scratchFolder(),
    before = process.cwd();
  await mkdir(join(film, "picture"));
  await writeFile(join(film, "picture/film.js"), source);
  process.chdir(film);
  try {
    return bandAudit(TIMELINE, ROWS, options);
  } finally {
    process.chdir(before);
  }
}

test("captions inside the rows and nothing else there pass, with the stretches that show no caption", async () => {
  const report = await audited(composition());
  assert.equal(report.verdict, "pass");
  assert.deepEqual([report.instants, report.fps], [120, 30]);
  assert.equal(report.caption_instants, 45);
  // The caption line at y 1000 in a 30 px face: its box, as the headless stand-in estimates it.
  const [first, last] = report.caption_rows;
  assert.ok(first > 960 && first < 1000 && last > 1000 && last < 1020, `${first}-${last}`);
  assert.deepEqual([report.escaping_instants, report.intruding_instants], [0, 0]);
  const stretches = report.free.map(([a, b]) => [Math.round(a * 30), Math.round(b * 30)]);
  assert.deepEqual(stretches, [
    [0, 29],
    [60, 74],
    [90, 119],
  ]);
});

test("a label of a scene that stands in the rows is an intrusion at every instant", async () => {
  const report = await audited(composition({ labelY: 980 }));
  assert.equal(report.verdict, "refuse");
  assert.equal(report.intruding_instants, 120);
  const [first] = report.intrusions;
  assert.deepEqual([first.time, first.kind, first.scene, first.text], [0, "text", "01", "Sources"]);
  assert.equal(report.intrusions.length, 20);
});

test("a stroke reaches the rows by half its width, and one drawn at no opacity reaches nothing", async () => {
  const line = (alpha) =>
    `ctx.globalAlpha = ${alpha}; ctx.lineWidth = 12; ctx.strokeStyle = P.ink; ctx.beginPath(); ctx.moveTo(100, 924); ctx.lineTo(900, 924); ctx.stroke(); ctx.globalAlpha = 1;`;
  const reached = await audited(composition({ extra: line(1) }));
  assert.equal(reached.verdict, "refuse");
  assert.deepEqual([reached.intrusions[0].kind, reached.intrusions[0].scene], ["stroke", null]);
  const unseen = await audited(composition({ extra: line(0) }));
  assert.equal(unseen.verdict, "pass");
  const clear = await audited(composition({ extra: line(1).replaceAll("924", "900") }));
  assert.equal(clear.verdict, "pass");
});

test("a caption painted partly above the rows is an escape", async () => {
  const report = await audited(composition({ captionY: 940 }));
  assert.equal(report.verdict, "refuse");
  assert.deepEqual([report.escaping_instants, report.intruding_instants], [45, 0]);
  assert.deepEqual([report.escapes[0].time, report.escapes[0].text], [1, "One"]);
});

for (const code of ["zh", "en"]) {
  test(`the ${code} sample film paints only captions in its caption band`, async () => {
    const timeline = await authoredTimeline(code);
    const { band } = equivalence(timeline);
    // The band as a comparison widens it: 24 rows on each side, out to blocks of 8 rows of this frame.
    const rows = [Math.floor((band.top - 24) / 8) * 8, Math.ceil((band.bottom + 24) / 8) * 8];
    const report = bandAudit(timeline, rows, { fps: 10 });
    assert.equal(report.verdict, "pass", JSON.stringify([report.escapes[0], report.intrusions[0]]));
    assert.ok(report.caption_instants > 0 && report.free.length > 0);
  });
}

test("the tool prints its report, exits 1 on a refusal and 2 on a malformed invocation", async () => {
  const film = await scratchFolder();
  await mkdir(join(film, "picture"));
  await writeFile(join(film, "timeline.json"), JSON.stringify(TIMELINE));
  const run = (source, ...args) => {
    return writeFile(join(film, "picture/film.js"), source).then(() =>
      spawnSync(process.execPath, [TOOL, ...args], { cwd: film, encoding: "utf8" }),
    );
  };
  const passed = await run(composition(), "timeline.json", "928", "1056");
  assert.equal(passed.status, 0, passed.stderr);
  assert.equal(JSON.parse(passed.stdout).verdict, "pass");
  const refused = await run(composition({ labelY: 980 }), "timeline.json", "928", "1056", "10");
  assert.equal(refused.status, 1);
  assert.deepEqual(
    [JSON.parse(refused.stdout).verdict, JSON.parse(refused.stdout).instants],
    ["refuse", 40],
  );
  for (const args of [
    [],
    ["timeline.json", "1056", "928"],
    ["timeline.json", "928", "1056", "0"],
  ]) {
    const malformed = await run(composition(), ...args);
    assert.equal(malformed.status, 2);
    assert.match(malformed.stderr, /Usage: python -m filmkit.tools band-audit/);
  }
});
