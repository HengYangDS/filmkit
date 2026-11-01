/** Exercise the headless runtime both audits run the composition on: where it reads the composition, every authored
 * scene against both scripts, the paints it hands over, the canvas stand-in and the timeline engine. */
import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { spanOf } from "../../src/filmkit/picture/frame-audit/marks.mjs";
import {
  canvasStandIn,
  openComposition,
  readTimeline,
} from "../../src/filmkit/picture/headless-composition.mjs";
import { authoredTimeline, SAMPLE, scratchFolder } from "./sample-film.mjs";

// Scripts run in a context keep their file name, so coverage attributes them to their sources.
const ENGINE = fileURLToPath(new URL("../../node_modules/gsap/dist/gsap.min.js", import.meta.url));

test("the composition is the picture/film.js of the film the tool runs in", async () => {
  const film = await mkdtemp(join(tmpdir(), "film-root-")),
    before = process.cwd();
  try {
    await mkdir(join(film, "picture"));
    await writeFile(
      join(film, "picture/film.js"),
      'var P = { ground: "#0F1519", ink: "#ECE8DF" };\n' +
        "window.renderFrame = (t) => { window.__filmLayout = { time: t, texts: [] }; };\n",
    );
    process.chdir(film);
    const composition = openComposition({});
    assert.deepEqual(composition.palette, { ground: "#0F1519", ink: "#ECE8DF" });
    const layout = composition.render(2);
    assert.equal(layout.time, 2);
    assert.equal(layout.texts.length, 0);
  } finally {
    process.chdir(before);
    await rm(film, { recursive: true, force: true });
  }
});

for (const code of ["zh", "en"]) {
  test(`${code} composition paints every authored scene from its own spoken cues`, async () => {
    const film = await authoredTimeline(code);
    const composition = openComposition(film);
    const painted = new Set();
    for (const segment of film.segments) {
      for (const q of [0.15, 0.5, 0.85, 1]) {
        const { texts } = composition.render(
          segment.voice_start + q * (segment.voice_end - segment.voice_start),
        );
        for (const v of texts) if (v.scene) painted.add(v.scene);
        assert.ok(
          texts.every((v) => v.bounds.every(Number.isFinite)),
          segment.id,
        );
      }
    }
    assert.equal(painted.size, film.segments.length);
    assert.ok(composition.render(film.duration - 1).texts.some((v) => v.text === film.author));
  });
}

for (const code of ["zh", "en"]) {
  test(`${code} speech never plays over an empty picture`, async () => {
    const film = await authoredTimeline(code);
    // A firm stroke or fill counts for the scene that paints it, as the film publishes while it draws, so the film's
    // own cuts apply: no scene function is replaced.
    let marks = 0;
    const composition = openComposition(film),
      count = (paint) => {
        if (paint.scene && paint.kind !== "text" && paint.alpha > 0.35) marks++;
      };
    const runs = [];
    for (const segment of film.segments) {
      let run = null;
      for (let t = segment.voice_start; t < segment.voice_end; t += 0.1) {
        marks = 0;
        const { texts } = composition.render(t, count);
        const empty = !marks && !texts.some((v) => v.scene && v.alpha > 0.35);
        if (empty) run ??= { segment: segment.id, start: t, end: t };
        if (empty) run.end = t + 0.1;
        if (!empty && run) {
          runs.push(run);
          run = null;
        }
      }
      if (run) runs.push(run);
    }
    assert.deepEqual(
      runs
        .filter((run) => run.end - run.start > 0.5)
        .map((run) => `${run.segment}@${run.start.toFixed(1)}`),
      [],
    );
  });
}

test("the headless timeline is the staged one: its language's edition and no render offset unless given", async () => {
  const folder = await scratchFolder(),
    path = join(folder, "timeline.json");
  await writeFile(path, JSON.stringify({ language: "English", duration: 10 }));
  assert.deepEqual(readTimeline(path), {
    language: "English",
    duration: 10,
    edition: "en",
    render_offset: 0,
  });
  await writeFile(
    path,
    JSON.stringify({ language: "Chinese", edition: "zh", render_offset: 12.5 }),
  );
  assert.deepEqual(readTimeline(path), { language: "Chinese", edition: "zh", render_offset: 12.5 });
});

