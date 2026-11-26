/** Exercise the declared frame stroke: the role a composition sets while it strokes a frame, the paints that carry it,
 * the role errors the composition's handle finds, and what the frame audit does with a declared frame stroke. */
import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

// Read as a namespace, so that each test meets a missing member by its own assertion.
import * as headless from "../../src/filmkit/picture/headless-composition.mjs";
import { scratchFolder } from "./sample-film.mjs";

const AUDIT_FRAMES = fileURLToPath(
  new URL("../../src/filmkit/picture/frame-audit.mjs", import.meta.url),
);

/* A scene of two rails at x 200 and 1720, a filled square and a name, each painted under the role the timeline's
 * `roles` gives it, and the ground under `roles.ground`. */
const ROLES = `"use strict";
const ctx = document.getElementById("picture").getContext("2d");
var P = { ground: "#0F1519", line: "#63758B", ink: "#ECE8DF" };
const roles = window.FILM.roles;
window.renderFrame = (t) => {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1;
  window.__paintRole = roles.ground ?? null;
  ctx.fillStyle = P.ground;
  ctx.fillRect(0, 0, 1920, 1080);
  window.__sceneId = "01";
  window.__paintRole = roles.rails ?? null;
  ctx.strokeStyle = P.line;
  ctx.lineWidth = 4;
  for (const x of [200, 1720]) {
    ctx.beginPath();
    ctx.moveTo(x, 120);
    ctx.lineTo(x, 919);
    ctx.stroke();
  }
  window.__paintRole = roles.square ?? null;
  ctx.fillStyle = P.line;
  ctx.beginPath();
  ctx.moveTo(800, 600);
  ctx.lineTo(900, 600);
  ctx.lineTo(900, 700);
  ctx.lineTo(800, 700);
  ctx.closePath();
  ctx.fill();
  window.__paintRole = roles.name ?? null;
  ctx.fillStyle = P.ink;
  ctx.font = "38px Sample";
  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";
  ctx.fillText("Sources", 960, 500);
  window.__paintRole = null;
  window.__sceneId = null;
  window.__filmLayout = { time: t, texts: [] };
};
`;

/* The paints and role errors of one frame of ROLES under `roles`, from the composition's handle in this process. */
async function painted(roles) {
  const root = await scratchFolder(),
    before = process.cwd();
  await mkdir(join(root, "picture"));
  await writeFile(join(root, "picture/film.js"), ROLES);
  process.chdir(root);
  try {
    const film = headless.openComposition({ edition: "en", roles });
    const paints = [];
    film.render(1, (paint) => paints.push(paint));
    return { paints, errors: film.roleErrors?.() };
  } finally {
    process.chdir(before);
  }
}

test("a stroke painted while the role is frame carries it, and a paint without one carries none", async () => {
  const { paints, errors } = await painted({ rails: "frame" });
  assert.deepEqual(
    paints.map((p) => [p.kind, p.scene, p.paintRole]),
    [
      ["stroke", "01", "frame"],
      ["stroke", "01", "frame"],
      ["fill", "01", null],
      ["text", "01", null],
    ],
  );
  assert.deepEqual(errors, []);
  assert.equal(headless.DECLARED_FRAME_ROLE, "frame");
});

test("a role of another value, or the frame role on a fill, a text or fillRect, is a role error", async () => {
  const misspelt = await painted({ rails: "frmae" });
  assert.equal(misspelt.errors?.length, 2);
  assert.ok(misspelt.errors.every((error) => error.includes('"frmae"')));
  for (const [roles, call] of [
    [{ square: "frame" }, "fill"],
    [{ name: "frame" }, "fillText"],
    [{ ground: "frame" }, "fillRect"],
  ]) {
    const { paints, errors } = await painted(roles);
    assert.equal(errors?.length, 1, call);
    assert.match(errors[0], new RegExp(`while ${call} paints.*only a stroke`));
    // The stand-in hands over the same paints as ever, and no new kind of paint for fillRect.
    assert.deepEqual(
      paints.map((p) => p.kind),
      ["stroke", "stroke", "fill", "text"],
    );
  }
  // The handle keeps the errors of the frame last rendered.
  assert.deepEqual((await painted({})).errors, []);
});

/* Scene 01 until 3 s and scene 02 after it, each between two rails at x 200 and 1720, stroked under the frame role
 * when the timeline's `declare` is true. Scene 01's names stand 150 px left of centre, or with `first` a first name
 * stands alone 624 px left for its first second before both names stand centred; scene 02's stand centred. */
