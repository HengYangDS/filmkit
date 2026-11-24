/** Exercise the detail audit on the sample film and on a composition that shows each artefact it looks for. */
import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { authoredTimeline, scratchFolder } from "./sample-film.mjs";

const AUDIT_DETAIL = fileURLToPath(
  new URL("../../src/filmkit/picture/detail-audit.mjs", import.meta.url),
);

test("the detail audit finds nothing in the sample film, which publishes no drawn strokes", async () => {
  const folder = await scratchFolder(),
    path = join(folder, "timeline.json"),
    out = join(folder, "detail.json");
  const film = await authoredTimeline("en");
  await writeFile(path, JSON.stringify(film));
  const summary = JSON.parse(
    execFileSync(process.execPath, [AUDIT_DETAIL, path, "--out", out], { encoding: "utf8" }),
  );
  const report = JSON.parse(await readFile(out, "utf8"));
  assert.equal(report.fps, 60);
  assert.deepEqual(report.lines, { pace: 450, race: 900, rail_clear: 48 });
  assert.equal(summary.frames, report.frames);
  assert.ok(report.frames > 60 * (film.duration - 1));
  assert.deepEqual(
    [report.ink_drops, report.outside_runs, report.part_drawn, report.racing_tips, report.rails],
    [[], [], [], [], []],
  );
  assert.equal(report.draws_published, false);
  assert.ok(report.quiets > 0);
});

/* A composition that shows each artefact the detail audit looks for, or with REPAIRED none of them: a path that
 * opens a 60 px gap within one frame at 3 s; a rule that splits on the stage cut the scene declares at 6 s; a
 * chapter title outside the scene that travels 1,200 px in one second from 1 s; a stroke keyed at 4.5 s that is
 * three fifths drawn in the quiet between the two thoughts (5 to 5.8 s); a stroke whose tip draws at 950 px/s from
 * 7 s; and three duties on two baselines, the second 14 px under the first, at the rest of the first thought. */
const composition = (repaired) => `var REPAIRED = ${repaired};
var P = { ground: "#0F1519", ink: "#ECE8DF" };
var ctx = document.getElementById("picture").getContext("2d");
var scenes = {};
var stageCuts = new Map([["01", [6]]]);
var texts = [];
var clamp = function (v) { return Math.min(1, Math.max(0, v)); };
function path(y, open) {
  ctx.strokeStyle = P.ink;
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.moveTo(300, y);
  if (open) {
    ctx.lineTo(570, y);
    ctx.moveTo(630, y);
  }
  ctx.lineTo(900, y);
  ctx.stroke();
}
function label(value, x0, top, x1, extra) {
  texts.push(Object.assign({ text: value, whole: value, bounds: [x0, top, x1, top + 30], alpha: 1, role: "label", scene: window.__sceneId }, extra));
}
scenes["01"] = function (t) {
  path(500, !REPAIRED && t >= 3);
  path(700, t >= 6);
  if (t >= 4.9 && t < 5.2) {
    label("Find the users", 300, 600, 520, { set: "duties" });
    label("Plan the release and its recovery", 500, REPAIRED ? 680 : 644, 760, { set: "duties" });
    label("Verify", 780, 600, 900, { set: "duties" });
  }
};
window.renderFrame = function (t) {
  texts = [];
  window.__sceneId = "01";
  scenes["01"](t);
  window.__sceneId = null;
  var x = REPAIRED ? 960 : 300 + 1200 * clamp(t - 1);
  texts.push({ text: "Chapter", bounds: [x - 100, 520, x + 100, 560], alpha: 1, role: "title", scene: null });
  window.__filmLayout = {
    time: t,
    texts: texts,
    draws: [
      { scene: "01", at: 4.5, share: clamp((t - 4.5) / (REPAIRED ? 0.4 : 1.5)), pace: 300 },
      { scene: "01", at: 7, share: clamp((t - 7) / 0.2), pace: REPAIRED ? 700 : 950 },
    ],
  };
};
`;
const word = (text, start, end) => ({ text, start, end });
const TIMELINE = {
  edition: "en",
  duration: 11,
  credits_duration: 1,
  captions: [],
  segments: [
    {
      id: "01",
      start: 0,
      end: 10,
      voice_start: 0.5,
      voice_end: 9.5,
      utterance_groups: ["One two three. ", "Four five six."],
      words: [
        word("One", 0.5, 1),
        word("two", 2, 2.5),
        word("three", 4.5, 5),
        word("Four", 5.8, 6.2),
        word("five", 7, 7.5),
        word("six", 9, 9.5),
      ],
    },
  ],
};
async function audit(repaired) {
  const root = await scratchFolder(),
    source = composition(repaired);
  await mkdir(join(root, "picture"));
  await writeFile(join(root, "picture/film.js"), source);
  const path = join(root, "timeline.json"),
    out = join(root, "detail.json");
  await writeFile(path, JSON.stringify(TIMELINE));
  execFileSync(process.execPath, [AUDIT_DETAIL, path, "--out", out], {
    cwd: root,
    encoding: "utf8",
  });
  const lines = source.split("\n");
  return {
    report: JSON.parse(await readFile(out, "utf8")),
    lineOf: (code) => `film.js:${lines.findIndex((v) => v.includes(code)) + 1}`,
  };
}

