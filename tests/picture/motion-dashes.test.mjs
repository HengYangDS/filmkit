/** A stroke's dashes open and close over time: the dash pattern the headless canvas records for each stroke, and the
 * dash snaps the follower finds where a followed stroke's gaps open or close within one frame. */
import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { canvasStandIn } from "../../src/filmkit/picture/headless-composition.mjs";
import { follower } from "../../src/filmkit/picture/motion-audit/follow.mjs";
import { scratchFolder } from "./sample-film.mjs";

const AUDIT_MOTION = fileURLToPath(
  new URL("../../src/filmkit/picture/motion-audit.mjs", import.meta.url),
);
const DT = 1 / 30;
const at = (t) => +t.toFixed(3);
const ease = (q) => (q <= 0 ? 0 : q >= 1 ? 1 : q * q * (3 - 2 * q));

test("the headless canvas records each stroke's dash pattern as a canvas holds it", () => {
  const paints = [],
    ctx = canvasStandIn((paint) => paints.push(paint));
  const line = (dash) => {
    ctx.setLineDash(dash);
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(100, 0);
    ctx.stroke();
  };
  // An odd pattern repeats, and a pattern with a negative or an infinite length leaves the pattern as it was.
  [[8, 8], [5], [4, -2], [4, Infinity], []].forEach(line);
  assert.deepEqual(
    paints.map((paint) => [paint.dash, paint.dashed]),
    [
      [[8, 8], true],
      [[5, 5], true],
      [[5, 5], true],
      [[5, 5], true],
      [[], false],
    ],
  );
});

/* Scene 13's join as the audit hands it to the follower: a stroke at ink 200 from x 300, `drawn` px long, with the
 * dash pattern `dash` and the opacity `alpha`. */
const join13 = (dash, { drawn = 600, alpha = 1, x = 300 } = {}) => ({
  scene: "13",
  kind: "stroke",
  text: "",
  width: 2.5,
  level: 200 * alpha,
  screen: [x, 500, x + drawn, 503],
  dash,
});
/* What the follower finds in frames 0 to 29 at 30 fps, frame n showing the marks `marksAt(n)` at ink 25 or more, as the
 * audit follows them, with the cut of each of `scenes` declared at frame 10. */
function follow(marksAt, scenes = []) {
  const viewer = follower(DT);
  for (let n = 0; n < 30; n++)
    viewer.frame(
      n * DT,
      marksAt(n).filter((m) => m.level >= 25),
      n === 10 ? scenes : [],
    );
  return viewer.finish();
}

test("a join that turns dashed within one frame snaps, and one that breaks over a third of a second does not", () => {
  const snapped = follow((n) => [join13(n < 10 ? [] : [8, 8])]);
  assert.deepEqual(
    snapped.dash_snaps.map((v) => [at(v.t), v.scene, v.kind, v.gaps]),
    [[at(10 * DT), "13", "stroke", [0, 0.5]]],
  );
  // A pattern of 6 on, 2 off, 2 on and 2 off is a third gap: a solid join that takes it within one frame snaps.
  const third = follow((n) => [join13(n < 10 ? [] : [6, 2, 2, 2])]);
  assert.deepEqual(
    third.dash_snaps.map((v) => v.gaps),
    [[0, 0.33]],
  );
  // Gaps that open from 0 to 8 px of each 16 px over 0.35 s, eased, open by at most 0.07 of the pattern a frame.
  const broken = follow((n) => {
    const b = ease((n * DT - 0.2) / 0.35);
    return [join13(b > 0 ? [16 - 8 * b, 8 * b] : [])];
  });
  assert.deepEqual(broken.dash_snaps, []);
  // A stage cut may switch a join's dashes, as it may replace the join.
  assert.deepEqual(follow((n) => [join13(n < 10 ? [] : [8, 8])], ["13"]).dash_snaps, []);
});

test("a dashed way drawn on, and a dashed outline crossfading into a solid one, snap no dash", () => {
  // The way draws on 20 px a frame in one pattern.
  assert.deepEqual(follow((n) => [join13([8, 6], { drawn: 40 + 20 * n })]).dash_snaps, []);
  // The two outlines stand on one box, at rest and gliding 3 px a frame, while the solid one rises from frame 5 to 20
  // and the dashed one falls: each continues the one of its own pattern.
  for (const glide of [0, 3]) {
    const found = follow((n) => {
      const solid = Math.min(1, Math.max(0, (n - 5) / 15)),
        x = 300 + glide * n;
      return [join13([], { alpha: solid, x }), join13([8, 6], { alpha: 1 - solid, x })];
    });
    assert.deepEqual([found.dash_snaps, found.pops], [[], []]);
  }
});

/* Scene 13 draws three ways: a join that turns dashed between frames 30 and 31, a join whose gaps open over 0.35 s from
 * 1.5 s, and a dashed way drawn on over 2 s. */
const DASHES = `var P = { ground: "#0F1519", ink: "#ECE8DF" };
var ctx = document.getElementById("picture").getContext("2d");
var scenes = {};
var ease = (q) => (q <= 0 ? 0 : q >= 1 ? 1 : q * q * (3 - 2 * q));
function way(y, dash, x1) {
  ctx.globalAlpha = 1;
  ctx.strokeStyle = P.ink;
  ctx.lineWidth = 2.5;
  ctx.setLineDash(dash);
  ctx.beginPath();
  ctx.moveTo(300, y);
  ctx.lineTo(x1, y);
  ctx.stroke();
  ctx.setLineDash([]);
}
scenes["13"] = function (t) {
  way(300, t < 30.5 / 30 ? [] : [8, 8], 1500);
  const broken = ease((t - 1.5) / 0.35);
  way(500, broken > 0 ? [16 - 8 * broken, 8 * broken] : [], 1500);
  way(700, [8, 6], 320 + 1180 * Math.min(1, t / 2));
};
window.renderFrame = function (t) {
  window.__sceneId = "13";
  scenes["13"](t);
  window.__sceneId = null;
  window.__filmLayout = { time: t, texts: [] };
};
`;

test("the motion audit reports a dash snap from the line that drew the stroke", async () => {
  const root = await scratchFolder();
  await mkdir(join(root, "picture"));
  await writeFile(join(root, "picture/film.js"), DASHES);
  const lines = DASHES.split("\n"),
    lineOf = (code) => `film.js:${lines.findIndex((line) => line.includes(code)) + 1}`;
  const path = join(root, "timeline.json"),
    out = join(root, "motion.json");
  const words = [{ text: "word", start: 0.5, end: 0.7 }];
  const segments = [{ id: "13", start: 0, end: 3, voice_start: 0.5, voice_end: 2.9, words }];
  await writeFile(
    path,
    JSON.stringify({
      language: "English",
      duration: 3,
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
    followed.findings.map((v) => [v.kind, v.scene, at(v.start), v.origin, v.paints, v.gaps]),
    [["dash", "13", 1.033, lineOf("way(300"), ["stroke"], [0, 0.5]]],
  );
  assert.equal(summary.followed.dash_snaps, 1);
});
