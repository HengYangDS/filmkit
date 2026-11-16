/** The detail audit's rules, each on the marks it reads: ink drops, marks outside scenes, strokes in quiets, rails. */
import test from "node:test";
import assert from "node:assert/strict";

import {
  INK,
  inkDrops,
  partialLoss,
  strokePieces,
} from "../../src/filmkit/picture/detail-audit/ink.mjs";
import {
  OUTSIDE,
  outsideRuns,
  outsideTexts,
} from "../../src/filmkit/picture/detail-audit/outside.mjs";
import {
  partDrawn,
  quietsOf,
  racingTips,
  thoughtsOf,
  TIP_RACE,
} from "../../src/filmkit/picture/detail-audit/quiets.mjs";
import { RAIL, railClearances, railsOf } from "../../src/filmkit/picture/detail-audit/rails.mjs";

const DT = 1 / 60;
const stroke = (points, extra = {}) => ({ kind: "stroke", scene: "01", subs: [points], ...extra });

test("the scan follows the pieces of firm solid strokes of scenes, 8 px or longer", () => {
  const line = [
    [0, 0],
    [30, 40],
    [30, 100],
  ];
  assert.deepEqual(strokePieces(stroke(line)), [110]);
  assert.deepEqual(
    strokePieces(
      stroke(
        [
          [0, 0],
          [7, 0],
        ],
        {},
      ),
    ),
    [],
  );
  assert.deepEqual(strokePieces(stroke(line, { dash: [6, 6] })), []);
  assert.deepEqual(strokePieces(stroke(line, { alpha: INK.FIRM - 0.01 })), []);
  assert.deepEqual(strokePieces(stroke(line, { scene: null })), []);
  assert.deepEqual(strokePieces({ kind: "fill", scene: "01", subs: [line] }), []);
});

test("a call loses ink only where a piece is replaced by shorter ones", () => {
  // A piece that leaves whole, or arrives, is the motion audit's: no partial loss.
  assert.equal(partialLoss([600, 200], [600]), 0);
  assert.equal(partialLoss([600], [600, 80]), 0);
  // A line split in two with a 60 px gap, and one cut short by 45 px.
  assert.equal(partialLoss([600], [270, 270]), 60);
  assert.equal(partialLoss([600, 200], [555, 200]), 45);
  // A piece within a hundredth of its length is the same piece.
  assert.equal(partialLoss([600], [596]), 0);
});

/* The drops of a draw call "01 film.js:7" whose single line has, frame by frame, the given lengths (an array of
 * pieces for each frame), with the scene's declared stage cuts. */
function drops(frames, cuts = []) {
  const scan = inkDrops(DT);
  frames.forEach((pieces, k) =>
    scan.frame(k * DT, new Map([["01 film.js:7", pieces]]), () => new Map([["01", new Set(cuts)]])),
  );
  return scan.finish();
}

test("a line that opens within one frame is a drop, at the frame that shows the loss", () => {
  const found = drops([[600], [600], [600], [270, 270], [270, 270], [270, 270]]);
  assert.equal(found.frames, 6);
  assert.deepEqual(found.drops, [
    { t: 3 * DT, scene: "01", origin: "film.js:7", lost: 60, of: 600 },
  ]);
  assert.equal(found.at_cuts, 0);
});

test("a line that is drawn off gradually is no drop, however fast", () => {
  // 8 px a frame, the pace of a calm picture, and 40 px a frame through five frames.
  assert.deepEqual(drops(Array.from({ length: 12 }, (_, k) => [600 - 8 * k])).drops, []);
  const fast = [[600], [600], ...[1, 2, 3, 4, 5].map((k) => [600 - 40 * k]), [400], [400]];
  assert.deepEqual(drops(fast).drops, []);
});

test("a loss under 30 px, and a piece that leaves whole, are no drops", () => {
  assert.deepEqual(drops([[600], [600], [575], [575], [575]]).drops, []);
  assert.deepEqual(drops([[600, 90], [600, 90], [600], [600], [600]]).drops, []);
});

test("a loss on the frame of a stage cut the scene declares is counted apart", () => {
  const found = drops([[600], [600], [600], [270, 270], [270, 270]], [3 * DT]);
  assert.deepEqual([found.drops, found.at_cuts], [[], 1]);
  // A cut two frames earlier does not cover the loss.
  assert.equal(drops([[600], [600], [600], [270, 270], [270, 270]], [DT]).drops.length, 1);
});

const title = (x, y, extra = {}) => ({
  text: "Chapter",
  bounds: [x - 100, y - 20, x + 100, y + 20],
  alpha: 1,
  role: "title",
  scene: null,
  ...extra,
});
/* The stretches of the texts `textsAt(k)` draws outside scenes at frame k, over `frames` frames. */
function outside(frames, textsAt) {
  const runs = outsideRuns(DT);
  for (let k = 0; k < frames; k++) runs.frame(k * DT, outsideTexts(textsAt(k)));
  return runs.finish();
}

test("the texts outside scenes are those of no scene that are no caption and can be seen", () => {
  const texts = [
    title(960, 540),
    title(960, 540, { scene: "01" }),
    title(960, 1000, { role: "caption" }),
    title(960, 72, { alpha: OUTSIDE.SEEN }),
  ];
  assert.deepEqual(outsideTexts(texts), [{ text: "Chapter", x: 960, y: 540 }]);
});

test("a title that travels over the pace line is one stretch, named by its fastest step", () => {
  // 20 px a frame, 1,200 px/s, from frame 10 through frame 39.
  const x = (k) => 300 + 20 * Math.min(30, Math.max(0, k - 9));
  const [run, ...others] = outside(60, (k) => [title(x(k), 540)]);
  assert.deepEqual(others, []);
  assert.deepEqual(
    [run.text, run.frames, run.speed, run.way, +run.start.toFixed(3), +run.end.toFixed(3)],
    ["Chapter", 30, 1200, 600, +(10 * DT).toFixed(3), +(39 * DT).toFixed(3)],
  );
});

