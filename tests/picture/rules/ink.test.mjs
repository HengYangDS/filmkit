/** Exercise ink level, reading contrast and lit marks over the film's ground, as the reviewers'
 * frames show them. */
import test from "node:test";
import assert from "node:assert/strict";

import {
  fillShare,
  inkLevel,
  litAtFullSize,
  litLevel,
  strokeShare,
} from "../../../src/filmkit/picture/rules/ink.mjs";
import { palette, contrast } from "./fixtures.mjs";

test("reading contrast separates legible names from faint clutter and gone residue", () => {
  // Every name colour of the sample reads at 3:1 at .68 of its ink and is gone below 1.8:1 at .18.
  assert.ok(contrast(palette.ink, 1) > 14);
  for (const color of [palette.ink, palette.muted, palette.accent, palette.done]) {
    assert.ok(contrast(color, 0.68) >= 3, color);
    assert.ok(contrast(color, 0.18) < 1.8, color);
  }
  assert.ok(contrast(palette.ink, 0.4) >= 1.8 && contrast(palette.ink, 0.4) < 3.4);
});

test("ink level and reading contrast are measured over the film's ground", () => {
  const level = inkLevel(palette);
  assert.equal(level(palette.ground, 1), 0);
  assert.equal(level(palette.ink, 0.5), 110.5);
  // A style without channels, such as a gradient, lifts nothing, and reads as the film's ink.
  assert.equal(level(undefined, 1), 0);
  assert.equal(contrast(undefined, 0.6), contrast(palette.ink, 0.6));
  assert.equal(contrast(palette.ground, 1), 1);
});

test("a mark is lit as the reviewers' gray frame shows it, a thin stroke at its worst share of a cell", () => {
  const lit = litLevel({ ground: palette.ground });
  // A 2 px rail in the line colour can straddle two cells and stay below gray 48, so it never balances a picture;
  // at 3 px, or in the muted colour, it is lit wherever it falls.
  assert.equal(lit(palette.line, 1, strokeShare(2)), false);
  assert.equal(lit(palette.line, 1, strokeShare(3)), true);
  assert.equal(lit(palette.muted, 1, strokeShare(2)), true);
  // A panel fill is never lit; a 9 px dot in the accent colour is, unless it has faded.
  assert.equal(lit(palette.panel, 1, fillShare([0, 0, 400, 300])), false);
  assert.equal(lit(palette.accent, 1, fillShare([0, 0, 9, 9])), true);
  assert.equal(lit(palette.accent, 0.15, fillShare([0, 0, 9, 9])), false);
  // A style other than a colour lifts nothing.
  assert.equal(lit("rgba(255,255,255,1)", 1), false);
});

test("a mark is lit at full size when its colour over the ground is brighter than grey 60", () => {
  const lit = litAtFullSize({ ground: "#0F1519" });
  // The film's ink is lit, its grey line colour too, and the ink at a tenth of its opacity is not.
  assert.equal(lit("#ECE8DF", 1), true);
  assert.equal(lit("#63758B", 1), true);
  assert.equal(lit("#ECE8DF", 0.1), false);
  // BT.601 luma: pure green (150) is lit, pure blue (29) is not, and a style other than #rrggbb never is.
  assert.equal(lit("#00FF00", 1), true);
  assert.equal(lit("#0000FF", 1), false);
  assert.equal(lit("rgba(255,255,255,1)", 1), false);
});