test("each rendered frame hands over every paint with the scene that drew it", async () => {
  const film = await authoredTimeline("zh"),
    paints = [];
  const composition = openComposition(film);
  const segment = film.segments[3],
    { texts } = composition.render(segment.voice_start + 1, (paint) => paints.push(paint));
  assert.ok(paints.some((paint) => paint.scene === segment.id));
  assert.ok(paints.some((paint) => paint.scene === null && paint.kind === "text"));
  // A text paint stands at its anchor, and the box film.js registers for it holds its box, mapped to the screen.
  const words = paints.filter((paint) => paint.kind === "text");
  assert.equal(words.length, texts.length);
  words.forEach((paint, i) => {
    assert.deepEqual([paint.text, paint.scene], [texts[i].text, texts[i].scene]);
    const [x0, y0, x1, y1] = spanOf(paint.points.map(paint.toScreen)),
      bounds = texts[i].bounds;
    assert.ok(bounds[0] <= x0 && bounds[1] <= y0 && bounds[2] >= x1 && bounds[3] >= y1, paint.text);
    assert.equal(paint.subs.length, 1);
  });
  // Strokes and fills carry their sampled screen subpaths and their drawing points.
  const shapes = paints.filter((paint) => paint.kind !== "text");
  assert.ok(shapes.length > 0);
  for (const paint of shapes) {
    assert.ok(paint.subs.flat().every((point) => point.every(Number.isFinite)));
    assert.ok(paint.points.length > 0 && paint.scale > 0 && paint.lineWidth > 0);
  }
});

test("a scene's paints are traced to their line of film.js and a composition's camera is its own", async () => {
  // A composition that opens each scene as `scenes["NN"] = function` and frames it with `cameraOf`.
  const root = await scratchFolder();
  await mkdir(join(root, "picture"));
  await writeFile(
    join(root, "picture/film.js"),
    [
      'var P = { ground: "#0F1519", ink: "#ECE8DF" };',
      "var ctx = document.getElementById('picture').getContext('2d');",
      "var scenes = {};",
      "function mark(x) {",
      "  ctx.beginPath();",
      "  ctx.moveTo(x, 300);",
      "  ctx.lineTo(x + 100, 300);",
      "  ctx.stroke();",
      "}",
      'scenes["01"] = function (t) {',
      "  mark(300 + t);",
      "};",
      "function cameraOf(segment, t) {",
      "  return { k: 1, ox: t, oy: 0, ax: 960, ay: 540 };",
      "}",
      "window.renderFrame = (t) => {",
      "  mark(100);",
      '  window.__sceneId = "01";',
      '  scenes["01"](t);',
      "  window.__sceneId = null;",
      "  window.__filmLayout = { time: t, texts: [] };",
      "};",
      "",
    ].join("\n"),
  );
  process.chdir(root);
  try {
    const composition = openComposition({}),
      origins = [];
    composition.render(2, (paint) => origins.push([paint.scene, composition.origin()]));
    // The scene's mark comes from line 11 inside its body, through the helper; the mark outside every scene has none.
    assert.deepEqual(origins, [
      [null, null],
      ["01", "film.js:11"],
    ]);
    // The camera's values belong to the composition's realm, so they are copied before comparing.
    assert.equal(composition.framed, true);
    assert.deepEqual(
      { ...composition.camera({ id: "01" }, 2) },
      { k: 1, ox: 2, oy: 0, ax: 960, ay: 540 },
    );
  } finally {
    process.chdir(SAMPLE);
  }
  // The sample composition frames nothing with a camera of its own.
  const sample = openComposition(await authoredTimeline("zh"));
  assert.equal(sample.framed, false);
  assert.throws(() => sample.camera({ id: "01" }, 1), /The composition defines no cameraOf/);
});

