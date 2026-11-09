/** What a stage cut excuses and what it shows: the marks a cut keeps where they stood, or moves whole as a jump, and
 * the marks a declared cut brings into a stage that stands. */
import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { follower } from "../../src/filmkit/picture/motion-audit/follow.mjs";
import { scratchFolder } from "./sample-film.mjs";

const AUDIT_MOTION = fileURLToPath(
  new URL("../../src/filmkit/picture/motion-audit.mjs", import.meta.url),
);
const DT = 1 / 30;
const at = (t) => +t.toFixed(3);

/* A firm text of a scene, as the audit hands it to the follower, its box from its left edge, top, width and height. */
const text = (scene, words, x, y, w, h = 36) => ({
  scene,
  kind: "text",
  text: words,
  width: 1,
  level: 236,
  screen: [x, y, x + w, y + h],
});
/* Scene 04's field, a square outline 450 px across, and its name above it, standing with the field's left side at x. */
const field = (x) => [
  { scene: "04", kind: "stroke", text: "", width: 3, level: 236, screen: [x, 275, x + 450, 725] },
  text("04", "Boundaries", x + 120, 214, 210),
];
/* A grid of firm names of a scene, six to a row, from the top `y`. */
const grid = (scene, prefix, count, y) =>
  Array.from({ length: count }, (_, k) =>
    text(scene, `${prefix} ${k}`, 100 + 300 * (k % 6), y + 80 * Math.floor(k / 6), 160),
  );

/* What the follower finds in frames 0 to 9 at 30 fps, frame n showing `marksAt(n)`, with the cut of each of `scenes`
 * declared at frame 5. */
function follow(marksAt, scenes = []) {
  const viewer = follower(DT);
  for (let n = 0; n < 10; n++) viewer.frame(n * DT, marksAt(n), n === 5 ? scenes : []);
  return viewer.finish();
}

test("a field and its name moved whole at a stage cut jump, whether the cut is declared or found", () => {
  for (const declared of [["04"], []]) {
    const found = follow((n) => field(n < 5 ? 735 : 381), declared);
    assert.deepEqual(
      found.jumps.map((v) => [at(v.t), v.scene, v.shift, v.distance, v.marks, v.paints, v.texts]),
      [[at(5 * DT), "04", [-354, 0], 354, 2, ["stroke", "text"], ["Boundaries"]]],
    );
    // The jump is named by its heaviest mark, the field, which holds most of the scene's firm ink.
    assert.deepEqual([found.jumps[0].kind, found.jumps[0].box], ["stroke", [381, 275, 831, 725]]);
    assert.deepEqual(found.pops, []);
  }
  // A cut that shifts its stage by 6 px leaves its marks where a viewer sees them: no jump.
  assert.deepEqual(follow((n) => field(n < 5 ? 735 : 741), ["04"]).jumps, []);
});

test("a field gliding through a stage cut keeps its motion, and one that sets off at the cut jumps by its step", () => {
  // The field and its name glide 12 px a frame before the cut the composition declares, at it and after it.
  const glide = follow((n) => field(735 - 12 * n), ["04"]);
  assert.deepEqual([glide.jumps, glide.pops], [[], []]);
  // Standing still until the cut, they step 15 px at it and glide 8 px a frame after: the step departs from rest.
  const start = follow((n) => field(n < 5 ? 735 : 720 - 8 * (n - 5)), ["04"]);
  assert.deepEqual(
    start.jumps.map((v) => [at(v.t), v.shift, v.marks]),
    [[at(5 * DT), [-15, 0], 2]],
  );
});

test("a cut that keeps its rail in place while it replaces the names on it shows no jump", () => {
  const rail = { scene: "04", kind: "stroke", text: "", width: 4, level: 160 };
  rail.screen = [200, 540, 1720, 544];
  const names = (words) => words.map((v, k) => text("04", v, 260 + 400 * k, 480, 160));
  const found = follow(
    (n) => [
      rail,
      ...names(n < 5 ? ["Sources", "Records", "Reviews"] : ["Owners", "Gates", "Proofs"]),
    ],
    ["04"],
  );
  assert.deepEqual([found.jumps, found.pops], [[], []]);
});

test("a heading moved while the rest of its stage is replaced holds too little ink to jump", () => {
  // The heading moves 200 px while the scene's twelve other firm marks give way to twelve new ones.
  const heading = (x) => text("04", "Heading", x, 120, 200, 40);
  const found = follow(
    (n) => [
      heading(n < 5 ? 860 : 660),
      ...grid("04", n < 5 ? "Old" : "New", 12, n < 5 ? 300 : 620),
    ],
    ["04"],
  );
  assert.deepEqual([found.jumps, found.pops], [[], []]);
});

