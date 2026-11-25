/** Exercise how an engine tool ends where it cannot finish: the module `filmkit.tools.run` loads before every tool
 * (`--import` in `NODE_OPTIONS`), which ends a tool with status 2 for an error that nothing catches, a top-level await
 * that rejects, a rejection that nothing handles and a module that throws as it loads, and leaves a finding's 1 and a
 * pass's 0. */
import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { UNFINISHED, unfinished } from "../src/filmkit/unfinished.mjs";

const MODULE = new URL("../src/filmkit/unfinished.mjs", import.meta.url).href;

/* Run a tool's body as `filmkit.tools.run` runs a tool: its status and what it wrote on standard error. */
async function ended(body, beside = {}) {
  const folder = await mkdtemp(join(tmpdir(), "filmkit-unfinished-"));
  for (const [name, text] of Object.entries(beside)) await writeFile(join(folder, name), text);
  await writeFile(join(folder, "tool.mjs"), body);
  const done = spawnSync(process.execPath, ["--import", MODULE, join(folder, "tool.mjs")], {
    encoding: "utf8",
  });
  await rm(folder, { recursive: true });
  return { status: done.status, said: done.stderr };
}

test("a tool that cannot finish ends with status 2, naming its error", async () => {
  const cases = {
    "an uncaught error": 'throw new Error("crashed");',
    "a top-level await that rejects": 'await Promise.reject(new Error("crashed"));',
    "a rejection that nothing handles":
      'Promise.reject(new Error("crashed")); setTimeout(() => {}, 50);',
  };
  for (const [kind, body] of Object.entries(cases)) {
    const { status, said } = await ended(body);
    assert.equal(status, UNFINISHED, kind);
    assert.match(said, /Error: crashed/, kind);
  }
  const loading = await ended('import "./broken.mjs";', {
    "broken.mjs": 'throw new Error("crashed as it loads");',
  });
  assert.equal(loading.status, UNFINISHED);
  assert.match(loading.said, /crashed as it loads/);
});

test("a finding and a pass keep their own status", async () => {
  assert.equal((await ended("process.exitCode = 1;")).status, 1);
  assert.equal((await ended("console.log('pass');")).status, 0);
});

test("the module ends the process that loads it on an error nothing catches", () => {
  assert.ok(process.listeners("uncaughtException").includes(unfinished));
});
