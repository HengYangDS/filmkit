/** The engine's test entry for a film's tests (filmkit/picture/testing.mjs), on the sample film. */
import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";

import { SAMPLE } from "./sample-film.mjs";
import {
  derivedTimeline,
  openComposition,
  openModules,
} from "../../src/filmkit/picture/testing.mjs";

/* The sample's derived timeline as filmkit.api gives it to Python. */
function apiTimeline(code) {
  const printed = execFileSync(
    "uv",
    [
      "run",
      "--frozen",
      "--offline",
      "--no-sync",
      "python",
      "-I",
      "-B",
      "-c",
      "import json, sys; from filmkit import api; print(json.dumps(api.derived_timeline(sys.argv[1])))",
      code,
    ],
    { cwd: SAMPLE, encoding: "utf8", stdio: ["ignore", "pipe", "inherit"] },
  );
  return JSON.parse(printed);
}

test("the Chinese composition opens on its derived timeline, which is filmkit.api's", () => {
  const timeline = derivedTimeline("zh");
  assert.deepEqual(timeline, apiTimeline("zh"));
  const film = openComposition("zh", timeline);
  const voice = timeline.segments[0].voice_start;
  const texts = [];
  film.render(voice + 0.5, (paint) => paint.kind === "text" && texts.push(paint.text));
  assert.ok(texts.length > 0);
  // An expression runs in the composition's own context.
  assert.equal(film.evaluate("typeof drawAt"), "function");
  assert.deepEqual({ ...film.evaluate("P") }, { ...film.palette });
  // A timeline of another edition is refused.
  assert.throws(() => openComposition("en", timeline), /of the zh edition, not of en/);
});

test("the sample's own modules render through openModules as the page loads them", async () => {
  const timeline = derivedTimeline("zh");
  const modules = await openModules("zh", timeline, "picture/film.js");
  const texts = [];
  const layout = modules.render(timeline.segments[0].voice_start + 0.5, (paint) =>
    texts.push(paint.kind),
  );
  assert.ok(texts.length > 0);
  assert.ok(Array.isArray(layout.texts));
});
