/** Run the composition headlessly in Node, as the staged document runs it, for the frame and motion audits.
 *
 * film.js runs in its own vm context on a canvas stand-in. Each stroke, fill and text it paints while the caller
 * renders a frame reaches the caller as one paint: its kind, the scene drawing it (film.js publishes window.__sceneId
 * around each scene), its opacity and colour, its line width, its dash pattern as the canvas holds it and whether it is
 * dashed, the scale of its transform, and its geometry twice over. `subs` is the path as screen subpaths, sampled the
 * way the real-browser check samples them (geometry-check.mjs); a text stands at its anchor. `points` are the drawing
 * points in the painter's own coordinates, as the motion audit identifies a mark across frames: an arc gives the
 * corners of its circle, a text the corners of its box, and `toScreen` maps them to the screen. A stroke whose path
 * holds a whole turn the renderer's browser may paint without ink (wholeTurnAtRisk) carries each such arc in `turns`,
 * its exact start and end angles and the line of film.js that drew it, which whole-turns.mjs draws in that browser. The
 * stand-in measures a text's width by the advances of the film's declared faces when it is given them
 * (readTextMetrics), and otherwise by an estimate; geometry-check.mjs measures real metrics. */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import vm from "node:vm";

/* The composition, below the root of the film, the folder an audit runs in. */
const COMPOSITION = "picture/film.js";

/** The timeline as staging hands it to the composition: the edition of its language and no render offset, unless
 * the timeline gives them. */
export function readTimeline(path) {
  const authored = JSON.parse(readFileSync(path, "utf8"));
  return {
    ...authored,
    edition: authored.edition ?? { Chinese: "zh", English: "en" }[authored.language],
    render_offset: authored.render_offset ?? 0,
  };
}

