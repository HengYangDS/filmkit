/** Follow every mark as a viewer sees it move: a composition that shows each motion the gate judges, at known frames. */
import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { leastCostAssignment } from "../../src/filmkit/picture/motion-audit/assignment.mjs";
import { scratchFolder } from "./sample-film.mjs";

const AUDIT_MOTION = fileURLToPath(
  new URL("../../src/filmkit/picture/motion-audit.mjs", import.meta.url),
);

/* Scene 01 runs to 6 s and scene 02 from then on; every motion is set by the frame's number at 30 fps, n. A dot flows
 * along a link at 300 px/s, entering and leaving by size; a dot moves at 240 px/s, halts dead and sets off again; a
 * name eases 440 px across 0.8 s; a name races 600 px in 0.4 s; a counter changes its words in place; a name pops in
 * and out; a card glides while a link draws on from it; a rule is drawn on in place, 1,200 px in eight frames, its end
 * at up to 225 px a frame; a larger dot around a standing dot vanishes at frame 120. None of these follows and
 * nothing is found: a name gives way to another at the stage cut the composition declares at frame 102; a bracket's
 * second end enters 360 px from its first by size, from frame 40; a span's moving end slides through its fixed end at
 * frame 101; a ring is drawn on from a point, from frame 31; a slab eases down and joins its stack at frame 60; a link
 * is drawn on from a start that glides 180 px/s and turns its corner at frame 71; a row of squares glides 90 px/s
 * while a square grows in at its end every ten frames; a link drawn on from a rising start turns its corner as the
 * start rises through it at frame 165; a box's dashed outline gives way to a solid one while the box glides, from frame
 * 77. Scene 02 hands five names to five others below them in one frame. */
