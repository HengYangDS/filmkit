/** Exercise the motion audit on the sample film and on a composition that shows each artefact it looks for. */
import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { authoredTimeline, scratchFolder } from "./sample-film.mjs";

const AUDIT_MOTION = fileURLToPath(
  new URL("../../src/filmkit/picture/motion-audit.mjs", import.meta.url),
);

test("the motion audit summarises marks across frames and traces them to their scene", async () => {
  const film = await authoredTimeline("en"),
    folder = await scratchFolder();
  const path = join(folder, "timeline.json"),
    out = join(folder, "motion.json");
  await writeFile(path, JSON.stringify(film));
  const at = film.segments[2].voice_start;
  const summary = JSON.parse(
    execFileSync(
      process.execPath,
      [AUDIT_MOTION, path, "10", "--from", String(at), "--to", String(at + 8), "--out", out],
      { encoding: "utf8" },
    ),
  );
  assert.equal(summary.fps, 10);
  const report = JSON.parse(await readFile(out, "utf8"));
  assert.ok(Array.isArray(report.colour_snaps) && Array.isArray(report.still));
  assert.ok(
    report.colour_snaps.every((snap) => snap.origin === null || /^film\.js:\d+$/.test(snap.origin)),
  );
});

/* A composition that shows each artefact the motion audit looks for, at a known time while its voice runs: a word
 * that pops in and out, a word that jumps, a rule whose colour snaps, two cards that cross, a word resting faint, a
 * picture that empties and stands again, the pauses between those changes, a still end and a camera that reframes. */
const ARTEFACTS = `var P = { ground: "#0F1519", ink: "#ECE8DF", accent: "#7DB7D8" };
var ctx = document.getElementById("picture").getContext("2d");
var scenes = {};
var layout = [];
function text(value, x, y, alpha) {
  ctx.font = "40px Sample";
  ctx.textAlign = "left";
  ctx.textBaseline = "alphabetic";
  ctx.globalAlpha = alpha;
  ctx.fillStyle = P.ink;
  ctx.fillText(value, x, y);
  ctx.globalAlpha = 1;
  layout.push({ text: value, alpha: alpha, role: "label", scene: window.__sceneId });
}
function card(x, y, alpha) {
  if (alpha <= 0) return;
  ctx.globalAlpha = alpha;
  ctx.fillStyle = P.ink;
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(x + 120, y);
  ctx.lineTo(x + 120, y + 90);
  ctx.lineTo(x, y + 90);
  ctx.closePath();
  ctx.fill();
  ctx.globalAlpha = 1;
}
function rule(color) {
  ctx.strokeStyle = color;
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.moveTo(300, 800);
  ctx.lineTo(900, 800);
  ctx.stroke();
}
scenes["01"] = function (t) {
  if (t >= 9 && t < 9.6) return;
  text("Stand", 300, 300, 1);
  rule(t < 5 ? P.ink : P.accent);
  if (t >= 2 && t < 4) text("Pop", 700, 400, 1);
  if (t < 9) text("Jump", t < 3 ? 1000 : 1040, t < 3 ? 600 : 645, 1);
  if (t >= 6 && t < 7) {
    card(1200, 300, 1 - (t - 6));
    card(1220, 320, t - 6);
  }
  if (t >= 7.5 && t < 9) text("Faint", 400, 500, 0.15);
};
function cameraOf(segment, t) {
  return { k: t < 6 ? 1 : 1.1, ox: 0, oy: 0, ax: 960, ay: 540 };
}
window.renderFrame = function (t) {
  layout = [];
  window.__sceneId = "01";
  scenes["01"](t);
  window.__sceneId = null;
  window.__filmLayout = { time: t, texts: layout };
};
`;

