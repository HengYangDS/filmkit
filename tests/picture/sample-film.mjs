/** What the picture tests share: the sample film's folder, a timeline staged from its scripts, and scratch folders. */
import { after } from "node:test";
import { execFileSync } from "node:child_process";
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

/* The engine's own placing of the anchors a timeline of other words takes from them (filmkit.api.place_anchors), run
 * by the engine's Python: the marks are read and resolved there alone. Each edition's placed timeline is kept for the
 * file's tests. */
const PLACE = [
  "run",
  "--frozen",
  "--offline",
  "--no-sync",
  "python",
  "-I",
  "-B",
  "-c",
  "import json, sys; from filmkit import api; " +
    "print(json.dumps(api.place_anchors(json.load(sys.stdin), sys.argv[1]), ensure_ascii=False))",
];
const placed = new Map();
async function withAnchors(timeline, code) {
  if (!placed.has(code)) {
    const printed = execFileSync("uv", [...PLACE, code], {
      cwd: SAMPLE,
      input: JSON.stringify(timeline),
      encoding: "utf8",
      stdio: ["pipe", "pipe", "inherit"],
    });
    placed.set(code, printed);
  }
  return JSON.parse(placed.get(code));
}

/* A timeline as staging builds it from a script: each word 0.2 s after the last, a chapter's first segment after a
 * longer pause, one caption over each segment's voice, the credits the film's declaration states, and each segment's
 * anchors on its words, as the engine places them, with the author, the frame rate and each segment's chapter values
 * that the engine derives for every timeline. */
export async function authoredTimeline(code) {
  const script = JSON.parse(
    await readFile(
      join(SAMPLE, code === "zh" ? "content/zh/film-script.json" : "content/en/film-script.json"),
      "utf8",
    ),
  );
  const declaration = await readFile(join(SAMPLE, "content/film.toml"), "utf8");
  const credits = Number(declaration.match(/^credits_duration = (\d+)$/m)[1]);
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
    segment.end = segments[index + 1]?.start ?? duration - credits;
  });
  const captions = segments.map((segment) => ({
    start: segment.voice_start,
    end: segment.voice_end,
    text: segment.words
      .slice(0, 8)
      .map((v) => v.text)
      .join(code === "zh" ? "" : " "),
  }));
  const timeline = {
    ...script,
    segments,
    captions,
    duration,
    credits_duration: credits,
    edition: code,
    render_offset: 0,
  };
  return withAnchors(timeline, code);
}
