/** Exercise how a whole turn the renderer's browser may paint without ink is found and judged: the stroked clockwise
 * arcs through a whole turn from a start that is not a whole number of turns, which the canvas stand-in records with
 * each stroke and the line of film.js that drew it, and the tool that draws each distinct start and end once in the
 * renderer's browser, here on a stand-in browser. */
import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  canvasStandIn,
  openComposition,
  wholeTurnAtRisk,
} from "../../src/filmkit/picture/headless-composition.mjs";
import {
  distinctTurns,
  paintedTurns,
  PAINTED,
  turnsDrawn,
} from "../../src/filmkit/picture/whole-turns.mjs";
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
      {
        start: 1.25,
        end: 1.25 + 2 * Math.PI,
        sweep: 1.25 + 2 * Math.PI - 1.25,
        origin: "film.js:5",
      },
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

/* Whole turns as the frame audit writes them: a ring at a fixed start drawn twice, and a start the browser fails on. */
const TURN = 2 * Math.PI,
  FAILING = 1.9335;
const draw = (scene, start, from, frames) => ({
  scene,
  origin: "film.js:9",
  module: null,
  start,
  end: start + TURN,
  from,
  to: from,
  frames,
});
const DRAWS = [draw("01", Math.PI, 1, 3), draw("02", Math.PI, 5, 2), draw("02", FAILING, 6, 1)];

/* A browser that paints each whole turn in full but the failing start's, and records what it was asked. */
function standInBrowser(asked) {
  const page = {
    evaluate: async (paint, turns) => {
      asked.push({ paint: paint.name, turns });
      return turns.map(([start]) => (start === FAILING ? 0 : 0.998));
    },
  };
  return async (options) => {
    asked.push({ options });
    return {
      newPage: async () => page,
      version: async () => "HeadlessChrome/152.0.7977.30",
      close: async () => asked.push("closed"),
    };
  };
}

test("each distinct start and end is drawn once in the renderer's browser and judged by its ink", async () => {
  assert.deepEqual(distinctTurns(DRAWS), [
    [Math.PI, Math.PI + TURN],
    [FAILING, FAILING + TURN],
  ]);
  const asked = [],
    judged = await paintedTurns(distinctTurns(DRAWS), standInBrowser(asked));
  assert.deepEqual(judged, {
    browser: "HeadlessChrome/152.0.7977.30",
    painted: PAINTED,
    turns: [
      { start: Math.PI, end: Math.PI + TURN, share: 0.998, paints: true },
      { start: FAILING, end: FAILING + TURN, share: 0, paints: false },
    ],
  });
  // One page draws every start, from one evaluation, and the browser closes.
  assert.deepEqual(asked.slice(1), [
    { paint: "turnsDrawn", turns: distinctTurns(DRAWS) },
    "closed",
  ]);
  assert.deepEqual(asked[0].options.defaultViewport, {
    width: 64,
    height: 64,
    deviceScaleFactor: 1,
  });
  // A picture without such a turn starts no browser.
  const none = await paintedTurns([], standInBrowser(asked));
  assert.deepEqual(none, { browser: null, painted: PAINTED, turns: [] });
  assert.equal(typeof turnsDrawn, "function");
});

test("a browser that cannot draw the turns still closes, and the tool refuses a malformed invocation", async () => {
  const closed = [],
    failing = async () => ({
      newPage: async () => ({ evaluate: async () => Promise.reject(Error("page crashed")) }),
      version: async () => "HeadlessChrome/152.0.7977.30",
      close: async () => closed.push(true),
    });
  await assert.rejects(paintedTurns([[FAILING, FAILING + TURN]], failing), /page crashed/);
  assert.deepEqual(closed, [true]);
  const tool = fileURLToPath(new URL("../../src/filmkit/picture/whole-turns.mjs", import.meta.url));
  for (const args of [[], ["a.json", "b.json"]]) {
    const result = spawnSync(process.execPath, [tool, ...args], { encoding: "utf8" });
    assert.equal(result.status, 2, args.join(" "));
    assert.equal(result.stdout, "");
    assert.ok(result.stderr.includes("Usage: python -m filmkit.tools whole-turns <turns.json>"));
  }
});
