/** The headless browser the film's real-browser checks drive: the chrome-headless-shell that the supply task installs
 * below the film's build/runtime/tool-cache, launched through the film's locked puppeteer-core. The checks run at the
 * film's root; FILM_CHROMIUM_PATH names another browser. */
import { readdir } from "node:fs/promises";
import { join, resolve } from "node:path";

import puppeteer from "puppeteer-core";

/* The supplied browser builds, below the root of the film, the folder a check runs in. */
const BROWSERS = "build/runtime/tool-cache/browsers/chrome-headless-shell";

/** The newest macOS arm64 chrome-headless-shell in a folder of builds, or none. */
export async function newestBrowser(folder) {
  const version = (await readdir(folder).catch(() => []))
    .filter((v) => v.startsWith("mac_arm-"))
    .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }))
    .at(-1);
  return version && join(folder, version, "chrome-headless-shell-mac-arm64/chrome-headless-shell");
}

/** The browser to run: FILM_CHROMIUM_PATH, or the newest supplied chrome-headless-shell. */
export async function browserPath() {
  if (process.env.FILM_CHROMIUM_PATH) return process.env.FILM_CHROMIUM_PATH;
  const supplied = await newestBrowser(resolve(BROWSERS));
  if (!supplied) throw Error("No supplied browser; run the supply task or set FILM_CHROMIUM_PATH");
  return supplied;
}

/** Launch that browser headless through `driver`; `options` are puppeteer's launch options, such as its arguments
 * and viewport. */
export async function launchBrowser(options, driver = puppeteer) {
  return driver.launch({ executablePath: await browserPath(), headless: true, ...options });
}
