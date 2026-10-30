/** Exercise where the headless audits read the composition: below the film, the folder the tools run in. */
import test from "node:test";
import assert from "node:assert/strict";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { openComposition } from "../../src/filmkit/picture/headless-composition.mjs";

test("the composition is the picture/film.js of the film the tool runs in", async () => {
  const film = await mkdtemp(join(tmpdir(), "film-root-")),
    before = process.cwd();
  try {
    await mkdir(join(film, "picture"));
    await writeFile(
      join(film, "picture/film.js"),
      'var P = { ground: "#0F1519", ink: "#ECE8DF" };\n' +
        "window.renderFrame = (t) => { window.__filmLayout = { time: t, texts: [] }; };\n",
    );
    process.chdir(film);
    const composition = openComposition({});
    assert.deepEqual(composition.palette, { ground: "#0F1519", ink: "#ECE8DF" });
    const layout = composition.render(2);
    assert.equal(layout.time, 2);
    assert.equal(layout.texts.length, 0);
  } finally {
    process.chdir(before);
    await rm(film, { recursive: true, force: true });
  }
});
