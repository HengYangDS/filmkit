/** Exercise the frame rules and the reviewers' measures that the real-browser check and the frame audit share. */
import test from "node:test";
import assert from "node:assert/strict";

import { openComposition } from "../../src/filmkit/picture/headless-composition.mjs";
import { balanceRuns, bandCover, pictureOffset } from "../../src/filmkit/picture/rules/balance.mjs";
import { analysis } from "../../src/filmkit/picture/rules/frame.mjs";
import {
  fillShare,
  inkLevel,
  litLevel,
  readingLoad,
  strokeShare,
} from "../../src/filmkit/picture/rules/ink.mjs";
import { faintLabels, listTracker, nameRules } from "../../src/filmkit/picture/rules/names.mjs";
import { authoredTimeline } from "./sample-film.mjs";

// The rules are measured against the film's own palette, as the composition defines it.
const { palette } = openComposition(await authoredTimeline("zh"));
const inspectFrame = analysis(inkLevel(palette));
const contrast = readingLoad(palette);
const label = (text, bounds, extra = {}) => ({
  text,
  bounds,
  alpha: 1,
  role: "label",
  scene: "01",
  seq: 10,
  ...extra,
});
const stroke = (points, extra = {}) => ({
  kind: "stroke",
  seq: 1,
  alpha: 1,
  width: 2,
  subs: [points],
  ...extra,
});
const fill = (box, extra = {}) => ({ kind: "fill", seq: 1, alpha: 1, box, ...extra });
const kinds = (findings) => findings.map((finding) => finding.kind).sort();
const names = nameRules();
const word = (text, extra = {}) => ({
  text,
  bounds: [0, 0, 10, 10],
  alpha: 1,
  role: "label",
  scene: "02",
  color: "#ECE8DF",
  whole: text,
  placed: true,
  size: 38,
  set: null,
  ...extra,
});

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

test("reading contrast separates legible names from faint clutter and gone residue", () => {
  // Every name colour of the sample reads at 3:1 at .68 of its ink and is gone below 1.8:1 at .18.
  assert.ok(contrast(palette.ink, 1) > 14);
  for (const color of [palette.ink, palette.muted, palette.accent, palette.done]) {
    assert.ok(contrast(color, 0.68) >= 3, color);
    assert.ok(contrast(color, 0.18) < 1.8, color);
  }
  assert.ok(contrast(palette.ink, 0.4) >= 1.8 && contrast(palette.ink, 0.4) < 3.4);
});

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

test("ink level and reading contrast are measured over the film's ground", () => {
  const level = inkLevel(palette);
  assert.equal(level(palette.ground, 1), 0);
  assert.equal(level(palette.ink, 0.5), 110.5);
  // A style without channels, such as a gradient, lifts nothing, and reads as the film's ink.
  assert.equal(level(undefined, 1), 0);
  assert.equal(contrast(undefined, 0.6), contrast(palette.ink, 0.6));
  assert.equal(contrast(palette.ground, 1), 1);
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

test("a picture's offset from the content centre is a share of the frame, as the reviewers measure it", () => {
  // The content band runs from 120 to 900 px, so its centre stands at (960, 510).
  assert.deepEqual(pictureOffset([760, 310, 1160, 710]), [0, 0]);
  // A rail alone in the top quarter stands a fifth of the frame's height above the centre.
  const [dx, dy] = pictureOffset([400, 250, 1520, 330]);
  assert.equal(dx, 0);
  assert.ok(Math.abs(dy - -220 / 1080) < 1e-12);
  // A panel on the right half stands 440 px, 23% of the width, right of the centre.
  assert.ok(Math.abs(pictureOffset([1100, 400, 1700, 620])[0] - 440 / 1920) < 1e-12);
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

test("a picture's cover is its box's share of the content band", () => {
  // The band runs from 120 to 900 px over the full width; a box reaching past it counts only its part inside.
  assert.equal(bandCover([0, 120, 1920, 900]), 1);
  assert.ok(Math.abs(bandCover([0, 0, 960, 510]) - 0.25) < 1e-12);
});

/* Frames every thirtieth of a second from `from` to `to`, each with the speaking scene and its lit box at t. */
function sampled(runs, from, to, scene, boxAt) {
  for (let k = 0; from + k / 30 < to - 1e-9; k++) {
    const t = from + k / 30;
    runs.frame(t, scene(t), boxAt(t));
  }
  return runs.finish();
}
// A centred picture covering a fifth of the band, and the same picture standing 13% of the height above the centre.
const CENTRED = [560, 360, 1360, 660],
  HIGH = [560, 220, 1360, 520];

test("balance through speech reports a run of 2 s or more beyond the reviewers' limits", () => {
  // The picture stands 13% high for 2.5 s of one thought, then returns to the centre.
  const off = sampled(
    balanceRuns(1 / 30),
    0,
    5,
    () => "04",
    (t) => (t >= 1 && t < 3.5 ? HIGH : CENTRED),
  );
  assert.equal(off.off.length, 1);
  assert.equal(off.off[0].scene, "04");
  assert.ok(Math.abs(off.off[0].start - 1) < 1e-9 && Math.abs(off.off[0].end - 3.5) < 1e-6);
  assert.ok(Math.abs(off.off[0].worst - 140 / 1080) < 1e-12);
  assert.deepEqual(off.thin, []);
  // A label alone, a twentieth of the band, through 3 s of speech is thin, its least cover recorded.
  const label = [860, 490, 1060, 530],
    thin = sampled(
      balanceRuns(1 / 30),
      0,
      4,
      () => "05",
      (t) => (t < 3 ? label : CENTRED),
    );
  assert.equal(thin.thin.length, 1);
  assert.ok(Math.abs(thin.thin[0].worst - bandCover(label)) < 1e-12);
  assert.ok(Math.abs(thin.thin[0].end - 3) < 1e-6);
});

test("balance through speech leaves a brief excursion, a scene change and quiet alone", () => {
  // 13% off for 1.5 s is an excursion, not a run.
  const brief = sampled(
    balanceRuns(1 / 30),
    0,
    4,
    () => "04",
    (t) => (t >= 1 && t < 2.5 ? HIGH : CENTRED),
  );
  assert.deepEqual(brief, { off: [], thin: [] });
  // Two scenes each off for 1.5 s in a row are two excursions.
  const cut = sampled(
    balanceRuns(1 / 30),
    0,
    3,
    (t) => (t < 1.5 ? "04" : "05"),
    () => HIGH,
  );
  assert.deepEqual(cut.off, []);
  // Nothing lit between voices is quiet: no thin run, and the pause ends the run of speech before it.
  const quiet = sampled(
    balanceRuns(1 / 30),
    0,
    6,
    (t) => (t >= 1.5 && t < 4.5 ? null : "06"),
    (t) => (t >= 1.5 && t < 4.5 ? null : [900, 500, 1000, 520]),
  );
  assert.deepEqual(quiet, { off: [], thin: [] });
});
