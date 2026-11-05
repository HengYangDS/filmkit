/** Exercise the frame audit on a stretch of the sample film: its report, its label and text traces, its marks and its
 * bounds. */
import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { TEXT_LAYOUT } from "../../src/filmkit/picture/frame-audit/typography/index.mjs";
import { authoredTimeline, scratchFolder } from "./sample-film.mjs";

// The headless audits run the composition itself on a timeline; a short stretch exercises every measurement.
const AUDIT_FRAMES = fileURLToPath(
  new URL("../../src/filmkit/picture/frame-audit.mjs", import.meta.url),
);

test("the frame audit reports a stretch of the film, its traces, its marks and its bounds", async () => {
  const film = await authoredTimeline("zh"),
    folder = await scratchFolder();
  const path = join(folder, "timeline.json"),
    trace = join(folder, "trace.tsv"),
    texts = join(folder, "texts.tsv"),
    marks = join(folder, "marks.tsv"),
    bounds = join(folder, "bounds.json"),
    balance = join(folder, "balance.json");
  await writeFile(path, JSON.stringify(film));
  const at = film.segments[1].voice_start;
  const report = JSON.parse(
    execFileSync(
      process.execPath,
      [AUDIT_FRAMES, path, "0.5", "--from", String(at), "--to", String(at + 6)],
      {
        env: {
          ...process.env,
          TRACE: trace,
          TEXTS: texts,
          MARKS: marks,
          BOUNDS: bounds,
          BALANCE: balance,
        },
        encoding: "utf8",
      },
    ),
  );
  assert.deepEqual(report.errors, []);
  assert.ok(report.frames_checked > 0);
  // Thoughts whose picture stands off the content centre at a reviewers' instant, with the instant and both offsets.
  assert.ok(report.off_centre && typeof report.off_centre === "object");
  for (const rows of Object.values(report.off_centre))
    assert.ok(rows.every((row) => /^\d\d\.\d+ (two|late) -?\d+%\/-?\d+%$/.test(row)));
  // Containers that stood under half filled through more than a second of speech, with their kind, box, run and fill.
  assert.ok(report.underfilled_containers && typeof report.underfilled_containers === "object");
  for (const runs of Object.values(report.underfilled_containers))
    assert.ok(runs.every((run) => /^(frame|bracket) [\d,-]+ [\d.]+-[\d.]+ \d+%$/.test(run)));
  // Thoughts whose lit picture covers too little of the band, and names that run past two lines; the captions that
  // labels repeat are the sync audit's to measure.
  assert.equal(report.caption_echoes, undefined);
  for (const key of [
    "thin_lit",
    "long_names",
    "sparse_runs",
    "off_centre_runs",
    "off_centre_builds",
    "off_centre_settled",
    "thin_runs",
  ])
    assert.ok(report[key] && typeof report[key] === "object", key);
  // The reviewers' balance runs, with their span and largest offset in px.
  for (const key of ["off_centre_builds", "off_centre_settled"])
    for (const runs of Object.values(report[key]))
      assert.ok(
        runs.every((run) => /^[\d.]+-[\d.]+ -?[\d.]+ px$/.test(run)),
        key,
      );
  // Runs of speech whose visible marks cover too little of the band, and runs whose lit picture stands off the content
  // centre or covers too little of it, with their span and worst share.
  for (const key of ["sparse_runs", "off_centre_runs", "thin_runs"])
    for (const runs of Object.values(report[key]))
      assert.ok(
        runs.every((run) => /^[\d.]+-[\d.]+ [\d.]+%$/.test(run)),
        key,
      );
  for (const rows of Object.values(report.thin_lit))
    assert.ok(rows.every((row) => /^\d\d\.\d+ (two|late) [\d.]+%$/.test(row)));
  for (const rows of Object.values(report.long_names))
    assert.ok(rows.every((row) => /@[\d.]+$/.test(row)));
  // How the text lines up, per scene: the stretch's names stand on their rows, columns and cards.
  for (const key of TEXT_LAYOUT) assert.deepEqual(report[key], {}, key);
  // Each thought instant in the stretch with its lit offsets and its share of the band.
  const instants = JSON.parse(await readFile(balance, "utf8"));
  assert.ok(
    instants.length > 0 &&
      instants.every(
        (v) => /^\d\d\.\d+$/.test(v.thought) && ["two", "late"].includes(v.at) && v.cover >= 0,
      ),
  );
  const rows = (await readFile(trace, "utf8"))
    .trim()
    .split("\n")
    .map((line) => line.split("\t"));
  assert.ok(
    rows.length > 0 && rows.every((row) => row.length === 5 && Number.isFinite(Number(row[2]))),
  );
  // Every text of every frame, whatever its role: its time, scene, role, contrast, opacity and whole text. The
  // captions are traced with the scene's names, and every label of the label trace is among them.
  const written = (await readFile(texts, "utf8"))
    .trim()
    .split("\n")
    .map((line) => line.split("\t"));
  assert.ok(
    written.every(
      (row) =>
        row.length === 6 &&
        [row[0], row[3], row[4]].every((v) => Number.isFinite(Number(v))) &&
        row[5].length > 0,
    ),
  );
  assert.ok(written.some((row) => row[2] === "caption" && row[1] === ""));
  const traced = new Set(written.map((row) => `${row[0]}\t${row[1]}\t${row[5]}`));
  assert.ok(rows.every((row) => traced.has(`${row[0]}\t${row[1]}\t${row[4]}`)));
  // Each firm mark of a voiced frame: its time, scene, box and whether a legible name stands at it.
  const marked = (await readFile(marks, "utf8"))
    .trim()
    .split("\n")
    .map((line) => line.split("\t"));
  assert.ok(
    marked.length > 0 &&
      marked.every(
        (row) =>
          row.length === 7 &&
          row.slice(2, 6).every((v) => Number.isInteger(Number(v))) &&
          ["0", "1"].includes(row[6]),
      ),
  );
  assert.ok(marked.some((row) => row[6] === "1"));
  // Each speaking scene's painted extent, within what the scene ever drew, and its mean share of the frame.
  const extents = JSON.parse(await readFile(bounds, "utf8"));
  assert.ok(Object.keys(extents).includes(film.segments[1].id));
  for (const { box, drawn, mean_frame_area } of Object.values(extents)) {
    assert.ok(box.every(Number.isInteger) && box[0] < box[2] && box[1] < box[3]);
    assert.ok(drawn[0] <= box[0] && drawn[1] <= box[1] && drawn[2] >= box[2] && drawn[3] >= box[3]);
    assert.ok(mean_frame_area > 0 && mean_frame_area <= 1);
  }
});

