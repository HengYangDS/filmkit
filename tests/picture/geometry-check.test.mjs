/** Exercise the real-browser check's page code on the headless canvas: its instrumentation against the stand-in, and
 * its page program with every rule run from its source. */
import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

import { spanOf } from "../../src/filmkit/picture/frame-audit/marks.mjs";
import { inspectFilm, instrument, judged } from "../../src/filmkit/picture/geometry-check.mjs";
import {
  canvasStandIn,
  canvasSweep,
  openComposition,
} from "../../src/filmkit/picture/headless-composition.mjs";
import { analysis } from "../../src/filmkit/picture/rules/frame.mjs";
import { inkLevel, readingLoad } from "../../src/filmkit/picture/rules/ink.mjs";
import { faintLabels, listTracker, nameRules } from "../../src/filmkit/picture/rules/names.mjs";
import { rowGaps } from "../../src/filmkit/picture/rules/rows.mjs";
import { authoredTimeline, SAMPLE } from "./sample-film.mjs";

// Scripts run in a context keep their file name, so coverage attributes them to their sources.
const COMPOSITION = join(SAMPLE, "picture/film.js");
// The page program is measured against the film's own palette, as the composition defines it.
const { palette } = openComposition(await authoredTimeline("zh"));
// Every rule the page program runs, by its source, as the check hands them to the page.
const RULES = Object.fromEntries(
  [inkLevel, readingLoad, analysis, nameRules, listTracker, faintLabels, rowGaps].map((rule) => [
    rule.name,
    rule.toString(),
  ]),
);

/* The real-browser check's page code on the headless canvas: a context class whose methods are the stand-in's, which
 * hands each paint to `deliver`, so the check's instrumentation wraps them as it wraps CanvasRenderingContext2D in the
 * browser, and film.js draws on it. The film element declares the frame's `width`. */
function pageCanvas(film, deliver = () => {}, width = "1920") {
  const STYLE = [
    "globalAlpha",
    "strokeStyle",
    "fillStyle",
    "lineWidth",
    "lineCap",
    "lineJoin",
  ].concat(["font", "textAlign", "textBaseline", "letterSpacing"]);
  class CanvasRenderingContext2D {
    constructor(inner) {
      this.inner = inner;
    }
  }
  const inner = canvasStandIn(deliver);
  for (const name of Object.keys(inner))
    CanvasRenderingContext2D.prototype[name] = function (...args) {
      return this.inner[name](...args);
    };
  for (const key of STYLE)
    Object.defineProperty(CanvasRenderingContext2D.prototype, key, {
      get() {
        return this.inner[key];
      },
      set(value) {
        this.inner[key] = value;
      },
    });
  const canvas = { getContext: () => new CanvasRenderingContext2D(inner) },
    element = { dataset: { width } };
  return {
    window: { FILM: film },
    document: { getElementById: (id) => (id === "picture" ? canvas : element) },
    CanvasRenderingContext2D,
  };
}

/* The page as the browser runs it: the instrumentation, then film.js, both in the page's own realm. `source` is a
 * composition to run in place of the sample film's, on a frame `width` wide. */
async function headlessPage(film, source = null, width = "1920") {
  const page = pageCanvas(film, () => {}, width),
    context = vm.createContext(page);
  vm.runInContext(`(${instrument})()`, context);
  vm.runInContext(source ?? (await readFile(COMPOSITION, "utf8")), context, {
    filename: COMPOSITION,
  });
  return { window: page.window, context };
}

/* The same page whose instrumentation and program run in the test's realm, on the page's window and document. */
async function testRealmPage(film) {
  const page = pageCanvas(film);
  Object.assign(globalThis, page);
  instrument();
  vm.runInContext(await readFile(COMPOSITION, "utf8"), vm.createContext({ ...page }), {
    filename: COMPOSITION,
  });
  return () => {
    for (const name of Object.keys(page)) delete globalThis[name];
  };
}

test("the stand-in samples every path as the real-browser instrumentation does", async () => {
  const film = await authoredTimeline("en"),
    { window } = await headlessPage(film),
    paints = [];
  const composition = openComposition(film);
  // Each scene draws rounded cards, outlines, dashed and solid lines, arrows and a tick.
  for (const segment of film.segments)
    for (const q of [0.3, 0.6, 0.9]) {
      const t = segment.voice_start + q * (segment.voice_end - segment.voice_start);
      paints.length = 0;
      composition.render(t, (paint) => paints.push(paint));
      window.__resetPaint();
      window.renderFrame(t);
      // The page records every stroke, a fill with a path, and the paint order of each text.
      const shapes = paints
        .map((paint, i) => ({ paint, seq: i + 1 }))
        .filter(
          ({ paint }) =>
            paint.kind === "stroke" || (paint.kind === "fill" && paint.subs.flat().length),
        );
      assert.equal(window.__paintedShapes.length, shapes.length, `${segment.id}@${t}`);
      shapes.forEach(({ paint, seq }, k) => {
        // The page's values belong to its own realm; a structured clone compares them by value.
        const shape = structuredClone(window.__paintedShapes[k]);
        assert.deepEqual(
          [shape.kind, shape.seq, shape.alpha, shape.color, shape.scene],
          [paint.kind, seq, paint.alpha, paint.color, paint.scene],
        );
        if (paint.kind === "stroke") {
          assert.equal(shape.width, paint.lineWidth * paint.scale);
          assert.deepEqual(shape.subs, paint.subs);
        } else assert.deepEqual(shape.box, spanOf(paint.subs.flat()));
      });
      assert.deepEqual(
        [...window.__paintedText],
        paints.flatMap((paint, i) => (paint.kind === "text" ? [i + 1] : [])),
      );
    }
});

