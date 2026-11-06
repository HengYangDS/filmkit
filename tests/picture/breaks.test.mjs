/** Exercise the frame audit's wrapped labels on layout records: how lines are read and grouped, and the rules each
 * label's lines are judged by at rest. */
import test from "node:test";
import assert from "node:assert/strict";
import { writeFile } from "node:fs/promises";
import { join } from "node:path";

import {
  CLOSES,
  LEAD_WORDS,
  labelBreaks,
  readWrapping,
  WRAPPING,
  wrapLayout,
  wrappedLabels,
} from "../../src/filmkit/picture/frame-audit/typography/breaks.mjs";
import { scratchFolder } from "./sample-film.mjs";

/* A text's width in a stand-in face: a CJK character an em, any other character half of one. */
const measure = (text, size) =>
  [...text].reduce((w, ch) => w + (/[\u3000-\u9fff\uff00-\uffef]/u.test(ch) ? 1 : 0.5) * size, 0);
/* A layout record as a composition registers it: a text centred on x, or starting at x, with its middle at y. */
function record(
  text,
  x,
  y,
  { size = 26, alpha = 1, whole = text, align = "center", ...rest } = {},
) {
  const w = measure(text, size),
    left = align === "left" ? x : x - w / 2;
  return {
    text,
    bounds: [left, y - 0.52 * size, left + w, y + 0.52 * size],
    alpha,
    size,
    scene: "01",
    role: "label",
    whole,
    placed: true,
    ...rest,
  };
}
/* A name wrapped onto `lines`, centred on x from y down at 1.4 times each line's size, the whole joined by spaces. */
function wrapped(lines, x = 960, y = 500, { sizes = [], alphas = [], ...rest } = {}) {
  const whole = lines.join(" ");
  let at = y;
  return lines.map((line, k) => {
    const size = sizes[k] ?? 26,
      v = record(line, x, at, { size, alpha: alphas[k] ?? 1, whole, ...rest });
    at += 1.4 * size;
    return v;
  });
}
const breaksOf = (lines, options = {}, rules = WRAPPING) => {
  const labels = wrappedLabels(wrapped(lines, 960, 500, options));
  assert.equal(labels.length, 1, lines.join(" / "));
  return labelBreaks(labels[0], rules);
};

test("an English line ending on a lead word, or one word left last in three, breaks the label", () => {
  assert.deepEqual(breaksOf(["A trade in", "the market"]), ['line 1 ends on the lead word "in"']);
  assert.deepEqual(breaksOf(["Bias may hide", "elsewhere"]), [
    'line 2 holds one of its block\'s 4 words, "elsewhere"',
  ]);
  assert.deepEqual(breaksOf(["Key findings", "reproducible"]), [
    'line 2 holds one of its block\'s 3 words, "reproducible"',
  ]);
  // Punctuation and case around the last word, and a film's own lead words.
  assert.deepEqual(breaksOf(["Plans, tasks and", "their results"]), [
    'line 1 ends on the lead word "and"',
  ]);
  assert.deepEqual(breaksOf(["Risk versus", "reward taken"]), []);
  assert.deepEqual(
    breaksOf(["Risk versus", "reward taken"], {}, { ...WRAPPING, lead_words: ["Versus"] }),
    ['line 1 ends on the lead word "versus"'],
  );
  // A two-word name stacked on two lines is its layout's to resolve, and a phrase ending on a noun is sound.
  assert.deepEqual(breaksOf(["Manual", "rescue"]), []);
  assert.deepEqual(breaksOf(["Prices arrive", "two hours late"]), []);
  assert.ok(["a", "of", "and", "its", "which", "is", "not"].every((v) => LEAD_WORDS.has(v)));
  // DDWG round 33 painted "Cannot prove what / was available then", which EN33-1 named: a wh-word leads its clause.
  assert.deepEqual(breaksOf(["Cannot prove what", "was available then"]), [
    'line 1 ends on the lead word "what"',
  ]);
  assert.ok(
    ["what", "when", "where", "why", "how", "if", "because", "until"].every((v) =>
      LEAD_WORDS.has(v),
    ),
  );
});

