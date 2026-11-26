/** Exercise the frame audit's vertical runs: still states whose box, of the scene drawn, stands off y 510. */
import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { scratchFolder } from "./sample-film.mjs";

const AUDIT_FRAMES = fileURLToPath(
  new URL("../../src/filmkit/picture/frame-audit.mjs", import.meta.url),
);

/* Each case's picture, by the timeline's `vertical`. A box of names 400 px wide and 100 px tall in scene 01, at y 590
 * from 0.5 s (`still`), at y 530 (`near`), a row at y 600 that grows sideways by a name every 0.6 s (`row`), a box at
 * y 600 whose bottom edge grows by 40 px over 3 s (`down`), a box at y 590 split by the stage cut the composition
 * declares at 1.5 s (`cut`), credits drawn with no scene, centred on y 584 (`credits`), and scene 01 drawn at y 600
 * from 2 s until 4.2 s, 1.2 s into the next segment (`outgoing`). Scene 02 stands centred from 3 s, or from 4.2 s in
 * `outgoing`. The audit samples t by adding its step, so each change falls between two samples. */
const VERTICAL = `"use strict";
const ctx = document.getElementById("picture").getContext("2d");
var P = { ground: "#0F1519", ink: "#ECE8DF" };
var stageCuts = new Map(window.FILM.vertical === "cut" ? [["01", [1.5]]] : []);
function box(x0, y0, x1, y1) {
  ctx.fillStyle = P.ink;
  ctx.beginPath();
  ctx.moveTo(x0, y0);
  ctx.lineTo(x1, y0);
  ctx.lineTo(x1, y1);
  ctx.lineTo(x0, y1);
  ctx.closePath();
  ctx.fill();
}
const centred = (y, width = 400, height = 100) =>
  box(960 - width / 2, y - height / 2, 960 + width / 2, y + height / 2);
window.renderFrame = (t) => {
  const kind = window.FILM.vertical;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1;
  ctx.fillStyle = P.ground;
  ctx.fillRect(0, 0, 1920, 1080);
  const next = t > (kind === "outgoing" ? 4.15 : 2.95);
  window.__sceneId = kind === "credits" ? null : next ? "02" : "01";
  if (next && kind !== "credits") centred(510);
  else if (kind === "still") centred(t < 0.45 ? 510 : 590);
  else if (kind === "near") centred(530);
  else if (kind === "row")
    for (let k = 0; k <= Math.floor((t + 0.05) / 0.6); k++) box(560 + 100 * k, 580, 640 + 100 * k, 620);
  else if (kind === "down") box(760, 550, 1160, 650 + (40 * t) / 3);
  else if (kind === "cut" || kind === "credits") centred(kind === "cut" ? 590 : 584);
  else centred(t < 1.95 ? 510 : 600);
  window.__sceneId = null;
  window.__filmLayout = { time: t, texts: [] };
};
`;

/* The frame report of one case, sampled every 0.1 s over segment 01 from 0 to 3 s and segment 02 from 3 to 6 s. */
async function audited(vertical) {
  const root = await scratchFolder(),
    path = join(root, "timeline.json");
  await mkdir(join(root, "picture"));
  await writeFile(join(root, "picture/film.js"), VERTICAL);
  const segment = (id, start) => ({
    id,
    chapter: "sample",
    start,
    end: start + 3,
    voice_start: start + 0.2,
    voice_end: start + 2.8,
    utterance_groups: ["Names"],
    words: [{ text: "Names", start: start + 0.2, end: start + 2.8 }],
  });
  const segments = [segment("01", 0), segment("02", 3)];
  await writeFile(
    path,
    JSON.stringify({ edition: "en", duration: 6, segments, captions: [], vertical }),
  );
  return JSON.parse(
    execFileSync(process.execPath, [AUDIT_FRAMES, path, "0.1"], { cwd: root, encoding: "utf8" }),
  );
}

test("a still box 80 px below y 510 for 2.5 s is a vertical run of its scene; 20 px is not", async () => {
  const report = await audited("still");
  assert.deepEqual(report.errors, []);
  assert.deepEqual(report.off_centre_vertical, { "01": ["0.50-3.00 80.0 px"] });
  assert.deepEqual((await audited("near")).off_centre_vertical, {});
});

test("a row that grows sideways and a box that grows downward are no still states", async () => {
  assert.deepEqual((await audited("row")).off_centre_vertical, {});
  assert.deepEqual((await audited("down")).off_centre_vertical, {});
});

test("a declared stage cut splits a still state, and credits drawn with no scene are not weighed", async () => {
  assert.deepEqual((await audited("cut")).off_centre_vertical, {});
  assert.deepEqual((await audited("credits")).off_centre_vertical, {});
});

test("the outgoing scene drawn into the next segment keeps its run past the segment's start", async () => {
  // Keyed by the segment, 1 s and 1.2 s of it would each be too short; keyed by the scene drawn, it is one run.
  assert.deepEqual((await audited("outgoing")).off_centre_vertical, {
    "01": ["2.00-4.20 90.0 px"],
  });
});