test("the frame audit finds the sample film's closing checklist on one left edge in both editions", async () => {
  const folder = await scratchFolder();
  for (const code of ["zh", "en"]) {
    const film = await authoredTimeline(code),
      path = join(folder, `timeline-${code}.json`),
      closing = film.segments.at(-1);
    await writeFile(path, JSON.stringify(film));
    const report = JSON.parse(
      execFileSync(
        process.execPath,
        [AUDIT_FRAMES, path, "0.0333333", "--from", String(closing.voice_start)],
        { encoding: "utf8" },
      ),
    );
    assert.deepEqual(report.errors, [], code);
    for (const key of TEXT_LAYOUT) assert.deepEqual(report[key], {}, `${code} ${key}`);
  }
});

/* A composition of one scene: two names of one row, the second 6 px low for its first 3 s. */
const RAGGED_ROW = `"use strict";
const ctx = document.getElementById("picture").getContext("2d");
const P = { ground: "#0F1519", panel: "#1E2932", line: "#63758B", ink: "#ECE8DF", muted: "#9BA8B1" };
let texts = [];
function name(value, x, y) {
  ctx.globalAlpha = 1;
  ctx.fillStyle = P.ink;
  ctx.font = "30px Sample";
  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";
  ctx.fillText(value, x, y);
  const width = ctx.measureText(value).width;
  texts.push({ text: value, bounds: [x - width / 2, y - 24, x + width / 2, y + 7], color: P.ink, alpha: 1,
    role: "label", scene: "01", placed: true, size: 30 });
}
window.renderFrame = (t) => {
  texts = [];
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = P.ground;
  ctx.fillRect(0, 0, 1920, 1080);
  window.__sceneId = "01";
  name("Sources", 760, 500);
  name("Films", 1160, t < 3 ? 506 : 500);
  window.__sceneId = null;
  window.__filmLayout = { time: t, texts };
};
`;