test("a title within the pace, one fast step, and a card beside its running head are no stretch", () => {
  // 7 px a frame is 420 px/s.
  assert.deepEqual(
    outside(40, (k) => [title(300 + 7 * k, 540)]),
    [],
  );
  assert.deepEqual(
    outside(40, (k) => [title(k < 20 ? 300 : 330, 540)]),
    [],
  );
  // The same words stand on the card and, 500 px away, in the running head while one fades into the other.
  assert.deepEqual(
    outside(40, (k) => (k < 20 ? [title(960, 540)] : [title(460, 72)])),
    [],
  );
  assert.deepEqual(
    outside(40, () => [title(960, 540), title(460, 72)]),
    [],
  );
});

const TIMELINE = {
  segments: [
    {
      id: "01",
      utterance_groups: ["One two, three. ", "Four five."],
      words: [
        { text: "One", start: 1, end: 1.2 },
        { text: "two", start: 1.3, end: 1.5 },
        { text: "three", start: 1.6, end: 2 },
        { text: "Four", start: 2.8, end: 3 },
        { text: "five", start: 3.1, end: 3.4 },
      ],
    },
    {
      id: "02",
      utterance_groups: ["数据。"],
      words: [
        { text: "数", start: 6, end: 6.2 },
        { text: "据", start: 6.2, end: 6.5 },
      ],
    },
  ],
};

test("a quiet runs from a thought's last word to the next thought's first, within one segment", () => {
  const thoughts = thoughtsOf(TIMELINE);
  assert.deepEqual(
    thoughts.map((v) => [v.scene, v.index, v.start, v.end]),
    [
      ["01", 1, 1, 2],
      ["01", 2, 2.8, 3.4],
      ["02", 1, 6, 6.5],
    ],
  );
  assert.deepEqual(quietsOf(thoughts), [{ id: "01.1", rest: 2, resume: 2.8 }]);
});

test("a stroke is part-drawn while it has set off and is not whole", () => {
  const draws = [0, 1e-9, 0.6, 1 - 1e-9, 1].map((share, at) => ({ scene: "01", at, share }));
  assert.deepEqual(
    partDrawn(draws).map((d) => d.share),
    [0.6],
  );
});

test("a tip races from the pace at which a mark races, while its stroke draws", () => {
  assert.equal(TIP_RACE, 900);
  const tips = racingTips();
  tips.frame([
    { scene: "01", at: 4, share: 0.2, pace: 950 },
    { scene: "01", at: 5, share: 0.5, pace: 899 },
    { scene: "02", at: 9, share: 1, pace: 2000 },
  ]);
  tips.frame([{ scene: "01", at: 4, share: 0.7, pace: 1010.4 }]);
  assert.deepEqual(tips.finish(), [{ scene: "01", cue: 4, pace: 1010 }]);
});

const name = (text, x0, top, x1, extra = {}) => ({
  text,
  whole: text,
  bounds: [x0, top, x1, top + 30],
  alpha: 1,
  scene: "13",
  set: "duties",
  ...extra,
});

test("names on alternate baselines are a rail, read by its least clearance", () => {
  // The second name reaches 20 px under the first, 14 px below it; the third stands 20 px right of the second.
  const [rail, ...others] = railsOf([
    name("Find the users", 300, 600, 520),
    name("Plan the release and its recovery", 500, 644, 760),
    name("Verify", 780, 600, 900),
  ]);
  assert.deepEqual(others, []);
  assert.deepEqual(
    [rail.scene, rail.set, rail.clear, rail.names, rail.across, rail.down],
    ["13", "duties", 14, ["Find the users", "Plan the release and its recovery"], -20, 14],
  );
  assert.ok(rail.clear < RAIL.CLEAR);
});

test("a row, a list wrapped onto two rows and a list of three with a wrapped name are no rails", () => {
  const row = [name("a", 300, 600, 400), name("b", 420, 600, 520), name("c", 540, 600, 640)];
  assert.deepEqual(railsOf(row), []);
  // Two names on each row: the names do not alternate along the rail.
  const wrapped = [
    name("a", 300, 600, 400),
    name("b", 420, 600, 520),
    name("c", 540, 644, 640),
    name("d", 660, 644, 760),
  ];
  assert.deepEqual(railsOf(wrapped), []);
  const tall = [
    name("a", 300, 600, 400),
    name("b first line", 420, 644, 520, { whole: "b" }),
    name("b second line", 420, 690, 520, { whole: "b" }),
    name("c", 540, 600, 640),
  ];
  assert.deepEqual(railsOf(tall), []);
  // Names below the opacity at which they count, and names of no list, form none.
  assert.deepEqual(
    railsOf([
      name("a", 300, 600, 520, { alpha: RAIL.SHOWN - 0.1 }),
      name("b", 500, 644, 760),
      name("c", 780, 600, 900, { set: undefined }),
    ]),
    [],
  );
});

test("a rail keeps its least clearance over the rests of the film", () => {
  const rails = railClearances();
  const at = (gap) => [
    name("a", 300, 600, 520),
    name("b", 500, 630 + gap, 760),
    name("c", 780, 600, 900),
  ];
  rails.rest("13.1", at(50));
  rails.rest("13.2", at(14));
  rails.rest("13.3", at(60));
  assert.deepEqual(
    rails.finish().map((v) => [v.scene, v.set, v.at, v.clear]),
    [["13", "duties", "13.2", 14]],
  );
});
