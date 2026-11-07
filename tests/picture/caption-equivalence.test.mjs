/** Exercise the caption equivalence: the sample film's composition without its captions, compositions that paint
 * something else from their captions, and the instants, cues and invocations the tool takes. */
import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  compareFrame,
  cuesInForce,
  equivalence,
  instants,
  isCaptionPaint,
  letters,
} from "../../src/filmkit/picture/caption-equivalence.mjs";
import { authoredTimeline, SAMPLE, scratchFolder } from "./sample-film.mjs";

const TOOL = fileURLToPath(
  new URL("../../src/filmkit/picture/caption-equivalence.mjs", import.meta.url),
);

for (const code of ["zh", "en"]) {
  test(`the ${code} sample film without its captions differs only by them`, async () => {
    const timeline = await authoredTimeline(code);
    const report = equivalence(timeline);
    assert.equal(report.verdict, "equivalent");
    assert.deepEqual(report.findings, []);
    assert.equal(report.differing_instants, 0);
    assert.equal(report.cues, timeline.captions.length);
    assert.equal(report.cues_shown_at_their_middle, report.cues);
    assert.ok(report.caption_paints >= report.cues);
    assert.equal(report.instants, instants(timeline, 0.5).length);
    // The sample paints its captions on one line at y 1000, above the frame's bottom edge.
    const { top, bottom } = report.band;
    assert.ok(top > 950 && bottom < 1020, `${top}-${bottom}`);
  });
}

/* A composition that paints a scene's name, a running head outside every scene and the caption of the moment, each as
 * the films do: a text in its layout with its role, and `extra` painted after them. */
const composition = (extra = "", { scene = "960", role = "caption", hold = false } = {}) => `
var P = { ground: "#0F1519", ink: "#ECE8DF" };
const film = window.FILM;
const ctx = document.getElementById("picture").getContext("2d");
let texts = [];
function text(value, x, y, role, scene = null) {
  window.__sceneId = scene;
  ctx.font = "30px sans-serif";
  ctx.fillStyle = P.ink;
  ctx.fillText(value, x, y);
  texts.push({ text: value, role, scene });
  window.__sceneId = null;
}
function caption(t) {
  const caps = film.captions;
  let i = caps.findIndex((c) => c.start <= t && t < c.end);
  if (i < 0 && ${hold}) i = caps.findIndex((c, k) => c.end <= t && t < caps[k + 1]?.start);
  if (i >= 0) text((caps[i].display_text ?? caps[i].text).trim(), 960, 1000, "${role}");
}
window.renderFrame = (t) => {
  texts = [];
  text("Sources", ${scene}, 500, "label", "01");
  text("01  Start", 96, 72, "chapter");
  caption(t);
  ${extra}
  window.__filmLayout = { time: t, texts };
};
`;
const TIMELINE = {
  duration: 6,
  segments: [],
  captions: [
    { start: 1, end: 2, text: "One " },
    { start: 2.2, end: 3, text: 'He said "two".', display_text: "He said “two”." },
    { start: 4, end: 5, text: "Three." },
  ],
};

/* Run the equivalence on a composition written into a film of its own. */
async function judged(source, options = {}) {
  const film = await scratchFolder(),
    before = process.cwd();
  await mkdir(join(film, "picture"));
  await writeFile(join(film, "picture/film.js"), source);
  process.chdir(film);
  try {
    return equivalence(TIMELINE, options);
  } finally {
    process.chdir(before);
  }
}

test("a painter that shows each cue, holds it through a short gap and sets its quotes is equivalent", async () => {
  const report = await judged(composition("", { hold: true }), { step: 0.1 });
  assert.equal(report.verdict, "equivalent");
  assert.equal(report.cues_shown_at_their_middle, 3);
  // Held through the gap from 2 s to 2.2 s, the first cue is a caption paint there too.
  assert.ok(report.frames_with_captions > 25);
  assert.deepEqual(report.band.top < 1000 && report.band.bottom > 1000, true);
});

test("a mark drawn from the captions is found at every instant that shows one", async () => {
  const dot =
    "if (film.captions.some((c) => c.start <= t && t < c.end)) { ctx.beginPath(); ctx.arc(400, 1000, 6, 0, 7); ctx.fill(); }";
  const report = await judged(composition(dot));
  assert.equal(report.verdict, "differs");
  const [first] = report.findings;
  assert.equal(first.time, 1);
  assert.deepEqual(
    [first.captioned.kind, first.captioned.scene, first.uncaptioned],
    ["fill", null, null],
  );
  assert.equal(report.differing_instants, report.frames_with_captions);
});