test("a declared cut that keeps its stage excuses the name it takes away and judges the one it brings", () => {
  // One name gives way to another of another width while the scene's 30 other firm names stand.
  const standing = grid("06", "Stand", 30, 100);
  const name = (n) =>
    n < 5 ? text("06", "Inference", 860, 800, 180) : text("06", "Hypothesis", 850, 800, 200);
  const found = follow((n) => [...standing, name(n)], ["06"]);
  assert.deepEqual(
    found.pops.map((v) => [at(v.t), v.way, v.text, v.declared_cut]),
    [[at(5 * DT), "in", "Hypothesis", true]],
  );
  // Without the declaration the frame is no cut at all, and the name that leaves pops out too.
  assert.deepEqual(
    follow((n) => [...standing, name(n)]).pops.map((v) => [v.way, v.text, v.declared_cut]),
    [
      ["in", "Hypothesis", undefined],
      ["out", "Inference", undefined],
    ],
  );
  // Where 20 of the scene's 24 firm marks give way to 18 others, the declared cut changes its stage: no pop.
  const handed = follow(
    (n) => [
      ...grid("06", "Keep", 4, 100),
      ...(n < 5 ? grid("06", "Old", 20, 300) : grid("06", "New", 18, 700)),
    ],
    ["06"],
  );
  assert.deepEqual([handed.pops, handed.jumps], [[], []]);
});

/* Scene 04 re-forms on the cut it declares between frames 30 and 31: its field and name move 354 px left. From 3 s
 * scene 06 shows six cases and a name, which gives way to another on the cut it declares between frames 120 and 121. */
const CUTS = `var P = { ground: "#0F1519", ink: "#ECE8DF" };
var ctx = document.getElementById("picture").getContext("2d");
var scenes = {};
var layout = [];
var stageCuts = new Map([["04", new Set([30.5 / 30])], ["06", new Set([120.5 / 30])]]);
function name(value, x, y) {
  ctx.font = "40px Sample";
  ctx.textAlign = "left";
  ctx.textBaseline = "alphabetic";
  ctx.globalAlpha = 1;
  ctx.fillStyle = P.ink;
  ctx.fillText(value, x, y);
  layout.push({ text: value, alpha: 1, role: "label", scene: window.__sceneId });
}
scenes["04"] = function (t) {
  const x = t < 30.5 / 30 ? 735 : 381;
  ctx.globalAlpha = 1;
  ctx.strokeStyle = P.ink;
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.roundRect(x, 275, 450, 450, 4);
  ctx.stroke();
  name("Boundaries", x + 120, 250);
};
scenes["06"] = function (t) {
  for (let k = 0; k < 6; k++) name("Case " + (k + 1), 200 + 260 * k, 300);
  name(t < 120.5 / 30 ? "Inference" : "Hypothesis", 800, 600);
};
window.renderFrame = function (t) {
  layout = [];
  window.__sceneId = t < 3 ? "04" : "06";
  scenes[window.__sceneId](t);
  window.__sceneId = null;
  window.__filmLayout = { time: t, texts: layout };
};
`;

test("the motion audit reports a jump and a pop a declared cut brings, each from the line that drew it", async () => {
  const root = await scratchFolder();
  await mkdir(join(root, "picture"));
  await writeFile(join(root, "picture/film.js"), CUTS);
  const lines = CUTS.split("\n"),
    lineOf = (code) => `film.js:${lines.findIndex((line) => line.includes(code)) + 1}`;
  const words = Array.from({ length: 22 }, (_, k) => ({
    text: "word",
    start: 0.5 + k * 0.2,
    end: 0.68 + k * 0.2,
  }));
  const path = join(root, "timeline.json"),
    out = join(root, "motion.json");
  const segments = [{ id: "01", start: 0, end: 5, voice_start: 0.5, voice_end: 4.9, words }];
  await writeFile(
    path,
    JSON.stringify({
      language: "English",
      duration: 5,
      credits_duration: 0,
      captions: [],
      segments,
    }),
  );
  const summary = JSON.parse(
    execFileSync(process.execPath, [AUDIT_MOTION, path, "30", "--out", out], {
      cwd: root,
      encoding: "utf8",
    }),
  );
  const { followed } = JSON.parse(await readFile(out, "utf8"));
  assert.deepEqual(
    followed.findings.map((v) => [v.kind, v.scene, at(v.start), v.origin, v.paints, v.texts]),
    [
      ["jump", "04", 1.033, lineOf("ctx.stroke();"), ["stroke", "text"], ["Boundaries"]],
      ["pop", "06", 4.033, lineOf('"Hypothesis"'), ["text"], ["Hypothesis"]],
    ],
  );
  const [jump, pop] = followed.findings;
  assert.deepEqual([jump.shift, jump.distance, jump.marks], [[-354, 0], 354, 2]);
  assert.deepEqual([pop.way, pop.level, pop.declared_cut], ["in", 221, true]);
  assert.deepEqual(summary.followed, {
    halts: 0,
    starts: 0,
    races: 0,
    pops: 1,
    jumps: 1,
    dash_snaps: 0,
  });
});
