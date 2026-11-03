/** Exercise the frame rule: labels apart and inside the safe area, shapes and fills clear of
 * labels, and frames that must keep their ink. */
import test from "node:test";
import assert from "node:assert/strict";

import { listTracker } from "../../../src/filmkit/picture/rules/names.mjs";
import {
  palette,
  inspectFrame,
  contrast,
  label,
  stroke,
  fill,
  kinds,
  names,
  word,
} from "./fixtures.mjs";

test("visible labels must stay apart and inside the safe area", () => {
  assert.deepEqual(
    kinds(inspectFrame([label("A", [300, 300, 400, 330]), label("B", [390, 310, 480, 340])], [])),
    ["label_overlap"],
  );
  assert.deepEqual(
    kinds(inspectFrame([label("A", [300, 300, 400, 330]), label("B", [402, 300, 480, 330])], [])),
    [],
  );
  assert.deepEqual(kinds(inspectFrame([label("A", [30, 300, 120, 330])], [])), [
    "outside_safe_area",
  ]);
  assert.deepEqual(
    kinds(inspectFrame([label("Caption", [30, 990, 1890, 1012], { role: "caption" })], [])),
    [],
  );
  assert.deepEqual(kinds(inspectFrame([label("A", [70, 300, 160, 330])], [])), [
    "outside_safe_area",
  ]);
  assert.deepEqual(kinds(inspectFrame([label("A", [30, 300, 120, 330], { alpha: 0.3 })], [])), [
    "outside_safe_area",
  ]);
  assert.deepEqual(kinds(inspectFrame([label("A", [30, 300, 120, 330], { alpha: 0.1 })], [])), []);
  // Labels end clear of the caption band.
  assert.deepEqual(kinds(inspectFrame([label("A", [300, 900, 400, 936])], [])), [
    "outside_safe_area",
  ]);
  assert.deepEqual(kinds(inspectFrame([label("A", [300, 880, 400, 916])], [])), []);
});

test("shapes stay inside the action-safe area", () => {
  assert.deepEqual(
    kinds(
      inspectFrame(
        [],
        [
          stroke([
            [1400, 600],
            [1880, 600],
          ]),
        ],
      ),
    ),
    ["stroke_outside_action_safe"],
  );
  assert.deepEqual(kinds(inspectFrame([], [fill([1360, 580, 1880, 620])])), [
    "fill_outside_action_safe",
  ]);
  assert.deepEqual(
    kinds(
      inspectFrame(
        [],
        [
          stroke([
            [100, 60],
            [1820, 1020],
          ]),
        ],
      ),
    ),
    [],
  );
  assert.deepEqual(
    kinds(
      inspectFrame(
        [],
        [
          stroke(
            [
              [1400, 600],
              [1880, 600],
            ],
            { alpha: 0.1 },
          ),
        ],
      ),
    ),
    [],
  );
});

test("strokes may not cross a label unless an opaque card painted after them hides them", () => {
  const word = label("Word", [300, 300, 400, 330]);
  const crossing = stroke([
    [250, 315],
    [450, 315],
  ]);
  assert.deepEqual(kinds(inspectFrame([word], [crossing])), ["label_stroke_collision"]);
  assert.deepEqual(
    kinds(
      inspectFrame(
        [word],
        [
          stroke([
            [250, 360],
            [450, 360],
          ]),
        ],
      ),
    ),
    [],
  );
  const card = fill([280, 290, 420, 340], { seq: 5 });
  assert.deepEqual(kinds(inspectFrame([word], [crossing, card])), []);
  assert.deepEqual(kinds(inspectFrame([word], [{ ...card, alpha: 0.5 }, crossing])), [
    "label_stroke_collision",
  ]);
});

test("a fill may contain a label but may not cut through it", () => {
  const word = label("Word", [300, 300, 400, 330]);
  assert.deepEqual(kinds(inspectFrame([word], [fill([280, 290, 420, 340])])), []);
  assert.deepEqual(kinds(inspectFrame([word], [fill([350, 290, 500, 340])])), [
    "label_fill_collision",
  ]);
  assert.deepEqual(
    kinds(
      inspectFrame(
        [label("Caption", [300, 300, 400, 330], { role: "caption" })],
        [fill([350, 290, 500, 340])],
      ),
    ),
    [],
  );
});

