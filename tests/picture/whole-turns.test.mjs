/** Exercise how the headless runtime finds a whole turn the renderer's browser may paint without ink: the stroked
 * clockwise arcs through a whole turn from a start that is not a whole number of turns, which the canvas stand-in
 * records with each stroke, and the line of film.js that drew each one. */
import test from "node:test";
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";

import {
  canvasStandIn,
  openComposition,
  wholeTurnAtRisk,
} from "../../src/filmkit/picture/headless-composition.mjs";
import { SAMPLE, scratchFolder } from "./sample-film.mjs";

test("a stroked clockwise arc through a whole turn from a start off a whole turn is recorded", () => {
  const paints = [],
    TURN = 2 * Math.PI,
    ctx = canvasStandIn(
      (paint) => paints.push(paint),
      null,
      () => "film.js:7",
    );
  const stroked = (draw) => {
    ctx.beginPath();
    draw();
    ctx.stroke();
    const { turns = [] } = paints.at(-1);
    return turns.map(({ start, sweep, origin }) => [start, +sweep.toFixed(6), origin]);
  };
  // The renderer's browser computes a clockwise arc in single precision and can paint no ink for these.
  assert.deepEqual(
    stroked(() => ctx.arc(100, 100, 24, 0.3, 0.3 + TURN)),
    [[0.3, 6.283185, "film.js:7"]],
  );
  assert.deepEqual(stroked(() => ctx.arc(100, 100, 24, 0.3, 0.3 + TURN - 1e-6)).length, 1);
  assert.deepEqual(stroked(() => ctx.arc(100, 100, 24, -20.1, -20.1 + 3 * TURN)).length, 1);
  // It paints these: a start at a whole turn, an arc anticlockwise or short of a turn, and an ellipse.
  assert.deepEqual(
    stroked(() => ctx.arc(100, 100, 24, 0, TURN)),
    [],
  );
  assert.deepEqual(
    stroked(() => ctx.arc(100, 100, 24, 2 * TURN, 3 * TURN)),
    [],
  );
  assert.deepEqual(
    stroked(() => ctx.arc(100, 100, 24, 0.3, 0.3 - TURN, true)),
    [],
  );
  assert.deepEqual(
    stroked(() => ctx.arc(100, 100, 24, 0.3, 0.3 + TURN - 1e-3)),
    [],
  );
  assert.deepEqual(
    stroked(() => ctx.ellipse(100, 100, 24, 24, 0.3, 0, TURN)),
    [],
  );
  assert.deepEqual(
    stroked(() => ctx.ellipse(100, 100, 24, 24, 0, 0.3, 0.3 + TURN)),
    [],
  );
  // A path keeps its arcs until the next begins, and a fill carries none.
  ctx.beginPath();
  ctx.arc(100, 100, 24, 0.3, 0.3 + TURN);
  ctx.fill();
  assert.equal(paints.at(-1).turns, undefined);
  ctx.stroke();
  assert.equal(paints.at(-1).turns.length, 1);
  ctx.beginPath();
  ctx.stroke();
  assert.equal(paints.at(-1).turns, undefined);
});

test("a whole turn the browser may not paint is traced to the line of film.js that drew its arc", async () => {
  const root = await scratchFolder(),
    LINES = [
      'var P = { ground: "#0F1519", ink: "#ECE8DF" };',
      "var ctx = document.getElementById('picture').getContext('2d');",
      "function ring(a) {",
      "  ctx.beginPath();",
      "  ctx.arc(960, 540, 24, a, a + 2 * Math.PI);",
      "  ctx.stroke();",
      "}",
      "window.renderFrame = (t) => {",
      '  window.__sceneId = "01";',
      "  ring(t);",
      "  window.__sceneId = null;",
      "  window.__filmLayout = { time: t, texts: [] };",
      "};",
      "",
    ];
  await mkdir(join(root, "picture"));
  await writeFile(join(root, "picture/film.js"), LINES.join("\n"));
  process.chdir(root);
  try {
    const composition = openComposition({}),
      turns = [];
    composition.render(1.25, (paint) => turns.push(...(paint.turns ?? [])));
    assert.deepEqual(turns, [
      { start: 1.25, sweep: 1.25 + 2 * Math.PI - 1.25, origin: "film.js:5" },
    ]);
  } finally {
    process.chdir(SAMPLE);
  }
});

test("a whole turn is at risk only clockwise, through a turn, from a start off a whole turn", () => {
  const TURN = 2 * Math.PI;
  assert.equal(wholeTurnAtRisk(0.3, 0.3 + TURN), true);
  assert.equal(wholeTurnAtRisk(0.3, 0.3 + TURN - 1e-5), true);
  assert.equal(wholeTurnAtRisk(0.3, 0.3 + TURN - 2e-5), false);
  assert.equal(wholeTurnAtRisk(-TURN, 0), false);
  assert.equal(wholeTurnAtRisk(TURN + 5e-7, 2 * TURN + 5e-7), false);
  assert.equal(wholeTurnAtRisk(TURN + 2e-6, 2 * TURN + 2e-6), true);
  assert.equal(wholeTurnAtRisk(0.3, 0.3 - TURN, true), false);
});