test("the real-browser page program runs every rule from its source and keeps the receipt's fields", async () => {
  const film = await authoredTimeline("zh"),
    { context, window } = await headlessPage(film);
  const rules = RULES;
  // The program runs in the page's realm, as page.evaluate runs it, on the palette read from the page.
  const program = vm.runInContext(`(${inspectFilm})`, context),
    pagePalette = structuredClone(vm.runInContext("({ ...P })", context));
  assert.deepEqual(pagePalette, { ...palette });
  const frames = Math.round(film.duration * 60);
  const result = structuredClone(program(rules, pagePalette, frames, 30, 60));
  assert.equal(result.checked, Math.ceil(frames / 30));
  assert.deepEqual(result.errors, []);
  for (const finding of result.findings)
    assert.deepEqual(Object.keys(finding), ["kind", "scene", "text", "first", "frames"]);
  // The cover is the title card on the ground: the title, its subtitle and the author.
  window.__resetPaint();
  window.renderCover();
  assert.equal(window.__paintedText.length, 3);
});

/* A composition of one scene whose three names stand on one row from its first frame, each painted in a 30 px face
 * and registered at the nominal size 20, on a frame of any width: the second starts `gap` px after the first ends and
 * the third 90 px after the second. */
const ROW = (gap) =>
  [
    'var P = { ground: "#0F1519", ink: "#ECE8DF" };',
    'var ctx = document.getElementById("picture").getContext("2d");',
    'var k = Number(document.getElementById("film").dataset.width) / 1920;',
    "var layout = [];",
    "function name(value, x) {",
    "  ctx.setTransform(k, 0, 0, k, 0, 0);",
    '  ctx.font = "30px Sample";',
    '  ctx.textAlign = "left";',
    '  ctx.textBaseline = "alphabetic";',
    "  ctx.globalAlpha = 1;",
    "  ctx.fillStyle = P.ink;",
    "  ctx.fillText(value, x, 500);",
    "  const right = x + ctx.measureText(value).width;",
    "  layout.push({ text: value, bounds: [x, 476, right, 506], color: P.ink, alpha: 1, role: 'label',",
    "    scene: window.__sceneId, placed: true, size: 20 });",
    "  return right;",
    "}",
    "window.renderFrame = function () {",
    "  layout = [];",
    '  window.__sceneId = "01";',
    `  name("Resource", name("Technical", name("Compliance", 400) + ${gap}) + 90);`,
    "  window.__sceneId = null;",
    "  window.__filmLayout = { time: 0, texts: layout };",
    "};",
    "",
  ].join("\n");
const ROW_FILM = {
  duration: 2,
  segments: [{ id: "01", chapter: 1, start: 0, voice_start: 0.2, voice_end: 1.8 }],
};
/* The findings of the page program over that composition's two seconds at 60 fps, every second frame. */
async function rowFindings(gap, width = "1920") {
  const { context } = await headlessPage(ROW_FILM, ROW(gap), width);
  const result = vm.runInContext(`(${inspectFilm})`, context)(RULES, { ...palette }, 120, 2, 60);
  assert.deepEqual(structuredClone(result.errors), []);
  // A row gap is recorded apart from the findings, which the check gates.
  assert.deepEqual(structuredClone(result.findings), []);
  return structuredClone(result.row_gaps);
}

test("the page program records names closer than 1.5 em on one row, by the size the frame paints them at", async () => {
  // 36 px is 1.2 em of the painted 30 px face, though 1.8 em of the nominal size the film registers.
  const pair = {
    kind: "row_gap",
    scene: "01",
    text: "Compliance | Technical",
    pair: ["Compliance", "Technical"],
    gap: 36,
    em: 1.2,
    floor: 1.5,
    first: 0,
    frames: 60,
  };
  assert.deepEqual(await rowFindings(36), [pair]);
  // A UHD frame paints the face twice as large; the finding stays in px and em of the logical 1080p frame.
  assert.deepEqual(await rowFindings(36, "3840"), [pair]);
  // 45 px is 1.5 em: the row passes.
  assert.deepEqual(await rowFindings(45), []);
});

