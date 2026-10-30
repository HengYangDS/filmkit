/** Exercise the picture tools on the sample film: the frame rules of the real-browser check, with its page program
 * and instrumentation on the headless canvas; the headless runtime both audits run the composition on; every authored
 * scene against both scripts; the audits' invocations; the seat check; and the timeline engine. */
import test, { after } from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  analysis,
  bandCover,
  faintLabels,
  fillShare,
  inkLevel,
  inspectFilm,
  instrument,
  listTracker,
  litLevel,
  nameRules,
  pictureOffset,
  readingLoad,
  strokeShare,
} from "../../src/filmkit/picture/geometry-check.mjs";
import {
  canvasStandIn,
  canvasSweep,
  openComposition,
  readTimeline,
} from "../../src/filmkit/picture/headless-composition.mjs";
import { containerFill, seatMarks } from "../../src/filmkit/picture/seat-marks.mjs";

// The headless runtime reads picture/film.js below the folder it runs in, as the audits run below their film.
const SAMPLE = fileURLToPath(new URL("../../examples/sample-film/", import.meta.url));
process.chdir(SAMPLE);

// Each folder a test writes its inputs and outputs into is removed once the file's tests have run.
const folders = [];
after(() => Promise.all(folders.map((folder) => rm(folder, { recursive: true, force: true }))));
async function scratchFolder() {
  const folder = await mkdtemp(join(tmpdir(), "filmkit-picture-"));
  folders.push(folder);
  return folder;
}

// Scripts run in a context keep their file name, so coverage attributes them to their sources.
const ENGINE = fileURLToPath(new URL("../../node_modules/gsap/dist/gsap.min.js", import.meta.url));
const COMPOSITION = join(SAMPLE, "picture/film.js");

/* A timeline as staging builds it from a script: each word 0.2 s after the last, a chapter's first segment after a
 * longer pause, and one caption over each segment's voice. */