test("the canvas stand-in paints what film.js draws and refuses any other member", () => {
  const paints = [],
    ctx = canvasStandIn((paint) => paints.push(paint));
  assert.throws(() => ctx.rotate(1), /The headless canvas has no rotate/);
  assert.throws(() => ctx.toString(), /The headless canvas has no toString/);
  assert.throws(() => {
    ctx.shadowBlur = 4;
  }, /The headless canvas has no shadowBlur to set/);
  // A stroke carries its path as sampled screen subpaths and as its drawing points.
  ctx.setTransform(2, 0, 0, 2, 10, 20);
  ctx.strokeStyle = "#ECE8DF";
  ctx.lineWidth = 3;
  ctx.globalAlpha = 0.5;
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(10, 5);
  ctx.closePath();
  ctx.stroke();
  const [line] = paints;
  assert.deepEqual(
    [line.kind, line.color, line.alpha, line.lineWidth, line.scale],
    ["stroke", "#ECE8DF", 0.5, 3, 2],
  );
  assert.deepEqual(line.subs, [
    [
      [10, 20],
      [30, 30],
      [10, 20],
    ],
  ]);
  assert.deepEqual(line.points, [
    [0, 0],
    [10, 5],
  ]);
  assert.deepEqual(line.toScreen([10, 5]), [30, 30]);
  // A restore returns the saved state and transform; one without a saved state does nothing, as on a canvas.
  ctx.save();
  ctx.globalAlpha = 0.2;
  ctx.translate(5, 0);
  ctx.restore();
  ctx.restore();
  assert.equal(ctx.globalAlpha, 0.5);
  assert.deepEqual(ctx.getTransform(), { a: 2, b: 0, c: 0, d: 2, e: 10, f: 20 });
  // An ellipse is sampled as an arc is, every 7.5 degrees, and its whole box spans its drawing points.
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.beginPath();
  ctx.ellipse(100, 100, 40, 20, 0, 0, Math.PI * 2);
  ctx.stroke();
  const [ring] = paints[1].subs;
  assert.equal(ring.length, 49);
  assert.ok(
    ring.every(([x, y]) => Math.abs(((x - 100) / 40) ** 2 + ((y - 100) / 20) ** 2 - 1) < 1e-9),
  );
  assert.deepEqual(spanOf(ring).map(Math.round), [60, 80, 140, 120]);
  assert.deepEqual(paints[1].points, [
    [60, 80],
    [140, 120],
  ]);
  ctx.beginPath();
  ctx.ellipse(0, 0, 40, 20, Math.PI / 2, 0, Math.PI * 2);
  ctx.fill();
  assert.deepEqual(
    paints[2].points.map((point) => point.map(Math.round)),
    [
      [-20, -40],
      [20, 40],
    ],
  );
  // A text stands at its anchor, its box estimated from its font, alignment and baseline: a capital is 0.66 of the
  // size and any other Latin letter 0.54 of it.
  ctx.font = "20px Sample";
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  ctx.fillStyle = "#7DB7D8";
  ctx.fillText("Ab", 50, 60);
  assert.equal(ctx.measureText("Ab").width, 24);
  const word = paints[3];
  assert.deepEqual([word.kind, word.text, word.size, word.color], ["text", "Ab", 20, "#7DB7D8"]);
  assert.deepEqual(word.subs, [[[50, 60]]]);
  assert.deepEqual(
    word.points.map((point) => point.map(Math.round)),
    [
      [38, 60],
      [62, 81],
    ],
  );
  // The ground laid under each frame is never a mark.
  ctx.fillRect(0, 0, 1920, 1080);
  assert.equal(paints.length, 4);
});

test("the vendored timeline engine seeks a paused timeline as the composition drives it", async () => {
  const scope = { console, setTimeout, clearTimeout };
  vm.createContext(scope);
  vm.runInContext(await readFile(ENGINE, "utf8"), scope, { filename: ENGINE });
  const { gsap } = scope.window;
  assert.equal(gsap.version, "3.15.0");
  const playhead = { time: 0 };
  const timeline = gsap.timeline({ paused: true });
  timeline.to(playhead, { time: 1500, duration: 1500, ease: "none" }, 0);
  timeline.seek(50);
  assert.equal(playhead.time, 50);
  timeline.kill();
  gsap.ticker.sleep();
});
