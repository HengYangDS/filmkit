/** The engine's test entry for a film's own Node tests (design decision 16 of build-a-film-by-its-verbs).
 *
 * A film's tests import this module alone, found through `filmkit.api.TEST_ENTRY`, and run with the film's root as
 * their working folder, as the engine's audits run below their film; R3 reimplements it with the same exports.
 *
 * openComposition(code, timeline) opens the film's bundled composition, picture/film.js, on the headless runtime
 * (headless-composition.mjs) with the film's declared faces where FILMKIT_TEXT_METRICS names them, on the edition's
 * `timeline`. Its handle offers `render(t, onPaint)` and `evaluate(expression)`, which runs an expression in the
 * composition's own context, beside the runtime's other members. A timeline that names another edition is refused.
 *
 * openModules(code, timeline, entry) loads the film's own modules from `entry`, below the film's root, as the render
 * page loads them: the timeline on the window, a stand-in canvas and the film element in the document. It returns
 * `render(t, onPaint)`. The modules read the timeline of the page they load in, so a process opens one edition.
 *
 * derivedTimeline(code) is `filmkit.api.derived_timeline(code)`, run by the film's Python, so that the timeline has one
 * source. */
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

import {
  canvasStandIn,
  openComposition as openHeadless,
  readTextMetrics,
  recordPaint,
} from "./headless-composition.mjs";

/* The film's Python, as its environment holds the engine: uv's environment of the film, used as it stands. */
const PYTHON = ["run", "--frozen", "--offline", "--no-sync", "python", "-I", "-B", "-c"];

/* Run Python code with the film's engine and give what it prints, parsed as JSON. */
function fromPython(code, ...args) {
  const printed = execFileSync("uv", [...PYTHON, code, ...args], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "inherit"],
  });
  return JSON.parse(printed);
}

export function derivedTimeline(code) {
  return fromPython(
    "import json, sys; from filmkit import api; " +
      "print(json.dumps(api.derived_timeline(sys.argv[1]), ensure_ascii=False))",
    code,
  );
}

/* The edition's timeline: refused where it names another edition. */
function editionOf(code, timeline) {
  if (timeline.edition !== code)
    throw new Error(`The timeline is of the ${timeline.edition} edition, not of ${code}`);
  return timeline;
}

export function openComposition(code, timeline) {
  return openHeadless(editionOf(code, timeline), { faces: readTextMetrics() });
}

export async function openModules(code, timeline, entry) {
  let onPaint = null;
  const context = canvasStandIn((paint) => {
    if (!onPaint) return;
    onPaint(recordPaint(paint, globalThis.window));
  });
  const elements = { picture: { getContext: () => context }, film: { dataset: { width: "1920" } } };
  globalThis.window = { FILM: editionOf(code, timeline) };
  globalThis.document = { getElementById: (id) => elements[id] };
  await import(pathToFileURL(resolve(entry)).href);
  return {
    render(t, paints = () => {}) {
      onPaint = paints;
      try {
        globalThis.window.renderFrame(t);
      } finally {
        onPaint = null;
      }
      return globalThis.window.__filmLayout;
    },
  };
}
