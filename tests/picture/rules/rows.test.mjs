/** Exercise the row-gap rule: neighbouring names that stand on one row keep a clear gap of 1.5 em. */
import test from "node:test";
import assert from "node:assert/strict";

import { inkLevel } from "../../../src/filmkit/picture/rules/ink.mjs";
import { rowGaps } from "../../../src/filmkit/picture/rules/rows.mjs";
import { contrast, fill, palette, stroke, word } from "./fixtures.mjs";

const STEP = 1 / 30;
/* A name of a 30 px face whose ink box starts at x and is `width` wide, its top at y. */
const name = (text, x, width, extra = {}, y = 500) =>
  word(text, { bounds: [x, y, x + width, y + 28], size: 30, ...extra });
/* The findings of `frames` checked frames a thirtieth of a second apart, each showing what `at(n)` returns: its texts,
 * or its texts and its shapes. */
function watch(frames, at) {
  const rows = rowGaps(inkLevel(palette));
  for (let n = 0; n < frames; n++) {
    const shown = at(n),
      [texts, shapes] = Array.isArray(shown[0]) ? shown : [shown, []];
    rows.see(texts, shapes, 10 + n * STEP, contrast);
  }
  return rows.findings();
}
const still = (texts, shapes = []) => watch(45, () => [texts, shapes]);
/* Two names on one row, the second `gap` px after the first. */
const pair = (gap, left = {}, right = {}) => [
  name("Compliance", 400, 150, left),
  name("Technical", 550 + gap, 130, right),
];

test("names that stand closer than 1.5 em on one row are found with their gap in px and em", () => {
  const [finding, ...others] = still(pair(36));
  assert.deepEqual(others, []);
  assert.deepEqual(finding, {
    kind: "row_gap",
    scene: "02",
    text: "Compliance | Technical",
    pair: ["Compliance", "Technical"],
    gap: 36,
    em: 1.2,
    floor: 1.5,
    at: 10,
    frames: 45,
  });
  // 1.5 em of the 30 px face is 45 px: a gap of 45 px passes and one of 44 px does not.
  assert.deepEqual(still(pair(45)), []);
  assert.deepEqual(
    still(pair(44)).map((v) => [v.gap, v.em]),
    [[44, 1.47]],
  );
});

test("the gap is measured in em of the smaller face as the frame shows it", () => {
  // A UHD frame, or a camera that draws the 30 px face at 60 px: 80 px is 1.33 em there, and 90 px is 1.5 em.
  const shown = (gap) => [
    name("左边的名字", 400, 300, { shown: 60 }),
    name("右边", 700 + gap, 120, { shown: 61 }),
  ];
  assert.deepEqual(
    still(shown(80)).map((v) => [v.text, v.gap, v.em]),
    [["左边的名字 | 右边", 80, 1.33]],
  );
  assert.deepEqual(still(shown(90)), []);
});

test("only names at rest for a second are judged", () => {
  // A pair stands from the frame before the first that shows it unmoved: thirty-one frames span a second.
  assert.equal(watch(31, () => pair(36)).length, 1);
  assert.deepEqual(
    watch(30, () => pair(36)),
    [],
  );
  // A name that glides past another, 3 px a frame, is never at rest beside it.
  assert.deepEqual(
    watch(90, (n) => [name("Compliance", 400, 150), name("Technical", 560 + 3 * n, 130)]),
    [],
  );
  // A camera that drifts 1 px a second leaves the pair at rest.
  const drift = watch(90, (n) => [
    name("Compliance", 400 + n / 30, 150),
    name("Technical", 586 + n / 30, 130),
  ]);
  assert.deepEqual(
    drift.map((v) => [v.text, v.frames]),
    [["Compliance | Technical", 90]],
  );
  // Two stands of one pair are one finding, from the first stand, with the frames of both and the tightest gap.
  const twice = watch(140, (n) =>
    n < 40 ? pair(40) : n < 80 ? [name("Compliance", 400, 150)] : pair(30),
  );
  assert.deepEqual(
    twice.map((v) => [v.at, v.frames, v.gap]),
    [[10, 40 + 60, 30]],
  );
});

