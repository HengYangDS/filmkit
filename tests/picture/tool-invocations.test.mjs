/** Exercise the invocations the picture tools document and refuse. */
import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { authoredTimeline, scratchFolder } from "./sample-film.mjs";

const AUDIT_FRAMES = fileURLToPath(
  new URL("../../src/filmkit/picture/frame-audit.mjs", import.meta.url),
);
const AUDIT_MOTION = fileURLToPath(
  new URL("../../src/filmkit/picture/motion-audit.mjs", import.meta.url),
);
// A malformed invocation must stop with exit code 2 and the usage, never print a report of no frames.
const GEOMETRY = fileURLToPath(
  new URL("../../src/filmkit/picture/geometry-check.mjs", import.meta.url),
);
const invoke = (tool, args) => spawnSync(process.execPath, [tool, ...args], { encoding: "utf8" });
function assertRefused(tool, args, usage) {
  const result = invoke(tool, args);
  assert.equal(result.status, 2, `${args.join(" ")}: ${result.stderr}`);
  assert.equal(result.stdout, "", args.join(" "));
  assert.ok(result.stderr.includes(usage), args.join(" "));
}

test("the headless audits take their documented invocations, a step omitted before its flags included", async () => {
  const folder = await scratchFolder(),
    path = join(folder, "timeline.json");
  await writeFile(path, JSON.stringify(await authoredTimeline("zh")));
  const frames = JSON.parse(
    execFileSync(process.execPath, [AUDIT_FRAMES, path, "--from", "10", "--to", "12"], {
      encoding: "utf8",
    }),
  );
  assert.equal(frames.frames_checked, 8);
  const probe = JSON.parse(
    execFileSync(process.execPath, [AUDIT_FRAMES, path, "--at", "11"], { encoding: "utf8" }),
  );
  assert.ok(probe.texts.length > 0 && Array.isArray(probe.strokes));
  const motion = JSON.parse(
    execFileSync(process.execPath, [AUDIT_MOTION, path, "--from", "10", "--to", "11"], {
      encoding: "utf8",
    }),
  );
  assert.deepEqual([motion.fps, motion.frames, motion.range], [30, 30, [10, 11]]);
});

test("the headless audits refuse a malformed invocation", async () => {
  const folder = await scratchFolder(),
    path = join(folder, "timeline.json");
  await writeFile(path, JSON.stringify(await authoredTimeline("zh")));
  const frames = "Usage: python -m filmkit.tools frame-audit";
  for (const args of [
    [],
    [path, "0"],
    [path, "abc"],
    [path, "0.25", "extra"],
    [path, "0.25", "--step", "1"],
    [path, "--from"],
    [path, "--from", "10", "--to", "10"],
    [path, "--from", "", "--to", "12"],
    [path, "--at", "never"],
    [path, "--at", "11", "--from", "10"],
  ])
    assertRefused(AUDIT_FRAMES, args, frames);
  const motion = "Usage: python -m filmkit.tools motion-audit";
  for (const args of [
    [],
    [path, "0"],
    [path, "fast"],
    [path, "30", "--bogus"],
    [path, "30", "--from", "5", "--to", "4"],
    [path, "30", "--from", "1.02", "--to", "1.025"],
    [path, "30", "--out"],
  ])
    assertRefused(AUDIT_MOTION, args, motion);
});

test("the geometry check refuses a malformed invocation before opening a browser", () => {
  const usage = "Usage: python -m filmkit.tools geometry-check";
  for (const args of [
    [],
    ["stage"],
    ["stage", "receipt.json", "0"],
    ["stage", "r", "1.5"],
    ["--bogus"],
  ])
    assertRefused(GEOMETRY, args, usage);
});
