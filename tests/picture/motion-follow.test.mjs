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
 * and out; a name gives way to another at the stage cut the composition declares at frame 102, which keeps the rest of
 * its stage, so the name it brings pops; a card glides while a link draws on from it; a rule is drawn on in place,
 * 1,200 px in eight frames, its end at up to 225 px a frame; a larger dot around a standing dot vanishes at frame 120.
 * None of these follows and nothing is found: the name the cut at frame 102 takes away; a bracket's second end enters
 * 360 px from its first by size, from frame 40; a span's moving end slides through its fixed end at frame 101; a ring
 * is drawn on from a point, from frame 31; a slab eases down and joins its stack at frame 60; a link is drawn on from a
 * start that glides 180 px/s and turns its corner at frame 71; a row of squares glides 90 px/s while a square grows in
 * at its end every ten frames; a link drawn on from a rising start turns its corner as the start rises through it at
 * frame 165; a box's dashed outline gives way to a solid one while the box glides, from frame 77. Scene 02 hands five
 * names to five others below them in one frame. */
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

async function audit(composition = MOTIONS) {
  const root = await scratchFolder();
  await mkdir(join(root, "picture"));
  await writeFile(join(root, "picture/film.js"), composition.join("\n"));
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
  // The declared cut at frame 102 brings its name onto a stage that stands, the larger dot vanishes at frame 120, named
  // by its own line though the dot it stood around shares its centre, and the name pops in at frame 150 and out at
  // frame 165; the scene's other marks, the flowing dot, the counter, the link drawn on from the gliding card and the
  // rule drawn on in place follow on, and scene 02's handover is a stage cut.
  assert.deepEqual(
    followed.pops.map((v) => [at(v.t), v.way, v.kind, v.text, v.origin]),
    [
      [3.4, "in", "text", "Swapped", lineOf('"Swapped"')],
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
      ["pop", "01", 3.4, lineOf('"Swapped"')],
      ["pop", "01", 4, lineOf("dot(1700, 900, 14)")],
      ["race", "01", 4.07, lineOf('"Race"')],
      ["pop", "01", 5, lineOf('"Pop"')],
      ["pop", "01", 5.5, lineOf('"Pop"')],
    ],
  );
  const race = followed.findings.find((v) => v.kind === "race");
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
    pops: 4,
    jumps: 0,
    dash_snaps: 0,
  });
});

/* Scene 01 draws four strokes of several pieces. The carried links: the first is said at frame 10 and inks in over
 * 0.3 s, the second joins the stroke whole at full ink at frame 30 while the first stands, the third draws on from its
 * first point from frame 45, 8 px in its first frame, and the first leaves the stroke whole at frame 100. The turning
 * stroke holds a short standing link and a link drawn on from a start that rises from frame 60, which turns from a
 * vertical stub into a horizontal line at frame 75 as the start rises through its corner; the standing link, which the
 * turned link's box holds, leaves the stroke whole at frame 95. From frame 100 a path that a gap splits from frame 120
 * and joins again at frame 150, and a ring's arcs, the second of which lights from its middle at frame 110 from a seed
 * 5 px across to 31 px across in the next frame, as a stamp's arc lights. */