test("the lines of one size stay even: a short line and a short last line break the label", () => {
  assert.deepEqual(breaksOf(["Never", "written down"]), [
    "line 1 spans 0.417 of the widest line of its size, under 0.8",
  ]);
  assert.deepEqual(breaksOf(["Preserve meaning with the smallest model", "that is enough"]), [
    "line 2, the last of its size, spans 0.35 of the widest, under 0.6",
  ]);
  // A film may declare its own shares; a share at the limit stands.
  const rules = { ...WRAPPING, line_share: 0.4, last_share: 0.35 };
  assert.deepEqual(breaksOf(["Never", "written down"], {}, rules), []);
  assert.deepEqual(
    breaksOf(["Preserve meaning with the smallest model", "that is enough"], {}, rules),
    [],
  );
  assert.deepEqual(breaksOf(["讲得清", "经得起查", "能用到哪里"]), [
    "line 1 spans 0.6 of the widest line of its size, under 0.8",
  ]);
});

test("a name over its smaller gloss is judged as two blocks", () => {
  // The short name over a wider gloss is not a short line, and the gloss's lines are judged among themselves.
  const gloss = { sizes: [26, 22, 22] };
  assert.deepEqual(breaksOf(["Agent", "checks the task", "before it acts"], gloss), []);
  assert.deepEqual(breaksOf(["Agent", "checks the whole task", "first"], gloss), [
    "line 3, the last of its size, spans 0.238 of the widest, under 0.6",
    'line 3 holds one of its block\'s 5 words, "first"',
  ]);
  // A name ending on an auxiliary over its gloss is not one phrase broken across lines.
  assert.deepEqual(
    breaksOf(["Bigger than it needs to be", "concepts they do not need"], { sizes: [26, 22] }),
    [],
  );
  assert.deepEqual(breaksOf(["研究员", "拿数据做回测"], { sizes: [26, 22] }), []);
});

test("a Chinese line opens on no closing punctuation, and its hung mark is not counted in its width", () => {
  assert.deepEqual(breaksOf(["先确认任务", "、要处理对象"]), ['line 2 opens on "、"']);
  // 13 ems less the half of its hung 、 over 6 ems: the last line spans 0.48 of the first.
  assert.deepEqual(breaksOf(["先确认任务、要处理的对象、", "现状和负责人"]), [
    "line 2, the last of its size, spans 0.48 of the widest, under 0.6",
  ]);
  assert.ok([..."，。、；：！？）》」』”’…"].every((v) => CLOSES.test(v)));
  // 更早认出来， sets its comma in the first half of its em: 5.5 of 7 ems is under 0.8, though its six advances are
  // not. The em is the size the record was painted at, its registered size without one.
  assert.deepEqual(breaksOf(["系统", "更早认出来，", "或者处理得更好"], { sizes: [26, 22, 22] }), [
    "line 2 spans 0.786 of the widest line of its size, under 0.8",
  ]);
  assert.deepEqual(breaksOf(["更早认出来，", "或者处理得更好"], { em: 13 }), []);
  // English lead words are not Chinese words.
  assert.deepEqual(breaksOf(["数据 in", "the 管道"]), []);
});

test("pieces on one line are read as one, and a name standing in two places is two labels", () => {
  // A word revealed after the rest of its line, a hung mark and a lit copy over a dim one join their lines; a word
  // set apart without its own space is a word.
  const whole = "研究员拿数据、做回测";
  const pieces = [
    record("研究员拿数据", 900, 500, { whole, align: "left" }),
    record("、", 900 + 6 * 26, 503, { whole, align: "left" }),
    record("做回测", 900, 536.4, { whole, align: "left", alpha: 0.4 }),
    record("做回测", 900, 536.4, { whole, align: "left" }),
  ];
  const [label] = wrappedLabels(pieces);
  assert.deepEqual(
    label.lines.map((l) => [l.text, l.alpha]),
    [
      ["研究员拿数据、", 1],
      ["做回测", 1],
    ],
  );
  // A piece whose box falls lower, as a descender's ink does, widens its line's band.
  const lower = record("trade in", 600 + 13 + 8, 500, {
    whole: "A trade in the market",
    align: "left",
  });
  lower.bounds[3] += 6.5;
  const words = wrappedLabels([
    record("A", 600, 500, { whole: "A trade in the market", align: "left" }),
    lower,
    record("the market", 600, 536.4, { whole: "A trade in the market", align: "left" }),
  ]);
  assert.deepEqual(
    words[0].lines.map((l) => [l.text, +(l.bottom - l.top).toFixed(2)]),
    [
      ["A trade in", 33.54],
      ["the market", 27.04],
    ],
  );
  // The same name at two places, broken differently, is judged at each.
  const twice = wrappedLabels([
    ...wrapped(["A trade in", "the market"], 500),
    ...wrapped(["A trade", "in the market"], 1400),
  ]);
  assert.deepEqual(
    twice.map((v) => v.lines.map((l) => l.text)),
    [
      ["A trade in", "the market"],
      ["A trade", "in the market"],
    ],
  );
  assert.deepEqual(
    twice.map((v) => labelBreaks(v)),
    [
      ['line 1 ends on the lead word "in"'],
      ["line 1 spans 0.538 of the widest line of its size, under 0.8"],
    ],
  );
});