test("the motion audit reports each artefact a composition shows, at its time and from its line", async () => {
  const root = await scratchFolder();
  await mkdir(join(root, "picture"));
  await writeFile(join(root, "picture/film.js"), ARTEFACTS);
  const lines = ARTEFACTS.split("\n"),
    lineOf = (code) => `film.js:${lines.findIndex((line) => line.includes(code)) + 1}`;
  const words = Array.from({ length: 70 }, (_, k) => ({
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
      duration: 16,
      credits_duration: 1,
      captions: [],
      segments: [{ id: "01", start: 0, end: 15, voice_start: 0.5, voice_end: 14.5, words }],
    }),
  );
  execFileSync(process.execPath, [AUDIT_MOTION, path, "10", "--out", out], {
    cwd: root,
    encoding: "utf8",
  });
  const report = JSON.parse(await readFile(out, "utf8"));
  const when = (t) => +t.toFixed(2);
  // A firm mark that appears or leaves within one frame: the word at 2 s and 4 s, the card arriving whole and the
  // one leaving at 0.9 opacity, and the picture leaving at 9 s and standing again, each from the line that paints it.
  assert.deepEqual(
    report.pops.map((v) => [when(v.t), v.way, v.kind, v.text, v.origin]),
    [
      [2, "in", "text", "Pop", lineOf('"Pop"')],
      [4, "out", "text", "Pop", lineOf('"Pop"')],
      [6, "in", "fill", undefined, lineOf("card(1200")],
      [7, "out", "fill", undefined, lineOf("card(1220")],
      [9, "out", "text", "Stand", lineOf('"Stand"')],
      [9, "out", "stroke", undefined, lineOf("rule(t < 5")],
      [9, "out", "text", "Jump", lineOf('"Jump"')],
      [9.6, "in", "text", "Stand", lineOf('"Stand"')],
      [9.6, "in", "stroke", undefined, lineOf("rule(t < 5")],
    ],
  );
  // The word moving 60 px within one frame at 3 s, and the rule turning from ink to accent at 5 s.
  assert.deepEqual(
    report.jumps.map((v) => [v.t, v.text, v.distance, v.origin]),
    [[3, "Jump", 60, lineOf('"Jump"')]],
  );
  assert.deepEqual(
    report.colour_snaps.map((v) => [v.t, v.kind, v.from, v.to, v.origin]),
    [[5, "stroke", "#ECE8DF", "#7DB7D8", lineOf("rule(t < 5")]],
  );
  // The two cards are both half there from 6.2 s to 6.8 s, one fading where the other rises.
  assert.deepEqual(report.double_exposure, [
    {
      start: 6.2,
      end: 6.8,
      frames: 7,
      area: 7000,
      at_cut: false,
      origins: [`-${lineOf("card(1200")}`, `+${lineOf("card(1220")}`],
    },
  ]);
  // The word resting in the faint band for 1.5 s, in the colour it rests in.
  assert.deepEqual(report.faint_rests, [
    {
      scene: "01",
      kind: "text",
      text: "Faint",
      color: "#ECE8DF",
      start: 7.5,
      seconds: 1.5,
      low: 33,
      high: 33,
      origin: lineOf('"Faint"'),
    },
  ]);
  // The empty picture from 9 s while the voice runs, the pauses after the pop, the jump and the empty picture, each
  // between two changes, and the still end once the picture stands again.
  assert.deepEqual(report.dips, [{ start: 9, end: 9.5, scene: "01", floor: 0, seconds: 0.5 }]);
  assert.deepEqual(report.hitches, [
    { t: 2.1, gap: 0.9, scene: "01" },
    { t: 3.1, gap: 0.9, scene: "01" },
    { t: 9.1, gap: 0.5, scene: "01" },
  ]);
  assert.deepEqual(
    report.still.map((v) => [when(v.start), when(v.end), v.scene, v.seconds]),
    [[9.7, 14.4, "01", 4.7]],
  );
  // The camera's one reframe at 6 s, and the size every label is shown at.
  assert.deepEqual(report.camera["01"], { k: [1, 1.1], reframes: 1, moves: [[0, 6, 1.1]] });
  assert.deepEqual(report.type["01"], { p05: 40, median: 40, p95: 40, vs_film: 1 });
});
