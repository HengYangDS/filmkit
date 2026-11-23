/* The engine's classes of characters as the Node audits read them (src/filmkit/languages/scripts.mjs). */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { CLASSES, characterClass, classTest } from "../../src/filmkit/languages/scripts.mjs";

const DATA = JSON.parse(
  readFileSync(new URL("../../src/filmkit/languages/scripts.json", import.meta.url), "utf8"),
);

test("every class of the data file is read, each holding its first member", () => {
  assert.deepEqual(Object.keys(CLASSES), [
    ...Object.keys(DATA.scripts),
    ...Object.keys(DATA.marks),
  ]);
  for (const [name, entry] of Object.entries(CLASSES)) {
    const first = entry.ranges
      ? String.fromCodePoint(Number.parseInt(entry.ranges[0].split("-")[0], 16))
      : [...entry.characters][0];
    assert.ok(classTest(name)(first), `${name} holds ${first}`);
  }
});

test("a class the data file does not hold is refused by name", () => {
  assert.throws(() => characterClass("cyrillic"), /scripts\.json holds no class cyrillic/);
});

/* Whether a point stands in any range of a class. */
const covered = (ranges, point) =>
  ranges.some((span) => {
    const [first, last] = span.split("-").map((hex) => Number.parseInt(hex, 16));
    return first <= point && point <= last;
  });

test("each class holds the edges of each of its ranges and nothing just outside them", () => {
  for (const [name, entry] of Object.entries(CLASSES)) {
    if (!entry.ranges) continue;
    const holds = classTest(name);
    for (const span of entry.ranges) {
      const [first, last] = span.split("-").map((hex) => Number.parseInt(hex, 16));
      assert.ok(
        holds(String.fromCodePoint(first)) && holds(String.fromCodePoint(last)),
        `${name} ${span}`,
      );
      for (const outside of [first - 1, last + 1])
        if (outside >= 0 && !(outside >= 0xd800 && outside <= 0xdfff))
          assert.equal(
            holds(String.fromCodePoint(outside)),
            covered(entry.ranges, outside),
            `${name} ${outside}`,
          );
    }
  }
  assert.ok(!classTest("han")("䷀"), "a Yijing hexagram is no Han character");
});

test("each listed mark is its class's, and the closing marks are one set for both typography checks", () => {
  for (const [name, entry] of Object.entries(CLASSES))
    for (const ch of entry.characters ?? "") assert.ok(classTest(name)(ch), `${name} ${ch}`);
  for (const ch of "】…’") assert.ok(classTest("line-closing")(ch), ch);
});

test("the typography checks and the composition's estimate read the classes alike", async () => {
  const { CJK, CLOSING } =
    await import("../../src/filmkit/picture/frame-audit/typography/layout.mjs");
  const { CLOSES } = await import("../../src/filmkit/picture/frame-audit/typography/breaks.mjs");
  assert.ok(CJK.test("㐀") && CJK.test("。") && CJK.test("Ａ"));
  for (const mark of ["】", "…", "’"]) {
    assert.ok(CLOSING.test(`甲${mark}`), `layout closes on ${mark}`);
    assert.ok(CLOSES.test(`${mark}乙`), `breaks opens on ${mark}`);
  }
});
