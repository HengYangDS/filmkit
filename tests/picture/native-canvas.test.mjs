/** Exercise the engine's renderer: how a film is divided into spans, the encoder's arguments, and real renders of the
 * sample film's composition in one process and in several: what they draw, state and write, and how they fail. The
 * tests that render run the host's FFmpeg and are skipped, by name, where it is not on PATH. */
import test from "node:test";
import assert from "node:assert/strict";
import { execFile, execFileSync, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { chmod, cp, mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

import { encoderArguments, planSpans } from "../../src/filmkit/picture/native-canvas.mjs";
import { authoredTimeline, SAMPLE, scratchFolder } from "./sample-film.mjs";

const run = promisify(execFile);
const MODULE = fileURLToPath(
  new URL("../../src/filmkit/picture/native-canvas.mjs", import.meta.url),
);
// The pictures' encoding as the engine's command gives it at 30 frames a second with a keyframe every 15.
const ENCODER = [
  ...["-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-g", "15", "-keyint_min", "15"],
  ...["-sc_threshold", "0", "-bf", "0", "-pix_fmt", "yuv420p"],
];
// The sample film's faces as a stage record names them.
const FACES = [
  { family: "Sample", path: "fonts/noto-sans-cjk-sc-subset-regular.otf" },
  { family: "SampleBold", path: "fonts/noto-sans-cjk-sc-subset-bold.otf" },
  { family: "SampleLatin", path: "fonts/ibm-plex-sans-regular.ttf" },
  { family: "SampleLatinBold", path: "fonts/ibm-plex-sans-bold.ttf" },
];
const found = (tool) => spawnSync(tool, ["-version"], { stdio: "ignore" }).status === 0;
// A render needs the host's FFmpeg and FFprobe, which the locked toolchain does not supply.
const rendering = {
  skip: found("ffmpeg") && found("ffprobe") ? false : "the host FFmpeg is not on PATH",
};

test("a film is divided into contiguous spans of whole groups, the longer first", () => {
  assert.deepEqual(planSpans(3600, 120, 4), [
    [0, 960],
    [960, 1920],
    [1920, 2760],
    [2760, 3600],
  ]);
  assert.deepEqual(planSpans(600, 20, 1), [[0, 600]]);
  // No more spans than the film has groups, and a last group that is not whole ends the film.
  assert.deepEqual(planSpans(240, 120, 8), [
    [0, 120],
    [120, 240],
  ]);
  assert.deepEqual(planSpans(250, 120, 2), [
    [0, 240],
    [240, 250],
  ]);
});

test("the encoder takes raw frames, converts them to BT.709 and encodes by the options it is given", () => {
  const settings = { width: 3840, height: 2160, fps: 60, encoder: ENCODER, output: "film.mp4" };
  const whole = encoderArguments({ ...settings, threads: null, faststart: true });
  const flag = (args, name) => args[args.indexOf(name) + 1];
  assert.deepEqual(
    ["-f", "-pix_fmt", "-s", "-r", "-i"].map((name) => flag(whole, name)),
    ["rawvideo", "rgba", "3840x2160", "60", "-"],
  );
  // The conversion states the range, the matrix, the chroma, the primaries and the transfer on every frame.
  assert.equal(
    flag(whole, "-vf"),
    "scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709",
  );
  // The encoding is the one given, whole and in its order, after the conversion; the module holds none of its own.
  const at = whole.indexOf("-c:v");
  assert.deepEqual(whole.slice(at, at + ENCODER.length), ENCODER);
  assert.ok(whole.indexOf("-vf") < at && !whole.includes("-color_primaries"));
  assert.ok(
    !whole.includes("-threads") && whole.includes("+faststart") && whole.at(-1) === "film.mp4",
  );
  // A span of several has its own thread count and is not finished for streaming: the join is.
  const span = encoderArguments({ ...settings, threads: 2, faststart: false });
  assert.ok(flag(span, "-threads") === "2" && !span.includes("+faststart"));
});

/* A stage as the engine writes it for the renderer, of the sample film's composition and an authored timeline: two
 * seconds at 1920x1080, with the record's faces and language. `record` changes the record, `script` the composition. */
async function stage(code, { record = {}, script = null } = {}) {
  const folder = join(await scratchFolder(), "stage");
  await mkdir(join(folder, "fonts"), { recursive: true });
  await cp(join(SAMPLE, "picture/film.js"), join(folder, "film.js"));
  if (script !== null) await writeFile(join(folder, "film.js"), script);
  // A stage holds the declared fonts and nothing beside them.
  for (const { path } of FACES) await cp(join(SAMPLE, "assets", path), join(folder, path));
  await writeFile(join(folder, "film.json"), JSON.stringify(await authoredTimeline(code)));
  const language = code === "en" ? "en" : "zh-CN";
  const whole = { duration: 2, fps: 30, width: 1920, height: 1080, edition: code, language };
  await writeFile(
    join(folder, "stage.json"),
    JSON.stringify({ ...whole, faces: FACES, ...record }),
  );
  return folder;
}

const settings = (output, ...more) => [
  ...["--output", output, "--fps", "30", "--group", "15"],
  ...["--encoder", JSON.stringify(ENCODER), "--text-renderer", "system", ...more],
];

async function render(folder, name, spans) {
  const output = join(folder, "..", `${name}.mp4`);
  const { stdout, stderr } = await run(process.execPath, [
    ...[MODULE, "render", folder],
    ...settings(output, "--spans", String(spans)),
  ]);
  const probe = ["-v", "error", "-select_streams", "v:0", "-of", "csv=p=0"];
  const packets = (await run("ffprobe", [...probe, "-show_entries", "packet=flags", output])).stdout
    .trim()
    .split("\n");
  const keyframes = packets.flatMap((flags, index) => (flags.startsWith("K") ? [index] : []));
  return { report: JSON.parse(stdout), stderr, frames: packets.length, keyframes, output };
}

test(
  "one process and three spans draw the same frames and write the same keyframes",
  rendering,
  async () => {
    const folder = await stage("zh");
    const whole = await render(folder, "whole", 1),
      joined = await render(folder, "joined", 3);
    assert.deepEqual([whole.report.frames, whole.report.spans, whole.frames], [60, 1, 60]);
    assert.deepEqual([joined.report.frames, joined.report.spans, joined.frames], [60, 3, 60]);
    assert.match(whole.report.drawn_sha256, /^[0-9a-f]{64}$/);
    assert.equal(joined.report.drawn_sha256, whole.report.drawn_sha256);
    assert.deepEqual(whole.keyframes, [0, 15, 30, 45]);
    assert.deepEqual(joined.keyframes, [0, 15, 30, 45]);
    // Each report states what its drawing processes ran: the text renderer, and the native library by the path it
    // was loaded from, its SHA-256 and the package that holds it. The spans state the same as one process.
    const library = whole.report.binary;
    assert.equal(whole.report.text_renderer, "system");
    assert.match(library.package, /^@napi-rs\/canvas-/);
    assert.equal(dirname(library.path).endsWith(library.package), true);
    assert.equal(
      library.sha256,
      createHash("sha256")
        .update(await readFile(library.path))
        .digest("hex"),
    );
    assert.deepEqual(joined.report.binary, library);
    assert.equal(joined.report.text_renderer, "system");
    // A render that passes writes no line at FFmpeg's error level: not the one about its input's size either.
    assert.equal(whole.stderr + joined.stderr, "");
    // The spans' folder is removed once they are joined.
    assert.deepEqual((await readdir(join(folder, ".."))).sort(), [
      "joined.mp4",
      "stage",
      "whole.mp4",
    ]);
    // The encoded picture is 4:2:0 in limited range and states BT.709 as its matrix, primaries and transfer.
    const entries = "stream=pix_fmt,color_range,color_space,color_primaries,color_transfer";
    const probed = await run("ffprobe", [
      ...["-v", "error", "-select_streams", "v:0", "-show_entries", entries],
      ...["-of", "default=nw=1:nk=1", whole.output],
    ]);
    assert.deepEqual(probed.stdout.trim().split("\n"), [
      "yuv420p",
      "tv",
      "bt709",
      "bt709",
      "bt709",
    ]);
  },
);

test("the English edition draws other frames than the Chinese one", rendering, async () => {
  const zh = await render(await stage("zh"), "zh", 1),
    en = await render(await stage("en"), "en", 1);
  assert.notEqual(zh.report.drawn_sha256, en.report.drawn_sha256);
});

test("a known colour is encoded as BT.709 in limited range", rendering, async () => {
  const script = `window.renderFrame = () => {
    const picture = document.getElementById("picture").getContext("2d");
    picture.fillStyle = "#ff0000";
    picture.fillRect(0, 0, 1920, 1080);
  };`;
  const { output } = await render(await stage("zh", { script }), "red", 1);
  // The first frame's first luma sample and the first sample of each chroma plane: red is (63, 102, 240).
  const raw = [
    "-v",
    "error",
    "-i",
    output,
    "-frames:v",
    "1",
    "-f",
    "rawvideo",
    "-pix_fmt",
    "yuv420p",
    "-",
  ];
  const frame = execFileSync("ffmpeg", raw, { maxBuffer: 1 << 23 });
  const [luma, blue, red] = [0, 1920 * 1080, 1920 * 1080 + 960 * 540].map((at) => frame[at]);
  assert.ok(Math.abs(luma - 63) <= 2 && Math.abs(blue - 102) <= 2 && Math.abs(red - 240) <= 2);
});

test("an invocation that names no render is refused with the usage's status", async () => {
  for (const args of [
    [],
    ["render"],
    ["render", "stage"],
    ["render", "stage", ...settings("o.mp4").slice(0, 2), "--fps", "0"],
    ["render", "stage", "--output", "o.mp4", "--fps", "30", "--group", "15"],
    ["render", "stage", ...settings("o.mp4").slice(0, 6), "--encoder", "not json"],
    ["render", "stage", ...settings("o.mp4").slice(0, 8)],
    ["render", "stage", ...settings("o.mp4"), "--unknown"],
  ]) {
    await assert.rejects(run(process.execPath, [MODULE, ...args]), (error) => error.code === 2);
  }
});

test("a face that does not register fails the render", async () => {
  const folder = await stage("zh");
  await writeFile(join(folder, "fonts/ibm-plex-sans-bold.ttf"), "no font");
  await assert.rejects(
    run(process.execPath, [MODULE, "render", folder, ...settings(join(folder, "..", "o.mp4"))]),
    (error) => error.code === 1 && /SampleLatinBold did not register/.test(error.stderr),
  );
});

test("a stage is drawn with the faces its record names, all of them, and with no other", async () => {
  const output = (folder) => settings(join(folder, "..", "o.mp4"));
  // A record that names no faces, as a stage of an earlier engine, is refused: the module reads no stylesheet.
  const unnamed = await stage("zh", { record: { faces: undefined } });
  await assert.rejects(
    run(process.execPath, [MODULE, "render", unnamed, ...output(unnamed)]),
    (error) =>
      error.code === 1 &&
      /names no faces or no language; stage the picture again/.test(error.stderr),
  );
  // A font that the stage holds and no face registers is refused by its name.
  const more = await stage("zh", { record: { faces: FACES.slice(0, 3) } });
  await assert.rejects(
    run(process.execPath, [MODULE, "render", more, ...output(more)]),
    (error) =>
      error.code === 1 &&
      /holds fonts\/ibm-plex-sans-bold\.ttf, which no face registers/.test(error.stderr),
  );
});

/* A composition that draws two frames and then fails as a scene would: by a TypeError, or with `range` by a
 * RangeError, which is no wrong invocation. */
const failing = (range = false) => `window.renderFrame = (seconds) => {
  const picture = document.getElementById("picture").getContext("2d");
  picture.fillRect(0, 0, 8, 8);
  if (seconds > 0.05) ${range ? "new Array(-1)" : "picture.noSuchCall()"};
};`;

test(
  "a draw that fails midway ends the render at once, in one process and in spans",
  rendering,
  async () => {
    for (const [spans, script] of [
      [1, failing()],
      [2, failing()],
      [1, failing(true)],
    ]) {
      const folder = await stage("zh", { script });
      const began = Date.now();
      await assert.rejects(
        run(process.execPath, [
          ...[MODULE, "render", folder],
          ...settings(join(folder, "..", "o.mp4"), "--spans", String(spans)),
        ]),
        // The status is a failed render's, also for a RangeError of the composition; a span's failure is named.
        (error) =>
          error.code === 1 &&
          (spans === 1 || /Span [12] of 2 ended with 1/.test(error.stderr)) &&
          /noSuchCall|Invalid array length/.test(error.stderr),
      );
      // It ended by itself, well before any deadline, and left no encoder and no span of this stage running.
      assert.ok(Date.now() - began < 20000);
      const left = spawnSync("pgrep", ["-f", folder], { encoding: "utf8" }).stdout.trim();
      assert.equal(left, "");
    }
  },
);

test("an encoder that takes fewer frames than the span fails it, though it exits 0", async () => {
  const folder = await stage("zh");
  // A stand-in for FFmpeg that reads one frame, writes its output and exits 0.
  const bin = join(folder, "..", "bin");
  await mkdir(bin);
  const standIn = `#!/bin/sh
for output; do :; done
head -c ${1920 * 1080 * 4} > /dev/null
echo "one frame" > "$output"
exit 0
`;
  await writeFile(join(bin, "ffmpeg"), standIn);
  await chmod(join(bin, "ffmpeg"), 0o755);
  const env = { ...process.env, PATH: `${bin}:${process.env.PATH}` };
  await assert.rejects(
    run(process.execPath, [MODULE, "render", folder, ...settings(join(folder, "..", "o.mp4"))], {
      env,
    }),
    (error) => error.code === 1 && /The encoder took \d+ of 60 frames/.test(error.stderr),
  );
});

test("the spans' folder holds nothing but spans, and one that holds anything else is refused", async () => {
  const folder = await stage("zh");
  const work = join(folder, "..", "kept");
  await mkdir(work);
  await writeFile(join(work, "notes.txt"), "a film's build");
  await assert.rejects(
    run(process.execPath, [
      ...[MODULE, "render", folder],
      ...settings(join(folder, "..", "o.mp4"), "--spans", "2", "--work", work),
    ]),
    (error) => error.code === 1 && /holds notes\.txt, which no render wrote/.test(error.stderr),
  );
  assert.equal(await readFile(join(work, "notes.txt"), "utf8"), "a film's build");
});