test("only names painted on two or more lines by a scene as labels are wrapped labels", () => {
  const lines = ["A trade in", "the market"];
  assert.deepEqual(wrappedLabels([record("A trade in the market", 960, 500)]), []);
  assert.deepEqual(wrappedLabels(wrapped(lines, 960, 500, { role: "caption" })), []);
  assert.deepEqual(wrappedLabels(wrapped(lines, 960, 500, { scene: null })), []);
  assert.deepEqual(wrappedLabels(wrapped(lines, 960, 500, { whole: null })), []);
  // Lines too far apart, or beside each other, are two names.
  const apart = wrapped(lines);
  apart[1].bounds = apart[1].bounds.map((v, i) => (i % 2 ? v + 200 : v));
  assert.deepEqual(wrappedLabels(apart), []);
  const beside = wrapped(lines);
  beside[1].bounds = beside[1].bounds.map((v, i) => (i % 2 ? v : v + 400));
  assert.deepEqual(wrappedLabels(beside), []);
});

test("a label is judged once, when every line stands at rest, and a name in two places is one entry", () => {
  const layout = wrapLayout();
  const frame = (t, texts) => layout.frame({ t, layout: { texts } });
  const lines = ["A trade in", "the market"];
  frame(1, wrapped(lines, 960, 500, { alphas: [1, 0.6] }));
  frame(1.5, [...wrapped(lines, 500, 500, { alphas: [1, 0.95] }), ...wrapped(lines, 1400, 500)]);
  frame(2, wrapped(["Bias may hide", "elsewhere"], 960, 300, { alphas: [0.3, 0.3] }));
  frame(2.5, wrapped(lines, 960, 500));
  assert.deepEqual(layout.finish(), {
    "01": [
      {
        lines,
        seen: 1,
        at: 1.5,
        breaks: ['line 1 ends on the lead word "in"'],
        sizes: [26, 26],
        shares: [1, 1],
      },
      { lines: ["Bias may hide", "elsewhere"], seen: 2, at: null, breaks: [] },
    ],
  });
  // The frame audit gives each record the sequence number of its paint, whose size and scale make its em.
  const painted = wrapLayout();
  const texts = wrapped(["更早认出来，", "或者处理得更好"], 960, 500).map((v, i) => ({
    ...v,
    seq: i + 1,
  }));
  const paints = texts.map(() => ({ kind: "text", size: 13, scale: 1 }));
  painted.frame({ t: 0, layout: { texts }, paints });
  assert.deepEqual(painted.finish()["01"][0].shares, [0.821, 1]);
});

test("the declared rules are read from the file FILMKIT_WRAPPING names", async () => {
  const folder = await scratchFolder(),
    path = join(folder, "wrapping.json");
  assert.equal(readWrapping(""), WRAPPING);
  await writeFile(path, JSON.stringify({ line_share: 0.75, lead_words: ["versus"] }));
  assert.deepEqual(readWrapping(path), {
    line_share: 0.75,
    last_share: 0.6,
    lead_words: ["versus"],
  });
  await writeFile(path, JSON.stringify({ last_share: 1.2 }));
  assert.throws(() => readWrapping(path), /last_share is not a share in \(0, 1\]: 1\.2/);
});
