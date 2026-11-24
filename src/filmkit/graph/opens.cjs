// The Node half of the recorder of what a run opens (`filmkit.graph.opens`). Loaded by `--require`
// into a Node process started with `--permission-audit`, it appends each file access that the
// permission model publishes, which is every one outside the process's allowances, to the file that
// FILMKIT_OPENS names, and refuses none. The log itself is among the allowances, so its own appends
// publish nothing.
"use strict";

const { appendFileSync } = require("node:fs");
const diagnostics = require("node:diagnostics_channel");

// Where Node publishes each access that its permission model would have refused.
const CHANNEL = "node:permission-model:fs";
// What each permission's name says of the access.
const KINDS = { FileSystemRead: "read", FileSystemWrite: "write" };

const log = process.env.FILMKIT_OPENS;
if (log) {
  diagnostics.subscribe(CHANNEL, ({ permission, resource }) => {
    const kind = KINDS[permission];
    if (!kind) return;
    const access = {
      node: process.env.FILMKIT_NODE ?? "",
      process: "node",
      pid: process.pid,
      kind,
      path: String(resource),
      cwd: process.cwd(),
    };
    appendFileSync(log, JSON.stringify(access) + "\n");
  });
}
