/** Exercise the mass audit: the grey it reads a frame on, the lit cells of the scene drawn and their mass centre, the
 * runs of the mass off x 960 and each scene's summary, on stages the renderer would draw. */
import test from "node:test";
import assert from "node:assert/strict";
import { join } from "node:path";
import { createCanvas, GlobalFonts } from "@napi-rs/canvas";

import { measureMass } from "../../src/filmkit/picture/mass-audit.mjs";
import { SAMPLE, stage } from "./sample-film.mjs";

/* A composition that lays the sample's ground, by `ground`, and draws, at each t, what `body` draws: `body` is JavaScript
 * run with `t`, the context `ctx`, the helpers `box(x0, y0, x1, y1, colour)` and `rail(x, declared)`, and the scene
 * set to "01" unless `body` sets another. The picture scales by the film element's width, as the sample's does. */
const FILL_RECT = "ctx.fillStyle = P.ground; ctx.fillRect(0, 0, 1920, 1080);";
const composition = (body, ground = FILL_RECT) => `"use strict";
const ctx = document.getElementById("picture").getContext("2d", { alpha: false });
const resolution = Number(document.getElementById("film").dataset.width) / 1920;
const P = { ground: "#0F1519", line: "#63758B", ink: "#ECE8DF" };
function box(x0, y0, x1, y1, colour = P.ink) {
  ctx.fillStyle = colour;
  ctx.beginPath();
  ctx.moveTo(x0, y0);
  ctx.lineTo(x1, y0);
  ctx.lineTo(x1, y1);
  ctx.lineTo(x0, y1);
  ctx.closePath();
  ctx.fill();
}
function rail(x, declared) {
  window.__paintRole = declared ? "frame" : null;
  ctx.strokeStyle = P.line;
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.moveTo(x, 120);
  ctx.lineTo(x, 919);
  ctx.stroke();
  window.__paintRole = null;
}
window.renderFrame = (t) => {
  ctx.setTransform(resolution, 0, 0, resolution, 0, 0);
  ctx.globalAlpha = 1;
  ${ground}
  window.__sceneId = "01";
  ${body}
  window.__sceneId = null;
};
`;

/* The mass report of a stage of `seconds` drawing `body`, at the renderer's frame unless `record` says otherwise. */
async function measured(body, { seconds = 2, record = {}, ground = FILL_RECT } = {}) {
  const folder = await stage("en", {
    script: composition(body, ground),
    record: { duration: seconds, ...record },
  });
  return measureMass(folder, "system");
}
const near = (a, b, within) => Math.abs(a - b) <= within;

test("a stage record that names no duration is refused, not measured as empty", async () => {
  const folder = await stage("en", {
    script: composition("box(200, 400, 600, 600);"),
    record: { duration: null },
  });
  await assert.rejects(
    async () => measureMass(folder, "system"),
    /names no duration; stage the picture again/,
  );
});

test("the audit lets the event loop turn while it draws, so each frame's readback is freed as it goes", async () => {
  // A frame's readback is native memory that Node frees only when its event loop turns (engine finding 11). On a
  // stage of 120 frames the audit yields at least twice: a task queued before it runs while it draws.
  const folder = await stage("en", {
    script: composition("box(200, 400, 600, 600);"),
    record: { duration: 30 },
  });
  let turns = 0,
    drawing = true;
  const turn = () => {
    if (!drawing) return;
    turns++;
    setImmediate(turn);
  };
  setImmediate(turn);
  const report = await measureMass(folder, "system");
  drawing = false;
  assert.equal(report.frames.length, 120);
  assert.ok(turns >= 2, `the event loop turned ${turns} times while the audit drew 120 frames`);
});

test("a cell is lit when the full-range luma of its mean colour is above 60", async () => {
  // A square of grey 61 from x 200 to 600 and one of grey 59 from x 1300 to 1700.
  const report = await measured(
    'box(200, 400, 600, 600, "#3D3D3D"); box(1300, 400, 1700, 600, "#3B3B3B");',
  );
  const [frame] = report.frames;
  assert.equal(frame.cells, 100 * 50);
  assert.ok(near(frame.centre[0], 400, 0.01), String(frame.centre));
});

