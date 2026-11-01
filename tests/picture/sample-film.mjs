/** What the picture tests share: the sample film's folder, a timeline staged from its scripts, and scratch folders. */
import { after } from "node:test";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

// The headless runtime reads picture/film.js below the folder it runs in, as the audits run below their film.
export const SAMPLE = fileURLToPath(new URL("../../examples/sample-film/", import.meta.url));
process.chdir(SAMPLE);

// Each folder a test writes its inputs and outputs into is removed once the file's tests have run.
const folders = [];
after(() => Promise.all(folders.map((folder) => rm(folder, { recursive: true, force: true }))));
export async function scratchFolder() {
  const folder = await mkdtemp(join(tmpdir(), "filmkit-picture-"));
  folders.push(folder);
  return folder;
}

/* A timeline as staging builds it from a script: each word 0.2 s after the last, a chapter's first segment after a
 * longer pause, and one caption over each segment's voice. */
export async function authoredTimeline(code) {
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
