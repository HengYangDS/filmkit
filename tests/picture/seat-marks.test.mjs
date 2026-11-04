/** Exercise the seat check and the container check on marks and names laid out by hand. */
import test from "node:test";
import assert from "node:assert/strict";

import { containerFill, seatMarks } from "../../src/filmkit/picture/seat-marks.mjs";

const segment = (x0, y0, x1, y1) => ({
  box: [Math.min(x0, x1), Math.min(y0, y1), Math.max(x0, x1), Math.max(y0, y1)],
  segs: [
    [
      [x0, y0],
      [x1, y1],
    ],
  ],
  kind: "open",
  frame: false,
});
const ringAt = (x, y, r) => {
  const points = Array.from({ length: 13 }, (_, k) => [
    x + r * Math.cos((k * Math.PI) / 6),
    y + r * Math.sin((k * Math.PI) / 6),
  ]);
  return {
    box: [x - r, y - r, x + r, y + r],
    segs: points.slice(1).map((point, k) => [points[k], point]),
    kind: "closed",
    frame: false,
  };
};
const seatRows = (rows) => rows.map((row) => [row.box.map(Math.round).join(","), row.named]);
/* A rectangle's outline, a frame from 120 by 100 px, solid unless dashed. */
const outline = (x0, y0, x1, y1, dashed = false) => ({
  box: [x0, y0, x1, y1],
  segs: [
    [
      [x0, y0],
      [x1, y0],
    ],
    [
      [x1, y0],
      [x1, y1],
    ],
    [
      [x1, y1],
      [x0, y1],
    ],
    [
      [x0, y1],
      [x0, y0],
    ],
  ],
  kind: "closed",
  frame: x1 - x0 >= 120 && y1 - y0 >= 100,
  dashed,
});

test("a dashed place at a link's end waits for its own name, whatever names the card it joins", () => {
  // A named card's link ends at a dashed place: the three touch, and the card's words name the mark they make.
  const card = outline(400, 400, 700, 480),
    link = segment(700, 440, 900, 440),
    words = { bounds: [450, 425, 650, 455] };
  const place = outline(906, 395, 1086, 485, true);
  assert.deepEqual(seatRows(seatMarks([card, link, place], [words], [words])), [
    ["400,395,1086,485", true],
    ["906,395,1086,485", false],
  ]);
  // A name below the place names it, and so does what arrives inside it.
  const name = { bounds: [930, 500, 1060, 530] },
    check = segment(980, 430, 1010, 450),
    placeRow = (rows) => seatRows(rows).find(([box]) => box === "906,395,1086,485");
  assert.deepEqual(placeRow(seatMarks([card, link, place], [words, name], [words, name])), [
    "906,395,1086,485",
    true,
  ]);
  assert.deepEqual(placeRow(seatMarks([card, link, place, check], [words], [words])), [
    "906,395,1086,485",
    true,
  ]);
  // A solid card at the link's end is part of the mark the link joins.
  const solid = outline(906, 395, 1086, 485);
  assert.deepEqual(seatRows(seatMarks([card, link, solid], [words], [words])), [
    ["400,395,1086,485", true],
  ]);
});

test("a frame that holds only a pictogram waits for a name, and one that holds a named mark is named", () => {
  // A tool's frame holds its pictogram, apart from its edge: neither names the other.
  const tool = outline(400, 300, 700, 500),
    branch = segment(450, 350, 450, 450);
  assert.deepEqual(seatRows(seatMarks([tool, branch], [], [])), [
    ["400,300,700,500", false],
    ["450,350,450,450", false],
  ]);
  // Its name inside names both.
  const git = { bounds: [480, 390, 540, 420] };
  assert.deepEqual(seatRows(seatMarks([tool, branch], [git], [git])), [
    ["400,300,700,500", true],
    ["450,350,450,450", true],
  ]);
  // A frame that holds a card named by a name below the frame is named through it.
  const store = outline(300, 300, 900, 600),
    record = outline(400, 500, 600, 560),
    below = { bounds: [420, 620, 580, 650] };
  assert.deepEqual(
    seatRows(seatMarks([store, record], [below], [below])).map(([, named]) => named),
    [true, true],
  );
});

test("each member repeated on a named rail waits for its own name", () => {
  const rail = segment(300, 500, 1300, 500),
    stations = [500, 800, 1100].map((x) => ringAt(x, 500, 20));
  const railName = { bounds: [300, 440, 420, 470] },
    firstName = { bounds: [470, 540, 530, 562] };
  const rows = seatMarks([rail, ...stations], [railName, firstName], [railName, firstName]);
  assert.deepEqual(seatRows(rows.filter((row) => row.member)), [
    ["480,480,520,520", true],
    ["780,480,820,520", false],
    ["1080,480,1120,520", false],
  ]);
  assert.ok(rows.some((row) => !row.member && row.named));
});

