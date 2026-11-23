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