test("a filled square weighs at its centre, on a canvas of the composition's frame", async () => {
  const report = await measured("box(200, 400, 600, 600);", {
    record: { width: 3840, height: 2160 },
  });
  // A stage recorded at the UHD frame is drawn at 1920 x 1080, each cell 4 x 4 px.
  assert.deepEqual(report.canvas, [1920, 1080]);
  assert.ok(near(report.frames[0].centre[0], 400, 4));
  // A running head above row 120 adds nothing.
  const headed = await measured("box(200, 400, 600, 600); box(800, 40, 1800, 100);");
  assert.deepEqual(headed.frames[0], report.frames[0]);
});

test("text weighs by its ink, which its box cannot tell", async () => {
  // "L." and ".L" drawn centred at one anchor: a box measure reads both on x 960 (their advances differ by the kerning
  // of "L." alone, 4 px at 160 px), while their ink stands apart.
  GlobalFonts.registerFromPath(
    join(SAMPLE, "assets/fonts/ibm-plex-sans-regular.ttf"),
    "SampleLatin",
  );
  const probe = createCanvas(10, 10).getContext("2d");
  probe.font = "160px SampleLatin";
  assert.ok(Math.abs(probe.measureText("L.").width - probe.measureText(".L").width) <= 4);
  const drawn = async (text, size) =>
    (
      await measured(
        `ctx.fillStyle = P.ink; ctx.font = "${size}px SampleLatin"; ctx.textAlign = "center"; ` +
          `ctx.fillText(${JSON.stringify(text)}, 960, 560);`,
      )
    ).frames[0];
  const [left, right] = [await drawn("L.", 160), await drawn(".L", 160)];
  assert.ok(left.cells >= 40 && right.cells >= 40, `${left.cells} ${right.cells}`);
  assert.ok(right.centre[0] - left.centre[0] > 15, `${left.centre} ${right.centre}`);
  // At the sample's label size each lights fewer than 40 cells and has no mass.
  for (const text of ["L.", ".L"]) assert.equal((await drawn(text, 38)).centre, null);
});

test("a frame of 39 lit cells has no mass, and a line half over a cell is lit over the ground", async () => {
  // 13 x 3 whole cells.
  assert.equal((await measured("box(400, 400, 452, 412);")).frames[0].centre, null);
  // A 2 px line in the line colour over x 400-402 from y 200 to 700 covers half of each cell of column 100: grey 67.4
  // over the ground, which is lit; over the canvas's starting black it would read 57.4.
  const line = await measured(
    "ctx.strokeStyle = P.line; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(401, 200); " +
      "ctx.lineTo(401, 700); ctx.stroke();",
  );
  assert.equal(line.frames[0].cells, 125);
  assert.ok(near(line.frames[0].centre[0], 402, 0.01));
});

test("credits drawn with no scene give no mass and no run, and are counted outside every scene", async () => {
  const report = await measured("window.__sceneId = null; box(200, 400, 600, 600);", {
    seconds: 3,
  });
  assert.ok(report.frames.every((frame) => frame.scene === null && frame.centre === null));
  assert.deepEqual(report.off_centre_mass, {});
  assert.deepEqual(report.mass_balance, {});
  assert.equal(report.outside_scenes, report.frames.length);
});

test("a declared rail is not weighed, and an undeclared one is", async () => {
  const declared = await measured("box(200, 400, 600, 600); rail(1720, true);");
  assert.ok(near(declared.frames[0].centre[0], 400, 4));
  assert.equal(declared.mass_balance["01"].declared, declared.frames.length);
  const undeclared = await measured("box(200, 400, 600, 600); rail(1720, false);");
  assert.ok(undeclared.frames[0].cells > declared.frames[0].cells);
  assert.ok(undeclared.frames[0].centre[0] > 404);
});

// Names of 1600 lit cells whose own mass stands at x 810, 150 px left, between rails at x 200 and 1720.
const LEANING = (declared, x = 810) =>
  `rail(200, ${declared}); rail(1720, ${declared}); box(${x - 160}, 470, ${x + 160}, 550);`;

