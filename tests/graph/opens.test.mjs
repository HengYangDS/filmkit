/* The Node half of the recorder of what a run opens (src/filmkit/graph/opens.cjs): loaded as the
 * engine loads it (`filmkit.graph.opens.node_options`), in a child Node with `--permission-audit`,
 * its allowances and the recorder by `--require`, with FILMKIT_OPENS naming the log; and loaded in
 * this process, where the channel's messages are published by hand. The second is the one Node's
 * coverage sees: a child under the permission model writes no coverage of its own. */
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import diagnostics from "node:diagnostics_channel";
import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  realpathSync,
  writeFileSync,
} from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const RECORDER = fileURLToPath(new URL("../../src/filmkit/graph/opens.cjs", import.meta.url));

/** A child Node, in a fresh folder, that reads one allowed file and one outside its allowances and
 * writes one outside them; its run and the log's entries. The folder is named by its real path,
 * since macOS lists the temporary folder under /private. */
function child(variables) {
  const folder = realpathSync(mkdtempSync(path.join(tmpdir(), "filmkit-opens-")));
  const files = {
    log: path.join(folder, "opens.jsonl"),
    inside: path.join(folder, "allowed", "in.txt"),
    outside: path.join(folder, "outside.txt"),
    written: path.join(folder, "written.txt"),
  };
  mkdirSync(path.dirname(files.inside));
  writeFileSync(files.inside, "inside\n");
  writeFileSync(files.outside, "outside\n");
  const code = [
    'const fs = require("node:fs");',
    `fs.readFileSync(${JSON.stringify(files.inside)});`,
    `fs.readFileSync(${JSON.stringify(files.outside)});`,
    `fs.writeFileSync(${JSON.stringify(files.written)}, "written\\n");`,
    'process.stdout.write("ran to its end\\n");',
  ].join("\n");
  const run = spawnSync(
    process.execPath,
    [
      "--permission-audit",
      `--allow-fs-read=${path.dirname(RECORDER)}`,
      `--allow-fs-read=${path.dirname(files.inside)}`,
      `--allow-fs-read=${files.log}`,
      `--allow-fs-write=${files.log}`,
      "--require",
      RECORDER,
      "-e",
      code,
    ],
    { cwd: folder, encoding: "utf8", env: { ...process.env, ...variables(files.log) } },
  );
  const entries = existsSync(files.log)
    ? readFileSync(files.log, "utf8")
        .split("\n")
        .filter(Boolean)
        .map((line) => JSON.parse(line))
    : [];
  return { folder, run, entries, ...files };
}

test("a read and a write outside the allowances are one entry each, and the child runs on", () => {
  const { folder, run, entries, inside, outside, written, log } = child((named) => ({
    FILMKIT_OPENS: named,
    FILMKIT_NODE: "stand:zh",
  }));
  assert.equal(run.status, 0, run.stderr);
  assert.equal(run.stdout, "ran to its end\n");
  const at = (file) => entries.filter((entry) => entry.path === file);
  const [read, ...more] = at(outside);
  assert.deepEqual(more, [], "one entry for one read");
  assert.equal(typeof read.pid, "number");
  assert.notEqual(read.pid, process.pid, "the entry is the child's");
  assert.deepEqual(
    { ...read, pid: 0 },
    { node: "stand:zh", process: "node", pid: 0, kind: "read", path: outside, cwd: folder },
  );
  assert.deepEqual(
    at(written).map((entry) => entry.kind),
    ["write"],
  );
  assert.deepEqual(at(inside), [], "a read within the allowances publishes nothing");
  assert.deepEqual(at(log), [], "the log's own appends publish nothing");
});

test("without FILMKIT_OPENS the recorder writes no log, and the child runs the same", () => {
  const { run, entries, log } = child(() => ({ FILMKIT_OPENS: "" }));
  assert.equal(run.status, 0, run.stderr);
  assert.equal(run.stdout, "ran to its end\n");
  assert.deepEqual(entries, []);
  assert.equal(existsSync(log), false);
});

test("in this process, each read and write the channel publishes is one entry, and other permissions none", () => {
  const folder = realpathSync(mkdtempSync(path.join(tmpdir(), "filmkit-opens-")));
  const log = path.join(folder, "opens.jsonl");
  process.env.FILMKIT_OPENS = log;
  process.env.FILMKIT_NODE = "stand:en";
  createRequire(import.meta.url)(RECORDER);
  const channel = diagnostics.channel("node:permission-model:fs");
  channel.publish({ permission: "FileSystemRead", resource: path.join(folder, "a.txt") });
  channel.publish({ permission: "FileSystemWrite", resource: path.join(folder, "b.txt") });
  channel.publish({ permission: "ChildProcess", resource: "ls" });
  const entries = readFileSync(log, "utf8")
    .split("\n")
    .filter(Boolean)
    .map((line) => JSON.parse(line));
  const where = { node: "stand:en", process: "node", pid: process.pid, cwd: process.cwd() };
  assert.deepEqual(entries, [
    { ...where, kind: "read", path: path.join(folder, "a.txt") },
    { ...where, kind: "write", path: path.join(folder, "b.txt") },
  ]);
});