test("the detail audit reports each artefact a composition shows, at its time and from its line", async () => {
  const { report, lineOf } = await audit(false);
  // The path opens at 3 s; the rule's split at 6 s falls on the declared stage cut.
  assert.deepEqual(report.ink_drops, [
    { t: 3, scene: "01", origin: lineOf("path(500,"), lost: 60, of: 600, module: null },
  ]);
  assert.equal(report.ink_at_cuts, 1);
  // The title travels 20 px a frame through sixty frames.
  assert.deepEqual(report.outside_runs, [
    {
      text: "Chapter",
      start: 1.017,
      end: 2,
      frames: 60,
      speed: 1200,
      at: 1.017,
      way: 1200,
      scene: "01",
    },
  ]);
  assert.equal(report.draws_published, true);
  assert.equal(report.quiets, 1);
  assert.deepEqual(report.part_drawn, [
    { quiet: "01.1", rest: 5, resume: 5.8, scene: "01", cue: 4.5, share: 0.6 },
  ]);
  assert.deepEqual(report.racing_tips, [{ scene: "01", cue: 7, pace: 950 }]);
  assert.deepEqual(report.rails, [
    {
      scene: "01",
      set: "duties",
      clear: 14,
      names: ["Find the users", "Plan the release and its recovery"],
      across: -20,
      down: 14,
      at: "01.1",
    },
  ]);
});

test("the detail audit reports none of them once the composition is repaired", async () => {
  const { report } = await audit(true);
  assert.deepEqual(
    [report.ink_drops, report.outside_runs, report.part_drawn, report.racing_tips],
    [[], [], [], []],
  );
  // The split on the declared stage cut stays the cut's, and the rail stands 50 px clear.
  assert.equal(report.ink_at_cuts, 1);
  assert.deepEqual(
    report.rails.map((v) => [v.set, v.clear]),
    [["duties", 50]],
  );
});

test("the detail audit refuses a malformed invocation", async () => {
  const folder = await scratchFolder(),
    path = join(folder, "timeline.json");
  await writeFile(path, JSON.stringify(await authoredTimeline("zh")));
  const usage = "Usage: python -m filmkit.tools detail-audit";
  for (const args of [
    [],
    [path, "abc"],
    [path, "60", "extra"],
    [path, "--from", "5", "--to", "5"],
  ]) {
    const result = spawnSync(process.execPath, [AUDIT_DETAIL, ...args], { encoding: "utf8" });
    assert.equal(result.status, 2, `${args.join(" ")}: ${result.stderr}`);
    assert.equal(result.stdout, "", args.join(" "));
    assert.ok(result.stderr.includes(usage), args.join(" "));
  }
});