test("names leaning left between rails make a mass run, declared or not; centred they make none", async () => {
  const undeclared = await measured(LEANING(false), { seconds: 3 });
  const [run] = undeclared.off_centre_mass["01"];
  const [span, offset] = /^(\S+) (-?[\d.]+) px$/.exec(run).slice(1);
  assert.equal(span, "0.00-3.00");
  assert.ok(Number(offset) < -90, run);
  const declared = await measured(LEANING(true), { seconds: 3 });
  const [kept] = declared.off_centre_mass["01"];
  assert.ok(near(Number(/(-?[\d.]+) px$/.exec(kept)[1]), -150, 4), kept);
  assert.deepEqual((await measured(LEANING(true, 960), { seconds: 3 })).off_centre_mass, {});
  // Each scene's summary: the frames it was measured in, the median offsets and the share within 90 px.
  const summary = declared.mass_balance["01"];
  // Three seconds at the audit's step of 0.25 s.
  assert.equal(summary.frames, 12);
  assert.equal(summary.faint, 0);
  assert.ok(near(summary.median_dx, -150, 4) && near(summary.median_dy, 0, 4));
  assert.equal(summary.within, 0);
});

test("the outgoing scene drawn into the next segment keeps its run past the segment's start", async () => {
  // The next segment starts at 0.5 s, and the composition draws scene 03 until the incoming scene's cut at 1.75 s,
  // 1.25 s into it, its mass 120 px left from 0 s; then scene 04 stands centred. The audit reads no segment: the run
  // is the scene drawn's, one of 1.75 s across the segment's start.
  const report = await measured(
    'if (t < 1.7) { window.__sceneId = "03"; box(680, 470, 1000, 550); }' +
      ' else { window.__sceneId = "04"; box(800, 470, 1120, 550); }',
    { seconds: 3 },
  );
  assert.deepEqual(report.off_centre_mass, { "03": ["0.00-1.75 -120.0 px"] });
  // Every frame is accounted for: weighed in a scene, too faint to weigh, or drawn outside every scene.
  const counted = Object.values(report.mass_balance).reduce((n, v) => n + v.frames + v.faint, 0);
  assert.equal(counted + report.outside_scenes, report.frames.length);
});

test("a frame that lays no ground over the whole canvas is refused, never weighed on the last one", async () => {
  // A ground laid by a path fill outside every scene, or none: the canvas would keep the frame before.
  for (const ground of [
    "box(0, 0, 1920, 1080, P.ground);",
    "",
    "ctx.fillStyle = P.ground; ctx.fillRect(0, 0, 960, 1080);",
  ])
    await assert.rejects(
      measured("box(200 + 100 * t, 400, 600 + 100 * t, 600);", { ground }),
      /lays no ground over the whole canvas with fillRect before it paints/,
    );
  // A translucent ground does not clear the canvas either.
  await assert.rejects(
    measured("box(200, 400, 600, 600);", {
      ground: "ctx.globalAlpha = 0.5; " + FILL_RECT + " ctx.globalAlpha = 1;",
    }),
    /lays no ground/,
  );
});

test("a frame that paints only declared frame strokes is the scene's, and a fillRect outside a scene is not weighed", async () => {
  const framed = await measured("rail(200, true); rail(1720, true);");
  assert.ok(framed.frames.every((frame) => frame.scene === "01" && frame.centre === null));
  assert.deepEqual(framed.mass_balance["01"].declared, 2 * framed.frames.length);
  assert.equal(framed.mass_balance["01"].faint, framed.frames.length);
  assert.equal(framed.outside_scenes, 0);
  // A mark drawn with fillRect outside every scene is no ground and no scene's paint.
  const outside = await measured(
    "window.__sceneId = null; ctx.fillStyle = P.ink; ctx.fillRect(1300, 400, 400, 200); " +
      'window.__sceneId = "01"; box(200, 400, 600, 600);',
  );
  assert.ok(near(outside.frames[0].centre[0], 400, 4), String(outside.frames[0].centre));
});