test("the page program finds the same in the test's realm as in the page's", async () => {
  const film = await authoredTimeline("en"),
    { context } = await headlessPage(film);
  const rules = RULES;
  const frames = Math.round(film.duration * 60);
  const inPage = structuredClone(
    vm.runInContext(`(${inspectFilm})`, context)(rules, palette, frames, 30, 60),
  );
  const restore = await testRealmPage(film);
  try {
    // The instrumentation records each shape and text as it does in the page, and the program reads them the same.
    assert.deepEqual(structuredClone(inspectFilm(rules, palette, frames, 30, 60)), inPage);
    assert.ok(globalThis.window.__paintedText.length > 0);
  } finally {
    restore();
  }
});

test("an arc samples the sweep a canvas draws, in the stand-in and the page instrumentation", () => {
  // A canvas draws arc(x, y, r, Math.PI, 0) clockwise through the top; drawn anticlockwise from 0 to Math.PI it
  // also passes the top. Every sampled point then stands at or above the centre.
  const above = (subs) => subs.flat().every(([, y]) => y <= 100 + 1e-9);
  const paints = [],
    ctx = canvasStandIn((paint) => paints.push(paint));
  for (const args of [
    [100, 100, 10, Math.PI, 0],
    [100, 100, 10, 0, Math.PI, true],
  ]) {
    ctx.beginPath();
    ctx.arc(...args);
    ctx.stroke();
  }
  assert.equal(paints.length, 2);
  assert.ok(paints.every((paint) => above(paint.subs)));
  // The page instrumentation wraps a context whose methods are the stand-in's, as in the browser.
  class CanvasRenderingContext2D {}
  const inner = canvasStandIn(() => {});
  for (const name of Object.keys(inner))
    CanvasRenderingContext2D.prototype[name] = (...args) => inner[name](...args);
  for (const key of ["globalAlpha", "lineWidth", "strokeStyle", "fillStyle"])
    Object.defineProperty(CanvasRenderingContext2D.prototype, key, {
      get: () => inner[key],
    });
  const window = {},
    context = vm.createContext({
      window,
      document: { getElementById: () => ({ dataset: { width: "1920" } }) },
      CanvasRenderingContext2D,
    });
  vm.runInContext(`(${instrument})()`, context);
  const page = new CanvasRenderingContext2D();
  page.beginPath();
  page.arc(100, 100, 10, Math.PI, 0);
  page.stroke();
  assert.equal(window.__paintedShapes.length, 1);
  assert.ok(above(window.__paintedShapes[0].subs));
  // A whole turn stays a whole turn, and a reversed span below one turn is brought into it.
  assert.equal(canvasSweep(0, 2 * Math.PI), 2 * Math.PI);
  assert.equal(canvasSweep(Math.PI, 0), Math.PI);
  assert.equal(canvasSweep(0, Math.PI, true), -Math.PI);
});

test("the stand-in and the page instrumentation sample each path a canvas draws alike", () => {
  const paints = [],
    page = pageCanvas({}, (paint) => paints.push(paint));
  Object.assign(globalThis, page);
  try {
    instrument();
    const ctx = page.document.getElementById("picture").getContext("2d");
    ctx.save();
    ctx.translate(40, 20);
    ctx.scale(2, 2);
    ctx.lineWidth = 3;
    ctx.strokeStyle = "#ECE8DF";
    ctx.beginPath();
    // An arc that opens the path starts its subpath, a curve after an ellipse starts where the ellipse ends, as on a
    // canvas, and a rounded rectangle is a subpath of its own.
    ctx.arc(100, 100, 10, 0, Math.PI / 2);
    ctx.lineTo(80, 120);
    ctx.closePath();
    ctx.moveTo(200, 200);
    ctx.ellipse(250, 200, 40, 20, Math.PI / 6, 0, Math.PI);
    ctx.quadraticCurveTo(250, 260, 300, 240);
    ctx.roundRect(500, 500, 80, 40);
    ctx.stroke();
    ctx.restore();
    assert.equal(paints.length, 1);
    const [shape] = globalThis.window.__paintedShapes;
    assert.deepEqual(shape.subs, paints[0].subs);
    assert.equal(shape.width, paints[0].lineWidth * paints[0].scale);
  } finally {
    for (const name of Object.keys(page)) delete globalThis[name];
  }
});

test("the row gaps refuse only for a film that gates them", () => {
  const gap = {
    kind: "row_gap",
    scene: "01",
    text: "Compliance | Technical",
    gap: 36,
    em: 1.2,
  };
  const report = { findings: [], row_gaps: [gap], errors: [] };
  // Recorded, and the check passes: reviews of some films accept closer names.
  assert.deepEqual(judged(report, false), { findings: [], passed: true });
  // Gated with --gate-row-gaps: the pair is a finding and the check fails.
  assert.deepEqual(judged(report, true), { findings: [gap], passed: false });
  // An error fails the check whatever the gate.
  assert.equal(
    judged({ ...report, row_gaps: [], errors: [{ message: "x", t: 0 }] }, false).passed,
    false,
  );
});
