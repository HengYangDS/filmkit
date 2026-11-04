/** Exercise the case measure: the names of one set or one row share one initial case. */
import test from "node:test";
import assert from "node:assert/strict";

import { canvasStandIn } from "../../src/filmkit/picture/headless-composition.mjs";
import { initialCase } from "../../src/filmkit/picture/frame-audit/typography/case.mjs";
import { textLayout } from "../../src/filmkit/picture/frame-audit/typography/index.mjs";

/* The case runs of a frame whose names `draw` lists, each [text, x, y, size, record], drawn every thirtieth of a
 * second for `seconds` of speech. A record gives the name's whole text, set and role as the composition registers
 * them; the frame audit copies them onto the name's paint. */
function caseRuns(seconds, names) {
  const layout = textLayout(1 / 30);
  for (let k = 0; k / 30 < seconds - 1e-9; k++) {
    const paints = [];
    const ctx = canvasStandIn((paint) => paints.push({ ...paint, scene: "01" }));
    for (const [text, x, y, size = 30, record = {}] of names) {
      ctx.font = `${size}px Sample`;
      ctx.textAlign = "center";
      ctx.textBaseline = "alphabetic";
      ctx.fillText(text, x, y);
      Object.assign(paints.at(-1), record);
    }
    layout.frame({ t: k / 30, speaking: { id: "01" }, paints });
  }
  return layout.finish().mixed_case;
}

test("three equal cards named in mixed case through 2 s of speech are one finding", () => {
  const runs = caseRuns(2, [
    ["The observation", 400, 500],
    ["The inference", 900, 500],
    ["the proposed remedy", 1400, 500],
    // A smaller lowercase qualifier under each name is a row of its own.
    ["still stands", 400, 560, 24],
    ["can be wrong", 900, 560, 24],
  ]);
  assert.equal(runs.length, 1);
  const [run] = runs;
  assert.deepEqual(run.texts, ["The observation", "The inference", "the proposed remedy"]);
  assert.deepEqual(run.detail, {
    upper: ["The observation", "The inference"],
    lower: ["the proposed remedy"],
  });
  assert.ok(Math.abs(run.end - run.start - 2) < 1e-6);
});

test("a set's names are judged together wherever they stand", () => {
  const lane = { set: "lane" };
  const runs = caseRuns(1.5, [
    ["Work Lane", 600, 300, 30, lane],
    ["checks once more", 600, 420, 30, lane],
    ["file under version control", 600, 540, 30, lane],
  ]);
  assert.deepEqual(
    runs.map((run) => run.texts),
    [["Work Lane", "checks once more", "file under version control"]],
  );
  // A brief state, under a second, is not a run.
  assert.deepEqual(
    caseRuns(0.9, [
      ["Work Lane", 600, 300, 30, lane],
      ["checks", 600, 420, 30, lane],
    ]),
    [],
  );
});

test("a wrapped name counts once, by its whole text at its first line", () => {
  const request = { whole: "The researcher’s request" },
    lane = { whole: "Work Lane" };
  assert.deepEqual(
    caseRuns(1.5, [
      ["The researcher’s", 400, 500, 30, request],
      ["request", 400, 540, 30, request],
      ["Work", 800, 500, 30, lane],
      ["Lane", 800, 540, 30, lane],
    ]),
    [],
  );
});

test("acronyms, names without case and titles are not judged", () => {
  assert.deepEqual(
    caseRuns(1.5, [
      ["ETHOS", 400, 500],
      ["each repository", 900, 500],
      ["GitLab", 1400, 500],
      ["权威依据", 400, 600],
      ["视图", 900, 600],
      ["Back to the beginning", 400, 700, 30, { role: "title" }],
      ["an index", 900, 700],
    ]),
    [],
  );
  assert.deepEqual(
    ["Done", "the vendor", "“Done.", "ETHOS mark", "Human-Agent", "3 inputs", "存证", "x-ray"].map(
      initialCase,
    ),
    ["upper", "lower", null, null, null, null, null, "lower"],
  );
});
