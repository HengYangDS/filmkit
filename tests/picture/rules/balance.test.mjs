/** Exercise balance and cover as the reviewers measure them, through speech and in every
 * frame. */
import test from "node:test";
import assert from "node:assert/strict";

import {
  balanceRuns,
  bandCover,
  pictureOffset,
  reviewedRuns,
} from "../../../src/filmkit/picture/rules/balance.mjs";

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

/* A box of the given width whose centre stands dx px from x 960, within the reviewers' band. */
const offBy = (dx, width = 400) => [960 + dx - width / 2, 300, 960 + dx + width / 2, 700];

const near = (a, b) => Math.abs(a - b) < 1e-6;

test("a build-up off centre for 1.5 s or more is a reviewers' run; a briefer state is not", () => {
  // 120 px left for 1.6 s while the parts arrive, then centred.
  const build = sampled(
    reviewedRuns(1 / 30),
    0,
    4,
    () => "07",
    (t) => (t >= 1 && t < 2.6 ? offBy(-120) : offBy(0)),
  );
  assert.equal(build.builds.length, 1);
  assert.equal(build.builds[0].scene, "07");
  assert.ok(near(build.builds[0].start, 1) && near(build.builds[0].end, 2.6));
  assert.ok(near(build.builds[0].worst, -120));
  // 200 px off for 1.4 s and then within 90 px is no run.
  const brief = sampled(
    reviewedRuns(1 / 30),
    0,
    4,
    () => "07",
    (t) => (t >= 1 && t < 2.4 ? offBy(200) : offBy(80)),
  );
  assert.deepEqual(brief.builds, []);
  // A scene change, a frame with nothing lit and a gap in the samples each end a run.
  const cut = sampled(
    reviewedRuns(1 / 30),
    0,
    3,
    (t) => (t < 1.2 ? "07" : "08"),
    () => offBy(150),
  );
  assert.deepEqual(
    cut.builds.map((v) => v.scene),
    ["08"],
  );
  const dark = sampled(
    reviewedRuns(1 / 30),
    0,
    3,
    () => "07",
    (t) => (t >= 1.2 && t < 1.3 ? null : offBy(150)),
  );
  assert.deepEqual(
    dark.builds.map((v) => near(v.start, 1.3)),
    [true],
  );
  const runs = reviewedRuns(0.1);
  for (const t of [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.4, 1.5, 1.6])
    runs.frame(t, "07", offBy(150));
  assert.deepEqual(runs.finish().builds, []);
});

test("a settled composition off centre for 2 s or more is a reviewers' run; a growing build-up is not", () => {
  // Still at 60 px right for 2.5 s.
  const still = sampled(
    reviewedRuns(1 / 30),
    0,
    3,
    () => "09",
    (t) => (t >= 0.5 ? offBy(60) : offBy(0)),
  );
  assert.equal(still.settled.length, 1);
  assert.ok(near(still.settled[0].worst, 60) && near(still.settled[0].start, 0.5));
  assert.deepEqual(still.builds, []);
  // 70 px off for 3 s while its right edge grows by 40 px is a build-up within its limit: neither run.
  const growing = sampled(
    reviewedRuns(1 / 30),
    0,
    3,
    () => "09",
    (t) => {
      const [x0, y0, x1, y1] = offBy(-70);
      return [x0, y0, x1 + (40 * t) / 3, y1];
    },
  );
  assert.deepEqual(growing, { builds: [], settled: [], finished: [] });
  // A still state that the next part grows from is a build-up held while it waits: no settled run. The same state
  // followed by another picture of its scene, or by nothing lit, is a settled composition.
  const waiting = (t) => (t < 2.5 ? offBy(70) : [offBy(70)[0], 300, offBy(70)[2] + 300, 700]);
  assert.deepEqual(sampled(reviewedRuns(1 / 30), 0, 3, () => "09", waiting).settled, []);
  const replaced = sampled(
    reviewedRuns(1 / 30),
    0,
    3,
    () => "09",
    (t) => (t < 2.5 ? offBy(70) : offBy(0, 100)),
  );
  assert.deepEqual(
    replaced.settled.map((v) => near(v.end, 2.5)),
    [true],
  );
  const fading = sampled(
    reviewedRuns(1 / 30),
    0,
    3,
    () => "09",
    (t) => (t < 2.5 ? offBy(70) : null),
  );
  assert.deepEqual(
    fading.settled.map((v) => near(v.worst, 70)),
    [true],
  );
  // A lone mark centred where it stands is within both limits.
  const lone = sampled(
    reviewedRuns(1 / 30),
    0,
    3,
    () => "09",
    () => offBy(0, 60),
  );
  assert.deepEqual(lone, { builds: [], settled: [], finished: [] });
});

test("a still state that a stage cut or the next scene replaces is finished, not grown from", () => {
  // 70 px off for 2.5 s; at 2.5 s a stage cut of its scene brings a wider box that contains it.
  const cutAt = 2.5,
    wider = [offBy(70)[0], 300, offBy(70)[2] + 300, 700];
  const runs = reviewedRuns(1 / 30);
  for (let k = 0; k / 30 < 3 - 1e-9; k++) {
    const t = k / 30;
    runs.frame(
      t,
      "07",
      t < cutAt ? offBy(70) : wider,
      t > cutAt - 1 / 30 + 1e-9 && t <= cutAt + 1e-9,
    );
  }
  const replaced = runs.finish();
  assert.deepEqual(replaced.settled, []);
  assert.deepEqual(
    replaced.finished.map((v) => [v.scene, near(v.start, 0), near(v.worst, 70)]),
    [["07", true, true]],
  );
  // The same state followed by the next scene's picture is finished too.
  const next = sampled(
    reviewedRuns(1 / 30),
    0,
    3,
    (t) => (t < 2.5 ? "07" : "08"),
    (t) => (t < 2.5 ? offBy(70) : offBy(0)),
  );
  assert.deepEqual([next.settled.length, next.finished.map((v) => v.scene)], [0, ["07"]]);
  // Without the cut the wider box grew from the state, which waited for it: no run.
  const grown = sampled(
    reviewedRuns(1 / 30),
    0,
    3,
    () => "07",
    (t) => (t < cutAt ? offBy(70) : wider),
  );
  assert.deepEqual(grown, { builds: [], settled: [], finished: [] });
});
