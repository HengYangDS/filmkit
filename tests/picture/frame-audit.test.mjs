/** Exercise the frame audit on a stretch of the sample film: its report, its label trace, its marks and its bounds. */
import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { authoredTimeline, scratchFolder } from "./sample-film.mjs";

// The headless audits run the composition itself on a timeline; a short stretch exercises every measurement.
const AUDIT_FRAMES = fileURLToPath(
  new URL("../../src/filmkit/picture/frame-audit.mjs", import.meta.url),
);

test("the frame audit reports a stretch of the film, its label trace, its marks and its bounds", async () => {
  const film = await authoredTimeline("zh"),
    folder = await scratchFolder();
  const path = join(folder, "timeline.json"),
    trace = join(folder, "trace.tsv"),
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
        env: { ...process.env, TRACE: trace, MARKS: marks, BOUNDS: bounds, BALANCE: balance },
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
  // Thoughts whose lit picture covers too little of the band, and names that repeat their caption or run past two lines.
  for (const key of ["thin_lit", "caption_echoes", "long_names", "sparse_runs"])
    assert.ok(report[key] && typeof report[key] === "object", key);
  // Runs of speech whose visible marks cover too little of the band, with their span and least cover.
  for (const runs of Object.values(report.sparse_runs))
    assert.ok(runs.every((run) => /^[\d.]+-[\d.]+ [\d.]+%$/.test(run)));
  for (const rows of Object.values(report.thin_lit))
    assert.ok(rows.every((row) => /^\d\d\.\d+ (two|late) [\d.]+%$/.test(row)));
  for (const rows of [...Object.values(report.caption_echoes), ...Object.values(report.long_names)])
    assert.ok(rows.every((row) => /@[\d.]+$/.test(row)));
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