test("a frame that must paint may not dim to bare ground", () => {
  const caption = label("Caption", [300, 990, 400, 1012], {
    role: "caption",
    scene: null,
    color: palette.ink,
  });
  const mark = (color, alpha, scene = "02") =>
    stroke(
      [
        [300, 300],
        [400, 300],
      ],
      { scene, alpha, color },
    );
  assert.deepEqual(kinds(inspectFrame([caption], [], { mustPaint: true, scene: "02" })), [
    "bare_ground",
  ]);
  // The brightest scene mark must rise 30 levels above the ground: ink at 20% does, ink at 10% or a dim panel does not.
  assert.deepEqual(
    kinds(inspectFrame([caption], [mark(palette.ink, 0.2)], { mustPaint: true })),
    [],
  );
  assert.deepEqual(kinds(inspectFrame([caption], [mark(palette.ink, 0.1)], { mustPaint: true })), [
    "bare_ground",
  ]);
  assert.deepEqual(
    kinds(inspectFrame([caption], [mark(palette.panel, 0.5)], { mustPaint: true })),
    ["bare_ground"],
  );
  assert.deepEqual(kinds(inspectFrame([], [mark(palette.ink, 1, null)], { mustPaint: true })), [
    "bare_ground",
  ]);
  assert.deepEqual(
    kinds(
      inspectFrame([label("Word", [300, 300, 400, 330], { alpha: 0.03, color: palette.ink })], [], {
        mustPaint: true,
      }),
    ),
    ["bare_ground"],
  );
  assert.deepEqual(kinds(inspectFrame([caption], [])), []);
  // The head band frames the picture: a chip alone in it leaves the frame bare.
  const chip = label("Illustrative", [1640, 60, 1800, 90], { scene: "02", color: palette.ink });
  assert.deepEqual(
    kinds(
      inspectFrame(
        [chip],
        [
          stroke(
            [
              [1630, 56],
              [1810, 56],
            ],
            { scene: "02", color: palette.ink },
          ),
        ],
        { mustPaint: true },
      ),
    ),
    ["bare_ground"],
  );
  assert.deepEqual(kinds(inspectFrame([chip], [mark(palette.ink, 0.5)], { mustPaint: true })), []);
  // The frame reports its brightest scene level, so a run of faint speech can be found across frames.
  assert.equal(
    inspectFrame([caption], [mark(palette.ink, 0.5)], { mustPaint: true }).brightest,
    110.5,
  );
  assert.equal(inspectFrame([caption], [], { mustPaint: true }).brightest, 0);
});

test("a chapter's first word lands on a standing first scene", () => {
  const mark = (alpha) =>
    stroke(
      [
        [300, 300],
        [400, 300],
      ],
      { scene: "02", alpha, color: palette.ink },
    );
  assert.deepEqual(kinds(inspectFrame([], [mark(0.3)], { mustPaint: true, firstWord: true })), [
    "faint_first_word",
  ]);
  assert.deepEqual(kinds(inspectFrame([], [mark(0.5)], { mustPaint: true, firstWord: true })), []);
  assert.deepEqual(kinds(inspectFrame([], [mark(0.3)], { mustPaint: true })), []);
});

test("a fill above 15% opacity that cuts through a label collides, however faint", () => {
  const word = label("Word", [300, 300, 400, 330]);
  for (const alpha of [0.3, 1])
    assert.deepEqual(kinds(inspectFrame([word], [fill([350, 290, 500, 340], { alpha })])), [
      "label_fill_collision",
    ]);
  assert.deepEqual(kinds(inspectFrame([word], [fill([350, 290, 500, 340], { alpha: 0.15 })])), []);
});

test("each finding carries the evidence a report shows", () => {
  const boxed = label("Word", [300, 300, 400, 330]);
  const [crossed] = inspectFrame(
    [boxed],
    [
      stroke([
        [250, 200],
        [250, 315],
        [450, 315],
      ]),
    ],
  );
  assert.deepEqual(crossed, {
    kind: "label_stroke_collision",
    scene: "01",
    text: "Word",
    shape: "stroke",
    bounds: [300, 300, 400, 330],
    graphic: [250, 315, 450, 315],
  });
  assert.deepEqual(
    inspectFrame([boxed, label("Next", [390, 310, 480, 340])], []).map((v) => v.pair),
    [["Word", "Next"]],
  );
  assert.deepEqual(
    inspectFrame([label("A", [30, 300, 120, 330])], [])[0].bounds,
    [30, 300, 120, 330],
  );
  const [outside] = inspectFrame([], [fill([1360, 580, 1880, 620])]);
  assert.deepEqual([outside.shape, outside.point], ["fill", [1880, 620]]);
  // Name findings count the legible names and give the sizes shown.
  const found = names([word("甲"), word("乙", { size: 28 }), word("丙", { size: 34 })], contrast);
  assert.equal(found.names, 3);
  assert.deepEqual(found.find((v) => v.kind === "type_sizes").sizes, [28, 34, 38]);
  // List findings name the set and the name, when it was last seen and a dimmed name's share of the brightest.
  const lists = listTracker();
  lists.see([word("甲", { set: "a" }), word("乙", { set: "a" })], 10, contrast);
  lists.see([word("甲", { set: "a" }), word("乙", { set: "a", alpha: 0.6 })], 11, contrast);
  lists.see([word("乙", { set: "a" })], 12, contrast);
  assert.deepEqual(
    lists.findings().map(({ kind, set, name, at, share }) => [kind, set, name, at, share]),
    [["list_leaving_early", "a", "甲", 11, undefined]],
  );
});
