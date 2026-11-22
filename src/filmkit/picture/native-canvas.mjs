/** Draw a staged picture on a native canvas and encode it: the engine's renderer (`filmkit.picture.renderer`).
 *
 * Usage: node native-canvas.mjs render <stage> --output <picture.mp4> --fps <n> --group <frames>
 *                                --encoder <json> --text-renderer <name>
 *                                [--spans <n>] [--work <folder>] [--report <report.json>]
 *
 * The stage (`filmkit.picture.rendering.stage_picture`) holds stage.json (the frame, the duration, the language and
 * the faces), film.json (the picture's data, `window.FILM`), the composition film.js and the fonts. The composition
 * runs unchanged in a vm context, as the audits run it and on the same document (headless-composition.mjs), on a
 * canvas of `@napi-rs/canvas` whose text renderer is the one `--text-renderer` names. The faces are the ones the
 * stage's record names, each family with its file: this module reads no stylesheet, and a stage that holds a font
 * its record does not register is refused. No browser runs.
 *
 * Each frame's RGBA pixels go to one FFmpeg child, which converts them to BT.709 in limited range and encodes them
 * with the options `--encoder` gives, the pictures' encoding (`filmkit.picture.encoding`): a keyframe at every
 * `--group` frames and nowhere else. With `--spans` above 1 the film is drawn in that many contiguous spans of whole
 * groups, one process of this module and one encoder of SPAN_THREADS threads each, all at once, and the spans are
 * joined by stream copy, so the film holds the keyframes one process would write. A span that fails, by its draw or
 * by its encoder, ends the others. The spans' folder, `--work` or <output>.spans, holds nothing but what a render
 * writes there; a folder that holds anything else is refused, and the spans are removed before a run and after a join.
 *
 * The report states what ran, as each drawing process read it of itself: the frames given to the encoders, the
 * spans, the text renderer, the native library the canvas loaded (its path, its SHA-256 and the package that holds
 * it) and `drawn_sha256`, the SHA-256 of the CRC-32 of every drawn frame's pixels in the film's order (four bytes
 * each, big-endian). Two draws of one stage state the same digest whatever their span counts; the encoded bytes are
 * not part of it. A CRC-32 costs 1 ms a UHD frame in this thread where a SHA-256 costs 10 ms, which is more than
 * drawing the frame.
 *
 * The module handles no signal: the command that starts it gives it a session of its own and ends that process
 * group, the span processes and the encoders with it (`filmkit.picture.renderer.run_renderer`). */
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { once } from "node:events";
import {
  existsSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  realpathSync,
  rmdirSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";
import vm from "node:vm";
import { crc32 } from "node:zlib";
import { createCanvas, getTextRenderer, GlobalFonts, setTextRenderer } from "@napi-rs/canvas";
import { compositionScope } from "./headless-composition.mjs";
import { RECORD } from "./stage-contract.mjs";

// The encoder threads of each span of a film drawn in several: the count the whole-film measurements ran with.
const SPAN_THREADS = 2;
const SELF = fileURLToPath(import.meta.url);
const USAGE =
  "Usage: native-canvas.mjs render <stage> --output <picture.mp4> --fps <n> --group <frames> --encoder <json> --text-renderer <name> [--spans <n>] [--work <folder>] [--report <report.json>]";
// The pixels' conversion: full-range RGBA to BT.709 in limited range, 4:2:0, with the primaries and the transfer
// stated on each frame, since FFmpeg takes neither from an output option once a filter has made the frames.
const CONVERSION =
  "scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709";
// What a render writes in its spans' folder.
const SPAN_FILE = /^(span-\d+\.(mp4|crc|json)|spans\.txt)$/;
// Node hands a child its input as a socket, whose size FFmpeg reads as its input's size, so every encoder prints
// this one line at its error level before its first frame and then reads every frame whole. From a shell's pipe
// the same input prints nothing (18 November 2026, FFmpeg 9.0.2, frames of 8.3 MB).
const INPUT_SIZE_LINE = /^Truncating packet of size \d+ to \d+$/;

/** An invocation that names no render: the usage's exit status. */
class UsageError extends Error {}

/** The contiguous frame ranges, first to last exclusive, of `spans` spans of whole groups over a film: as even as
 * the groups divide, the longer spans first, and no more spans than the film has groups. */
export function planSpans(frames, group, spans) {
  const groups = Math.ceil(frames / group),
    count = Math.max(1, Math.min(spans, groups)),
    plan = [];
  for (let index = 0, at = 0; index < count; index++) {
    const held = Math.floor(groups / count) + (index < groups % count ? 1 : 0);
    plan.push([at * group, Math.min((at + held) * group, frames)]);
    at += held;
  }
  return plan;
}

/** FFmpeg's arguments for the frames of one process: raw RGBA in, converted, and encoded by the options given. */
export function encoderArguments({ width, height, fps, encoder, threads, faststart, output }) {
  return [
    ...["-hide_banner", "-loglevel", "error", "-nostdin", "-y"],
    ...["-f", "rawvideo", "-pix_fmt", "rgba", "-s", `${width}x${height}`, "-r", String(fps)],
    ...["-i", "-", "-vf", CONVERSION],
    ...encoder,
    ...(threads ? ["-threads", String(threads)] : []),
    ...(faststart ? ["-movflags", "+faststart"] : []),
    output,
  ];
}

/** The native library this process loaded for the canvas: its path, its SHA-256, and the package that holds it by
 * the manifest beside it, which is none where the loader was pointed at a bare file. */
function loadedLibrary() {
  const loaded = process.report.getReport().sharedObjects.filter((path) => path.endsWith(".node"));
  if (loaded.length !== 1)
    throw Error(`This process loaded ${loaded.length} native libraries, not the canvas's one`);
  let manifest = {};
  try {
    manifest = JSON.parse(readFileSync(join(dirname(loaded[0]), "package.json"), "utf8"));
  } catch {
    // A library that stands beside no manifest belongs to no package.
  }
  return {
    path: loaded[0],
    sha256: createHash("sha256").update(readFileSync(loaded[0])).digest("hex"),
    package: manifest.name ?? null,
    version: manifest.version ?? null,
  };
}

/** Open a stage's picture: its record, its canvas and the composition's `renderFrame`. */
function openPicture(stage, textRenderer) {
  const record = JSON.parse(readFileSync(join(stage, RECORD), "utf8"));
  if (!Array.isArray(record.faces) || typeof record.language !== "string")
    throw Error(`The record of ${stage} names no faces or no language; stage the picture again`);
  for (const { family, path } of record.faces) {
    if (!GlobalFonts.registerFromPath(resolve(stage, path), family))
      throw Error(`The face ${family} did not register from ${path} in ${stage}`);
  }
  // A font the stage holds and no face registers would be left out of the picture without a word.
  const fonts = join(stage, "fonts");
  const held = existsSync(fonts) ? readdirSync(fonts).map((name) => `fonts/${name}`) : [];
  const unregistered = held.filter((path) => !record.faces.some((face) => face.path === path));
  if (unregistered.length)
    throw Error(`The stage ${stage} holds ${unregistered.join(", ")}, which no face registers`);
  // The text renderer is set once, before any canvas exists.
  setTextRenderer(textRenderer);
  const canvas = createCanvas(record.width, record.height);
  const context = canvas.getContext("2d", { alpha: false });
  // The language is the staged document's; the canvas's default follows the host's.
  context.lang = record.language;
  const window = { FILM: JSON.parse(readFileSync(join(stage, "film.json"), "utf8")) };
  const composition = join(stage, "film.js");
  vm.runInContext(
    readFileSync(composition, "utf8"),
    compositionScope(window, context, record.width),
    { filename: composition },
  );
  return { record, canvas, renderFrame: (seconds) => window.renderFrame(seconds) };
}

/** A child's end: its exit status, the signal that ended it, or why it could not start. */
function ended(child, onEnd = () => {}) {
  return new Promise((done) => {
    const end = (status) => {
      onEnd(status);
      done(status);
    };
    child.once("error", (error) => end(error.message));
    child.once("close", (code, signal) => end(code ?? signal));
  });
}

/** Pass an encoder's error lines on, but for the one line about its input's size. */
function passErrors(stream) {
  let pending = "",
    dropped = false;
  const pass = (line) => {
    if (!dropped && INPUT_SIZE_LINE.test(line)) dropped = true;
    else process.stderr.write(line + "\n");
  };
  stream.setEncoding("utf8");
  stream.on("data", (text) => {
    const lines = (pending + text).split("\n");
    pending = lines.pop();
    lines.forEach(pass);
  });
  stream.on("end", () => pending && pass(pending));
}

/** Draw the frames first to last exclusive into one encoder; the frames' CRC-32, four bytes each. A draw that
 * fails ends the encoder before the failure goes on, and an encoder that takes fewer frames than the span fails it. */
async function drawSpan(picture, { first, last, fps, encoder, threads, faststart, output }) {
  const { width, height } = picture.record;
  const settings = { width, height, fps, encoder, threads, faststart, output };
  const child = spawn("ffmpeg", encoderArguments(settings), {
    stdio: ["pipe", "inherit", "pipe"],
  });
  passErrors(child.stderr);
  let status = null,
    given = 0;
  const closed = ended(child, (ending) => (status = ending));
  // An encoder that ends early is read from its status, not from the closed pipe.
  child.stdin.on("error", () => {});
  const checksums = Buffer.alloc((last - first) * 4);
  try {
    for (let frame = first; frame < last && status === null; frame++, given++) {
      picture.renderFrame(frame / fps);
      const pixels = picture.canvas.data();
      checksums.writeUInt32BE(crc32(pixels), given * 4);
      if (!child.stdin.write(pixels))
        await Promise.race([once(child.stdin, "drain").catch(() => {}), closed]);
    }
  } catch (error) {
    // FFmpeg asked once to end still waits for its input, so the input is closed and the encoder killed: what
    // it has written of an unfinished picture is of no use.
    child.stdin.destroy();
    child.kill("SIGKILL");
    await closed;
    throw error;
  }
  child.stdin.end();
  if ((await closed) !== 0) throw Error(`The encoder ended with ${status} at ${output}`);
  if (given !== last - first)
    throw Error(`The encoder took ${given} of ${last - first} frames at ${output}`);
  return checksums;
}

/** Draw a film in several spans, each a process of this module, and join them; every frame's CRC-32 in order and
 * what the spans state of themselves. */
async function drawInSpans(options, plan) {
  const { stage, work } = options;
  mkdirSync(work, { recursive: true });
  const spans = plan.map(([first, last], index) => ({ name: `span-${index}`, first, last }));
  let failed = null;
  const children = spans.map((span) =>
    spawn(
      process.execPath,
      [
        ...[SELF, "render", stage, "--output", join(work, `${span.name}.mp4`)],
        ...["--fps", String(options.fps), "--group", String(options.group)],
        ...["--encoder", JSON.stringify(options.encoder)],
        ...["--text-renderer", options.textRenderer],
        ...["--span", `${span.first}-${span.last}`, "--checksums", join(work, `${span.name}.crc`)],
      ],
      { stdio: ["ignore", "inherit", "inherit"] },
    ),
  );
  await Promise.all(
    children.map((child, index) =>
      ended(child, (status) => {
        if (status === 0 || failed !== null) return;
        // The film cannot be joined without this span, so the others end now.
        failed = `Span ${index + 1} of ${spans.length} ended with ${status}`;
        for (const other of children) if (other !== child) other.kill();
      }),
    ),
  );
  if (failed !== null) throw Error(failed);
  // The list names the spans beside it, in the film's order.
  writeFileSync(join(work, "spans.txt"), spans.map((span) => `file '${span.name}.mp4'\n`).join(""));
  const joining = spawn(
    "ffmpeg",
    [
      ...["-hide_banner", "-loglevel", "error", "-nostdin", "-y"],
      ...["-f", "concat", "-i", join(work, "spans.txt")],
      ...["-c", "copy", "-movflags", "+faststart", options.output],
    ],
    { stdio: ["ignore", "inherit", "inherit"] },
  );
  const joined = await ended(joining);
  if (joined !== 0) throw Error(`The join of ${spans.length} spans ended with ${joined}`);
  const stated = spans.map((span) => JSON.parse(readFileSync(join(work, `${span.name}.json`))));
  const alike = (fact) => new Set(stated.map((span) => JSON.stringify(fact(span)))).size === 1;
  if (!alike((span) => [span.text_renderer, span.binary]))
    throw Error("The spans did not run one canvas with one text renderer");
  return {
    checksums: Buffer.concat(spans.map((span) => readFileSync(join(work, `${span.name}.crc`)))),
    ran: { text_renderer: stated[0].text_renderer, binary: stated[0].binary },
  };
}

/** Remove what an earlier render left in the spans' folder, and the folder; refuse one that holds anything else. */
function clearSpans(work) {
  if (!existsSync(work)) return;
  const names = readdirSync(work),
    other = names.filter((name) => !SPAN_FILE.test(name));
  if (other.length)
    throw Error(
      `${work} holds ${other[0]}, which no render wrote; name a folder for the spans alone`,
    );
  for (const name of names) rmSync(join(work, name));
  rmdirSync(work);
}

/** A whole number an option must name, at least `least`. */
function whole(values, name, least) {
  const value = Number(values[name]);
  if (!Number.isInteger(value) || value < least)
    throw new UsageError(`--${name} names no whole number from ${least}`);
  return value;
}

function readArguments(args) {
  const text = { type: "string" };
  let parsed, encoder;
  try {
    parsed = parseArgs({
      args,
      allowPositionals: true,
      options: {
        ...{ output: text, fps: text, group: text, encoder: text, "text-renderer": text },
        ...{ spans: text, work: text, report: text, span: text, checksums: text },
      },
    });
    encoder = JSON.parse(parsed.values.encoder ?? "null");
  } catch (error) {
    throw new UsageError(`${error.message}\n${USAGE}`);
  }
  const { values, positionals } = parsed;
  if (positionals.length !== 2 || positionals[0] !== "render" || !values.output)
    throw new UsageError(USAGE);
  if (!Array.isArray(encoder) || !encoder.every((word) => typeof word === "string"))
    throw new UsageError("--encoder names no JSON list of FFmpeg's options");
  if (!values["text-renderer"]) throw new UsageError("--text-renderer names no text renderer");
  const options = {
    stage: resolve(positionals[1]),
    output: resolve(values.output),
    fps: whole(values, "fps", 1),
    group: whole(values, "group", 1),
    encoder,
    textRenderer: values["text-renderer"],
    spans: values.spans === undefined ? 1 : whole(values, "spans", 1),
    report: values.report,
    work: resolve(values.work ?? `${values.output}.spans`),
  };
  if (values.span === undefined) return options;
  const [first, last] = values.span.split("-").map(Number);
  if (
    !(Number.isInteger(first) && Number.isInteger(last) && 0 <= first && first < last) ||
    !values.checksums
  ) {
    throw new UsageError("--span names frames as <first>-<last> and needs --checksums");
  }
  return { ...options, span: { first, last, checksums: values.checksums } };
}

/** Render a stage as the arguments ask; the report, or for one span of a film nothing. */
async function render(args) {
  const options = readArguments(args);
  const { stage, output, fps, group, encoder, textRenderer, work } = options;
  // What this process ran, read once it has drawn: the text renderer the canvas holds and the library it loaded.
  const ran = () => ({ text_renderer: getTextRenderer(), binary: loadedLibrary() });
  if (options.span) {
    const { first, last, checksums } = options.span;
    const settings = { first, last, fps, encoder, threads: SPAN_THREADS, faststart: false, output };
    writeFileSync(checksums, await drawSpan(openPicture(stage, textRenderer), settings));
    writeFileSync(checksums.replace(/\.crc$/, "") + ".json", JSON.stringify(ran()));
    return null;
  }
  const record = JSON.parse(readFileSync(join(stage, RECORD), "utf8"));
  const frames = Math.round(record.duration * fps),
    plan = planSpans(frames, group, options.spans);
  clearSpans(work);
  rmSync(output, { force: true });
  let drawn;
  if (plan.length === 1) {
    const settings = {
      first: 0,
      last: frames,
      fps,
      encoder,
      threads: null,
      faststart: true,
      output,
    };
    drawn = { checksums: await drawSpan(openPicture(stage, textRenderer), settings), ran: ran() };
  } else {
    drawn = await drawInSpans(options, plan);
    clearSpans(work);
  }
  const report = {
    frames: drawn.checksums.length / 4,
    spans: plan.length,
    ...drawn.ran,
    drawn_sha256: createHash("sha256").update(drawn.checksums).digest("hex"),
  };
  if (report.frames !== frames) throw Error(`The spans drew ${report.frames} frames of ${frames}`);
  if (options.report) writeFileSync(options.report, JSON.stringify(report, null, 2) + "\n");
  return report;
}

if (process.argv[1] && realpathSync(process.argv[1]) === SELF) {
  try {
    const report = await render(process.argv.slice(2));
    if (report) console.log(JSON.stringify(report));
  } catch (error) {
    // The process ends by its status once its words are written, whatever a failed render left running.
    const status = error instanceof UsageError ? 2 : 1;
    process.stderr.write(`${error.message}\n`, () => process.exit(status));
  }
}
