/** Exercise the runs of the mass and of the still box on the content, as the fused film's rule 3 limits them: where
 * a run starts and ends, what ends it and what a step counts. */
import test from "node:test";
import assert from "node:assert/strict";

import { MASS, massRuns, verticalRuns } from "../../../src/filmkit/picture/rules/balance.mjs";

const near = (a, b) => Math.abs(a - b) < 1e-6;

/* Frames every `step` seconds from `from` to `to`, each with the scene drawn at t and what the rule reads at t: a mass
 * centre or a box. The times are whole multiples of the step, as an audit samples them. */
function stepped(runs, step, from, to, scene, valueAt, cutAt = () => false) {
  for (let k = Math.round(from / step); k * step < to - 1e-9; k++) {
    const t = k * step;
    runs.frame(t, scene(t), valueAt(t), cutAt(t));
  }
  return runs.finish();
}
// A mass centre dx px off x 960 on the content centre's row.
const massAt = (dx) => [960 + dx, 510];

test("the mass leaning more than 90 px for 1.5 s or more is a run of the scene drawn; less is not", () => {
  // Sampled at the audit's own step: a lean of 1.5 s or more holds six samples or more, one of 1.2 s at most five.
  const lean = (seconds, from = 1) =>
    stepped(
      massRuns(MASS.step),
      MASS.step,
      0,
      4,
      () => "05",
      (t) => massAt(t >= from - 1e-9 && t < from + seconds - 1e-9 ? -120 : 0),
    );
  const [run] = lean(1.75);
  assert.deepEqual(
    [run.scene, near(run.start, 1), near(run.end, 2.75), run.worst],
    ["05", true, true, -120],
  );
  assert.equal(lean(1.5).length, 1);
  assert.deepEqual(lean(1.2), []);
  assert.deepEqual(lean(1.2, 1.1), []);
  // Exactly 90 px is within the limit, however long it stands.
  assert.deepEqual(
    stepped(
      massRuns(MASS.step),
      MASS.step,
      0,
      3,
      () => "05",
      () => massAt(90),
    ),
    [],
  );
  // A frame without a mass 1.25 s into 2.5 s of a lean leaves parts of 1.25 s and 1 s: no run.
  const dark = stepped(
    massRuns(MASS.step),
    MASS.step,
    0,
    2.5,
    () => "05",
    (t) => (Math.abs(t - 1.25) < 1e-9 ? null : massAt(-120)),
  );
  assert.deepEqual(dark, []);
  // Another scene drawn inside a lean ends it: 1.25 s of one scene and 1.25 s of the next hold none.
  const cut = stepped(
    massRuns(MASS.step),
    MASS.step,
    0,
    2.5,
    (t) => (t < 1.25 - 1e-9 ? "05" : "06"),
    () => massAt(-120),
  );
  assert.deepEqual(cut, []);
});

test("a lean of the outgoing scene drawn into the next segment is one run of that scene", () => {
  // The next segment starts at 10 s, and the composition draws scene 03 until the incoming scene's cut at 11.25 s; its
  // mass stands 120 px left from 9.5 s. Keyed by the scene drawn, not the segment, the lean is one run of 1.75 s.
  const runs = stepped(
    massRuns(MASS.step),
    MASS.step,
    9,
    12,
    (t) => (t < 11.25 - 1e-9 ? "03" : "04"),
    (t) => massAt(t >= 9.5 - 1e-9 && t < 11.25 - 1e-9 ? -120 : 0),
  );
  assert.deepEqual(
    runs.map((v) => [v.scene, near(v.start, 9.5), near(v.end, 11.25), v.worst]),
    [["03", true, true, -120]],
  );
});

test("the mass's step must divide both of rule 3's limits into whole steps", () => {
  assert.equal(MASS.step, 0.25);
  for (const step of [0.1, 0.25]) assert.doesNotThrow(() => massRuns(step));
  // At 0.2 s, 1.5 s is no whole number of steps: a lean of 1.5 to 1.6 s could pass.
  assert.throws(() => massRuns(0.2), /0\.2 s divides 1\.5 s into no whole number of steps/);
});

// A box 100 px tall whose centre stands at y, from x0 to x1.
const boxAt = (y, x0 = 760, x1 = 1160) => [x0, y - 50, x1, y + 50];

test("a still box more than 50 px off y 510 for 2 s or more is a vertical run; a growing one is not", () => {
  const [run, ...more] = stepped(
    verticalRuns(1 / 30),
    1 / 30,
    0,
    3,
    () => "02",
    (t) => (t >= 0.5 - 1e-9 ? boxAt(590) : boxAt(510)),
  );
  assert.deepEqual(more, []);
  assert.deepEqual(
    [run.scene, near(run.start, 0.5), near(run.end, 3), run.worst],
    ["02", true, true, 80],
  );
  // At y 530 it stands within 50 px: no run.
  assert.deepEqual(
    stepped(
      verticalRuns(1 / 30),
      1 / 30,
      0,
      3,
      () => "02",
      () => boxAt(530),
    ),
    [],
  );
  // A row of names at y 600 that grows sideways, one name after another, is no still state.
  const row = stepped(
    verticalRuns(1 / 30),
    1 / 30,
    0,
    3,
    () => "02",
    (t) => boxAt(600, 760 - 100 * Math.floor(t / 0.6), 1160 + 100 * Math.floor(t / 0.6)),
  );
  assert.deepEqual(row, []);
  // A box 80 px low whose bottom edge grows by 40 px over 3 s is no still state either.
  const down = stepped(
    verticalRuns(1 / 30),
    1 / 30,
    0,
    3,
    () => "02",
    (t) => {
      const [x0, y0, x1, y1] = boxAt(590);
      return [x0, y0, x1, y1 + (40 * t) / 3];
    },
  );
  assert.deepEqual(down, []);
});

test("a declared stage cut, another scene and a frame without a box each end a vertical run", () => {
  // 1.5 s at y 590, a stage cut the composition declares, then 1.5 s more: two still states of 1.5 s.
  const cut = stepped(
    verticalRuns(1 / 30),
    1 / 30,
    0,
    3,
    () => "02",
    () => boxAt(590),
    (t) => Math.abs(t - 1.5) < 1e-6,
  );
  assert.deepEqual(cut, []);
  const scenes = stepped(
    verticalRuns(1 / 30),
    1 / 30,
    0,
    3,
    (t) => (t < 1.5 - 1e-9 ? "02" : "03"),
    () => boxAt(590),
  );
  assert.deepEqual(scenes, []);
  const dark = stepped(
    verticalRuns(1 / 30),
    1 / 30,
    0,
    3,
    () => "02",
    (t) => (Math.abs(t - 1.5) < 1e-6 ? null : boxAt(590)),
  );
  assert.deepEqual(dark, []);
});