const PIECES = [
  'var P = { ground: "#0F1519", ink: "#ECE8DF" };',
  'var ctx = document.getElementById("picture").getContext("2d");',
  "var scenes = {};",
  'scenes["01"] = function (t) {',
  "  const n = Math.round(t * 30);",
  "  ctx.strokeStyle = P.ink;",
  "  ctx.lineWidth = 3;",
  "  if (n >= 10) {",
  "    ctx.globalAlpha = Math.min(1, (n - 9) / 9);",
  "    ctx.beginPath();",
  "    if (n < 100) ctx.moveTo(200, 300), ctx.lineTo(400, 300);",
  "    if (n >= 30) ctx.moveTo(200, 360), ctx.lineTo(400, 360);",
  "    if (n >= 45) ctx.moveTo(200, 420), ctx.lineTo(200 + Math.min(200, 8 * (n - 44)), 420);",
  "    ctx.stroke(); // the carried links",
  "  }",
  "  if (n >= 50) {",
  "    const k = Math.min(20, Math.max(0, n - 60)), sy = 830 - (k <= 8 ? k * k : 64 + 16 * (k - 8));",
  "    const reach = Math.min(200, Math.max(0, 40 * (n - 74)));",
  "    ctx.globalAlpha = Math.min(1, (n - 49) / 10);",
  "    ctx.beginPath();",
  "    if (n < 95) ctx.moveTo(1250, 600), ctx.lineTo(1350, 600);",
  "    ctx.moveTo(1400, sy), ctx.lineTo(1400, 650);",
  "    if (reach > 0) ctx.lineTo(1400 - reach, 650);",
  "    ctx.stroke(); // the turning link",
  "  }",
  "  if (n >= 100) {",
  "    const gap = n >= 120 && n < 150, lit = n < 110 ? 0 : ([1, 6, 15][n - 110] ?? 30) * (Math.PI / 180);",
  "    ctx.globalAlpha = Math.min(1, (n - 99) / 9);",
  "    ctx.beginPath();",
  "    for (const [a, b] of gap ? [[200, 572], [628, 1000]] : [[200, 1000]]) ctx.moveTo(a, 950), ctx.lineTo(b, 950);",
  "    ctx.stroke(); // the path a gap splits",
  "    ctx.beginPath();",
  "    for (const [m, w] of [[0.75 * Math.PI, Math.PI / 6], [0.25 * Math.PI, lit]].filter(([, w]) => w > 0)) {",
  "      ctx.moveTo(1500 + 150 * Math.cos(m - w), 300 + 150 * Math.sin(m - w));",
  "      ctx.arc(1500, 300, 150, m - w, m + w);",
  "    }",
  "    ctx.stroke(); // the lit arcs",
  "  }",
  "  ctx.globalAlpha = 1;",
  "};",
  "window.renderFrame = function (t) {",
  '  window.__sceneId = "01";',
  '  scenes["01"](t);',
  "  window.__sceneId = null;",
  "  window.__filmLayout = { time: t, texts: [] };",
  "};",
  "",
];
const pieceLine = (code) => `film.js:${PIECES.findIndex((line) => line.includes(code)) + 1}`;
let piecesAudit;
/* The pops of the stroke drawn at the line holding `code`, from one audit of the composition. */
async function popsOf(code) {
  const { report } = await (piecesAudit ??= audit(PIECES));
  const at = (t) => +t.toFixed(2);
  return report.followed.pops
    .filter((v) => v.origin === pieceLine(code))
    .map((v) => [at(v.t), v.way, v.kind, v.level, v.piece]);
}

test("a stroke pops by a link that joins it whole at full ink, from the stroke's line", async () => {
  const { report } = await (piecesAudit ??= audit(PIECES));
  // The second link joins at frame 30 while the first, inked in over 0.3 s, stands: the stroke pops in by that link.
  assert.deepEqual(
    (await popsOf("the carried links")).find((v) => v[0] === 1),
    [1, "in", "stroke", 221, [200, 360, 400, 360]],
  );
  // check-picture refuses it as a pop that names the stroke's line.
  const finding = report.followed.findings.find((v) => v.origin === pieceLine("the carried links"));
  assert.deepEqual(
    [finding?.kind, finding?.scene, finding?.start, finding?.way, finding?.level, finding?.frames],
    ["pop", "01", 1, "in", 221, 1],
  );
});

test("a link drawn on from its first point pops no piece of its stroke", async () => {
  // The third link draws on from frame 45, 8 px long in its first frame: the stroke pops only where a link joins or
  // leaves it whole.
  assert.deepEqual(await popsOf("the carried links"), [
    [1, "in", "stroke", 221, [200, 360, 400, 360]],
    [3.33, "out", "stroke", 221, [200, 300, 400, 300]],
  ]);
});

test("a stroke that loses its first link whole pops out by that link, not by one its order shifts", async () => {
  // In their order the links that stay stand where the one before each stood; the stroke's motion places them.
  assert.deepEqual(
    (await popsOf("the carried links")).find((v) => v[1] === "out"),
    [3.33, "out", "stroke", 221, [200, 300, 400, 300]],
  );
});

test("a link that turns from a vertical stub into a horizontal line keeps its piece by its first point", async () => {
  // Its start rises up to 16 px a frame while the short link stands, and its box flips at the corner at frame 75: no
  // pop. The short link, drawn ahead of it, leaves the stroke whole at frame 95 and pops out.
  assert.deepEqual(await popsOf("the turning link"), [
    [3.17, "out", "stroke", 221, [1250, 600, 1350, 600]],
  ]);
});

test("a path that a gap splits and joins again, and an arc lit from a seed, pop no piece", async () => {
  // Each piece of the split path keeps one end of the path, and the joined path both ends of its pieces; the arc grows
  // from a seed too small to place by its own growth.
  assert.deepEqual(await popsOf("the path a gap splits"), []);
  assert.deepEqual(await popsOf("the lit arcs"), []);
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