const MOTIONS = [
  'var P = { ground: "#0F1519", ink: "#ECE8DF" };',
  'var ctx = document.getElementById("picture").getContext("2d");',
  "var scenes = {};",
  "var layout = [];",
  "var ease = (q) => (q <= 0 ? 0 : q >= 1 ? 1 : q * q * (3 - 2 * q));",
  "var stageCuts = new Map([['01', new Set([101.5 / 30, 175.5 / 30])]]);",
  "function dot(x, y, r) {",
  "  ctx.globalAlpha = 1;",
  "  ctx.fillStyle = P.ink;",
  "  ctx.beginPath();",
  "  ctx.arc(x, y, r, 0, Math.PI * 2);",
  "  ctx.fill();",
  "}",
  "function name(value, x, y) {",
  '  ctx.font = "40px Sample";',
  '  ctx.textAlign = "left";',
  '  ctx.textBaseline = "alphabetic";',
  "  ctx.globalAlpha = 1;",
  "  ctx.fillStyle = P.ink;",
  "  ctx.fillText(value, x, y);",
  '  layout.push({ text: value, alpha: 1, role: "label", scene: window.__sceneId });',
  "}",
  "function rule(x0, y0, x1, y1) {",
  "  ctx.globalAlpha = 1;",
  "  ctx.strokeStyle = P.ink;",
  "  ctx.lineWidth = 4;",
  "  ctx.beginPath();",
  "  ctx.moveTo(x0, y0);",
  "  ctx.lineTo(x1, y1);",
  "  ctx.stroke();",
  "}",
  'scenes["01"] = function (t) {',
  "  const n = Math.round(t * 30), q = (n % 30) / 30;",
  '  name("Stand", 300, 200);',
  "  dot(300 + 300 * q, 400, 5 * Math.min(1, 6 * q, 6 * (1 - q)));",
  "  dot(1000 + 8 * Math.min(n, 61) + 8 * Math.max(0, n - 91), 500, 6);",
  '  name("Ease", 300 + 440 * ease((n - 30) / 24), 600);',
  '  name("Race", 300 + 600 * ease((n - 120) / 12), 700);',
  "  name((100 + 0.37 * n).toFixed(2), 1300, 800);",
  '  if (n >= 150 && n < 165) name("Pop", 900, 900);',
  "  const x = 1300 + 200 * ease((n - 75) / 30);",
  "  ctx.fillStyle = P.ink;",
  "  ctx.beginPath();",
  "  ctx.moveTo(x, 300);",
  "  ctx.lineTo(x + 120, 300);",
  "  ctx.lineTo(x + 120, 345);",
  "  ctx.lineTo(x, 345);",
  "  ctx.closePath();",
  "  ctx.fill();",
  "  if (n > 75) rule(x + 120, 345, x + 120, 345 + 200 * Math.min(1, (n - 75) / 30));",
  "  if (n >= 170) rule(300, 1000, 304 + 1200 * ease((n - 170) / 8), 1000);",
  "  dot(1700, 900, 8);",
  "  if (n < 120) dot(1700, 900, 14);",
  '  name(n < 102 ? "Swap" : "Swapped", 1000, 200);',
  "  ctx.strokeStyle = P.ink;",
  "  ctx.lineWidth = 3;",
  "  ctx.beginPath();",
  "  ctx.moveTo(400, 1030);",
  "  ctx.lineTo(400, 1050);",
  "  const g = Math.min(1, (n - 39) / 6);",
  "  if (g > 0) ctx.moveTo(760, 1040 - 10 * g), ctx.lineTo(760, 1040 + 10 * g);",
  "  ctx.stroke();",
  "  ctx.beginPath();",
  "  ctx.moveTo(500, 60);",
  "  ctx.lineTo(500, 80);",
  "  ctx.moveTo(505 + 10 * (100 - n), 60);",
  "  ctx.lineTo(505 + 10 * (100 - n), 80);",
  "  ctx.stroke();",
  "  if (n > 30) ctx.beginPath(), ctx.arc(1800, 650, 30, 0, Math.PI * Math.min(2, (n - 30) / 10)), ctx.stroke();",
  "  ctx.lineWidth = 2;",
  "  ctx.beginPath();",
  "  for (let k = 0; k < (n >= 60 ? 3 : 2); k++) ctx.roundRect(1600, 100 - 14 * k, 60, 10, 2);",
  "  ctx.stroke();",
  "  if (n >= 50 && n < 60) {",
  "    ctx.globalAlpha = Math.min(1, (n - 49) / 4);",
  "    ctx.beginPath();",
  "    ctx.roundRect(1600, 72 - 30 * (1 - ease((n - 50) / 9)), 60, 10, 2);",
  "    ctx.stroke();",
  "    ctx.globalAlpha = 1;",
  "  }",
  "  ctx.lineWidth = 2;",
  "  if (n >= 60) {",
  "    const sx = 1300 - 6 * (n - 60), drawn = 12 * (n - 60);",
  "    ctx.beginPath();",
  "    ctx.moveTo(sx, 760);",
  "    ctx.lineTo(sx, 760 - Math.min(drawn, 120));",
  "    if (drawn > 120) ctx.lineTo(Math.min(sx + drawn - 120, 1500), 640);",
  "    ctx.stroke();",
  "  }",
  "  if (n >= 30) {",
  "    const gx = 700 - 3 * n, cells = 1 + Math.floor((n - 30) / 10), grown = Math.min(1, ((n - 30) % 10) / 3);",
  "    ctx.beginPath();",
  "    for (let i = 0; i < cells; i++) {",
  "      const r = 10 * (i < cells - 1 ? 1 : grown);",
  "      ctx.roundRect(gx + 40 * i - r, 200 - r, 2 * r, 2 * r, 2);",
  "    }",
  "    ctx.stroke();",
  "  }",
  "  if (n >= 140 && n <= 175) {",
  "    const k = Math.max(0, n - 150), sy = 630 - (k <= 8 ? k * k : 64 + 16 * (k - 8)), reach = Math.max(0, 40 * (n - 164));",
  "    ctx.globalAlpha = Math.min(1, (n - 139) / 10);",
  "    ctx.beginPath();",
  "    ctx.moveTo(600, sy);",
  "    ctx.lineTo(600, 450);",
  "    if (reach > 0) ctx.lineTo(600 - reach, 450);",
  "    ctx.stroke();",
  "  }",
  "  if (n >= 30) {",
  "    const bx = 400 + 600 * ease((n - 40) / 60), shown = Math.min(1, (n - 29) / 10), solid = Math.min(1, Math.max(0, (n - 75) / 15));",
  "    ctx.globalAlpha = shown * solid;",
  "    ctx.beginPath();",
  "    ctx.roundRect(bx, 830, 80, 40, 6);",
  "    ctx.stroke();",
  "    ctx.globalAlpha = shown * (1 - solid);",
  "    ctx.setLineDash([8, 6]);",
  "    ctx.beginPath();",
  "    ctx.roundRect(bx, 830, 80, 40, 6);",
  "    ctx.stroke();",
  "    ctx.setLineDash([]);",
  "    ctx.globalAlpha = 1;",
  "  }",
  "};",
  'scenes["02"] = function (t) {',
  "  const n = Math.round(t * 30);",
  '  const names = n < 240 ? ["A1", "A2", "A3", "A4", "A5"] : ["B1", "B2", "B3", "B4", "B5"];',
  "  names.forEach((v, i) => name(v, 300 + 250 * i, n < 240 ? 300 : 500));",
  "};",
  "window.renderFrame = function (t) {",
  "  layout = [];",
  '  window.__sceneId = t < 6 ? "01" : "02";',
  "  scenes[window.__sceneId](t);",
  "  window.__sceneId = null;",
  "  window.__filmLayout = { time: t, texts: layout };",
  "};",
  "",
];
const lineOf = (code) => `film.js:${MOTIONS.findIndex((line) => line.includes(code)) + 1}`;