const MEASURED = `"use strict";
const ctx = document.getElementById("picture").getContext("2d");
var P = { ground: "#0F1519", line: "#63758B", ink: "#ECE8DF" };
const { declare, first } = window.FILM.measured;
let texts = [];
function rails() {
  ctx.strokeStyle = P.line;
  ctx.lineWidth = 4;
  window.__paintRole = declare ? "frame" : null;
  for (const x of [200, 1720]) {
    ctx.beginPath();
    ctx.moveTo(x, 120);
    ctx.lineTo(x, 919);
    ctx.stroke();
  }
  window.__paintRole = null;
}
function name(value, x, y) {
  ctx.fillStyle = P.ink;
  ctx.font = "38px Sample";
  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";
  ctx.fillText(value, x, y);
  const width = ctx.measureText(value).width;
  texts.push({ text: value, bounds: [x - width / 2, y - 30, x + width / 2, y + 8], color: P.ink, alpha: 1,
    role: "label", scene: window.__sceneId, placed: true, size: 38 });
}
window.renderFrame = (t) => {
  texts = [];
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1;
  ctx.fillStyle = P.ground;
  ctx.fillRect(0, 0, 1920, 1080);
  window.__sceneId = t < 3 ? "01" : "02";
  rails();
  // The audit samples t by adding its step, so the first second ends between two samples.
  if (t < 3 && first && t < 0.95) name("Sources", 336, 480);
  else {
    const x = t < 3 && !first ? 810 : 960;
    name("Sources", x, 480);
    name("Films", x, 560);
  }
  window.__sceneId = null;
  window.__filmLayout = { time: t, texts };
};
`;

/* The frame report of MEASURED, sampled every 0.1 s, and the audit's exit status. */
async function audited(measured, composition = MEASURED) {
  const root = await scratchFolder(),
    path = join(root, "timeline.json");
  await mkdir(join(root, "picture"));
  await writeFile(join(root, "picture/film.js"), composition);
  const segment = (id, start) => ({
    id,
    chapter: "sample",
    start,
    end: start + 3,
    voice_start: start + 0.2,
    voice_end: start + 2.8,
    utterance_groups: ["Sources and films"],
    words: ["Sources", "and", "films"].map((text, i) => ({
      text,
      start: start + 0.2 + 0.8 * i,
      end: start + 0.9 + 0.8 * i,
    })),
  });
  const segments = [segment("01", 0), segment("02", 3)];
  await writeFile(
    path,
    JSON.stringify({ edition: "en", duration: 6, segments, captions: [], measured }),
  );
  const done = spawnSync(process.execPath, [AUDIT_FRAMES, path, "0.1"], {
    cwd: root,
    encoding: "utf8",
  });
  return { status: done.status, report: JSON.parse(done.stdout) };
}

test("the reviewers' box leaves declared rails out, and records them per scene", async () => {
  const { status, report } = await audited({ declare: true });
  assert.equal(status, 0);
  assert.deepEqual(report.errors, []);
  assert.deepEqual(report.off_centre_builds, { "01": ["0.00-3.00 -150.0 px"] });
  assert.deepEqual(report.off_centre_finished, { "01": ["0.00-3.00 -150.0 px"] });
  // Two rails 4 px wide from row 120 to row 919, refused by nothing.
  assert.deepEqual(report.declared_frames["01"].strokes, 2);
  assert.deepEqual(report.declared_frames["01"].box, [198, 118, 1722, 921]);
  assert.deepEqual(Object.keys(report.declared_frames), ["01", "02"]);
  // The same rails undeclared centre the box: no build-up and no still run.
  const undeclared = (await audited({ declare: false })).report;
  for (const key of ["builds", "held", "settled", "finished"])
    assert.deepEqual(undeclared[`off_centre_${key}`], {}, key);
  assert.deepEqual(undeclared.declared_frames, {});
  // Every other measure counts the rails as before: the cover at the reviewers' instants and the sparse runs.
  assert.deepEqual(undeclared.thin_lit, report.thin_lit);
  assert.deepEqual(undeclared.sparse_runs, report.sparse_runs);
});

test("a first mark alone far left inside declared rails is a far run, as without the rails", async () => {
  const { report } = await audited({ declare: true, first: true });
  assert.deepEqual(report.off_centre_far, { "01": ["0.00-1.00 -624.0 px"] });
  assert.deepEqual((await audited({ declare: false, first: true })).report.off_centre_far, {});
});

test("the frame audit reports a misspelt role as an error and exits with a finding", async () => {
  const misspelt = MEASURED.replace('declare ? "frame" : null', '"frmae"');
  const { status, report } = await audited({}, misspelt);
  assert.equal(status, 1);
  assert.ok(report.errors.some((error) => error.message.includes('"frmae"')));
});
