/** Read the delivered players back in a real browser, and paint the cover from a staged document.
 *
 * players: a binding names the destination, the film's file prefix, each edition's runtime by its code, and the
 * SHA-256 of each of the delivery members (the delivery readback, or a review round's artifacts binding). The member bytes are checked before and after the browser read.
 * The read (player-read.mjs, judged by player-verdict.mjs) opens the language entry page and each language's player, and records each page with a
 * verdict of its own in the receipt's `pages`: every link leads to a member or a sibling page; the captioned viewing
 * edition plays first with its captions control pressed; the control turns the captions off and on, paused and
 * playing, onto the other film of the version, and a version button keeps them off, each keeping the time and whether
 * the film plays; the one track, which embeds the delivered WebVTT and whose cues equal the SRT's, stays hidden on
 * every film since the pictures draw the captions, and no control of the page or the browser can show it; a cue marks
 * its transcript paragraph; a version switch keeps the time; all four films' duration and dimensions with decoding at
 * three seek points; a chapter jump and a transcript time that play from their time; the language links; the sizes the
 * files list names, each film and cover link opening its file in a new tab while the player stays, no link that opens
 * raw text, and the bytes each download saves without leaving the page. Requests outside the destination are refused
 * and recorded; screenshots are written beside the receipt.
 * cover: paints window.renderCover() from a staged UHD document and compares its pixels with the tracked cover; a
 * painting with no tracked cover yet is written, reported uncompared and fails, so the painting can become the cover.
 * No human hearing or complete-film playback is claimed.
 * Its usage is `USAGE`, which it prints when it is invoked wrongly. */
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { isAbsolute, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { parseArgs } from "node:util";

import { launchBrowser } from "../picture/headless-browser.mjs";
import { frameContract, PAGE, StageError } from "../picture/stage-contract.mjs";
import { decodePng } from "./player-frames.mjs";
import { digestFile, readDelivery } from "./player-read.mjs";
import { seekPoints } from "./player-verdict.mjs";

export { decodePng, digestFile, seekPoints };

const USAGE =
  "Usage: python -m filmkit.tools player-check players <binding.json> <receipt.json>\n" +
  "       python -m filmkit.tools player-check cover <stage-dir> <cover.png> <output.png>";
/* A film's file prefix: lowercase words joined by hyphens. */
const SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/;
const DEADLINE = 300000;
/* The signal that asks a check to end, which the engine's tools send. An interrupt is left to the
 * browser's driver, which kills its browser and exits the process with status 130: the check then
 * writes no receipt. */
const ENDING = "SIGTERM";

const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");

/** A film's delivery members, as its binding names its editions in the declared order: the language entry page, then
 * each edition's members below the folder of its code. */
export function deliveryMembers(film) {
  return [
    "index.html",
    ...film.editions.flatMap(({ code, members }) => members.map((name) => `${code}/${name}`)),
  ];
}

/* An edition of a binding: its code, its language's BCP 47 tag and its members' names. */
const EDITION = (edition) =>
  typeof edition?.code === "string" &&
  /^[a-z]{2,3}$/.test(edition.code) &&
  typeof edition?.tag === "string" &&
  edition.tag.length > 0 &&
  Array.isArray(edition?.members) &&
  edition.members.length > 0 &&
  edition.members.every(
    (name) => typeof name === "string" && name.length > 0 && !name.includes("/"),
  );

/** Why a binding does not name one delivery; none for a binding with an absolute destination, the film's file prefix
 * and each edition's runtime by its code, a positive whole number of seconds, and exactly the film's delivery members,
 * each once with a SHA-256. A binding that names one duration for the film, as bindings did before the editions could
 * differ in length, is refused. A delivery readback must also have matched its sources with nothing beside them. */
export function bindingProblems(binding) {
  const problems = [];
  if (typeof binding?.destination !== "string" || !isAbsolute(binding.destination))
    problems.push("destination is not an absolute path");
  const slug = binding?.film?.slug,
    named = typeof slug === "string" && SLUG.test(slug);
  if (!named) problems.push("film names no file prefix");
  const runtimes = binding?.film?.runtimes;
  if (binding?.film && Object.hasOwn(binding.film, "duration"))
    problems.push(
      "film names one duration for both editions; a binding names each edition's runtime by its code",
    );
  const editions = binding?.film?.editions,
    listed = Array.isArray(editions) && editions.length > 0 && editions.every(EDITION);
  if (!listed) problems.push("film names no editions, each with its code, tag and members");
  const codes = listed ? editions.map((edition) => edition.code) : [];
  if (new Set(codes).size !== codes.length) problems.push("film names an edition twice");
  for (const code of codes)
    if (!(Number.isInteger(runtimes?.[code]) && runtimes[code] > 0))
      problems.push(`film names no runtime for ${code}`);
  const other = Object.keys(runtimes ?? {}).filter((code) => !codes.includes(code));
  if (other.length) problems.push(`film names a runtime for no edition: ${other.join(", ")}`);
  if (binding?.all_match === false) problems.push("the readback does not match its sources");
  if (binding?.unexpected?.length)
    problems.push(`unexpected entries at the destination: ${binding.unexpected.join(", ")}`);
  const members = Array.isArray(binding?.members) ? binding.members : [];
  const paths = members.map((member) => member?.path),
    expected = named && listed ? deliveryMembers(binding.film) : paths;
  const missing = expected.filter((path) => !paths.includes(path)),
    extra = paths.filter((path) => !expected.includes(path));
  if (missing.length) problems.push(`missing members: ${missing.join(", ")}`);
  if (extra.length) problems.push(`unexpected members: ${extra.join(", ")}`);
  if (new Set(paths).size !== paths.length) problems.push("duplicate members");
  for (const member of members)
    if (!/^[0-9a-f]{64}$/.test(member?.sha256 ?? "")) problems.push(`${member?.path}: no SHA-256`);
  return problems;
}

/** The bound members whose bytes at the destination differ from the binding or are absent. */
export async function changedMembers(binding) {
  const changed = [];
  for (const member of binding.members) {
    const value = await digestFile(join(binding.destination, member.path)).catch(() => null);
    if (value !== member.sha256) changed.push(member.path);
  }
  return changed;
}

/** Compare two decoded images: how many pixels differ and the largest channel difference. Images of different
 * sizes are not compared. */
export function compareImages(a, b) {
  const sizes = [
    [a.width, a.height],
    [b.width, b.height],
  ];
  if (a.width !== b.width || a.height !== b.height)
    return { sizes, differing_pixels: null, max_difference: null, identical: false };
  let differing = 0,
    largest = 0;
  for (let i = 0; i < a.data.length; i += 4) {
    let difference = 0;
    for (let k = i; k < i + 4; k++)
      difference = Math.max(difference, Math.abs(a.data[k] - b.data[k]));
    if (difference) {
      differing++;
      largest = Math.max(largest, difference);
    }
  }
  return {
    sizes,
    differing_pixels: differing,
    max_difference: largest,
    identical: differing === 0,
  };
}

/** Each named screenshot that was written, with its SHA-256, as a receipt lists it. The read
 * removes a file where it names its screenshot, so a file that stands under a name is the one this
 * check wrote. */
export async function writtenScreenshots(paths) {
  const written = [];
  for (const path of paths) {
    const sha256 = await digestFile(path).catch(() => null);
    if (sha256) written.push({ path, sha256 });
  }
  return written;
}

async function readPlayers(browser, binding, receiptPath, report, screenshots) {
  assert.deepEqual(
    await changedMembers(binding),
    [],
    "Delivered members differ from their binding",
  );
  const page = await browser.newPage();
  page.setDefaultTimeout(30000);
  page.on("pageerror", (error) => report.console_errors.push(String(error)));
  page.on("console", (message) => {
    if (message.type() === "error") report.console_errors.push(message.text());
    if (message.type() === "warn") report.console_warnings.push(message.text());
  });
  page.on("requestfailed", (request) => {
    const error = request.failure()?.errorText;
    if (error !== "net::ERR_ABORTED") report.request_failures.push({ url: request.url(), error });
  });
  await page.setRequestInterception(true);
  page.on("request", (request) => {
    if (
      request.url().startsWith(pathToFileURL(binding.destination + "/").href) ||
      request.url().startsWith("data:")
    )
      request.continue();
    else {
      report.external_requests.push(request.url());
      request.abort();
    }
  });
  report.pages = await readDelivery(page, binding, receiptPath, screenshots);
  const failed = report.pages.filter((item) => item.verdict !== "pass").map((item) => item.page);
  assert.deepEqual(failed, [], "Pages failed their checks");
  assert.deepEqual(report.external_requests, []);
  assert.deepEqual(report.request_failures, []);
  assert.deepEqual(report.console_errors, []);
  assert.deepEqual(await changedMembers(binding), [], "Delivered members changed during the read");
  report.members_unchanged = binding.members.length;
  await page.close();
}

/** What ends a read that does not end by itself, in one place: `ended` rejects once `deadline` ms
 * have passed or the process is asked to end (`ENDING`), which the report then names as its
 * `signal`; `disarm()` takes both back. */
function readEnd(report, deadline) {
  let disarm;
  const ended = new Promise((_, reject) => {
    const timer = setTimeout(() => reject(Error("Owned browser deadline exceeded")), deadline);
    const asked = (signal) => {
      report.signal = signal;
      reject(Error(`The check was asked to end by ${signal}`));
    };
    process.on(ENDING, asked);
    disarm = () => {
      clearTimeout(timer);
      process.off(ENDING, asked);
    };
  });
  return { ended, disarm };
}

/** Read the bound delivery's players back within an owned browser deadline and write the receipt.
 * `launch` launches the browser and `deadline` is the read's time in ms. A read that throws, meets
 * its deadline or is asked to end (`ENDING`) closes the same way: the browser is closed and the
 * receipt written, listing what the read wrote. */
export async function checkPlayers(
  bindingPath,
  receiptPath,
  launch = launchBrowser,
  deadline = DEADLINE,
) {
  const binding = JSON.parse(await readFile(bindingPath, "utf8"));
  const report = {
    started_at: new Date().toISOString(),
    destination: binding.destination,
    binding_sha256: await digestFile(bindingPath),
    scope:
      "Real-browser links, the captions control, the hidden caption track and every control that could show it, version switching, decode at seek points, chapter and transcript seeking, the files list, the new tabs its film and cover links open and its downloads, with a verdict per page; no human hearing or complete-film playback",
    pages: [],
    console_errors: [],
    console_warnings: [],
    request_failures: [],
    external_requests: [],
    screenshots: [],
  };
  // The screenshots' paths as the read names them, each before its player is read.
  const screenshots = [];
  let browser, end;
  try {
    const problems = bindingProblems(binding);
    if (problems.length) throw Error(`Not a delivery binding: ${problems.join("; ")}`);
    browser = await launch({
      args: ["--autoplay-policy=no-user-gesture-required"],
      defaultViewport: { width: 1600, height: 1000, deviceScaleFactor: 1 },
    });
    report.browser_version = await browser.version();
    end = readEnd(report, deadline);
    const reading = readPlayers(browser, binding, receiptPath, report, screenshots);
    // A read still running when it is ended fails once its browser closes; that late failure is
    // already reported.
    reading.catch(() => {});
    await Promise.race([reading, end.ended]);
    report.pass = true;
  } catch (error) {
    report.pass = false;
    report.error = String(error.stack ?? error);
  } finally {
    if (browser) await browser.close();
    report.browser_closed = true;
    // Listed once the browser is closed, so that a read that stopped, met its deadline or was asked
    // to end leaves no screenshot beside the receipt that the receipt does not name.
    report.screenshots = await writtenScreenshots(screenshots);
    report.finished_at = new Date().toISOString();
    await writeFile(receiptPath, JSON.stringify(report, null, 2) + "\n");
    // A signal is held off until the receipt is written.
    end?.disarm();
  }
  return report;
}

/** Print a check's summary and end the process as the check ended: with status 0 for a pass and 1
 * for a refusal, or, for a check that a signal ended, by that signal, now that its receipt is
 * written. */
export function endAs(report) {
  const pages = report.pages.map((item) => `${item.page}: ${item.verdict}`);
  console.log(JSON.stringify({ pass: report.pass, error: report.error, pages }));
  process.exitCode = report.pass ? 0 : 1;
  if (report.signal) process.kill(process.pid, report.signal);
}

/** Report a painted cover against the tracked cover's bytes. A painting without a tracked cover is uncompared and does
 * not pass, so a first painting is never taken for a match. */
export function coverReport(painted, tracked) {
  const image = decodePng(painted);
  if (tracked === null)
    return {
      sha256: digest(painted),
      cover_sha256: null,
      sizes: [[image.width, image.height], null],
      differing_pixels: null,
      max_difference: null,
      identical: false,
    };
  return {
    sha256: digest(painted),
    cover_sha256: digest(tracked),
    ...compareImages(image, decodePng(tracked)),
  };
}

/** Paint the cover from a staged UHD document at the frame its stage states, write it, and compare its pixels with
 * the tracked cover, if any. A stage whose record and page disagree throws `StageError` before a browser opens, as the
 * geometry check refuses it (`stage-contract.mjs`). */
export async function paintCover(stage, cover, output) {
  const [width, height] = await frameContract(stage);
  const browser = await launchBrowser({
    args: ["--allow-file-access-from-files"],
    defaultViewport: { width, height, deviceScaleFactor: 1 },
  });
  try {
    const page = await browser.newPage();
    await page.goto(pathToFileURL(resolve(stage, PAGE)).href, {
      waitUntil: "load",
      timeout: 60000,
    });
    await page.evaluate(() => window.__filmReady);
    await page.evaluate(() => document.fonts.ready);
    const data = await page.evaluate(() => {
      window.renderCover();
      return document.getElementById("picture").toDataURL("image/png");
    });
    const painted = Buffer.from(data.split(",")[1], "base64");
    await writeFile(output, painted);
    const tracked = await readFile(cover).catch((error) => {
      if (error.code === "ENOENT") return null;
      throw error;
    });
    return { output, cover, ...coverReport(painted, tracked) };
  } finally {
    await browser.close();
  }
}

if (import.meta.main) {
  let positionals = [];
  try {
    ({ positionals } = parseArgs({ allowPositionals: true }));
  } catch (error) {
    console.error(error.message);
  }
  const [command, ...args] = positionals;
  if (command === "players" && args.length === 2) {
    endAs(await checkPlayers(args[0], args[1]));
  } else if (command === "cover" && args.length === 3) {
    // A folder that is no whole stage is refused in one line with status 1, before a browser opens or a painting is
    // written.
    const result = await paintCover(args[0], args[1], args[2]).catch((error) => {
      if (!(error instanceof StageError)) throw error;
      console.error(`player-check: ${error.message}`);
      return null;
    });
    if (result !== null) console.log(JSON.stringify(result));
    process.exitCode = result?.identical ? 0 : 1;
  } else {
    console.error(USAGE);
    process.exitCode = 2;
  }
}
