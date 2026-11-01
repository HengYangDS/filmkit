/** Inspect painted Canvas labels and shapes with the real browser at native output frames. */
import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { parseArgs } from "node:util";

import { launchBrowser } from "./headless-browser.mjs";
import { analysis } from "./rules/frame.mjs";
import { inkLevel, readingLoad } from "./rules/ink.mjs";
import { faintLabels, listTracker, nameRules } from "./rules/names.mjs";

/** Page instrumentation: record every painted path and fill in logical frame coordinates. */
export function instrument() {
  const proto = CanvasRenderingContext2D.prototype;
  const state = new WeakMap();
  const shapes = (window.__paintedShapes = []);
  window.__paintedText = [];
  let seq = 0;
  const scale = () => Number(document.getElementById("film").dataset.width) / 1920;
  const of = (ctx) => {
    if (!state.has(ctx)) state.set(ctx, { subs: [], sub: null, last: [0, 0] });
    return state.get(ctx);
  };
  const point = (ctx, x, y) => {
    const m = ctx.getTransform(),
      s = scale();
    return [(m.a * x + m.c * y + m.e) / s, (m.b * x + m.d * y + m.f) / s];
  };
  const extend = (ctx, pts) => {
    const p = of(ctx);
    if (!p.sub) {
      p.sub = pts;
      p.subs.push(p.sub);
    } else p.sub.push(...pts);
  };
  const wrap = (name, record) => {
    const original = proto[name];
    proto[name] = function (...args) {
      record(this, ...args);
      return original.apply(this, args);
    };
  };
  window.__resetPaint = () => {
    shapes.length = 0;
    window.__paintedText.length = 0;
    seq = 0;
  };
  wrap("beginPath", (ctx) => {
    const p = of(ctx);
    p.subs = [];
    p.sub = null;
  });
  wrap("moveTo", (ctx, x, y) => {
    const p = of(ctx);
    p.sub = [point(ctx, x, y)];
    p.subs.push(p.sub);
    p.last = [x, y];
  });
  wrap("lineTo", (ctx, x, y) => {
    extend(ctx, [point(ctx, x, y)]);
    of(ctx).last = [x, y];
  });
  wrap("closePath", (ctx) => {
    const p = of(ctx);
    if (p.sub?.length) p.sub.push(p.sub[0]);
  });
  // The page code is serialised whole, so it carries its own copy of the canvas sweep that headless-composition.mjs
  // exports as canvasSweep: clockwise unless anticlockwise, a whole turn once the angles span one.
  const arcPoints = (ctx, x, y, rx, ry, rotation, a0, a1, anticlockwise = false) => {
    const turn = 2 * Math.PI,
      delta = anticlockwise ? a0 - a1 : a1 - a0,
      span = delta >= turn ? turn : ((delta % turn) + turn) % turn,
      sweep = anticlockwise ? -span : span,
      n = Math.max(4, Math.ceil(Math.abs(sweep) / (Math.PI / 24))),
      pts = [];
    for (let i = 0; i <= n; i++) {
      const a = a0 + (sweep * i) / n,
        ex = rx * Math.cos(a),
        ey = ry * Math.sin(a);
      pts.push(
        point(
          ctx,
          x + ex * Math.cos(rotation) - ey * Math.sin(rotation),
          y + ex * Math.sin(rotation) + ey * Math.cos(rotation),
        ),
      );
    }
    return pts;
  };
  wrap("arc", (ctx, x, y, r, a0, a1, anticlockwise) => {
    extend(ctx, arcPoints(ctx, x, y, r, r, 0, a0, a1, anticlockwise));
    of(ctx).last = [x + r * Math.cos(a1), y + r * Math.sin(a1)];
  });
  // As on a canvas, the path continues from where the ellipse ends.
  wrap("ellipse", (ctx, x, y, rx, ry, rotation, a0, a1, anticlockwise) => {
    extend(ctx, arcPoints(ctx, x, y, rx, ry, rotation, a0, a1, anticlockwise));
    const ex = rx * Math.cos(a1),
      ey = ry * Math.sin(a1);
    of(ctx).last = [
      x + ex * Math.cos(rotation) - ey * Math.sin(rotation),
      y + ex * Math.sin(rotation) + ey * Math.cos(rotation),
    ];
  });
  wrap("quadraticCurveTo", (ctx, cx, cy, x, y) => {
    const [x0, y0] = of(ctx).last,
      pts = [];
    for (let i = 1; i <= 12; i++) {
      const q = i / 12,
        u = 1 - q;
      pts.push(
        point(
          ctx,
          u * u * x0 + 2 * u * q * cx + q * q * x,
          u * u * y0 + 2 * u * q * cy + q * q * y,
        ),
      );
    }
    extend(ctx, pts);
    of(ctx).last = [x, y];
  });
  wrap("roundRect", (ctx, x, y, w, h) => {
    const p = of(ctx);
    p.subs.push([
      point(ctx, x, y),
      point(ctx, x + w, y),
      point(ctx, x + w, y + h),
      point(ctx, x, y + h),
      point(ctx, x, y),
    ]);
    p.sub = null;
    p.last = [x, y];
  });
  wrap("stroke", (ctx) => {
    const m = ctx.getTransform();
    shapes.push({
      kind: "stroke",
      seq: ++seq,
      alpha: ctx.globalAlpha,
      width: (ctx.lineWidth * Math.hypot(m.a, m.b)) / scale(),
      subs: of(ctx).subs.map((v) => v.slice()),
      color: typeof ctx.strokeStyle === "string" ? ctx.strokeStyle : null,
      scene: window.__sceneId ?? null,
    });
  });
  wrap("fill", (ctx) => {
    const pts = of(ctx).subs.flat();
    seq++;
    if (pts.length)
      shapes.push({
        kind: "fill",
        seq,
        alpha: ctx.globalAlpha,
        box: [
          Math.min(...pts.map((v) => v[0])),
          Math.min(...pts.map((v) => v[1])),
          Math.max(...pts.map((v) => v[0])),
          Math.max(...pts.map((v) => v[1])),
        ],
        color: typeof ctx.fillStyle === "string" ? ctx.fillStyle : null,
        scene: window.__sceneId ?? null,
      });
  });
  wrap("fillText", () => {
    window.__paintedText.push(++seq);
  });
}

