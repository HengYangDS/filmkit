/** Read a delivery's pages back in a real browser, each page with a verdict of its own.
 *
 * This part only collects what each page shows and does: it opens the entry page and each player, switches versions,
 * clicks every control of the page, reads the browser's own captions control, plays from a chapter and a transcript
 * time and saves each download. player-verdict.mjs judges what it collects. */
import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";
import { mkdtemp, readFile, rm, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { pathToFileURL } from "node:url";

import {
  embeddedText,
  entryProblems,
  KEPT,
  LANGUAGES,
  parseCues,
  playerProblems,
  verdict,
  visibleCaptionControls,
} from "./player-verdict.mjs";

/* Each delivered film's name ending and size. */
const EDITIONS = [
  ["-uhd.mp4", [3840, 2160]],
  ["-1080p-captioned.mp4", [1920, 1080]],
];
/* A saved download has this long to end, and a page this long to show it left, in milliseconds. */
const SAVING = 10000,
  SETTLING = 150;

/** A file's SHA-256, streamed so that a film need not fit in memory. */
export async function digestFile(path) {
  const hash = createHash("sha256");
  for await (const block of createReadStream(path)) hash.update(block);
  return hash.digest("hex");
}

/** Two seconds in, the middle, and four seconds before the end. */
export const seekPoints = (duration) => [2, duration / 2, duration - 4];

/* The page's video and its caption track as the browser holds them. */
const videoState = (page) =>
  page.$eval("video", (video) => {
    const track = video.textTracks[0];
    return {
      src: video.currentSrc.split("/").pop(),
      time: video.currentTime,
      tracks: video.textTracks.length,
      mode: track?.mode ?? null,
    };
  });

/* Pause the film at a time and wait until it is shown there. */
async function standAt(page, time) {
  await page.$eval(
    "video",
    (video, target) => {
      video.pause();
      video.muted = true;
      video.currentTime = target;
    },
    time,
  );
  await page.waitForFunction(
    (target) => {
      const v = document.querySelector("video");
      return !v.seeking && v.readyState >= 2 && Math.abs(v.currentTime - target) < 0.2;
    },
    {},
    time,
  );
}

/* Switch to a version from a known time, then play it from each seek point; returns what the browser showed. */
async function switchVersion(page, file, dimensions, duration) {
  const from = duration / 3;
  await standAt(page, from);
  await page.click(`[data-file$="${file}"]`);
  await page.waitForFunction(
    (suffix) =>
      document.querySelector("video").currentSrc.endsWith(suffix) &&
      document.querySelector("video").readyState >= 1,
    {},
    file,
  );
  // The page restores the time once the film's metadata loads; a page that does not is judged, not waited for.
  await page
    .waitForFunction(
      (target, kept) => Math.abs(document.querySelector("video").currentTime - target) < kept,
      { timeout: 5000 },
      from,
      KEPT,
    )
    .catch(() => {});
  const state = await page.$eval("video", (video) => ({
    duration: video.duration,
    width: video.videoWidth,
    height: video.videoHeight,
    src: video.currentSrc,
    error: video.error?.code ?? null,
  }));
  const { time, mode } = await videoState(page);
  // The middle of the middle cue: the hidden track holds it active there, and it marks its paragraph.
  const cueAt = await page.$eval("video", (video) => {
    const { cues } = video.textTracks[0],
      cue = cues[cues.length >> 1];
    return (cue.startTime + cue.endTime) / 2;
  });
  await standAt(page, cueAt);
  await page
    .waitForFunction(
      () => {
        const [cue] = document.querySelector("video").textTracks[0].activeCues ?? [],
          current = document.querySelector('#transcript p[aria-current="true"]'),
          letters = (text) => text.replace(/[^\p{L}\p{N}]/gu, "");
        return cue && current && letters(current.textContent).includes(letters(cue.text));
      },
      { timeout: 5000 },
    )
    .catch(() => {});
  const marked = await page.$eval("video", (video) => ({
    active_cue: video.textTracks[0].activeCues?.[0]?.text ?? null,
    current_paragraph:
      document.querySelector('#transcript p[aria-current="true"]')?.textContent ?? null,
  }));
  Object.assign(state, {
    file,
    dimensions,
    kept_time: [from, time],
    track_mode: mode,
    cue_at: cueAt,
    ...marked,
    seek_checks: [],
  });
  for (const target of seekPoints(duration)) {
    await standAt(page, target);
    await page.$eval("video", (video) => video.play());
    await page.waitForFunction(
      (at) => document.querySelector("video").currentTime > at + 0.35,
      {},
      target,
    );
    const decoded = await page.$eval("video", (video) => {
      video.pause();
      const q = video.getVideoPlaybackQuality();
      return {
        time: video.currentTime,
        ready_state: video.readyState,
        error: video.error?.code ?? null,
        decoded_frames: q.totalVideoFrames,
        dropped_frames: q.droppedVideoFrames,
      };
    });
    state.seek_checks.push({ target, ...decoded });
  }
  return state;
}

/* Click a button that names a time and wait until the film plays from there. */
async function playFrom(page, selector) {
  const time = await page.$eval(selector, (button) => Number(button.dataset.time));
  await page.click(selector);
  await page.waitForFunction(
    (at) =>
      !document.querySelector("video").paused && document.querySelector("video").currentTime >= at,
    {},
    time,
  );
  const played = await page.$eval("video", (video) => {
    video.pause();
    return video.currentTime;
  });
  return { time, played };
}

const hrefs = (page, selector) =>
  page.$$eval(selector, (as) => as.map((a) => a.getAttribute("href")));

/* How many captions controls the browser's own video controls show. */
async function nativeCaptionControls(page) {
  const client = await page.createCDPSession();
  try {
    const { root } = await client.send("DOM.getDocument", { depth: -1, pierce: true });
    return visibleCaptionControls(root);
  } finally {
    await client.detach();
  }
}

/* Click each download the files list holds, compare what the browser saved with the delivered file, and see that the
 * page stayed where it was. A page that left is opened again, so the read goes on. */
async function saveDownloads(page, root, code, files) {
  const folder = await mkdtemp(join(tmpdir(), "filmkit-downloads-")),
    client = await page.createCDPSession(),
    home = page.url(),
    saved = [];
  try {
    await client.send("Browser.setDownloadBehavior", {
      behavior: "allow",
      downloadPath: folder,
      eventsEnabled: true,
    });
    for (const [index, { target, embedded }] of files.entries()) {
      if (!embedded) continue;
      const ended = new Promise((resolve) => {
        const watch = ({ state }) => {
          if (state === "inProgress") return;
          client.off("Browser.downloadProgress", watch);
          resolve(state);
        };
        client.on("Browser.downloadProgress", watch);
        setTimeout(() => resolve("timed out"), SAVING);
      });
      await (await page.$$("a.file"))[index].click();
      const state = await ended;
      await new Promise((resolve) => setTimeout(resolve, SETTLING));
      const bytes = await readFile(join(folder, target)).catch(() => null),
        delivered = await readFile(join(root, code, target)).catch(() => null),
        navigated = page.url() !== home;
      saved.push({
        name: target,
        state,
        bytes: bytes?.length ?? 0,
        same: !!delivered && !!bytes?.equals(delivered),
        navigated,
      });
      if (navigated) await page.goto(home, { waitUntil: "networkidle0" });
    }
    return saved;
  } finally {
    await client.detach();
    await rm(folder, { recursive: true, force: true });
  }
}

/* Click every control of the page in turn, hiding the track again after any that shows it, so each is named. */
const sweepControls = (page) =>
  page.evaluate(async () => {
    const film = document.querySelector("video"),
      controls = [...document.querySelectorAll("button, summary, input, select")],
      shown = [];
    for (const control of controls) {
      control.click();
      await new Promise((resolve) => setTimeout(resolve));
      if (film.textTracks[0].mode === "hidden") continue;
      shown.push(control.textContent);
      film.textTracks[0].mode = "hidden";
    }
    film.pause();
    return { controls: controls.length, shown };
  });

/** Read the language entry page; the record holds its links and its verdict. */
export async function readEntry(page, root, members) {
  const read = {};
  let stopped = [];
  try {
    await page.goto(pathToFileURL(join(root, "index.html")).href, { waitUntil: "networkidle0" });
    read.links = await hrefs(page, "a");
    read.language_links = await hrefs(page, "nav a");
  } catch (error) {
    stopped = [`the read stopped: ${error.message}`];
  }
  return { ...verdict("index.html", [...entryProblems(read, members), ...stopped]), ...read };
}

/** What one edition's player holds by the delivery: its chapters, the size of each of its members, its WebVTT and
 * the cues of its SRT. */
async function delivered(root, code, binding) {
  const { slug, duration } = binding.film,
    members = binding.members.map((member) => member.path),
    sizes = new Map();
  for (const member of members.filter((m) => m.startsWith(`${code}/`)))
    sizes.set(member, (await stat(join(root, member))).size);
  const { chapters } = JSON.parse(await readFile(join(root, code, "chapters.json"), "utf8"));
  const vtt = await readFile(join(root, code, `${slug}-${code}.vtt`), "utf8"),
    srt = await readFile(join(root, code, `${slug}-${code}.srt`), "utf8");
  return { code, slug, duration, chapters, members, sizes, vtt, srt_cues: parseCues(srt) };
}

/** Read one edition's player, `code`, and screenshot it to `screenshot`; the record holds what was read and the
 * page's verdict. A read that stops is a problem of its page, and the reads of the other pages go on. */
export async function readPlayer(page, root, code, binding, screenshot) {
  const path = `${code}/index.html`,
    read = { language: code, editions: [] };
  let expected = null,
    stopped = [];
  try {
    expected = await delivered(root, code, binding);
    await page.goto(pathToFileURL(join(root, path)).href, { waitUntil: "networkidle0" });
    await page.waitForFunction(() => document.querySelector("video").readyState >= 1);
    read.lang = await page.$eval("html", (e) => e.lang);
    read.chapters = await page.$$eval("#chapters button", (bs) => bs.map((b) => b.textContent));
    read.links = (await hrefs(page, "a")).filter((href) => !href?.startsWith("data:"));
    read.language_links = await hrefs(page, "#languages a");
    read.plain_downloads = await hrefs(page, 'a[download]:not([href^="data:"])');
    read.files = await page.$$eval("a.file", (as) =>
      as.map((a) => ({
        // A data URL names no file, so a link without its `download` name leads nowhere.
        target:
          a.getAttribute("download") ||
          (a.getAttribute("href").startsWith("data:") ? "" : a.getAttribute("href")),
        text: a.textContent,
        embedded: a.getAttribute("href").startsWith("data:"),
      })),
    );
    const track = await page.$eval("track", (t) => ({
      kind: t.kind,
      srclang: t.srclang,
      label: t.label,
      src: t.getAttribute("src"),
    }));
    read.track = {
      kind: track.kind,
      srclang: track.srclang,
      label: track.label,
      text: embeddedText(track.src ?? ""),
    };
    await page.waitForFunction(() => document.querySelector("track").readyState >= 2);
    read.opening = await videoState(page);
    read.cues = await page.$eval("video", (video) =>
      [...video.textTracks[0].cues].map((cue) => [
        Math.round(cue.startTime * 1000),
        Math.round(cue.endTime * 1000),
        cue.text,
      ]),
    );
    read.native_caption_controls = await nativeCaptionControls(page);
    read.saved = await saveDownloads(page, root, code, read.files);
    for (const [file, dimensions] of EDITIONS)
      read.editions.push(await switchVersion(page, file, dimensions, binding.film.duration));
    read.chapter_jump = (await playFrom(page, "#chapters button:nth-child(2)")).played;
    await page.screenshot({ path: screenshot, fullPage: true });
    read.transcript_chapters = await page.$$eval("#transcript h2", (hs) => hs.length);
    await page.click('footer a[href="#transcript"]');
    read.transcript_open = await page.$eval("#transcript details", (details) => details.open);
    read.transcript_time = await playFrom(page, "#transcript h3:nth-of-type(2) button.time");
    read.control_sweep = await sweepControls(page);
  } catch (error) {
    stopped = [`the read stopped: ${error.message}`];
  }
  const problems = expected ? playerProblems(read, expected) : [];
  const track = read.track && { ...read.track, text: undefined },
    cues = read.cues?.length,
    srt_cues = expected?.srt_cues.length;
  return { ...verdict(path, [...problems, ...stopped]), ...read, track, cues, srt_cues };
}

/** Read the entry page and both players of the bound delivery, writing each player's screenshot beside the receipt. */
export async function readDelivery(page, binding, receiptPath) {
  const members = binding.members.map((member) => member.path);
  const pages = [await readEntry(page, binding.destination, members)];
  for (const code of Object.keys(LANGUAGES)) {
    const screenshot = join(dirname(receiptPath), `player-${code}.png`);
    pages.push(await readPlayer(page, binding.destination, code, binding, screenshot));
  }
  return pages;
}
