/** Draw each whole turn the frame audit found on a scratch canvas in the renderer's browser, and report whether it
 * paints. The frame audit (frame-audit.mjs, TURNS) lists every stroked clockwise arc through a whole turn from a start
 * that is not a whole number of turns, with its exact start and end angles. Chrome Headless Shell 152 computes such an
 * arc's end angle in single precision and paints some of them without ink, which only that browser tells. Each
 * distinct start and end is drawn once, alone in a cell of a scratch canvas, at a radius of 24 px and a line width of
 * 3 px, the radius being free, and its ink is measured against a circle from 0 drawn on the same canvas: a turn paints
 * when it holds PAINTED of that ink. filmkit.picture.gates refuses each line whose turn paints no ink from one of its
 * starts and records the others.
 * Usage: python -m filmkit.tools whole-turns <turns.json> */
import { readFile } from "node:fs/promises";
import { parseArgs } from "node:util";

import { launchBrowser } from "./headless-browser.mjs";

const USAGE = "Usage: python -m filmkit.tools whole-turns <turns.json>";
/* A turn paints when it holds this share of a circle's ink: those that failed in the measurements held none of it,
 * and the others all of it. */
export const PAINTED = 0.6;

/** Each distinct start and end of the frame audit's draws, in the order they were first drawn. */
export function distinctTurns(draws) {
  const seen = new Map();
  for (const { start, end } of draws)
    if (!seen.has(`${start}|${end}`)) seen.set(`${start}|${end}`, [start, end]);
  return [...seen.values()];
}

/** In the page: draw each turn alone in a 64 px cell of a scratch canvas of 32 by 32 cells, clockwise from its start to
 * its end, and return the share it holds of the ink of a circle from 0 in the canvas's first cell. The canvas is read
 * back once for every 1023 turns. */
export function turnsDrawn(turns) {
  const CELL = 64,
    SIDE = 32,
    canvas = document.createElement("canvas"),
    ctx = canvas.getContext("2d");
  canvas.width = canvas.height = CELL * SIDE;
  const at = (k) => [(k % SIDE) * CELL + CELL / 2, Math.floor(k / SIDE) * CELL + CELL / 2];
  const stroke = ([x, y], a0, a1) => {
    ctx.beginPath();
    ctx.arc(x, y, 24, a0, a1);
    ctx.stroke();
  };
  const ink = (data, k) => {
    const [x, y] = at(k);
    let sum = 0;
    for (let row = y - CELL / 2; row < y + CELL / 2; row++)
      for (let column = x - CELL / 2; column < x + CELL / 2; column++)
        sum += data[(row * canvas.width + column) * 4 + 3];
    return sum;
  };
  const shares = [];
  for (let first = 0; first < turns.length; first += SIDE * SIDE - 1) {
    const batch = turns.slice(first, first + SIDE * SIDE - 1);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.lineWidth = 3;
    ctx.strokeStyle = "#000";
    stroke(at(0), 0, 2 * Math.PI);
    batch.forEach(([a0, a1], k) => stroke(at(k + 1), a0, a1));
    const { data } = ctx.getImageData(0, 0, canvas.width, canvas.height),
      full = ink(data, 0);
    batch.forEach((_, k) => shares.push(ink(data, k + 1) / full));
  }
  return shares;
}

/** Draw each start and end, [start, end], once in the browser `launch` starts, and return the browser's version, the
 * share that paints and, for each turn, the share of a circle's ink it holds and whether it paints. A picture without
 * such a turn starts no browser. */
export async function paintedTurns(turns, launch = launchBrowser) {
  if (!turns.length) return { browser: null, painted: PAINTED, turns: [] };
  const browser = await launch({
    defaultViewport: { width: 64, height: 64, deviceScaleFactor: 1 },
  });
  try {
    const page = await browser.newPage(),
      shares = await page.evaluate(turnsDrawn, turns);
    return {
      browser: await browser.version(),
      painted: PAINTED,
      turns: turns.map(([start, end], k) => ({
        start,
        end,
        share: +shares[k].toFixed(3),
        paints: shares[k] >= PAINTED,
      })),
    };
  } finally {
    await browser.close();
  }
}

if (import.meta.main) {
  let positionals = [];
  try {
    ({ positionals } = parseArgs({ allowPositionals: true }));
  } catch (error) {
    console.error(error.message);
  }
  if (positionals.length !== 1) {
    console.error(USAGE);
    process.exitCode = 2;
  } else {
    const { draws } = JSON.parse(await readFile(positionals[0], "utf8"));
    console.log(JSON.stringify(await paintedTurns(distinctTurns(draws))));
  }
}