/** The page program: render every `every`-th of `frames` frames at `rate` and collect each finding once, with the
 * first frame it was seen and how many frames show it. `rules` are the sources of the serialisable rules and
 * `palette` the film's colours, from which the page derives its measures. */
export function inspectFilm(rules, palette, frames, every, rate) {
  const make = (name) => new Function(`return (${rules[name]})`)();
  const contrast = make("readingLoad")(palette),
    inspectFrame = make("analysis")(make("inkLevel")(palette)),
    nameFindings = make("nameRules")(),
    lists = make("listTracker")(),
    faintSeen = make("faintLabels")();
  const seen = new Map(),
    errors = new Map();
  // Speech whose brightest scene mark stays below 90 levels for half a second shows only faint placeholders.
  let dimSpeech = null;
  // A receipt keeps each finding's kind, scene and text; the evidence a finding carries is for the frame audit.
  const add = ({ kind, scene, text }, t) => {
    const key = `${kind}:${scene}:${text}`;
    const entry = seen.get(key) ?? { kind, scene, text, first: t, frames: 0 };
    entry.frames++;
    seen.set(key, entry);
  };
  let checked = 0;
  for (let frame = 0; frame < frames; frame += every) {
    const t = frame / rate,
      filmTime = t + (window.FILM.render_offset || 0);
    window.__resetPaint();
    try {
      window.renderFrame(t);
    } catch (error) {
      if (!errors.has(String(error))) errors.set(String(error), t);
      continue;
    }
    checked++;
    const texts = window.__filmLayout.texts.map((v, i) => ({
      ...v,
      seq: window.__paintedText[i],
    }));
    // A frame must paint while a voice speaks, and in a pause within a chapter once the next scene has begun.
    const segments = window.FILM.segments,
      at = segments.findLastIndex((v) => v.start <= filmTime),
      shown = segments[at];
    const speaking = segments.find((v) => v.voice_start <= filmTime && filmTime < v.voice_end);
    const between =
      at > 0 && segments[at - 1].chapter === shown.chapter && filmTime < shown.voice_start;
    // The checked frame that carries a chapter's first word: its first scene must already stand.
    const firstWord =
      at > 0 &&
      segments[at - 1].chapter !== shown.chapter &&
      shown.voice_start <= filmTime &&
      filmTime < shown.voice_start + every / rate;
    const context = {
      mustPaint: Boolean(speaking) || between,
      firstWord,
      scene: (speaking ?? shown)?.id ?? null,
    };
    const found = inspectFrame(texts, window.__paintedShapes, context);
    for (const finding of found) add(finding, t);
    if (speaking && found.brightest < 90) dimSpeech ??= { start: t, scene: speaking.id };
    else if (dimSpeech) {
      if (t - dimSpeech.start >= 0.5)
        add({ kind: "faint_during_speech", scene: dimSpeech.scene, text: "" }, dimSpeech.start);
      dimSpeech = null;
    }
    // Names: only scene words count; marks such as "?" or a bare value are seen rather than read.
    const words = texts.filter((v) => v.scene && v.role === "label" && /\p{L}/u.test(v.text));
    if (speaking) for (const finding of nameFindings(words, contrast)) add(finding, t);
    lists.see(words, t, contrast);
    for (const run of faintSeen(words, t, contrast))
      add({ kind: "faint_label", scene: run.scene, text: run.text }, run.start);
  }
  for (const finding of lists.findings()) add(finding, 0);
  return {
    checked,
    findings: [...seen.values()],
    errors: [...errors].map(([message, t]) => ({ message, t })),
  };
}