test("the words and lines of one name, and a name beside its qualifier, are not neighbours", () => {
  // Two runs of one line and a term with its qualifier each share the whole their name is registered with.
  const whole = { whole: "Task, target, current state" };
  assert.deepEqual(
    still([name("Task, target", 400, 170, whole), name(", current state", 590, 190, whole)]),
    [],
  );
  // A name ends where its last run ends, a closing comma painted on its own included: 44 px from the words is 36 px
  // from the comma, and the pair is named by the wholes.
  const next = { whole: "Reversible, verifiable steps" };
  const runs = [
    name("Task, target", 400, 170, whole),
    name(", current state", 570, 190, whole),
    name(",", 760, 8, whole),
    name("Reversible,", 804, 150, next),
    name(" verifiable steps", 954, 210, next),
  ];
  assert.deepEqual(
    still(runs).map((v) => [v.text, v.gap]),
    [["Task, target, current state | Reversible, verifiable steps", 36]],
  );
  // Runs a word space apart, under half an em, read as one line whatever they are registered as.
  assert.deepEqual(still(pair(12)), []);
  assert.equal(still(pair(16)).length, 1);
  // One sentence set as two runs, the first ending in a joining mark (a Chinese enumeration or clause mark, a comma
  // or a semicolon), reads on into the second whatever each is registered as: the mark says the line continues.
  assert.deepEqual(still([name("威胁到数据、生产、", 400, 230), name("下游或合规", 648, 130)]), []);
  assert.deepEqual(
    still([name("Threatens data, production,", 400, 300), name("downstream use", 736, 170)]),
    [],
  );
  // A note beside a name is set in the other text size: a lead-in or a qualifier, not a neighbouring name.
  const note = { size: 25, bounds: [400, 503, 550, 526] };
  assert.deepEqual(still(pair(30, note)), []);
});

test("names on different rows, faint names and marks that are no names are not judged", () => {
  // A quarter of an em keeps two boxes level: 7 px between their middles is one row and 8 px is not.
  const lower = (dy) => [name("Compliance", 400, 150), name("Technical", 586, 130, {}, 500 + dy)];
  assert.equal(still(lower(7)).length, 1);
  assert.deepEqual(still(lower(8)), []);
  // A name below 3:1 is not read, and a cross or a bare number is a mark.
  assert.deepEqual(still(pair(36, {}, { alpha: 0.2 })), []);
  assert.deepEqual(still([name("Compliance", 400, 150), name("×", 586, 20)]), []);
  assert.deepEqual(still(pair(36, { scene: null })), []);
  assert.deepEqual(still(pair(36, { role: "caption" }, { role: "caption" })), []);
  // Names of two scenes that cross-fade are not one row.
  assert.deepEqual(still(pair(36, { scene: "01" })), []);
});

test("a gap that holds a lit mark is not a clear gap between neighbours", () => {
  const ink = { color: palette.ink, scene: "02" };
  // A link drawn through the gap, an icon's fill standing in it, and a cross set between the names.
  const link = stroke(
    [
      [560, 514],
      [580, 514],
    ],
    ink,
  );
  assert.deepEqual(still(pair(36), [link]), []);
  assert.deepEqual(still(pair(36), [fill([560, 505, 576, 521], ink)]), []);
  assert.deepEqual(still([...pair(36), name("×", 561, 14)]), []);
  // A rail below the row, a faint link and the dark panel behind both names leave the gap clear.
  const rail = stroke(
    [
      [300, 540],
      [900, 540],
    ],
    ink,
  );
  const faint = { ...link, alpha: 0.1 };
  const panel = fill([380, 480, 740, 550], { color: palette.panel, scene: "02" });
  assert.equal(still(pair(36), [rail, faint, panel]).length, 1);
});

test("each name is judged against its nearest neighbour on the row", () => {
  // Three names in a row: the outer two are 36 + 130 + 60 px apart, and only the first gap is close.
  const found = still([...pair(36), name("Resource", 776, 120)]);
  assert.deepEqual(
    found.map((v) => v.text),
    ["Compliance | Technical"],
  );
  // Names that overlap are the overlap rule's, not a gap.
  assert.deepEqual(still(pair(-20)), []);
});
