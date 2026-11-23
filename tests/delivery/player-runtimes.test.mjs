/** Exercise that each edition's player is read against its own edition's runtime: the binding names each edition's
 * runtime by its code, and the films of each edition are played and sought against their own. */
import { SAMPLE_FILM } from "./film.mjs";
import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { seekPoints } from "../../src/filmkit/delivery/player-check.mjs";
import { delivered } from "../../src/filmkit/delivery/player-read.mjs";
import { playbackProblems } from "../../src/filmkit/delivery/player-verdict.mjs";

/* A PNG of one pixel, which an edition's read decodes as the delivery's cover. */
const COVER = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
  "base64",
);
/* A film as the player shows it, which lasts `duration` seconds and was sought at the points of a runtime of `at`
 * seconds, its own by default. */
const played = (duration, at = duration) => ({
  file: "f.mp4",
  dimensions: [1920, 1080],
  duration,
  width: 1920,
  height: 1080,
  error: null,
  seek_checks: seekPoints(at).map((target) => ({ target, error: null, decoded_frames: 31 })),
});

test("each edition's player is read against its own edition's runtime", async () => {
  // The editions last 1636 s and 1476 s; each one's films are played and sought against its own.
  const root = await mkdtemp(join(tmpdir(), "player-runtimes-"));
  try {
    for (const code of ["zh", "en"]) {
      await mkdir(join(root, code));
      await writeFile(join(root, code, "chapters.json"), JSON.stringify({ chapters: [] }));
      await writeFile(join(root, code, `sample-reel-${code}.vtt`), "WEBVTT\n");
      await writeFile(join(root, code, `sample-reel-${code}.srt`), "");
      await writeFile(join(root, code, "sample-reel-cover.png"), COVER);
    }
    const binding = {
      film: SAMPLE_FILM,
      members: [],
    };
    const zh = await delivered(root, "zh", binding),
      en = await delivered(root, "en", binding);
    assert.deepEqual([zh.duration, en.duration], [1636, 1476]);
    assert.deepEqual(seekPoints(zh.duration), [2, 818, 1632]);
    // A Chinese film that lasts the English edition's runtime does not play as delivered.
    assert.deepEqual(playbackProblems(played(1476, 1636), zh.duration), [
      "f.mp4 lasts 1476 s, not 1636 s",
    ]);
    assert.deepEqual(playbackProblems(played(1476), en.duration), []);
    // A Chinese film played at the English edition's runtime is sought at the wrong points, which the verdict names:
    // the read plays each edition against the runtime its binding names for it.
    assert.deepEqual(playbackProblems(played(1636, 1476), zh.duration), [
      "f.mp4 was sought at 2, 738, 1472 s, not at 2, 818, 1632 s, the points of its 1636 s",
    ]);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