const RULES = { inkLevel, readingLoad, analysis, nameRules, listTracker, faintLabels };

export async function inspectWorkspace(workspace, { step = 2 } = {}) {
  const entry = resolve(workspace, "index.html");
  const source = await readFile(entry, "utf8");
  const attribute = (name) => Number(source.match(new RegExp(`data-${name}="([0-9.]+)"`))?.[1]);
  const [width, height, duration, fps] = ["width", "height", "duration", "fps"].map(attribute);
  if (![width, height, duration, fps].every(Number.isFinite))
    throw Error("Workspace does not declare its frame contract");
  const browser = await launchBrowser({
    args: ["--allow-file-access-from-files", "--no-sandbox"],
    defaultViewport: { width, height, deviceScaleFactor: 1 },
  });
  try {
    const page = await browser.newPage();
    await page.evaluateOnNewDocument(instrument);
    await page.goto(pathToFileURL(entry).href, { waitUntil: "load", timeout: 45000 });
    await page.evaluate(() => window.__filmReady);
    const result = await page.evaluate(
      inspectFilm,
      Object.fromEntries(Object.entries(RULES).map(([name, rule]) => [name, rule.toString()])),
      // The film's own palette, read where the film runs.
      await page.evaluate("P"),
      Math.round(duration * fps),
      step,
      fps,
    );
    return {
      width,
      height,
      duration,
      fps,
      step_frames: step,
      browser: await browser.version(),
      index_sha256: createHash("sha256").update(source).digest("hex"),
      ...result,
    };
  } finally {
    await browser.close();
  }
}

if (import.meta.main) {
  const USAGE =
    "Usage: python -m filmkit.tools geometry-check <workspace> <receipt.json> [step-frames]";
  // A malformed invocation stops before the browser opens, so it can never write a passing receipt.
  const refuse = (problem) => {
    console.error(`${problem}\n${USAGE}`);
    process.exit(2);
  };
  let positionals = [];
  try {
    ({ positionals } = parseArgs({ allowPositionals: true }));
  } catch (error) {
    refuse(error.message);
  }
  const [workspace, receipt, every = "2"] = positionals;
  if (positionals.length < 2 || positionals.length > 3)
    refuse("Expected one workspace, one receipt and at most one step");
  const step = Number(every);
  if (!Number.isInteger(step) || step < 1)
    refuse(`The step is not a positive whole number of frames: ${every}`);
  const report = await inspectWorkspace(workspace, { step });
  const passed = report.errors.length === 0 && report.findings.length === 0;
  await writeFile(
    receipt,
    JSON.stringify(
      { format: "picture-geometry", workspace: resolve(workspace), passed, ...report },
      null,
      2,
    ) + "\n",
  );
  console.log(
    JSON.stringify({
      passed,
      frames_checked: report.checked,
      findings: report.findings.length,
      errors: report.errors.length,
    }),
  );
  process.exitCode = passed ? 0 : 1;
}
