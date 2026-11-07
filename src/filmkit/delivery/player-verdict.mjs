/** Judge what a delivery's pages show and do, as the real-browser read collects it (player-read.mjs), a page at a time.
 *
 * Every link of a page must lead to a delivery member, a sibling page or a place in the page. The language entry page
 * leads to both players. A player opens on the viewing film with its captions drawn and its captions control pressed.
 * The control switches to the other film of the same version, with or without captions, and a version button to its
 * version's film with the captions as they are, each keeping the time and whether the film plays; every film plays at
 * its size and duration and decodes at three seek points. The pictures draw the captions, so a player's one track of
 * the edition's cues stays hidden: it embeds the delivered WebVTT, its cues equal the SRT's, it is hidden on every
 * film, and neither the page's controls nor the browser's own can show it. On each version a cue active at its time
 * marks the transcript paragraph that holds it. A chapter button and a transcript time play from their time; the
 * language links lead to the other edition's player and to the entry page; each file the list names carries the size
 * of the member it leads to; no link opens raw text in a tab, and each text file is a download that saves the
 * delivered bytes and leaves the page where it is. */
import { posix } from "node:path";
import { isDeepStrictEqual } from "node:util";

/* Each edition's page language. */
export const LANGUAGES = { zh: "zh-CN", en: "en" };
/* A version or captions switch keeps the time within half a second; a time button has played from its time within
 * two. */