test("a repeated icon is one member, however many parts draw it", () => {
  const person = (x) => [ringAt(x, 480, 12), segment(x - 20, 500, x + 20, 500)],
    shapes = [...person(500), ...person(800)],
    first = { bounds: [470, 515, 530, 535] },
    second = { bounds: [770, 515, 830, 535] };
  assert.deepEqual(seatRows(seatMarks(shapes, [first, second], [first, second])), [
    ["480,468,520,500", true],
    ["780,468,820,500", true],
  ]);
  assert.deepEqual(seatRows(seatMarks(shapes, [first], [first])), [
    ["480,468,520,500", true],
    ["780,468,820,500", false],
  ]);
});

test("a station is one member: its disc's fill and outline, and the figure drawn on it", () => {
  const station = (x) => [
      { box: [x - 36, 424, x + 36, 496], segs: null, kind: "fill", frame: false },
      { ...ringAt(x, 460, 36), box: [x - 36, 424, x + 36, 496] },
      { box: [x - 11, 442, x + 11, 464], segs: null, kind: "fill", frame: false },
      segment(x - 16, 476, x + 16, 476),
    ],
    shapes = [...station(500), ...station(800)],
    names = [{ bounds: [450, 536, 550, 566] }, { bounds: [750, 536, 850, 566] }];
  assert.deepEqual(seatRows(seatMarks(shapes, names, names)), [
    ["464,424,536,496", true],
    ["764,424,836,496", true],
  ]);
});

test("nine repeated shapes are a texture, such as a gear's teeth, not a list", () => {
  const teeth = Array.from({ length: 9 }, (_, k) => segment(400 + k * 40, 500, 400 + k * 40, 524)),
    gear = { bounds: [400, 540, 520, 570] };
  assert.deepEqual(
    seatMarks(teeth, [gear], [gear]).filter((row) => row.member),
    [],
  );
});

test("a panel that holds only its corner marks waits whatever name stands beside it", () => {
  const record = { box: [700, 300, 1500, 700], segs: null, kind: "fill", frame: true },
    fold = segment(1478, 300, 1478, 322),
    beside = { bounds: [700, 710, 900, 735] };
  assert.deepEqual(seatRows(seatMarks([record, fold], [beside], [beside])), [
    ["700,300,1500,700", false],
  ]);
  const row = segment(760, 420, 1400, 420);
  assert.equal(seatMarks([record, fold, row], [beside], [beside])[0].named, true);
});

test("a frame holding only its title is filled by a sliver of its interior, and grows full as its members arrive", () => {
  const frame = { box: [100, 100, 500, 400], segs: null, kind: "fill", frame: true },
    title = { bounds: [120, 120, 380, 146] };
  const [only] = containerFill([frame], [title], [title]);
  assert.equal(only.kind, "frame");
  assert.deepEqual(only.box, [100, 100, 500, 400]);
  // The title covers 260 by 26 px of the 372 by 272 px interior inside the frame's edge band.
  assert.ok(Math.abs(only.fill - (260 * 26) / (372 * 272)) < 1e-9);
  const rows = { box: [130, 160, 470, 380], segs: null, kind: "fill", frame: false };
  assert.ok(containerFill([frame, rows], [title], [title])[0].fill > 0.5);
});

test("a bracket is filled by what stands on its open side along its spine", () => {
  // "[" with 30 px ticks pointing right and a 400 px spine.
  const bracket = {
    box: [170, 100, 200, 500],
    segs: [
      [
        [200, 100],
        [170, 100],
      ],
      [
        [170, 100],
        [170, 500],
      ],
      [
        [170, 500],
        [200, 500],
      ],
    ],
    kind: "open",
    frame: false,
  };
  const first = { bounds: [220, 120, 400, 160] },
    behind = { bounds: [20, 120, 150, 480] };
  const [one] = containerFill([bracket], [first, behind], [first, behind]);
  assert.equal(one.kind, "bracket");
  assert.ok(Math.abs(one.fill - 40 / 400) < 1e-9);
  const all = [first, { bounds: [220, 160, 400, 490] }];
  assert.ok(containerFill([bracket], all, all)[0].fill > 0.9);
  // A plain line is no container.
  assert.deepEqual(containerFill([segment(100, 100, 900, 100)], [first], [first]), []);
});