async function audit() {
  const root = await scratchFolder();
  await mkdir(join(root, "picture"));
  await writeFile(join(root, "picture/film.js"), MOTIONS.join("\n"));
  const words = Array.from({ length: 45 }, (_, k) => ({
    text: "word",
    start: 0.5 + k * 0.2,
    end: 0.68 + k * 0.2,
  }));
  const path = join(root, "timeline.json"),
    out = join(root, "motion.json");
  await writeFile(
    path,
    JSON.stringify({
      language: "English",
      duration: 10,
      credits_duration: 1,
      captions: [],
      segments: [{ id: "01", start: 0, end: 9, voice_start: 0.5, voice_end: 9.5, words }],
    }),
  );
  const summary = JSON.parse(
    execFileSync(process.execPath, [AUDIT_MOTION, path, "30", "--out", out], {
      cwd: root,
      encoding: "utf8",
    }),
  );
  return { summary, report: JSON.parse(await readFile(out, "utf8")) };
}

test("the motion audit follows every mark and finds each motion a viewer sees as not smooth", async () => {
  const { summary, report } = await audit();
  const followed = report.followed;
  const at = (t) => +t.toFixed(2);
  // The dot halts dead from 240 px/s after frame 61, and sets off at 240 px/s at frame 92.
  assert.deepEqual(
    followed.halts.map((v) => [at(v.t), v.scene, v.kind, v.from, v.origin]),
    [[2.07, "01", "fill", 240, lineOf("dot(1000")]],
  );
  assert.deepEqual(
    followed.starts.map((v) => [at(v.t), v.scene, v.kind, v.to, v.origin]),
    [[3.07, "01", "fill", 240, lineOf("dot(1000")]],
  );
  // The name races between frames 120 and 132; its eased start and end are neither a start nor a halt.
  assert.ok(followed.races.length > 0);
  assert.ok(followed.races.every((v) => v.text === "Race" && v.t > 4 && v.t < 4.4));
  assert.ok(followed.races.every((v) => v.speed >= 900 && v.origin === lineOf('"Race"')));
  // The larger dot vanishes at frame 120, named by its own line though the dot it stood around shares its centre, and
  // the name pops in at frame 150 and out at frame 165; the scene's other marks, the flowing dot, the counter, the
  // link drawn on from the gliding card and the rule drawn on in place follow on, and scene 02's handover is a stage
  // cut.
  assert.deepEqual(
    followed.pops.map((v) => [at(v.t), v.way, v.kind, v.text, v.origin]),
    [
      [4, "out", "fill", "", lineOf("dot(1700, 900, 14)")],
      [5, "in", "text", "Pop", lineOf('"Pop"')],
      [5.5, "out", "text", "Pop", lineOf('"Pop"')],
    ],
  );
  // Each finding groups one mark's frames: the race is one finding with its peak speed.
  assert.deepEqual(
    followed.findings.map((v) => [v.kind, v.scene, at(v.start), v.origin]),
    [
      ["halt", "01", 2.07, lineOf("dot(1000")],
      ["start", "01", 3.07, lineOf("dot(1000")],
      ["pop", "01", 4, lineOf("dot(1700, 900, 14)")],
      ["race", "01", 4.07, lineOf('"Race"')],
      ["pop", "01", 5, lineOf('"Pop"')],
      ["pop", "01", 5.5, lineOf('"Pop"')],
    ],
  );
  const race = followed.findings[3];
  assert.equal(race.speed, Math.max(...followed.races.map((v) => v.speed)));
  assert.ok(race.speed > 2000 && race.frames === followed.races.length);
  assert.deepEqual([race.paints, race.texts], [["text"], ["Race"]]);
  // The speeds a viewer meets: the dot flows at 300 px/s, and the fastest glide is the race.
  assert.equal(followed.speeds["01"].flow.speed, 300);
  assert.equal(followed.speeds["01"].glide.speed, race.speed);
  assert.equal(followed.speeds["02"], undefined);
  assert.deepEqual(summary.followed, {
    halts: 1,
    starts: 1,
    races: followed.races.length,
    pops: 3,
  });
});

test("the least-cost assignment pairs each row with the column that costs least in all", () => {
  // Greedy pairing would take the 1 and be left with 9 and 10; the least total is 2 + 3.
  assert.deepEqual(
    [
      ...leastCostAssignment([
        [2, 1],
        [9, 3],
      ]),
    ],
    [0, 1],
  );
  assert.deepEqual(
    [
      ...leastCostAssignment([
        [4, 1, 3],
        [2, 0, 5],
        [3, 2, 2],
      ]),
    ],
    [1, 0, 2],
  );
});