test("a scene placed by whether the film has captions differs at every instant", async () => {
  const report = await judged(composition("", { scene: "film.captions.length ? 960 : 900" }));
  assert.equal(report.differing_instants, report.instants);
  const [first] = report.findings;
  assert.deepEqual([first.captioned.text, first.uncaptioned.text], ["Sources", "Sources"]);
  assert.notDeepEqual(first.captioned.box, first.uncaptioned.box);
});

test("a cue's text painted outside the caption role, or painted only without captions, is found", async () => {
  const unnamed = await judged(composition("", { role: "label" }));
  assert.equal(unnamed.verdict, "differs");
  assert.equal(unnamed.findings[0].captioned.text, "One");
  const placeholder = await judged(
    composition('if (!film.captions.length) text("No captions", 960, 1000, "label");'),
  );
  assert.equal(placeholder.differing_instants, placeholder.instants);
  assert.deepEqual(placeholder.findings[0], {
    time: 0,
    captioned: null,
    uncaptioned: { ...placeholder.findings[0].uncaptioned, text: "No captions" },
  });
});

test("the instants are every step and every cue's start, middle and end, each once and in order", () => {
  assert.deepEqual(instants(TIMELINE, 1), [0, 1, 1.5, 2, 2.2, 2.6, 3, 4, 4.5, 5]);
  assert.deepEqual(instants({ duration: 2, captions: [{ start: 1.5, end: 2.5 }] }, 1), [0, 1, 1.5]);
});

test("the cues in force are the last to start and the next, and a paint is a caption by its letters and role", () => {
  const { captions } = TIMELINE;
  assert.deepEqual(cuesInForce(captions, 0.5), [captions[0]]);
  assert.deepEqual(cuesInForce(captions, 2.1), [captions[0], captions[1]]);
  assert.deepEqual(cuesInForce(captions, 5.5), [captions[2]]);
  assert.equal(letters('He said "two".'), letters("He said “two”."));
  const paint = { kind: "text", scene: null, text: "He said “two”." };
  const layout = { texts: [{ text: paint.text, role: "caption" }] };
  assert.ok(isCaptionPaint(paint, 2.5, captions, layout));
  assert.ok(!isCaptionPaint({ ...paint, scene: "01" }, 2.5, captions, layout));
  assert.ok(!isCaptionPaint(paint, 4.5, captions, layout));
  assert.ok(
    !isCaptionPaint(paint, 2.5, captions, { texts: [{ text: paint.text, role: "label" }] }),
  );
  assert.ok(!isCaptionPaint({ ...paint, kind: "fill" }, 2.5, captions, layout));
});

test("frames are matched in order, setting aside only caption paints", () => {
  const paint = (kind, text = "") => ({ kind, text, scene: null, toScreen: () => [0, 0] });
  const caption = paint("text", "One");
  const same = compareFrame(
    [paint("stroke"), caption, paint("fill")],
    [paint("stroke"), paint("fill")],
    (p) => p === caption,
  );
  assert.deepEqual([same.removed, same.matched, same.finding], [[caption], 2, null]);
  const missing = compareFrame([paint("stroke"), paint("fill")], [paint("stroke")], () => false);
  assert.equal(missing.finding.captioned.kind, "fill");
  const extra = compareFrame(
    [paint("stroke")],
    [paint("stroke"), paint("text", "More")],
    () => false,
  );
  assert.deepEqual([extra.finding.captioned, extra.finding.uncaptioned.text], [null, "More"]);
});

test("the tool prints its report for a timeline and refuses a malformed invocation", async () => {
  const folder = await scratchFolder(),
    path = join(folder, "timeline.json");
  await writeFile(path, JSON.stringify(await authoredTimeline("en")));
  const run = (args) =>
    spawnSync(process.execPath, [TOOL, ...args], { encoding: "utf8", cwd: SAMPLE });
  const printed = run([path, "1"]);
  assert.equal(printed.status, 0, printed.stderr);
  const report = JSON.parse(printed.stdout);
  assert.deepEqual(
    [report.format, report.step, report.verdict],
    ["caption-equivalence", 1, "equivalent"],
  );
  for (const args of [[], [path, "0"], [path, "fast"], [path, "1", "extra"], [path, "--step"]]) {
    const refused = run(args);
    assert.equal(refused.status, 2, args.join(" "));
    assert.equal(refused.stdout, "", args.join(" "));
    assert.ok(
      refused.stderr.includes("Usage: python -m filmkit.tools caption-equivalence"),
      args.join(" "),
    );
  }
});