const fontSize = (font) => Number(/(\d+(?:\.\d+)?)px/.exec(font)?.[1] ?? 30);
/* The family a CSS font names first, after its size: "700 30px FilmLatin, sans-serif" names FilmLatin. */
const fontFamily = (font) =>
  /\d(?:\.\d+)?px(?:\/\S+)?\s+(.+)$/
    .exec(font)?.[1]
    .split(",")[0]
    .trim()
    .replace(/^(['"])(.*)\1$/, "$2") ?? null;
const spacingOf = (value) => Number(/(-?\d+(?:\.\d+)?)px/.exec(String(value))?.[1] ?? 0);
/* The estimate's share of the size for one character: a CJK character as wide as the size, a capital 0.66 of it and
 * any other character 0.54. */
const estimated = (ch) =>
  /[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]/u.test(ch) ? 1 : /[A-Z]/.test(ch) ? 0.66 : 0.54;

/** The advance widths of the film's declared faces (filmkit.picture.metrics), read from the file that
 * `FILMKIT_TEXT_METRICS` names, or null without one: per family, its default advance, its other advances and the
 * characters its character map holds, in em. */
export function readTextMetrics(path = process.env.FILMKIT_TEXT_METRICS) {
  if (!path) return null;
  const { faces } = JSON.parse(readFileSync(path, "utf8"));
  return Object.fromEntries(
    Object.entries(faces).map(([family, face]) => [
      family,
      { default: face.default, advances: face.advances, mapped: new Set(face.mapped) },
    ]),
  );
}

/* A text's metrics. In a face the table declares, the width is the sum of the characters' advances at the size, plus
 * the letter spacing for each character, as a canvas measures it; a character the face does not map, and any text in
 * a family the table does not hold, take the estimate. The box rises and falls from its baseline in proportion to the
 * size. */
function textMetrics(text, { font, textAlign, textBaseline, letterSpacing }, faces = null) {
  const size = fontSize(font),
    face = faces?.[fontFamily(font)] ?? null,
    chars = [...text];
  const width = face
    ? chars.reduce(
        (w, ch) =>
          w + size * (face.mapped.has(ch) ? (face.advances[ch] ?? face.default) : estimated(ch)),
        0,
      ) +
      spacingOf(letterSpacing) * chars.length
    : chars.reduce((w, ch) => w + size * estimated(ch), 0);
  const left = textAlign === "center" ? width / 2 : textAlign === "right" ? width : 0;
  const ascent = textBaseline === "top" ? 0 : textBaseline === "middle" ? size * 0.52 : size * 0.8;
  const descent =
    textBaseline === "top" ? size * 1.05 : textBaseline === "middle" ? size * 0.52 : size * 0.22;
  return {
    width,
    actualBoundingBoxLeft: left,
    actualBoundingBoxRight: width - left,
    actualBoundingBoxAscent: ascent,
    actualBoundingBoxDescent: descent,
  };
}

/* The drawing state a canvas saves and restores, as a fresh canvas starts it; film.js sets every property it uses. */
const STATE = {
  globalAlpha: 1,
  strokeStyle: "#000000",
  fillStyle: "#000000",
  lineWidth: 1,
  lineCap: "butt",
  lineJoin: "miter",
  font: "10px sans-serif",
  textAlign: "start",
  textBaseline: "alphabetic",
  letterSpacing: "0px",
};

/** The signed angle a canvas arc sweeps from a0 toward a1: clockwise unless anticlockwise, a whole turn once the
 * angles span one, and otherwise the difference brought into one turn, as the HTML canvas specification draws it. */
export function canvasSweep(a0, a1, anticlockwise = false) {
  const turn = 2 * Math.PI,
    delta = anticlockwise ? a0 - a1 : a1 - a0,
    sweep = delta >= turn ? turn : ((delta % turn) + turn) % turn;
  return anticlockwise ? -sweep : sweep;
}

/* A sweep counts as a whole turn from TURN_SHORT radians short of one, and a start as a whole number of turns within
 * TURN_START radians of one. */
const TURN_SHORT = 1e-5,
  TURN_START = 1e-6;

/** Whether the renderer's browser may paint no ink for arc(x, y, r, a0, a1, anticlockwise). Chrome Headless Shell
 * 152 computes a clockwise arc's end angle in single precision; through a whole turn or more from a start that is not
 * a whole number of turns, 64 of 4000 starts drew no ink for a whole turn and 13 of 1000 for every longer sweep, with
 * Metal and with SwiftShader alike. Starts at whole turns, anticlockwise arcs and ellipses from any start all drew.
 * Whether a given start and end paints only that browser tells, so whole-turns.mjs draws each one there. */
export function wholeTurnAtRisk(a0, a1, anticlockwise = false) {
  const turn = 2 * Math.PI,
    off = ((a0 % turn) + turn) % turn;
  return !anticlockwise && a1 - a0 >= turn - TURN_SHORT && Math.min(off, turn - off) > TURN_START;
}

/** The 2D context film.js draws on: exactly the members it uses, each refusing any other. `deliver` receives each
 * stroke, fill and text as a paint, called directly by the method painting it, so a paint can be traced into film.js.
 * fillRect lays the ground under each frame, which no audit counts as a mark, so it paints nothing. `turned()`, called
 * as an arc at risk (wholeTurnAtRisk) is drawn, names the line that drew it. */
export function canvasStandIn(deliver, faces = null, turned = () => null) {
  let m = [1, 0, 0, 1, 0, 0],
    state = { ...STATE, dash: [] };
  const stack = [];
  // The current path twice over: screen subpaths as sampled, and the drawing points in the painter's coordinates; and
  // its whole turns at risk.
  let subs = [],
    sub = null,
    last = [0, 0],
    points = [],
    turns = [];
  const tx = (x, y) => [m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]];
  const begin = (pts) => {
    sub = pts;
    subs.push(sub);
  };
  const extend = (pts) => {
    if (!sub) begin(pts);
    else sub.push(...pts);
  };
  const mul = (a, b) => [
    a[0] * b[0] + a[2] * b[1],
    a[1] * b[0] + a[3] * b[1],
    a[0] * b[2] + a[2] * b[3],
    a[1] * b[2] + a[3] * b[3],
    a[0] * b[4] + a[2] * b[5] + a[4],
    a[1] * b[4] + a[3] * b[5] + a[5],
  ];
  // An arc or ellipse is sampled every 7.5 degrees, at least four steps, along the sweep a canvas draws: clockwise
  // from the start angle unless anticlockwise, through less than one turn unless the angles span a whole one. So
  // arc(x, y, r, Math.PI, 0) draws the upper half, not the lower one that a straight interpolation would give.
  const sampled = (x, y, rx, ry, rotation, a0, a1, anticlockwise = false) => {
    const sweep = canvasSweep(a0, a1, anticlockwise),
      n = Math.max(4, Math.ceil(Math.abs(sweep) / (Math.PI / 24))),
      pts = [];
    for (let i = 0; i <= n; i++) {
      const a = a0 + (sweep * i) / n,
        ex = rx * Math.cos(a),
        ey = ry * Math.sin(a);
      pts.push(
        tx(
          x + ex * Math.cos(rotation) - ey * Math.sin(rotation),
          y + ex * Math.sin(rotation) + ey * Math.cos(rotation),
        ),
      );
    }
    return pts;
  };
  // A paint carries the state it was painted in and its geometry: `subs` and `points`, and a text's own fields.
  const paintOf = (kind, color, geometry) => {
    const [a, b, c, d, e, f] = m;
    return {
      kind,
      alpha: state.globalAlpha,
      color,
      lineWidth: state.lineWidth,
      dash: state.dash.slice(),
      dashed: state.dash.some((v) => v > 0),
      scale: Math.hypot(a, b),
      toScreen: ([x, y]) => [a * x + c * y + e, b * x + d * y + f],
      ...geometry,
    };
  };
  const path = () => ({ subs: subs.map((v) => v.slice()), points: points.slice() });
  const members = {
    setTransform(a, b, c, d, e, f) {
      m = [a, b, c, d, e, f];
    },
    getTransform: () => ({ a: m[0], b: m[1], c: m[2], d: m[3], e: m[4], f: m[5] }),
    translate(x, y) {
      m = mul(m, [1, 0, 0, 1, x, y]);
    },
    scale(x, y) {
      m = mul(m, [x, 0, 0, y, 0, 0]);
    },
    save() {
      stack.push([m, { ...state }]);
    },
    // As on a canvas, a restore without a saved state does nothing.
    restore() {
      if (stack.length) [m, state] = stack.pop();
    },
    setLineDash(segments) {
      // As on a canvas, a pattern with a negative or an infinite length is ignored and an odd one repeats.
      const list = [...segments].map(Number);
      if (list.some((v) => !(v >= 0 && Number.isFinite(v)))) return;
      state.dash = list.length % 2 ? [...list, ...list] : list;
    },
    measureText: (v) => textMetrics(v, state, faces),
    beginPath() {
      subs = [];
      sub = null;
      points = [];
      turns = [];
    },
    moveTo(x, y) {
      begin([tx(x, y)]);
      last = [x, y];
      points.push([x, y]);
    },
    lineTo(x, y) {
      extend([tx(x, y)]);
      last = [x, y];
      points.push([x, y]);
    },
    closePath() {
      if (sub?.length) sub.push(sub[0]);
    },
    arc(x, y, r, a0, a1, anticlockwise = false) {
      if (wholeTurnAtRisk(a0, a1, anticlockwise))
        turns.push({ start: a0, end: a1, sweep: a1 - a0, origin: turned() });
      extend(sampled(x, y, r, r, 0, a0, a1, anticlockwise));
      last = [x + r * Math.cos(a1), y + r * Math.sin(a1)];
      points.push([x - r, y - r], [x + r, y + r]);
    },
    ellipse(x, y, rx, ry, rotation, a0, a1, anticlockwise = false) {
      extend(sampled(x, y, rx, ry, rotation, a0, a1, anticlockwise));
      const ex = rx * Math.cos(a1),
        ey = ry * Math.sin(a1);
      last = [
        x + ex * Math.cos(rotation) - ey * Math.sin(rotation),
        y + ex * Math.sin(rotation) + ey * Math.cos(rotation),
      ];
      // Like an arc's circle, the whole ellipse spans the drawing points.
      const hx = Math.hypot(rx * Math.cos(rotation), ry * Math.sin(rotation)),
        hy = Math.hypot(rx * Math.sin(rotation), ry * Math.cos(rotation));
      points.push([x - hx, y - hy], [x + hx, y + hy]);
    },
    quadraticCurveTo(cx, cy, x, y) {
      const [x0, y0] = last,
        pts = [];
      for (let i = 1; i <= 12; i++) {
        const q = i / 12,
          u = 1 - q;
        pts.push(
          tx(u * u * x0 + 2 * u * q * cx + q * q * x, u * u * y0 + 2 * u * q * cy + q * q * y),
        );
      }
      extend(pts);
      last = [x, y];
      points.push([cx, cy], [x, y]);
    },
    roundRect(x, y, w, h) {
      begin([tx(x, y), tx(x + w, y), tx(x + w, y + h), tx(x, y + h), tx(x, y)]);
      sub = null;
      last = [x, y];
      points.push([x, y], [x + w, y + h]);
    },
    stroke() {
      const atRisk = turns.length ? { turns: turns.map((turn) => ({ ...turn })) } : {};
      deliver(paintOf("stroke", state.strokeStyle, { ...path(), ...atRisk }));
    },
    fill() {
      deliver(paintOf("fill", state.fillStyle, path()));
    },
    fillText(v, x, y) {
      const text = String(v),
        k = textMetrics(text, state, faces);
      deliver(
        paintOf("text", state.fillStyle, {
          subs: [[tx(x, y)]],
          points: [
            [x - k.actualBoundingBoxLeft, y - k.actualBoundingBoxAscent],
            [x + k.actualBoundingBoxRight, y + k.actualBoundingBoxDescent],
          ],
          text,
          size: fontSize(state.font),
        }),
      );
    },
    fillRect() {},
  };
  return new Proxy(members, {
    get(target, key) {
      if (Object.hasOwn(target, key)) return target[key];
      if (Object.hasOwn(STATE, key)) return state[key];
      // Symbols are how Node inspects a value; any other name is a member film.js does not use.
      if (typeof key === "symbol") return undefined;
      throw TypeError(`The headless canvas has no ${key}`);
    },
    set(target, key, value) {
      if (!Object.hasOwn(STATE, key))
        throw TypeError(`The headless canvas has no ${String(key)} to set`);
      state[key] = value;
      return true;
    },
  });
}

/** Load film.js on `timeline`, measuring text with the declared `faces` (readTextMetrics) when they are given.
 * Returns `palette`, the film's colours; `render(t, onPaint)`, which renders the frame at t, hands each of its paints
 * to `onPaint` and returns the layout film.js publishes; `framed`, whether film.js defines a camera `cameraOf`;
 * `camera(segment, t)`, that camera of a segment at t; `origin()`, called while a paint is handed over, the line of
 * film.js that drew it, as `film.js:<line>`, or null; `module(origin)`, the module of the bundle that holds such a
 * line, or null; and `declaredCuts()`, the stage cuts film.js has declared for each scene so far, in its own
 * `stageCuts` map of scene to the times of its cuts, as a Map of sets, empty for a composition that keeps none.
 *
 * The origin is the innermost line of a scene's own code on the call stack, rather than a helper that scenes share:
 * a line in a scene's body, `scenes["NN"] = function`, or in a module the bundle places in a folder below `scenes/`,
 * as the path comments esbuild writes before each module name it (`// picture/film/scenes/p02/hard.js`). A paint
 * that no scene's own code drew takes the innermost line of film.js that drew it. */
export function openComposition(timeline, { faces = null } = {}) {
  const composition = resolve(COMPOSITION),
    source = readFileSync(composition, "utf8");
  // The scene whose body each line of film.js lies in, and the module of the bundle that holds it.
  const sceneOfLine = [],
    moduleOfLine = [];
  let open = null,
    module = null;
  for (const line of source.split("\n")) {
    open = /^scenes\["(\d+)"\] = function/.exec(line)?.[1] ?? open;
    module = /^\/\/ (\S+\.m?js)$/.exec(line)?.[1] ?? module;
    sceneOfLine.push(open);
    moduleOfLine.push(module);
    if (line === "};") open = null;
  }
  const sceneCode = (n) =>
    sceneOfLine[n - 1] !== null || /(^|\/)scenes\/[^/]+\//.test(moduleOfLine[n - 1] ?? "");
  const window = { FILM: timeline };
  // Paints reach the caller only while it renders a frame, not while film.js paints its first frame on loading.
  let onPaint = null;
  function deliver(paint) {
    if (!onPaint) return;
    paint.scene = window.__sceneId ?? null;
    onPaint(paint);
  }
  // The line that drew an arc at risk: the innermost line of film.js below the stand-in's arc.
  function turned() {
    const limit = Error.stackTraceLimit,
      trace = {};
    Error.stackTraceLimit = Infinity;
    Error.captureStackTrace(trace, turned);
    Error.stackTraceLimit = limit;
    const line = /film\.js:(\d+):\d+/.exec(trace.stack)?.[1];
    return line ? `film.js:${line}` : null;
  }
  // The document holds the picture's canvas and the film element whose width sets the resolution, nothing else.
  const ctx = canvasStandIn(deliver, faces, turned);
  const elements = {
    picture: {
      getContext(type) {
        if (type !== "2d") throw TypeError(`The headless canvas has no ${type} context`);
        return ctx;
      },
    },
    film: { dataset: { width: "1920" } },
  };
  const context = vm.createContext({
    window,
    document: {
      getElementById(id) {
        if (!Object.hasOwn(elements, id)) throw TypeError(`The headless document has no #${id}`);
        return elements[id];
      },
    },
  });
  vm.runInContext(source, context, { filename: composition });
  const palette = Object.freeze({ ...vm.runInContext("P", context) });
  const framed = vm.runInContext('typeof cameraOf === "function"', context);
  let cameraOf;
  return {
    palette,
    framed,
    render(t, paints = () => {}) {
      onPaint = paints;
      try {
        window.renderFrame(t);
      } finally {
        onPaint = null;
      }
      return window.__filmLayout;
    },
    camera(segment, t) {
      cameraOf ??= vm.runInContext('typeof cameraOf === "function" ? cameraOf : null', context);
      if (!cameraOf) throw Error("The composition defines no cameraOf");
      return cameraOf(segment, t);
    },
    origin() {
      // The whole stack below the paint: V8 keeps ten frames, fewer than a helper nested in a scene may need.
      const limit = Error.stackTraceLimit,
        trace = {};
      Error.stackTraceLimit = Infinity;
      Error.captureStackTrace(trace, deliver);
      Error.stackTraceLimit = limit;
      const lines = [...trace.stack.matchAll(/film\.js:(\d+):\d+/g)].map((match) =>
        Number(match[1]),
      );
      const line = lines.find(sceneCode) ?? lines[0];
      return line === undefined ? null : `film.js:${line}`;
    },
    module(origin) {
      const line = Number(/^film\.js:(\d+)$/.exec(origin ?? "")?.[1]);
      return (line && moduleOfLine[line - 1]) || null;
    },
    declaredCuts() {
      // The map lives in the composition's realm, so it is read by its entries, not by its class.
      const cuts = vm.runInContext(
        'typeof stageCuts !== "undefined" && stageCuts && typeof stageCuts.entries === "function" ? stageCuts : null',
        context,
      );
      return new Map(cuts ? [...cuts.entries()].map(([scene, at]) => [scene, new Set(at)]) : []);
    },
  };
}
