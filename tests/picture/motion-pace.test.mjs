/** The pace of glides and flows: the stretches of marks over the reviewers' line, and how the follower finds them. */
import test from "node:test";
import assert from "node:assert/strict";

import { follower, VIEWER } from "../../src/filmkit/picture/motion-audit/follow.mjs";
import { overPace, PACE, paceRuns } from "../../src/filmkit/picture/motion-audit/pace.mjs";

const DT = 1 / 30;
/* A card 200 by 80 px, a name 120 by 30 px on it and a dot 10 px across, each at ink 200 in scene `scene`. */
const card = (x, y, scene = "01") => ({
  scene,
  kind: "fill",
  width: 0,
  level: 200,
  screen: [x, y, x + 200, y + 80],
});
const name = (text, x, y, scene = "01") => ({
  scene,
  kind: "text",
  text,
  width: 0,
  level: 200,
  screen: [x, y, x + 120, y + 30],
});
const dot = (x, y, scene = "01") => ({
  scene,
  kind: "fill",
  width: 0,
  level: 200,
  screen: [x - 5, y - 5, x + 5, y + 5],
});
/* What a follower finds in `frames` frames of the marks `marksAt(n)` draws at frame n. */
function follow(frames, marksAt) {
  const viewer = follower(DT);
  for (let n = 0; n < frames; n++) viewer.frame(n * DT, marksAt(n));
  return viewer.finish();
}
/* A smooth step from 0 to 1 over `frames` frames from frame `from`: its fastest frame covers just under 1.5 / frames. */
const ease = (n, from, frames) => {
  const q = Math.min(1, Math.max(0, (n - from) / frames));
  return q * q * (3 - 2 * q);
};
const at = (t) => +t.toFixed(3);

test("the pace line is the reviewers' 450 px/s, read to the whole pixel per second", () => {
  assert.equal(PACE, 450);
  assert.equal(VIEWER.PACE, PACE);
  assert.ok(!overPace(450));
  assert.ok(!overPace(450.4));
  assert.ok(overPace(450.6));
  assert.ok(overPace(708));
});

test("marks over the line in consecutive frames of one scene are one stretch, named by its fastest mark", () => {
  const runs = paceRuns(DT);
  const row = (t, scene, text, speed, move = "glide") => ({ t, scene, text, speed, move });
  runs.frame(1, [row(1, "01", "a", 460), row(1, "01", "b", 470), row(1, "02", "c", 500)]);
  runs.frame(1 + DT, [row(1 + DT, "01", "a", 520, "flow")]);
  // A frame without a mark over the line ends scene 01's stretch; the next one is its own.
  runs.frame(1 + 3 * DT, [row(1 + 3 * DT, "01", "a", 455)]);
  assert.deepEqual(
    runs.finish().map((v) => [v.scene, v.text, v.speed, v.move, at(v.t), v.frames, v.marks]),
    [
      ["02", "c", 500, "glide", 1, 1, 1],
      ["01", "a", 520, "flow", at(1 + DT), 2, 2],
      ["01", "a", 455, "glide", at(1 + 3 * DT), 1, 1],
    ],
  );
  const [, long] = runs.finish();
  assert.deepEqual([at(long.start), at(long.end)], [1, at(1 + DT)]);
});

test("a glide at the line passes and one over it is found once, with its peak, its time and its mark", () => {
  // 15 px a frame is 450 px/s, the line itself, and 15.1 px a frame is 453 px/s.
  const calm = follow(20, (n) => [name("Calm", 300 + 15 * n, 300)]);
  assert.deepEqual(calm.paces, []);
  assert.equal(Math.round(calm.speeds["01"].glide.speed), 450);
  const over = follow(20, (n) => [name("Over", 300 + 15.1 * n, 300)]);
  assert.deepEqual(
    over.paces.map((v) => [v.text, Math.round(v.speed), v.frames]),
    [["Over", 453, 19]],
  );
  // 320 px eased over 24 frames is 599 px/s in its fastest frame.
  const brisk = follow(40, (n) => [name("Brisk", 300 + 320 * ease(n, 5, 24), 300)]);
  assert.equal(brisk.paces.length, 1);
  const [pace] = brisk.paces;
  assert.deepEqual([pace.scene, pace.kind, pace.text, pace.move], ["01", "text", "Brisk", "glide"]);
  assert.equal(Math.round(pace.speed), 599);
  assert.equal(pace.speed, brisk.speeds["01"].glide.speed);
  assert.equal(pace.t, brisk.speeds["01"].glide.t);
  assert.ok(pace.start < pace.t && pace.t < pace.end && pace.marks === 1);
  // None of it races, halts or sets off at speed: the pace is its own finding.
  assert.deepEqual([brisk.races, brisk.halts, brisk.starts], [[], [], []]);
});

test("a stage that glides with what it carries, and a dot moving within it, are one stretch", () => {
  // The card, its name and a standing dot glide 320 px together; a second dot also runs 90 px along the card.
  const found = follow(40, (n) => {
    const x = 300 + 320 * ease(n, 5, 24);
    return [
      card(x, 300),
      name("Carried", x + 40, 325),
      dot(x + 20, 400),
      dot(x + 20 + 90 * ease(n, 5, 24), 440),
    ];
  });
  assert.equal(found.paces.length, 1);
  const [pace] = found.paces;
  // The dot that moves within the stage is the fastest mark a viewer sees: the stage's 599 px/s and its own 168.
  assert.deepEqual([pace.kind, pace.move, pace.marks], ["fill", "flow", 4]);
  assert.equal(Math.round(pace.speed), 767);
  assert.equal(Math.round(found.speeds["01"].glide.speed), 599);
  assert.equal(pace.speed, found.speeds["01"].flow.speed);
});

test("a flow over the line is found by its dot, and two scenes keep their own stretches", () => {
  const found = follow(40, (n) => [
    name("Stands", 300, 200),
    dot(300 + 16 * n, 400),
    name("Other", 300 + 320 * ease(n, 5, 24), 600, "02"),
  ]);
  // The dot flows at 480 px/s throughout; scene 02's name glides over the line for a stretch of its own.
  assert.deepEqual(
    found.paces.map((v) => [v.scene, v.move, v.text, Math.round(v.speed), v.frames]).sort(),
    [
      ["01", "flow", "", 480, 39],
      ["02", "glide", "Other", 599, found.paces.find((v) => v.scene === "02").frames],
    ],
  );
  assert.ok(found.paces.find((v) => v.scene === "02").frames < 24);
});
