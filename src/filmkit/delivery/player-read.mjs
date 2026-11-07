/** Read a delivery's pages back in a real browser, each page with a verdict of its own.
 *
 * This part only collects what each page shows and does: it opens the entry page and each player, switches versions,
 * turns the captions off and on, paused and playing, and switches a version with them off, watching what the page
 * paints through each switch (player-frames.mjs), clicks every control of the page, reads the browser's own captions
 * control, plays from a chapter and a transcript time and saves each download. The page's film is the video `#film`.
 * player-verdict.mjs judges what it collects. */
import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";
import { mkdtemp, readFile, rm, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { pathToFileURL } from "node:url";

import { coverSamples, decodePng, watchScreen } from "./player-frames.mjs";
import {
  embeddedText,
  entryProblems,
  LANGUAGES,
  parseCues,
  playerProblems,
  verdict,
  visibleCaptionControls,
} from "./player-verdict.mjs";

/* Each version's films, with and without captions, by name ending, and their size, in the order the read switches to
 * them: the UHD version, then the viewing film the page opens on. */
const VERSIONS = [
  ["-uhd.mp4", "-uhd-uncaptioned.mp4", [3840, 2160]],
  ["-1080p-captioned.mp4", "-1080p-uncaptioned.mp4", [1920, 1080]],
];
/* A saved download has this long to end, a page this long to show it left, a switched film this long to show, and a
 * switch is watched this long after it shows, in milliseconds. */
const SAVING = 10000,
  SETTLING = 150,
  SWITCHING = 10000,
  SETTLED = 300;

/** A file's SHA-256, streamed so that a film need not fit in memory. */
export async function digestFile(path) {
  const hash = createHash("sha256");
  for await (const block of createReadStream(path)) hash.update(block);
  return hash.digest("hex");
}

/** Two seconds in, the middle, and four seconds before the end. */
export const seekPoints = (duration) => [2, duration / 2, duration - 4];

/* The page's video, its caption track and its captions control as the browser holds them. */
const videoState = (page) =>
  page.$eval("#film", (video) => {
    const track = video.textTracks[0];
    return {
      src: video.currentSrc.split("/").pop(),
      time: video.currentTime,
      paused: video.paused,
      tracks: video.textTracks.length,
      mode: track?.mode ?? null,
      captions: document.getElementById("captions")?.getAttribute("aria-pressed") ?? null,
    };
  });

/* Pause the film at a time and wait until it is shown there. */
async function standAt(page, time) {
  await page.$eval(
    "#film",
    (video, target) => {
      video.pause();
      video.muted = true;
      video.currentTime = target;
    },
    time,
  );
  await page.waitForFunction(
    (target) => {
      const v = document.getElementById("film");
      return !v.seeking && v.readyState >= 2 && Math.abs(v.currentTime - target) < 0.2;
    },
    {},
    time,
  );
}

/* Play the film the page shows from each seek point; returns its duration, size and error and what each point
 * decoded. */
async function playback(page, file, dimensions, duration) {
  const state = await page.$eval("#film", (video) => ({
    duration: video.duration,
    width: video.videoWidth,
    height: video.videoHeight,
    src: video.currentSrc,
    error: video.error?.code ?? null,
  }));
  Object.assign(state, { file, dimensions, seek_checks: [] });
  for (const target of seekPoints(duration)) {
    await standAt(page, target);
    await page.$eval("#film", (video) => video.play());
    await page.waitForFunction(
      (at) => document.getElementById("film").currentTime > at + 0.35,
      {},
      target,
    );
    const decoded = await page.$eval("#film", (video) => {
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

/* Click a control with the film in view, watching the screen, and wait until the film whose name ends `file` shows,
 * paused or playing as before, then a little longer; returns the time before the click, what the browser showed after
 * it, the seconds that passed until then, and what the page painted meanwhile. A page that does not switch or play on
 * is judged, not waited for. */
async function watchedSwitch(page, selector, file, playing, cover) {
  await page.$eval("#film", (video) => video.scrollIntoView({ block: "start" }));
  const watch = await watchScreen(page, cover);
  const from = await page.$eval("#film", (video) => video.currentTime);
  watch.clicked = Date.now();
  await page.click(selector);
  await page
    .waitForFunction(
      (suffix, play) => {
        const video = document.getElementById("film");
        return video.currentSrc.endsWith(suffix) && video.readyState >= 2 && video.paused === !play;
      },
      { timeout: SWITCHING },
      file,
      playing,
    )
    .catch(() => {});
  const shown = await videoState(page),
    elapsed = (Date.now() - watch.clicked) / 1000;
  await new Promise((resolve) => setTimeout(resolve, SETTLED));
  return { from, ...shown, elapsed, painted: await watch.stop() };
}

/* Switch to a version from a known time, then play it from each seek point; returns what the browser showed. */
async function switchVersion(page, file, dimensions, duration, cover) {
  const from = duration / 3;
  await standAt(page, from);
  const { time, mode, painted } = await watchedSwitch(
    page,
    `[data-captioned$="${file}"]`,
    file,
    false,
    cover,
  );
  // The middle of the middle cue: the hidden track holds it active there, and it marks its paragraph.
  const cueAt = await page.$eval("#film", (video) => {
    const { cues } = video.textTracks[0],
      cue = cues[cues.length >> 1];
    return (cue.startTime + cue.endTime) / 2;
  });
  await standAt(page, cueAt);
  await page
    .waitForFunction(
      () => {
        const [cue] = document.getElementById("film").textTracks[0].activeCues ?? [],
          current = document.querySelector('#transcript p[aria-current="true"]'),
          letters = (text) => text.replace(/[^\p{L}\p{N}]/gu, "");
        return cue && current && letters(current.textContent).includes(letters(cue.text));
      },
      { timeout: 5000 },
    )
    .catch(() => {});
  const marked = await page.$eval("#film", (video) => ({
    active_cue: video.textTracks[0].activeCues?.[0]?.text ?? null,
    current_paragraph:
      document.querySelector('#transcript p[aria-current="true"]')?.textContent ?? null,
  }));
  return {
    ...(await playback(page, file, dimensions, duration)),
    kept_time: [from, time],
    track_mode: mode,
    cue_at: cueAt,
    ...marked,
    painted,
  };
}

/* Click a control from a known time, the film paused or playing, and watch it switch to the film whose name ends
 * `file`; returns what the browser showed. */
async function switchBy(page, selector, file, at, playing, cover) {
  await standAt(page, at);
  if (playing) {
    await page.$eval("#film", (video) => video.play());
    await page.waitForFunction(
      (start) => document.getElementById("film").currentTime > start + 0.1,
      {},
      at,
    );
  }
  const switched = await watchedSwitch(page, selector, file, playing, cover);
  await page.$eval("#film", (video) => video.pause());
  const { from, src, time, paused, mode, captions, elapsed, painted } = switched;
  return {
    file,
    from,
    playing,
    src,
    time,
    paused,
    track_mode: mode,
    pressed: captions,
    elapsed,
    painted,
  };
}

/* Turn the captions off on the viewing film while it is paused, and play it; switch to the UHD version with them off,
 * and play it; then turn them on while the UHD film plays. Returns each switch as the browser showed it. */
async function switchCaptions(page, duration, cover) {
  const [uhd, viewing] = VERSIONS;
  const off = await switchBy(page, "#captions", viewing[1], duration / 3, false, cover);
  const offPlayed = await playback(page, viewing[1], viewing[2], duration);
  const version = `[data-captioned$="${uhd[0]}"]`;
  const moved = await switchBy(page, version, uhd[1], duration / 3, false, cover);
  const movedPlayed = await playback(page, uhd[1], uhd[2], duration);
  const on = await switchBy(page, "#captions", uhd[0], duration / 2, true, cover);
  return [
    { control: "captions", captions: false, ...offPlayed, ...off },
    { control: "version", captions: false, ...movedPlayed, ...moved },
    { control: "captions", captions: true, ...on },
  ];
}

/* Click a button that names a time and wait until the film plays from there. */
async function playFrom(page, selector) {
  const time = await page.$eval(selector, (button) => Number(button.dataset.time));
  await page.click(selector);
  await page.waitForFunction(
    (at) =>
      !document.getElementById("film").paused && document.getElementById("film").currentTime >= at,
    {},
    time,
  );
  const played = await page.$eval("#film", (video) => {
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
    const film = () => document.getElementById("film"),
      controls = [...document.querySelectorAll("button, summary, input, select")],
      shown = [];
    for (const control of controls) {
      control.click();
      await new Promise((resolve) => setTimeout(resolve));
      if (film().textTracks[0].mode === "hidden") continue;
      shown.push(control.textContent);
      film().textTracks[0].mode = "hidden";
    }
    film().pause();
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

/** What one edition's player holds by the delivery: its chapters, the size of each of its members, its WebVTT, the
 * cues of its SRT and its cover's samples, against which a switch's frames are judged. */
async function delivered(root, code, binding) {
  const { slug, duration } = binding.film,
    members = binding.members.map((member) => member.path),
    sizes = new Map();
  for (const member of members.filter((m) => m.startsWith(`${code}/`)))
    sizes.set(member, (await stat(join(root, member))).size);
  const { chapters } = JSON.parse(await readFile(join(root, code, "chapters.json"), "utf8"));
  const vtt = await readFile(join(root, code, `${slug}-${code}.vtt`), "utf8"),
    srt = await readFile(join(root, code, `${slug}-${code}.srt`), "utf8"),
    cover = coverSamples(decodePng(await readFile(join(root, code, `${slug}-cover.png`))));
  return { code, slug, duration, chapters, members, sizes, vtt, srt_cues: parseCues(srt), cover };
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
    await page.waitForFunction(() => document.getElementById("film").readyState >= 1);
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
    read.cues = await page.$eval("#film", (video) =>
      [...video.textTracks[0].cues].map((cue) => [
        Math.round(cue.startTime * 1000),
        Math.round(cue.endTime * 1000),
        cue.text,
      ]),
    );
    read.native_caption_controls = await nativeCaptionControls(page);
    read.saved = await saveDownloads(page, root, code, read.files);
    const { duration } = binding.film;
    for (const [file, , dimensions] of VERSIONS)
      read.editions.push(await switchVersion(page, file, dimensions, duration, expected.cover));
    read.captions = await switchCaptions(page, duration, expected.cover);
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