async function authoredTimeline(code) {
  const script = JSON.parse(
    await readFile(
      join(SAMPLE, code === "zh" ? "content/film-script.json" : "content/en/film-script.json"),
      "utf8",
    ),
  );
  let cursor = 3;
  const segments = script.segments.map((segment, index) => {
    if (index) cursor += script.segments[index - 1].chapter === segment.chapter ? 1.8 : 3.6;
    const tokens =
      code === "zh"
        ? segment.text.match(/[\p{Script=Han}]|[A-Za-z0-9][A-Za-z0-9'’.-]*/gu)
        : segment.text.split(/\s+/).filter(Boolean);
    const voiceStart = cursor;
    const words = tokens.map((text) => {
      const word = { text, start: cursor, end: cursor + 0.18 };
      cursor += 0.2;
      return word;
    });
    return { ...segment, voice_start: voiceStart, voice_end: cursor, words };
  });
  segments.forEach((segment, index) => {
    segment.start = index
      ? segment.voice_start - 0.6 * (segment.voice_start - segments[index - 1].voice_end)
      : 0;
  });
  const duration = cursor + 6;
  segments.forEach((segment, index) => {
    segment.end = segments[index + 1]?.start ?? duration - script.credits_duration;
  });
  const captions = segments.map((segment) => ({
    start: segment.voice_start,
    end: segment.voice_end,
    text: segment.words
      .slice(0, 8)
      .map((v) => v.text)
      .join(code === "zh" ? "" : " "),
  }));
  return { ...script, segments, captions, duration, edition: code, render_offset: 0 };
}

// The rules are measured against the film's own palette, as the composition defines it.
const { palette } = openComposition(await authoredTimeline("zh"));
const inspectFrame = analysis(inkLevel(palette));
const contrast = readingLoad(palette);
const label = (text, bounds, extra = {}) => ({
  text,
  bounds,
  alpha: 1,
  role: "label",
  scene: "01",
  seq: 10,
  ...extra,
});
const stroke = (points, extra = {}) => ({
  kind: "stroke",
  seq: 1,
  alpha: 1,
  width: 2,
  subs: [points],
  ...extra,
});
const fill = (box, extra = {}) => ({ kind: "fill", seq: 1, alpha: 1, box, ...extra });
const kinds = (findings) => findings.map((finding) => finding.kind).sort();
const names = nameRules();
const word = (text, extra = {}) => ({
  text,
  bounds: [0, 0, 10, 10],
  alpha: 1,
  role: "label",
  scene: "02",
  color: "#ECE8DF",
  whole: text,
  placed: true,
  size: 38,
  set: null,
  ...extra,
});

test("visible labels must stay apart and inside the safe area", () => {
  assert.deepEqual(
    kinds(inspectFrame([label("A", [300, 300, 400, 330]), label("B", [390, 310, 480, 340])], [])),
    ["label_overlap"],
  );
  assert.deepEqual(
    kinds(inspectFrame([label("A", [300, 300, 400, 330]), label("B", [402, 300, 480, 330])], [])),
    [],
  );
  assert.deepEqual(kinds(inspectFrame([label("A", [30, 300, 120, 330])], [])), [
    "outside_safe_area",
  ]);
  assert.deepEqual(
    kinds(inspectFrame([label("Caption", [30, 990, 1890, 1012], { role: "caption" })], [])),
    [],
  );
  assert.deepEqual(kinds(inspectFrame([label("A", [70, 300, 160, 330])], [])), [
    "outside_safe_area",
  ]);
  assert.deepEqual(kinds(inspectFrame([label("A", [30, 300, 120, 330], { alpha: 0.3 })], [])), [
    "outside_safe_area",
  ]);
  assert.deepEqual(kinds(inspectFrame([label("A", [30, 300, 120, 330], { alpha: 0.1 })], [])), []);
  // Labels end clear of the caption band.
  assert.deepEqual(kinds(inspectFrame([label("A", [300, 900, 400, 936])], [])), [
    "outside_safe_area",
  ]);
  assert.deepEqual(kinds(inspectFrame([label("A", [300, 880, 400, 916])], [])), []);
});

test("reading contrast separates legible names from faint clutter and gone residue", () => {
  // Every name colour of the sample reads at 3:1 at .68 of its ink and is gone below 1.8:1 at .18.
  assert.ok(contrast(palette.ink, 1) > 14);
  for (const color of [palette.ink, palette.muted, palette.accent, palette.done]) {
    assert.ok(contrast(color, 0.68) >= 3, color);
    assert.ok(contrast(color, 0.18) < 1.8, color);
  }
  assert.ok(contrast(palette.ink, 0.4) >= 1.8 && contrast(palette.ink, 0.4) < 3.4);
});

test("names are read whole and at most twelve are legible at once", () => {
  const many = Array.from({ length: 13 }, (_, i) => word(`名${i}`));
  assert.deepEqual(kinds(names(many, contrast)), ["name_load"]);
  assert.deepEqual(kinds(names(many.slice(0, 12), contrast)), []);
  // The lines of a wrapped name share one whole and count once; a name below 3:1 is not read.
  const wrapped = [
    ...many.slice(0, 11),
    word("第一行", { whole: "第一行 第二行" }),
    word("第二行", { whole: "第一行 第二行" }),
  ];
  assert.deepEqual(kinds(names(wrapped, contrast)), []);
  assert.deepEqual(kinds(names([...many.slice(0, 12), word("淡", { alpha: 0.2 })], contrast)), []);
});

test("every legible name is placed by a layout primitive", () => {
  assert.deepEqual(kinds(names([word("手放", { placed: false })], contrast)), ["unplaced_label"]);
  assert.deepEqual(kinds(names([word("手放", { placed: false, alpha: 0.2 })], contrast)), []);
});

test("names use at most two text sizes and never join items with a dot", () => {
  assert.deepEqual(
    kinds(names([word("甲"), word("乙", { size: 28 }), word("丙", { size: 34 })], contrast)),
    ["type_sizes"],
  );
  assert.deepEqual(kinds(names([word("甲"), word("乙", { size: 28 })], contrast)), []);
  assert.deepEqual(kinds(names([word("来源 · 时间")], contrast)), ["dot_join"]);
});

test("a list leaves whole, every name at its set's level", () => {
  const dimmed = listTracker();
  dimmed.see([word("甲", { set: "a", alpha: 0.58 }), word("乙", { set: "a" })], 10, contrast);
  assert.deepEqual(kinds(dimmed.findings()), ["list_leaving_dimmed"]);
  const whole = listTracker();
  whole.see([word("甲", { set: "a", alpha: 0.58 }), word("乙", { set: "a" })], 10, contrast);
  whole.see([word("甲", { set: "a" }), word("乙", { set: "a" })], 10.2, contrast);
  assert.deepEqual(kinds(whole.findings()), []);
  // A refused name is muted by design, so it is held to its own colour, not to the set's ink.
  const refused = listTracker();
  refused.see(
    [word("甲", { set: "a" }), word("拒", { set: "a", color: palette.muted, alpha: 0.7 })],
    10,
    contrast,
  );
  assert.deepEqual(kinds(refused.findings()), []);
});

test("a list leaves as a whole", () => {
  const early = listTracker();
  early.see([word("甲", { set: "a" }), word("乙", { set: "a" })], 10, contrast);
  early.see([word("乙", { set: "a" })], 11, contrast);
  assert.deepEqual(kinds(early.findings()), ["list_leaving_early"]);
  const whole = listTracker();
  whole.see([word("甲", { set: "a" }), word("乙", { set: "a" })], 10, contrast);
  whole.see([word("乙", { set: "a" })], 10.5, contrast);
  assert.deepEqual(kinds(whole.findings()), []);
});

test("the second list level stays legible in every name colour", () => {
  // Ink, muted, accent and done at the second level (0.58).
  for (const color of [palette.ink, palette.muted, palette.accent, palette.done])
    assert.ok(contrast(color, 0.58) >= 3, color);
});

test("shapes stay inside the action-safe area", () => {
  assert.deepEqual(
    kinds(
      inspectFrame(
        [],
        [
          stroke([
            [1400, 600],
            [1880, 600],
          ]),
        ],
      ),
    ),
    ["stroke_outside_action_safe"],
  );
  assert.deepEqual(kinds(inspectFrame([], [fill([1360, 580, 1880, 620])])), [
    "fill_outside_action_safe",
  ]);
  assert.deepEqual(
    kinds(
      inspectFrame(
        [],
        [
          stroke([
            [100, 60],
            [1820, 1020],
          ]),
        ],
      ),
    ),
    [],
  );
  assert.deepEqual(
    kinds(
      inspectFrame(
        [],
        [
          stroke(
            [
              [1400, 600],
              [1880, 600],
            ],
            { alpha: 0.1 },
          ),
        ],
      ),
    ),
    [],
  );
});

test("strokes may not cross a label unless an opaque card painted after them hides them", () => {
  const word = label("Word", [300, 300, 400, 330]);
  const crossing = stroke([
    [250, 315],
    [450, 315],
  ]);
  assert.deepEqual(kinds(inspectFrame([word], [crossing])), ["label_stroke_collision"]);
  assert.deepEqual(
    kinds(
      inspectFrame(
        [word],
        [
          stroke([
            [250, 360],
            [450, 360],
          ]),
        ],
      ),
    ),
    [],
  );
  const card = fill([280, 290, 420, 340], { seq: 5 });
  assert.deepEqual(kinds(inspectFrame([word], [crossing, card])), []);
  assert.deepEqual(kinds(inspectFrame([word], [{ ...card, alpha: 0.5 }, crossing])), [
    "label_stroke_collision",
  ]);
});

test("a fill may contain a label but may not cut through it", () => {
  const word = label("Word", [300, 300, 400, 330]);
  assert.deepEqual(kinds(inspectFrame([word], [fill([280, 290, 420, 340])])), []);
  assert.deepEqual(kinds(inspectFrame([word], [fill([350, 290, 500, 340])])), [
    "label_fill_collision",
  ]);
  assert.deepEqual(
    kinds(
      inspectFrame(
        [label("Caption", [300, 300, 400, 330], { role: "caption" })],
        [fill([350, 290, 500, 340])],
      ),
    ),
    [],
  );
});

test("a frame that must paint may not dim to bare ground", () => {
  const caption = label("Caption", [300, 990, 400, 1012], {
    role: "caption",
    scene: null,
    color: palette.ink,
  });
  const mark = (color, alpha, scene = "02") =>
    stroke(
      [
        [300, 300],
        [400, 300],
      ],
      { scene, alpha, color },
    );
  assert.deepEqual(kinds(inspectFrame([caption], [], { mustPaint: true, scene: "02" })), [
    "bare_ground",
  ]);
  // The brightest scene mark must rise 30 levels above the ground: ink at 20% does, ink at 10% or a dim panel does not.
  assert.deepEqual(
    kinds(inspectFrame([caption], [mark(palette.ink, 0.2)], { mustPaint: true })),
    [],
  );
  assert.deepEqual(kinds(inspectFrame([caption], [mark(palette.ink, 0.1)], { mustPaint: true })), [
    "bare_ground",
  ]);
  assert.deepEqual(
    kinds(inspectFrame([caption], [mark(palette.panel, 0.5)], { mustPaint: true })),
    ["bare_ground"],
  );
  assert.deepEqual(kinds(inspectFrame([], [mark(palette.ink, 1, null)], { mustPaint: true })), [
    "bare_ground",
  ]);
  assert.deepEqual(
    kinds(
      inspectFrame([label("Word", [300, 300, 400, 330], { alpha: 0.03, color: palette.ink })], [], {
        mustPaint: true,
      }),
    ),
    ["bare_ground"],
  );
  assert.deepEqual(kinds(inspectFrame([caption], [])), []);
  // The head band frames the picture: a chip alone in it leaves the frame bare.
  const chip = label("Illustrative", [1640, 60, 1800, 90], { scene: "02", color: palette.ink });
  assert.deepEqual(
    kinds(
      inspectFrame(
        [chip],
        [
          stroke(
            [
              [1630, 56],
              [1810, 56],
            ],
            { scene: "02", color: palette.ink },
          ),
        ],
        { mustPaint: true },
      ),
    ),
    ["bare_ground"],
  );
  assert.deepEqual(kinds(inspectFrame([chip], [mark(palette.ink, 0.5)], { mustPaint: true })), []);
  // The frame reports its brightest scene level, so a run of faint speech can be found across frames.
  assert.equal(
    inspectFrame([caption], [mark(palette.ink, 0.5)], { mustPaint: true }).brightest,
    110.5,
  );
  assert.equal(inspectFrame([caption], [], { mustPaint: true }).brightest, 0);
});

test("a chapter's first word lands on a standing first scene", () => {
  const mark = (alpha) =>
    stroke(
      [
        [300, 300],
        [400, 300],
      ],
      { scene: "02", alpha, color: palette.ink },
    );
  assert.deepEqual(kinds(inspectFrame([], [mark(0.3)], { mustPaint: true, firstWord: true })), [
    "faint_first_word",
  ]);
  assert.deepEqual(kinds(inspectFrame([], [mark(0.5)], { mustPaint: true, firstWord: true })), []);
  assert.deepEqual(kinds(inspectFrame([], [mark(0.3)], { mustPaint: true })), []);
});

test("ink level and reading contrast are measured over the film's ground", () => {
  const level = inkLevel(palette);
  assert.equal(level(palette.ground, 1), 0);
  assert.equal(level(palette.ink, 0.5), 110.5);
  // A style without channels, such as a gradient, lifts nothing, and reads as the film's ink.
  assert.equal(level(undefined, 1), 0);
  assert.equal(contrast(undefined, 0.6), contrast(palette.ink, 0.6));
  assert.equal(contrast(palette.ground, 1), 1);
});

test("a fill above 15% opacity that cuts through a label collides, however faint", () => {
  const word = label("Word", [300, 300, 400, 330]);
  for (const alpha of [0.3, 1])
    assert.deepEqual(kinds(inspectFrame([word], [fill([350, 290, 500, 340], { alpha })])), [
      "label_fill_collision",
    ]);
  assert.deepEqual(kinds(inspectFrame([word], [fill([350, 290, 500, 340], { alpha: 0.15 })])), []);
});

test("each finding carries the evidence a report shows", () => {
  const boxed = label("Word", [300, 300, 400, 330]);
  const [crossed] = inspectFrame(
    [boxed],
    [
      stroke([
        [250, 200],
        [250, 315],
        [450, 315],
      ]),
    ],
  );
  assert.deepEqual(crossed, {
    kind: "label_stroke_collision",
    scene: "01",
    text: "Word",
    shape: "stroke",
    bounds: [300, 300, 400, 330],
    graphic: [250, 315, 450, 315],
  });
  assert.deepEqual(
    inspectFrame([boxed, label("Next", [390, 310, 480, 340])], []).map((v) => v.pair),
    [["Word", "Next"]],
  );
  assert.deepEqual(
    inspectFrame([label("A", [30, 300, 120, 330])], [])[0].bounds,
    [30, 300, 120, 330],
  );
  const [outside] = inspectFrame([], [fill([1360, 580, 1880, 620])]);
  assert.deepEqual([outside.shape, outside.point], ["fill", [1880, 620]]);
  // Name findings count the legible names and give the sizes shown.
  const found = names([word("甲"), word("乙", { size: 28 }), word("丙", { size: 34 })], contrast);
  assert.equal(found.names, 3);
  assert.deepEqual(found.find((v) => v.kind === "type_sizes").sizes, [28, 34, 38]);
  // List findings name the set and the name, when it was last seen and a dimmed name's share of the brightest.
  const lists = listTracker();
  lists.see([word("甲", { set: "a" }), word("乙", { set: "a" })], 10, contrast);
  lists.see([word("甲", { set: "a" }), word("乙", { set: "a", alpha: 0.6 })], 11, contrast);
  lists.see([word("乙", { set: "a" })], 12, contrast);
  assert.deepEqual(
    lists.findings().map(({ kind, set, name, at, share }) => [kind, set, name, at, share]),
    [["list_leaving_early", "a", "甲", 11, undefined]],
  );
});

test("a label held faint for more than a second is reported when it leaves the faint band", () => {
  const see = faintLabels(),
    faint = word("淡", { alpha: 0.3 });
  assert.ok(contrast(faint.color, faint.alpha) >= 1.8 && contrast(faint.color, faint.alpha) < 3);
  assert.deepEqual(see([faint], 10, contrast), []);
  assert.deepEqual(see([faint], 11, contrast), []);
  assert.deepEqual(see([], 11.2, contrast), [{ scene: "02", text: "淡", start: 10, end: 11.2 }]);
  // A faint stretch of one second or less is a fade, not clutter.
  assert.deepEqual(see([faint], 20, contrast), []);
  assert.deepEqual(see([word("淡")], 21, contrast), []);
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

const spanOf = (points) => [
  Math.min(...points.map((p) => p[0])),
  Math.min(...points.map((p) => p[1])),
  Math.max(...points.map((p) => p[0])),
  Math.max(...points.map((p) => p[1])),
];

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

/* The real-browser check's page code on the headless canvas: a context class whose methods are the stand-in's, which
 * hands each paint to `deliver`, so the check's instrumentation wraps them as it wraps CanvasRenderingContext2D in the
 * browser, and film.js draws on it. */
function pageCanvas(film, deliver = () => {}) {
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
    element = { dataset: { width: "1920" } };
  return {
    window: { FILM: film },
    document: { getElementById: (id) => (id === "picture" ? canvas : element) },
    CanvasRenderingContext2D,
  };
}

/* The page as the browser runs it: the instrumentation, then film.js, both in the page's own realm. */
async function headlessPage(film) {
  const page = pageCanvas(film),
    context = vm.createContext(page);
  vm.runInContext(`(${instrument})()`, context);
  vm.runInContext(await readFile(COMPOSITION, "utf8"), context, { filename: COMPOSITION });
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
  const rules = Object.fromEntries(
    [inkLevel, readingLoad, analysis, nameRules, listTracker, faintLabels].map((rule) => [
      rule.name,
      rule.toString(),
    ]),
  );
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

test("the page program finds the same in the test's realm as in the page's", async () => {
  const film = await authoredTimeline("en"),
    { context } = await headlessPage(film);
  const rules = Object.fromEntries(
    [inkLevel, readingLoad, analysis, nameRules, listTracker, faintLabels].map((rule) => [
      rule.name,
      rule.toString(),
    ]),
  );
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

// The headless audits run the composition itself on a timeline; a short stretch exercises every measurement.
const AUDIT_FRAMES = fileURLToPath(
  new URL("../../src/filmkit/picture/frame-audit.mjs", import.meta.url),
);
const AUDIT_MOTION = fileURLToPath(
  new URL("../../src/filmkit/picture/motion-audit.mjs", import.meta.url),
);

test("the frame audit reports a stretch of the film, its label trace, its marks and its bounds", async () => {
  const film = await authoredTimeline("zh"),
    folder = await scratchFolder();
  const path = join(folder, "timeline.json"),
    trace = join(folder, "trace.tsv"),
    marks = join(folder, "marks.tsv"),
    bounds = join(folder, "bounds.json"),
    balance = join(folder, "balance.json");
  await writeFile(path, JSON.stringify(film));
  const at = film.segments[1].voice_start;
  const report = JSON.parse(
    execFileSync(
      process.execPath,
      [AUDIT_FRAMES, path, "0.5", "--from", String(at), "--to", String(at + 6)],
      {
        env: { ...process.env, TRACE: trace, MARKS: marks, BOUNDS: bounds, BALANCE: balance },
        encoding: "utf8",
      },
    ),
  );
  assert.deepEqual(report.errors, []);
  assert.ok(report.frames_checked > 0);
  // Thoughts whose picture stands off the content centre at a reviewers' instant, with the instant and both offsets.
  assert.ok(report.off_centre && typeof report.off_centre === "object");
  for (const rows of Object.values(report.off_centre))
    assert.ok(rows.every((row) => /^\d\d\.\d+ (two|late) -?\d+%\/-?\d+%$/.test(row)));
  // Containers that stood under half filled through more than a second of speech, with their kind, box, run and fill.
  assert.ok(report.underfilled_containers && typeof report.underfilled_containers === "object");
  for (const runs of Object.values(report.underfilled_containers))
    assert.ok(runs.every((run) => /^(frame|bracket) [\d,-]+ [\d.]+-[\d.]+ \d+%$/.test(run)));
  // Thoughts whose lit picture covers too little of the band, and names that repeat their caption or run past two lines.
  for (const key of ["thin_lit", "caption_echoes", "long_names", "sparse_runs"])
    assert.ok(report[key] && typeof report[key] === "object", key);
  // Runs of speech whose visible marks cover too little of the band, with their span and least cover.
  for (const runs of Object.values(report.sparse_runs))
    assert.ok(runs.every((run) => /^[\d.]+-[\d.]+ [\d.]+%$/.test(run)));
  for (const rows of Object.values(report.thin_lit))
    assert.ok(rows.every((row) => /^\d\d\.\d+ (two|late) [\d.]+%$/.test(row)));
  for (const rows of [...Object.values(report.caption_echoes), ...Object.values(report.long_names)])
    assert.ok(rows.every((row) => /@[\d.]+$/.test(row)));
  // Each thought instant in the stretch with its lit offsets and its share of the band.
  const instants = JSON.parse(await readFile(balance, "utf8"));
  assert.ok(
    instants.length > 0 &&
      instants.every(
        (v) => /^\d\d\.\d+$/.test(v.thought) && ["two", "late"].includes(v.at) && v.cover >= 0,
      ),
  );
  const rows = (await readFile(trace, "utf8"))
    .trim()
    .split("\n")
    .map((line) => line.split("\t"));
  assert.ok(
    rows.length > 0 && rows.every((row) => row.length === 5 && Number.isFinite(Number(row[2]))),
  );
  // Each firm mark of a voiced frame: its time, scene, box and whether a legible name stands at it.
  const marked = (await readFile(marks, "utf8"))
    .trim()
    .split("\n")
    .map((line) => line.split("\t"));
  assert.ok(
    marked.length > 0 &&
      marked.every(
        (row) =>
          row.length === 7 &&
          row.slice(2, 6).every((v) => Number.isInteger(Number(v))) &&
          ["0", "1"].includes(row[6]),
      ),
  );
  assert.ok(marked.some((row) => row[6] === "1"));
  // Each speaking scene's painted extent, within what the scene ever drew, and its mean share of the frame.
  const extents = JSON.parse(await readFile(bounds, "utf8"));
  assert.ok(Object.keys(extents).includes(film.segments[1].id));
  for (const { box, drawn, mean_frame_area } of Object.values(extents)) {
    assert.ok(box.every(Number.isInteger) && box[0] < box[2] && box[1] < box[3]);
    assert.ok(drawn[0] <= box[0] && drawn[1] <= box[1] && drawn[2] >= box[2] && drawn[3] >= box[3]);
    assert.ok(mean_frame_area > 0 && mean_frame_area <= 1);
  }
});

const segment = (x0, y0, x1, y1) => ({
  box: [Math.min(x0, x1), Math.min(y0, y1), Math.max(x0, x1), Math.max(y0, y1)],
  segs: [
    [
      [x0, y0],
      [x1, y1],
    ],
  ],
  kind: "open",
  frame: false,
});
const ringAt = (x, y, r) => {
  const points = Array.from({ length: 13 }, (_, k) => [
    x + r * Math.cos((k * Math.PI) / 6),
    y + r * Math.sin((k * Math.PI) / 6),
  ]);
  return {
    box: [x - r, y - r, x + r, y + r],
    segs: points.slice(1).map((point, k) => [points[k], point]),
    kind: "closed",
    frame: false,
  };
};
const seatRows = (rows) => rows.map((row) => [row.box.map(Math.round).join(","), row.named]);

test("each member repeated on a named rail waits for its own name", () => {
  const rail = segment(300, 500, 1300, 500),
    stations = [500, 800, 1100].map((x) => ringAt(x, 500, 20));
  const railName = { bounds: [300, 440, 420, 470] },
    firstName = { bounds: [470, 540, 530, 562] };
  const rows = seatMarks([rail, ...stations], [railName, firstName], [railName, firstName]);
  assert.deepEqual(seatRows(rows.filter((row) => row.member)), [
    ["480,480,520,520", true],
    ["780,480,820,520", false],
    ["1080,480,1120,520", false],
  ]);
  assert.ok(rows.some((row) => !row.member && row.named));
});

test("a repeated icon is one member, however many parts draw it", () => {
  const person = (x) => [ringAt(x, 480, 12), segment(x - 20, 500, x + 20, 500)],
    shapes = [...person(500), ...person(800)],
    first = { bounds: [470, 515, 530, 535] },
    second = { bounds: [770, 515, 830, 535] };
  assert.deepEqual(seatRows(seatMarks(shapes, [first, second], [first, second])), [
    ["480,468,520,500", true],
    ["780,468,820,500", true],
  ]);
  assert.deepEqual(seatRows(seatMarks(shapes, [first], [first])), [
    ["480,468,520,500", true],
    ["780,468,820,500", false],
  ]);
});

test("a station is one member: its disc's fill and outline, and the figure drawn on it", () => {
  const station = (x) => [
      { box: [x - 36, 424, x + 36, 496], segs: null, kind: "fill", frame: false },
      { ...ringAt(x, 460, 36), box: [x - 36, 424, x + 36, 496] },
      { box: [x - 11, 442, x + 11, 464], segs: null, kind: "fill", frame: false },
      segment(x - 16, 476, x + 16, 476),
    ],
    shapes = [...station(500), ...station(800)],
    names = [{ bounds: [450, 536, 550, 566] }, { bounds: [750, 536, 850, 566] }];
  assert.deepEqual(seatRows(seatMarks(shapes, names, names)), [
    ["464,424,536,496", true],
    ["764,424,836,496", true],
  ]);
});

test("nine repeated shapes are a texture, such as a gear's teeth, not a list", () => {
  const teeth = Array.from({ length: 9 }, (_, k) => segment(400 + k * 40, 500, 400 + k * 40, 524)),
    gear = { bounds: [400, 540, 520, 570] };
  assert.deepEqual(
    seatMarks(teeth, [gear], [gear]).filter((row) => row.member),
    [],
  );
});

test("a panel that holds only its corner marks waits whatever name stands beside it", () => {
  const record = { box: [700, 300, 1500, 700], segs: null, kind: "fill", frame: true },
    fold = segment(1478, 300, 1478, 322),
    beside = { bounds: [700, 710, 900, 735] };
  assert.deepEqual(seatRows(seatMarks([record, fold], [beside], [beside])), [
    ["700,300,1500,700", false],
  ]);
  const row = segment(760, 420, 1400, 420);
  assert.equal(seatMarks([record, fold, row], [beside], [beside])[0].named, true);
});

test("a frame holding only its title is filled by a sliver of its interior, and grows full as its members arrive", () => {
  const frame = { box: [100, 100, 500, 400], segs: null, kind: "fill", frame: true },
    title = { bounds: [120, 120, 380, 146] };
  const [only] = containerFill([frame], [title], [title]);
  assert.equal(only.kind, "frame");
  assert.deepEqual(only.box, [100, 100, 500, 400]);
  // The title covers 260 by 26 px of the 372 by 272 px interior inside the frame's edge band.
  assert.ok(Math.abs(only.fill - (260 * 26) / (372 * 272)) < 1e-9);
  const rows = { box: [130, 160, 470, 380], segs: null, kind: "fill", frame: false };
  assert.ok(containerFill([frame, rows], [title], [title])[0].fill > 0.5);
});

test("a bracket is filled by what stands on its open side along its spine", () => {
  // "[" with 30 px ticks pointing right and a 400 px spine.
  const bracket = {
    box: [170, 100, 200, 500],
    segs: [
      [
        [200, 100],
        [170, 100],
      ],
      [
        [170, 100],
        [170, 500],
      ],
      [
        [170, 500],
        [200, 500],
      ],
    ],
    kind: "open",
    frame: false,
  };
  const first = { bounds: [220, 120, 400, 160] },
    behind = { bounds: [20, 120, 150, 480] };
  const [one] = containerFill([bracket], [first, behind], [first, behind]);
  assert.equal(one.kind, "bracket");
  assert.ok(Math.abs(one.fill - 40 / 400) < 1e-9);
  const all = [first, { bounds: [220, 160, 400, 490] }];
  assert.ok(containerFill([bracket], all, all)[0].fill > 0.9);
  // A plain line is no container.
  assert.deepEqual(containerFill([segment(100, 100, 900, 100)], [first], [first]), []);
});

test("the motion audit summarises marks across frames and traces them to their scene", async () => {
  const film = await authoredTimeline("en"),
    folder = await scratchFolder();
  const path = join(folder, "timeline.json"),
    out = join(folder, "motion.json");
  await writeFile(path, JSON.stringify(film));
  const at = film.segments[2].voice_start;
  const summary = JSON.parse(
    execFileSync(
      process.execPath,
      [AUDIT_MOTION, path, "10", "--from", String(at), "--to", String(at + 8), "--out", out],
      { encoding: "utf8" },
    ),
  );
  assert.equal(summary.fps, 10);
  const report = JSON.parse(await readFile(out, "utf8"));
  assert.ok(Array.isArray(report.colour_snaps) && Array.isArray(report.still));
  assert.ok(
    report.colour_snaps.every((snap) => snap.origin === null || /^film\.js:\d+$/.test(snap.origin)),
  );
});

/* A composition that shows each artefact the motion audit looks for, at a known time while its voice runs: a word
 * that pops in and out, a word that jumps, a rule whose colour snaps, two cards that cross, a word resting faint, a
 * picture that empties and stands again, the pauses between those changes, a still end and a camera that reframes. */
const ARTEFACTS = `var P = { ground: "#0F1519", ink: "#ECE8DF", accent: "#7DB7D8" };
var ctx = document.getElementById("picture").getContext("2d");
var scenes = {};
var layout = [];
function text(value, x, y, alpha) {
  ctx.font = "40px Sample";
  ctx.textAlign = "left";
  ctx.textBaseline = "alphabetic";
  ctx.globalAlpha = alpha;
  ctx.fillStyle = P.ink;
  ctx.fillText(value, x, y);
  ctx.globalAlpha = 1;
  layout.push({ text: value, alpha: alpha, role: "label", scene: window.__sceneId });
}
function card(x, y, alpha) {
  if (alpha <= 0) return;
  ctx.globalAlpha = alpha;
  ctx.fillStyle = P.ink;
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(x + 120, y);
  ctx.lineTo(x + 120, y + 90);
  ctx.lineTo(x, y + 90);
  ctx.closePath();
  ctx.fill();
  ctx.globalAlpha = 1;
}
function rule(color) {
  ctx.strokeStyle = color;
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.moveTo(300, 800);
  ctx.lineTo(900, 800);
  ctx.stroke();
}
scenes["01"] = function (t) {
  if (t >= 9 && t < 9.6) return;
  text("Stand", 300, 300, 1);
  rule(t < 5 ? P.ink : P.accent);
  if (t >= 2 && t < 4) text("Pop", 700, 400, 1);
  if (t < 9) text("Jump", t < 3 ? 1000 : 1040, t < 3 ? 600 : 645, 1);
  if (t >= 6 && t < 7) {
    card(1200, 300, 1 - (t - 6));
    card(1220, 320, t - 6);
  }
  if (t >= 7.5 && t < 9) text("Faint", 400, 500, 0.15);
};
function cameraOf(segment, t) {
  return { k: t < 6 ? 1 : 1.1, ox: 0, oy: 0, ax: 960, ay: 540 };
}
window.renderFrame = function (t) {
  layout = [];
  window.__sceneId = "01";
  scenes["01"](t);
  window.__sceneId = null;
  window.__filmLayout = { time: t, texts: layout };
};
`;

test("the motion audit reports each artefact a composition shows, at its time and from its line", async () => {
  const root = await scratchFolder();
  await mkdir(join(root, "picture"));
  await writeFile(join(root, "picture/film.js"), ARTEFACTS);
  const lines = ARTEFACTS.split("\n"),
    lineOf = (code) => `film.js:${lines.findIndex((line) => line.includes(code)) + 1}`;
  const words = Array.from({ length: 70 }, (_, k) => ({
    text: "word",
    start: 0.5 + k * 0.2,
    end: 0.68 + k * 0.2,
  }));
  const path = join(root, "timeline.json"),
    out = join(root, "motion.json");
  await writeFile(
    path,
    JSON.stringify({
      language: "English",
      duration: 16,
      credits_duration: 1,
      captions: [],
      segments: [{ id: "01", start: 0, end: 15, voice_start: 0.5, voice_end: 14.5, words }],
    }),
  );
  execFileSync(process.execPath, [AUDIT_MOTION, path, "10", "--out", out], {
    cwd: root,
    encoding: "utf8",
  });
  const report = JSON.parse(await readFile(out, "utf8"));
  const when = (t) => +t.toFixed(2);
  // A firm mark that appears or leaves within one frame: the word at 2 s and 4 s, the card arriving whole and the
  // one leaving at 0.9 opacity, and the picture leaving at 9 s and standing again, each from the line that paints it.
  assert.deepEqual(
    report.pops.map((v) => [when(v.t), v.way, v.kind, v.text, v.origin]),
    [
      [2, "in", "text", "Pop", lineOf('"Pop"')],
      [4, "out", "text", "Pop", lineOf('"Pop"')],
      [6, "in", "fill", undefined, lineOf("card(1200")],
      [7, "out", "fill", undefined, lineOf("card(1220")],
      [9, "out", "text", "Stand", lineOf('"Stand"')],
      [9, "out", "stroke", undefined, lineOf("rule(t < 5")],
      [9, "out", "text", "Jump", lineOf('"Jump"')],
      [9.6, "in", "text", "Stand", lineOf('"Stand"')],
      [9.6, "in", "stroke", undefined, lineOf("rule(t < 5")],
    ],
  );
  // The word moving 60 px within one frame at 3 s, and the rule turning from ink to accent at 5 s.
  assert.deepEqual(
    report.jumps.map((v) => [v.t, v.text, v.distance, v.origin]),
    [[3, "Jump", 60, lineOf('"Jump"')]],
  );
  assert.deepEqual(
    report.colour_snaps.map((v) => [v.t, v.kind, v.from, v.to, v.origin]),
    [[5, "stroke", "#ECE8DF", "#7DB7D8", lineOf("rule(t < 5")]],
  );
  // The two cards are both half there from 6.2 s to 6.8 s, one fading where the other rises.
  assert.deepEqual(report.double_exposure, [
    {
      start: 6.2,
      end: 6.8,
      frames: 7,
      area: 7000,
      at_cut: false,
      origins: [`-${lineOf("card(1200")}`, `+${lineOf("card(1220")}`],
    },
  ]);
  // The word resting in the faint band for 1.5 s, in the colour it rests in.
  assert.deepEqual(report.faint_rests, [
    {
      scene: "01",
      kind: "text",
      text: "Faint",
      color: "#ECE8DF",
      start: 7.5,
      seconds: 1.5,
      low: 33,
      high: 33,
      origin: lineOf('"Faint"'),
    },
  ]);
  // The empty picture from 9 s while the voice runs, the pauses after the pop, the jump and the empty picture, each
  // between two changes, and the still end once the picture stands again.
  assert.deepEqual(report.dips, [{ start: 9, end: 9.5, scene: "01", floor: 0, seconds: 0.5 }]);
  assert.deepEqual(report.hitches, [
    { t: 2.1, gap: 0.9, scene: "01" },
    { t: 3.1, gap: 0.9, scene: "01" },
    { t: 9.1, gap: 0.5, scene: "01" },
  ]);
  assert.deepEqual(
    report.still.map((v) => [when(v.start), when(v.end), v.scene, v.seconds]),
    [[9.7, 14.4, "01", 4.7]],
  );
  // The camera's one reframe at 6 s, and the size every label is shown at.
  assert.deepEqual(report.camera["01"], { k: [1, 1.1], reframes: 1, moves: [[0, 6, 1.1]] });
  assert.deepEqual(report.type["01"], { p05: 40, median: 40, p95: 40, vs_film: 1 });
});

// A malformed invocation must stop with exit code 2 and the usage, never print a report of no frames.
const GEOMETRY = fileURLToPath(
  new URL("../../src/filmkit/picture/geometry-check.mjs", import.meta.url),
);
const invoke = (tool, args) => spawnSync(process.execPath, [tool, ...args], { encoding: "utf8" });
function assertRefused(tool, args, usage) {
  const result = invoke(tool, args);
  assert.equal(result.status, 2, `${args.join(" ")}: ${result.stderr}`);
  assert.equal(result.stdout, "", args.join(" "));
  assert.ok(result.stderr.includes(usage), args.join(" "));
}

test("the headless audits take their documented invocations, a step omitted before its flags included", async () => {
  const folder = await scratchFolder(),
    path = join(folder, "timeline.json");
  await writeFile(path, JSON.stringify(await authoredTimeline("zh")));
  const frames = JSON.parse(
    execFileSync(process.execPath, [AUDIT_FRAMES, path, "--from", "10", "--to", "12"], {
      encoding: "utf8",
    }),
  );
  assert.equal(frames.frames_checked, 8);
  const probe = JSON.parse(
    execFileSync(process.execPath, [AUDIT_FRAMES, path, "--at", "11"], { encoding: "utf8" }),
  );
  assert.ok(probe.texts.length > 0 && Array.isArray(probe.strokes));
  const motion = JSON.parse(
    execFileSync(process.execPath, [AUDIT_MOTION, path, "--from", "10", "--to", "11"], {
      encoding: "utf8",
    }),
  );
  assert.deepEqual([motion.fps, motion.frames, motion.range], [30, 30, [10, 11]]);
});

test("the headless audits refuse a malformed invocation", async () => {
  const folder = await scratchFolder(),
    path = join(folder, "timeline.json");
  await writeFile(path, JSON.stringify(await authoredTimeline("zh")));
  const frames = "Usage: python -m filmkit.tools frame-audit";
  for (const args of [
    [],
    [path, "0"],
    [path, "abc"],
    [path, "0.25", "extra"],
    [path, "0.25", "--step", "1"],
    [path, "--from"],
    [path, "--from", "10", "--to", "10"],
    [path, "--from", "", "--to", "12"],
    [path, "--at", "never"],
    [path, "--at", "11", "--from", "10"],
  ])
    assertRefused(AUDIT_FRAMES, args, frames);
  const motion = "Usage: python -m filmkit.tools motion-audit";
  for (const args of [
    [],
    [path, "0"],
    [path, "fast"],
    [path, "30", "--bogus"],
    [path, "30", "--from", "5", "--to", "4"],
    [path, "30", "--from", "1.02", "--to", "1.025"],
    [path, "30", "--out"],
  ])
    assertRefused(AUDIT_MOTION, args, motion);
});

test("the geometry check refuses a malformed invocation before opening a browser", () => {
  const usage = "Usage: python -m filmkit.tools geometry-check";
  for (const args of [
    [],
    ["stage"],
    ["stage", "receipt.json", "0"],
    ["stage", "r", "1.5"],
    ["--bogus"],
  ])
    assertRefused(GEOMETRY, args, usage);
});

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

test("a mark is lit as the reviewers' gray frame shows it, a thin stroke at its worst share of a cell", () => {
  const lit = litLevel({ ground: palette.ground });
  // A 2 px rail in the line colour can straddle two cells and stay below gray 48, so it never balances a picture;
  // at 3 px, or in the muted colour, it is lit wherever it falls.
  assert.equal(lit(palette.line, 1, strokeShare(2)), false);
  assert.equal(lit(palette.line, 1, strokeShare(3)), true);
  assert.equal(lit(palette.muted, 1, strokeShare(2)), true);
  // A panel fill is never lit; a 9 px dot in the accent colour is, unless it has faded.
  assert.equal(lit(palette.panel, 1, fillShare([0, 0, 400, 300])), false);
  assert.equal(lit(palette.accent, 1, fillShare([0, 0, 9, 9])), true);
  assert.equal(lit(palette.accent, 0.15, fillShare([0, 0, 9, 9])), false);
  // A style other than a colour lifts nothing.
  assert.equal(lit("rgba(255,255,255,1)", 1), false);
});

test("a picture's cover is its box's share of the content band", () => {
  // The band runs from 120 to 900 px over the full width; a box reaching past it counts only its part inside.
  assert.equal(bandCover([0, 120, 1920, 900]), 1);
  assert.ok(Math.abs(bandCover([0, 0, 960, 510]) - 0.25) < 1e-12);
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
    Object.defineProperty(CanvasRenderingContext2D.prototype, key, { get: () => inner[key] });
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
