/** Exercise the name rules: whole and placed names, at most two text sizes, lists that leave
 * whole, and labels held faint. */
import test from "node:test";
import assert from "node:assert/strict";

import { faintLabels, listTracker } from "../../../src/filmkit/picture/rules/names.mjs";
import { palette, contrast, kinds, names, word } from "./fixtures.mjs";

test("names are read whole and at most twelve are legible at once", () => {
  const many = Array.from({ length: 13 }, (_, i) => word(`名${i}`));
  assert.deepEqual(kinds(names(many, contrast)), ["name_load"]);
  assert.deepEqual(kinds(names(many.slice(0, 12), contrast)), []);
  // The lines of a wrapped name share one whole and count once; a name below 3:1 is not read.
  const wrapped = [
    ...many.slice(0, 11),
    word("第一行", { whole: "第一行 第二行" }),
    word("第二行", { whole: "第一行 第二行" }),
  ];
  assert.deepEqual(kinds(names(wrapped, contrast)), []);
  assert.deepEqual(kinds(names([...many.slice(0, 12), word("淡", { alpha: 0.2 })], contrast)), []);
});

test("every legible name is placed by a layout primitive", () => {
  assert.deepEqual(kinds(names([word("手放", { placed: false })], contrast)), ["unplaced_label"]);
  assert.deepEqual(kinds(names([word("手放", { placed: false, alpha: 0.2 })], contrast)), []);
});

test("names use at most two text sizes and never join items with a dot", () => {
  assert.deepEqual(
    kinds(names([word("甲"), word("乙", { size: 28 }), word("丙", { size: 34 })], contrast)),
    ["type_sizes"],
  );
  assert.deepEqual(kinds(names([word("甲"), word("乙", { size: 28 })], contrast)), []);
  assert.deepEqual(kinds(names([word("来源 · 时间")], contrast)), ["dot_join"]);
});

test("a list leaves whole, every name at its set's level", () => {
  const dimmed = listTracker();
  dimmed.see([word("甲", { set: "a", alpha: 0.58 }), word("乙", { set: "a" })], 10, contrast);
  assert.deepEqual(kinds(dimmed.findings()), ["list_leaving_dimmed"]);
  const whole = listTracker();
  whole.see([word("甲", { set: "a", alpha: 0.58 }), word("乙", { set: "a" })], 10, contrast);
  whole.see([word("甲", { set: "a" }), word("乙", { set: "a" })], 10.2, contrast);
  assert.deepEqual(kinds(whole.findings()), []);
  // A refused name is muted by design, so it is held to its own colour, not to the set's ink.
  const refused = listTracker();
  refused.see(
    [word("甲", { set: "a" }), word("拒", { set: "a", color: palette.muted, alpha: 0.7 })],
    10,
    contrast,
  );
  assert.deepEqual(kinds(refused.findings()), []);
});

test("a list leaves as a whole", () => {
  const early = listTracker();
  early.see([word("甲", { set: "a" }), word("乙", { set: "a" })], 10, contrast);
  early.see([word("乙", { set: "a" })], 11, contrast);
  assert.deepEqual(kinds(early.findings()), ["list_leaving_early"]);
  const whole = listTracker();
  whole.see([word("甲", { set: "a" }), word("乙", { set: "a" })], 10, contrast);
  whole.see([word("乙", { set: "a" })], 10.5, contrast);
  assert.deepEqual(kinds(whole.findings()), []);
});

test("the second list level stays legible in every name colour", () => {
  // Ink, muted, accent and done at the second level (0.58).
  for (const color of [palette.ink, palette.muted, palette.accent, palette.done])
    assert.ok(contrast(color, 0.58) >= 3, color);
});

test("a label held faint for more than a second is reported when it leaves the faint band", () => {
  const see = faintLabels(),
    faint = word("淡", { alpha: 0.3 });
  assert.ok(contrast(faint.color, faint.alpha) >= 1.8 && contrast(faint.color, faint.alpha) < 3);
  assert.deepEqual(see([faint], 10, contrast), []);
  assert.deepEqual(see([faint], 11, contrast), []);
  assert.deepEqual(see([], 11.2, contrast), [{ scene: "02", text: "淡", start: 10, end: 11.2 }]);
  // A faint stretch of one second or less is a fade, not clutter.
  assert.deepEqual(see([faint], 20, contrast), []);
  assert.deepEqual(see([word("淡")], 21, contrast), []);
});