test("the frame audit reports a ragged row with its scene, span, texts and baselines", async () => {
  const root = await scratchFolder(),
    path = join(root, "timeline.json");
  await mkdir(join(root, "picture"));
  await writeFile(join(root, "picture/film.js"), RAGGED_ROW);
  const words = ["Sources", "and", "films"].map((text, i) => ({
    text,
    start: 0.45 + i,
    end: 1.35 + i,
  }));
  const segment = {
    id: "01",
    chapter: "sample",
    start: 0,
    end: 6,
    voice_start: 0.45,
    voice_end: 5.5,
    utterance_groups: ["Sources and films"],
    words,
  };
  await writeFile(
    path,
    JSON.stringify({ language: "English", duration: 6, segments: [segment], captions: [] }),
  );
  const report = JSON.parse(
    execFileSync(process.execPath, [AUDIT_FRAMES, path, "0.0333333"], {
      cwd: root,
      encoding: "utf8",
    }),
  );
  assert.deepEqual(report.errors, []);
  assert.deepEqual(Object.keys(report.ragged_rows), ["01"]);
  const [row] = report.ragged_rows["01"];
  assert.deepEqual(row.texts, ["Sources", "Films"]);
  assert.deepEqual(row.baselines, [500, 506]);
  // The run spans the voiced frames sampled while the name stands low, each within one step.
  assert.ok(
    Math.abs(row.start - 0.45) <= 0.04 && Math.abs(row.end - 3) <= 0.04,
    `${row.start}-${row.end}`,
  );
  for (const key of TEXT_LAYOUT.filter((v) => v !== "ragged_rows"))
    assert.deepEqual(report[key], {}, key);
});

/* A composition whose one name stands left-aligned at x 900, so its box is centred by its width: measured by a
 * declared face of 0.5 em a character, "Sources and films" is 255 px wide and stands 67.5 px right of centre; before
 * 2 s it stands 300 px further left. */
const OFF_CENTRE = `"use strict";
const ctx = document.getElementById("picture").getContext("2d");
const P = { ground: "#0F1519", panel: "#1E2932", line: "#63758B", ink: "#ECE8DF", muted: "#9BA8B1" };
let texts = [];
window.renderFrame = (t) => {
  texts = [];
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = P.ground;
  ctx.fillRect(0, 0, 1920, 1080);
  window.__sceneId = "01";
  const value = "Sources and films", x = t < 2 ? 600 : 900;
  ctx.globalAlpha = 1;
  ctx.fillStyle = P.ink;
  ctx.font = "30px Sample";
  ctx.textAlign = "left";
  ctx.textBaseline = "alphabetic";
  ctx.fillText(value, x, 500);
  const width = ctx.measureText(value).width;
  texts.push({ text: value, bounds: [x, 476, x + width, 507], color: P.ink, alpha: 1, role: "label", scene: "01",
    placed: true, size: 30 });
  window.__sceneId = null;
  window.__filmLayout = { time: t, texts };
};
`;

test("the frame audit measures balance as the reviewers do, with the widths of the declared faces", async () => {
  const root = await scratchFolder(),
    path = join(root, "timeline.json"),
    metrics = join(root, "text-metrics.json");
  await mkdir(join(root, "picture"));
  await writeFile(join(root, "picture/film.js"), OFF_CENTRE);
  const words = ["Sources", "and", "films"].map((text, i) => ({
    text,
    start: 0.5 + 1.5 * i,
    end: 1.5 + 1.5 * i,
  }));
  const segment = {
    id: "01",
    chapter: "sample",
    start: 0,
    end: 6,
    voice_start: 0.5,
    voice_end: 5.5,
    utterance_groups: ["Sources and films"],
    words,
  };
  await writeFile(
    path,
    JSON.stringify({ language: "English", duration: 6, segments: [segment], captions: [] }),
  );
  await writeFile(
    metrics,
    JSON.stringify({
      faces: { Sample: { default: 0.5, advances: {}, mapped: "Sacdefilmnorsu " } },
    }),
  );
  const audit = (env) =>
    JSON.parse(
      execFileSync(process.execPath, [AUDIT_FRAMES, path, "0.1"], {
        cwd: root,
        env: { ...process.env, ...env },
        encoding: "utf8",
      }),
    );
  const report = audit({ FILMKIT_TEXT_METRICS: metrics });
  assert.deepEqual(report.errors, []);
  // 232.5 px left for the first 2 s is a build-up, and settled; still at 67.5 px right from 2 s on is settled.
  assert.deepEqual(report.off_centre_builds, { "01": ["0.00-2.00 -232.5 px"] });
  assert.deepEqual(report.off_centre_settled, {
    "01": ["0.00-2.00 -232.5 px", "2.00-6.10 67.5 px"],
  });
  // Without the table the estimate measures the name 24 px wider, and its box stands 12 px further right.
  const estimated = audit({ FILMKIT_TEXT_METRICS: "" });
  assert.deepEqual(estimated.off_centre_settled, {
    "01": ["0.00-2.00 -220.5 px", "2.00-6.10 79.5 px"],
  });
});