export const KEPT = 0.5;
/* The films and controls a player holds: a file listed for each delivered film and cover and each text download. */
const LISTED = 11;
const PLAYED = 2;
/* A delivered file a browser would show as raw text, however a link names it. */
const RAW_TEXT = /\.(md|json|ffmeta|srt|vtt)(#.*)?$/i;
/* The browser's own control for a film's captions, in the video's user-agent shadow tree. */
const CAPTION_CONTROL = "-webkit-media-controls-toggle-closed-captions-button";

/** The letters and digits of a text, by which a cue is found in its paragraph. */
export const bare = (text) => text.replace(/[^\p{L}\p{N}]/gu, "");

/* A SubRip or WebVTT time in milliseconds. */
function milliseconds(stamp) {
  const [, hours, minutes, seconds, thousandths] = /(\d+):(\d\d):(\d\d)[,.](\d{3})/.exec(stamp);
  return (
    ((Number(hours) * 60 + Number(minutes)) * 60 + Number(seconds)) * 1000 + Number(thousandths)
  );
}

/** The cues of a SubRip or WebVTT document, each as its start and end in milliseconds and its text. */
export function parseCues(text) {
  const cues = [];
  for (const block of text.replaceAll("\r", "").split(/\n{2,}/)) {
    const lines = block.split("\n"),
      at = lines.findIndex((line) => line.includes("-->"));
    if (at < 0) continue;
    const [start, end] = lines[at].split("-->").map(milliseconds);
    cues.push([
      start,
      end,
      lines
        .slice(at + 1)
        .join("\n")
        .trim(),
    ]);
  }
  return cues;
}

/** Why a track's cues differ from the SRT's: in number, or at the first that differs in its times or text. */
export function cueProblems(cues, srt) {
  if (cues.length !== srt.length)
    return [`the track holds ${cues.length} cues, the SRT ${srt.length}`];
  const at = cues.findIndex((cue, k) => !isDeepStrictEqual(cue, srt[k]));
  if (at < 0) return [];
  const shown = ([start, end, text]) => `${start}-${end} ${text}`;
  return [`cue ${at + 1} of the track is ${shown(cues[at])}, in the SRT ${shown(srt[at])}`];
}

/** How many captions controls the browser's own video controls show, in a DOM tree read with its shadow roots. */
export function visibleCaptionControls(node) {
  const list = node.attributes ?? [],
    attributes = {};
  for (let k = 0; k + 1 < list.length; k += 2) attributes[list[k]] = list[k + 1];
  const shown =
    attributes.pseudo === CAPTION_CONTROL && !/display:\s*none/.test(attributes.style ?? "");
  return [...(node.children ?? []), ...(node.shadowRoots ?? [])].reduce(
    (count, child) => count + visibleCaptionControls(child),
    shown ? 1 : 0,
  );
}

/** The text a data URL carries, decoded from base64 or percent-encoding, or null for any other URL. */
export function embeddedText(src) {
  const match = /^data:([^,]*),(.*)$/s.exec(src);
  if (!match) return null;
  return match[1].split(";").includes("base64")
    ? Buffer.from(match[2], "base64").toString("utf8")
    : decodeURIComponent(match[2]);
}

/* A link's target below the destination, its fragment dropped. */
const resolved = (pagePath, href) =>
  posix.normalize(posix.join(posix.dirname(pagePath), href.split("#")[0]));

/** Why links of the page at `pagePath` do not lead to a delivery member, a sibling page or a place in the page, or
 * would open raw text in a tab. */
export function linkProblems(pagePath, hrefs, members) {
  const problems = [];
  for (const href of hrefs) {
    if (!href) problems.push("a link has no target");
    else if (href.startsWith("#")) continue;
    else if (/^[a-z][a-z0-9+.-]*:/i.test(href) || resolved(pagePath, href).startsWith("../"))
      problems.push(`${href} leaves the delivery`);
    else if (!members.includes(resolved(pagePath, href)))
      problems.push(`${href} resolves to ${resolved(pagePath, href)}, which is no delivery member`);
    else if (RAW_TEXT.test(href)) problems.push(`${href} opens raw text in a tab`);
  }
  return problems;
}

/** A file's size in decimal units, rounded half up, exactly as the engine's player names it
 * (filmkit.delivery.player.size_label). */
export function sizeLabel(bytes) {
  if (bytes < 1000) return `${bytes} B`;
  for (const [unit, scale] of [
    ["KB", 1e3],
    ["MB", 1e6],
  ]) {
    const value = Math.floor(bytes / scale + 0.5);
    if (value < 1000) return `${value} ${unit}`;
  }
  return `${(Math.floor(bytes / 1e8 + 0.5) / 10).toFixed(1)} GB`;
}

/** Why the files a list names do not carry the sizes of the members they lead to, read into `sizes` by path. */
export function fileProblems(pagePath, entries, sizes) {
  const problems = [];
  for (const { target: name, text } of entries) {
    const target = resolved(pagePath, name);
    if (!sizes.has(target)) problems.push(`${text} leads to ${target}, which was not read`);
    else if (!text.endsWith(` · ${sizeLabel(sizes.get(target))}`))
      problems.push(`${text} names another size than ${target}'s ${sizeLabel(sizes.get(target))}`);
  }
  return problems;
}

/** A page's verdict: it passes when its checks found no problem. */
export const verdict = (page, problems) => ({
  page,
  verdict: problems.length ? "fail" : "pass",
  problems,
});

/** Why the entry page does not lead to both players, or a link of it leads outside the delivery. */
export function entryProblems(read, members) {
  const expected = Object.keys(LANGUAGES).map((code) => `${code}/index.html`),
    problems = read.links ? linkProblems("index.html", read.links, members) : [];
  if (read.language_links && !isDeepStrictEqual(read.language_links, expected))
    problems.push(
      `the language links are ${read.language_links.join(", ")}, not ${expected.join(", ")}`,
    );
  return problems;
}

/** Why a film, as the player shows it, does not play as delivered: its duration, its size, a media error, or nothing
 * decoded at a seek point. */
export function playbackProblems(state, duration) {
  const { file } = state,
    problems = [],
    expect = (ok, problem) => ok || problems.push(problem);
  expect(state.duration === duration, `${file} lasts ${state.duration} s, not ${duration} s`);
  expect(
    isDeepStrictEqual([state.width, state.height], state.dimensions),
    `${file} is ${state.width}x${state.height}, not ${state.dimensions.join("x")}`,
  );
  expect(state.error === null, `${file} reports media error ${state.error}`);
  for (const check of state.seek_checks)
    expect(
      check.error === null && check.decoded_frames > 0,
      `${file} decodes nothing at ${check.target} s`,
    );
  return problems;
}

/** Why a version, as the player switched to it from a known time, differs from what it must be: the same time, the
 * caption track hidden, an active cue marking the transcript paragraph that holds it, and its playback. */
export function versionProblems(state, duration) {
  const { file } = state,
    [from, time] = state.kept_time,
    problems = [],
    expect = (ok, problem) => ok || problems.push(problem);
  expect(
    Math.abs(time - from) < KEPT,
    `switching to ${file} moved the time from ${from} s to ${time} s`,
  );
  expect(
    state.track_mode === "hidden",
    `the caption track is ${state.track_mode} on ${file}, not hidden`,
  );
  if (state.active_cue === null) problems.push(`no cue is active at ${state.cue_at} s on ${file}`);
  else
    expect(
      bare(state.current_paragraph ?? "").includes(bare(state.active_cue)),
      `the transcript's current paragraph at ${state.cue_at} s on ${file} does not hold the active cue`,
    );
  return [...problems, ...playbackProblems(state, duration)];
}

/** Why a switch by the captions control or by a version button with the captions off, as the player made it from a
 * known time, playing or paused, differs from what it must be: the film of the other captions state or of the other
 * version, the same time, the film playing or paused as before, the captions control pressed as the captions show,
 * the track hidden and, where the read played the film, its playback. */
export function switchProblems(step, duration) {
  const { control, file, from } = step,
    problems = [],
    expect = (ok, problem) => ok || problems.push(problem);
  const by = control === "captions" ? "the captions control" : "a version button";
  expect(step.src?.endsWith(file), `${by} switched to ${step.src}, not the film ending ${file}`);
  expect(
    Math.abs(step.time - from) < KEPT,
    `${by} moved the time from ${from} s to ${step.time} s`,
  );
  expect(
    step.paused === !step.playing,
    `${by} left the film ${step.paused ? "paused" : "playing"}, not ${step.playing ? "playing" : "paused"}`,
  );
  expect(
    step.pressed === String(step.captions),
    `the captions control is pressed ${step.pressed} with the captions ${step.captions ? "on" : "off"}`,
  );
  expect(step.track_mode === "hidden", `the caption track is ${step.track_mode} on ${step.src}`);
  return step.seek_checks ? [...problems, ...playbackProblems(step, duration)] : problems;
}

/** Why a player's read, `read`, differs from what the delivery holds, `expected`: its language, chapters, links,
 * language links, files list and caption downloads, its track and opening film, each version, whether any control can
 * show the track, and the chapter and transcript times. Only what was read is judged, so a read that stopped is judged
 * as far as it got. */
export function playerProblems(read, expected) {
  const { code, slug, duration, chapters, members, sizes, vtt, srt_cues } = expected,
    path = `${code}/index.html`,
    other = Object.keys(LANGUAGES).find((c) => c !== code),
    downloads = [
      `${slug}-${code}-transcript.md`,
      "chapters.json",
      "chapters.ffmeta",
      `${slug}-${code}.vtt`,
      `${slug}-${code}.srt`,
    ],
    problems = [],
    expect = (ok, problem) => ok || problems.push(problem),
    has = (key) => read[key] !== undefined;
  if (has("lang")) expect(read.lang === LANGUAGES[code], `the page's language is ${read.lang}`);
  if (has("chapters"))
    expect(
      isDeepStrictEqual(
        read.chapters,
        chapters.map((chapter) => chapter.title),
      ),
      "the chapter buttons differ from chapters.json",
    );
  if (has("links")) problems.push(...linkProblems(path, read.links, members));
  if (has("language_links"))
    expect(
      isDeepStrictEqual(read.language_links, [`../${other}/index.html`, "../index.html"]),
      "the language links do not lead to the other edition's player and the entry page",
    );
  if (has("files")) {
    problems.push(...fileProblems(path, read.files, sizes));
    expect(
      read.files.length === LISTED,
      `the files list names ${read.files.length} files, not ${LISTED}`,
    );
  }
  for (const href of read.plain_downloads ?? [])
    problems.push(`${href} asks for a download, which a browser ignores on a file beside the page`);
  if (has("files"))
    for (const name of downloads)
      expect(
        read.files.some((file) => file.target === name && file.embedded),
        `${name} is no download the page holds`,
      );
  if (has("saved"))
    for (const name of downloads) {
      const saved = read.saved.find((file) => file.name === name);
      if (!saved) problems.push(`${name} was not saved`);
      else {
        expect(
          saved.state === "completed" && saved.same,
          `${name} saved ${saved.state}, not the delivered bytes`,
        );
        expect(!saved.navigated, `${name} navigated away from the page`);
      }
    }
  if (has("track")) {
    const { kind, srclang, label, text } = read.track;
    expect(
      kind === "metadata" && srclang === code && label,
      "the track is no hidden metadata track with a label in its language",
    );
    expect(text === vtt, "the track does not carry the delivered WebVTT");
  }
  if (has("opening")) {
    const { src, tracks, mode, captions } = read.opening;
    expect(src === `${slug}-${code}-1080p-captioned.mp4`, `the page opens on ${src}`);
    expect(tracks === 1, `the film has ${tracks} text tracks, not one`);
    expect(mode === "hidden", `the caption track is ${mode} on the viewing film, not hidden`);
    expect(captions === "true", `the page opens with its captions control pressed ${captions}`);
  }
  if (has("cues")) problems.push(...cueProblems(read.cues, srt_cues));
  if (has("native_caption_controls"))
    expect(
      read.native_caption_controls === 0,
      "the browser's own controls offer the track, so a viewer could double the captions",
    );
  if (has("control_sweep"))
    expect(
      !read.control_sweep.shown.length,
      `a control shows the track: ${read.control_sweep.shown.join(", ")}`,
    );
  for (const state of read.editions ?? []) problems.push(...versionProblems(state, duration));
  if (has("captions")) {
    expect(
      read.captions.length === 3,
      `the captions control was read ${read.captions.length} times, not 3`,
    );
    for (const step of read.captions) problems.push(...switchProblems(step, duration));
  }
  if (has("chapter_jump"))
    expect(
      read.chapter_jump >= chapters[1].start && read.chapter_jump < duration,
      "the second chapter does not play from its start",
    );
  if (has("transcript_chapters"))
    expect(
      read.transcript_chapters === chapters.length,
      "the transcript does not head every chapter",
    );
  if (has("transcript_open"))
    expect(read.transcript_open, "the transcript link does not open the transcript");
  if (has("transcript_time")) {
    const { time, played } = read.transcript_time;
    expect(
      played >= time && played < time + PLAYED,
      `a transcript time of ${time} s played from ${played} s`,
    );
  }
  return problems;
}
