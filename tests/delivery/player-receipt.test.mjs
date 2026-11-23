/** Exercise what the player check's receipt lists and how a check ends, against a stand-in browser:
 * the screenshots a read names and wrote, a read that meets its deadline, screenshots an earlier
 * check left, the interrupt the driver is told to leave, and a check asked to end by a signal. */
import { SAMPLE_FILM } from "./film.mjs";
import test from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdir, mkdtemp, readdir, readFile, rm, stat, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { setTimeout as wait } from "node:timers/promises";

import {
  checkPlayers,
  deliveryMembers,
  writtenScreenshots,
} from "../../src/filmkit/delivery/player-check.mjs";
import { readDelivery } from "../../src/filmkit/delivery/player-read.mjs";

const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const FILM = SAMPLE_FILM;
/* A PNG of one pixel, which an edition's read decodes as the delivery's cover. */
const COVER = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhf" +
    "DwAChwGA60e6kgAAAABJRU5ErkJggg==",
  "base64",
);

test("a delivery's read names each screenshot before its player is read, also when the reads stop", async () => {
  const closed = { goto: async () => Promise.reject(Error("net::ERR_FILE_NOT_FOUND")) };
  const binding = {
    destination: "/nowhere",
    film: FILM,
    members: [],
  };
  const named = [];
  const pages = await readDelivery(closed, binding, "/receipts/player-check.json", named);
  assert.deepEqual(
    pages.map((page) => page.verdict),
    ["fail", "fail", "fail"],
  );
  // The receipt lists what the read wrote by these names, the one place a screenshot is named.
  assert.deepEqual(named, ["/receipts/player-zh.png", "/receipts/player-en.png"]);
});

test("a receipt lists each named screenshot that was written, with its SHA-256, and no other", async () => {
  const folder = await mkdtemp(join(tmpdir(), "receipt-"));
  try {
    const written = join(folder, "player-zh.png"),
      stopped = join(folder, "player-en.png");
    await writeFile(written, "a screenshot");
    // A read that stopped before its screenshot leaves a name without a file: it is not listed.
    assert.deepEqual(await writtenScreenshots([written, stopped]), [
      { path: written, sha256: sha("a screenshot") },
    ]);
    assert.deepEqual(await writtenScreenshots([]), []);
  } finally {
    await rm(folder, { recursive: true, force: true });
  }
});

/** Write a delivery's 25 members below `folder`/delivery and its binding beside them, and return
 * the binding's and the receipt's paths: each member holds what an edition's read takes from the
 * folder before it opens the player. */
async function boundDelivery(folder) {
  const destination = join(folder, "delivery"),
    members = [];
  for (const path of deliveryMembers(FILM)) {
    const body = path.endsWith(".png") ? COVER : path.endsWith(".json") ? '{"chapters": []}' : path;
    await mkdir(dirname(join(destination, path)), { recursive: true });
    await writeFile(join(destination, path), body);
    members.push({ path, sha256: sha(body) });
  }
  await writeFile(
    join(folder, "binding.json"),
    JSON.stringify({ destination, film: FILM, members }),
  );
  return [join(folder, "binding.json"), join(folder, "player-check.json")];
}

/** A stand-in for the browser's launcher, by a plan of plain values. Its page reads nothing:
 * opening the player of an edition among `writes` writes that player's screenshot into `folder`,
 * as its read would further on; the player of the edition `hangs` then never opens, and any other
 * page's read stops there. Like the driver, the launcher ends the process at once on an interrupt,
 * with status 130, unless its options tell it to leave the interrupt to its caller. */
const standIn =
  ({ folder, writes, hangs }) =>
  async (options) => {
    // Read in node_modules/@puppeteer/browsers/lib/launch.js: `handleSIGINT`, `process.exit(130)`.
    if (options.handleSIGINT !== false) process.on("SIGINT", () => process.exit(130));
    return {
      version: async () => "stand-in",
      close: async () => {},
      newPage: async () => ({
        setDefaultTimeout() {},
        on() {},
        setRequestInterception: async () => {},
        goto: async (url) => {
          const code = url.split("/").at(-2);
          if (writes.includes(code))
            await writeFile(`${folder}/player-${code}.png`, `${code} screenshot`);
          if (code === hangs) await new Promise(() => {});
          throw Error("the stand-in opens no page");
        },
      }),
    };
  };

const listed = async (receipt) => JSON.parse(await readFile(receipt, "utf8")).screenshots;
const images = async (folder) => (await readdir(folder)).filter((name) => name.endsWith(".png"));

for (const [hangs, title] of [
  ["zh", "the first player wrote its screenshot and never returned"],
  ["en", "the second player never returned"],
])
  test(`a check that meets its deadline lists the screenshot it wrote: ${title}`, async () => {
    const folder = await mkdtemp(join(tmpdir(), "deadline-"));
    try {
      const [binding, receipt] = await boundDelivery(folder);
      // The deadline is short for a test and long against the stand-in's work, which a busy
      // host slows.
      const report = await checkPlayers(
        binding,
        receipt,
        standIn({ folder, writes: ["zh"], hangs }),
        1500,
      );
      assert.equal(report.pass, false);
      assert.match(report.error, /Owned browser deadline exceeded/);
      // The receipt on disk lists the one screenshot the check wrote, and the folder holds no
      // other image.
      assert.deepEqual(await listed(receipt), [
        { path: join(folder, "player-zh.png"), sha256: sha("zh screenshot") },
      ]);
      assert.deepEqual(await images(folder), ["player-zh.png"]);
    } finally {
      await rm(folder, { recursive: true, force: true });
    }
  });

test("a receipt lists no screenshot that an earlier check left, and the folder keeps none", async () => {
  const folder = await mkdtemp(join(tmpdir(), "earlier-"));
  try {
    const [binding, receipt] = await boundDelivery(folder);
    for (const code of ["zh", "en"])
      await writeFile(join(folder, `player-${code}.png`), "an earlier check's");
    // Both players' reads stop before their screenshots.
    const report = await checkPlayers(
      binding,
      receipt,
      standIn({ folder, writes: [], hangs: null }),
    );
    assert.match(report.error, /Pages failed their checks/);
    assert.deepEqual(await listed(receipt), []);
    assert.deepEqual(await images(folder), []);
  } finally {
    await rm(folder, { recursive: true, force: true });
  }
});

/** Wait until `path` stands, at most 20 s and no longer than the process `check` lives. */
async function standing(check, path) {
  for (
    let tries = 0;
    tries < 1000 && check.exitCode === null && !(await stat(path).catch(() => null));
    tries++
  )
    await wait(20);
}

/** Run the check as a process of its own, as the engine's tools run it, with the stand-in for its
 * browser, whose first player writes its screenshot and never returns. Once the screenshot stands,
 * the check is sent `asked`. Returns the status and the signal the process ended by, its receipt,
 * or null where it wrote none, the screenshot's path and the images its folder then held. */
async function sent(asked) {
  const folder = await mkdtemp(join(tmpdir(), "signal-"));
  try {
    const [binding, receipt] = await boundDelivery(folder),
      shot = join(folder, "player-zh.png"),
      tool = new URL("../../src/filmkit/delivery/player-check.mjs", import.meta.url).href,
      planned = JSON.stringify({ folder, writes: ["zh"], hangs: "zh" });
    const script = [
      'import { writeFile } from "node:fs/promises";',
      `import { checkPlayers, endAs } from ${JSON.stringify(tool)};`,
      `const launch = (${standIn})(${planned});`,
      `endAs(await checkPlayers(${JSON.stringify(binding)}, ${JSON.stringify(receipt)}, launch));`,
    ].join("\n");
    const check = spawn(process.execPath, ["--input-type=module", "-e", script], {
      stdio: "ignore",
    });
    const ended = new Promise((resolve) =>
      check.on("exit", (status, signal) => resolve({ status, signal })),
    );
    await standing(check, shot);
    check.kill(asked);
    const { status, signal } = await ended;
    const written = JSON.parse(await readFile(receipt, "utf8").catch(() => "null"));
    return { status, signal, receipt: written, shot, left: await images(folder) };
  } finally {
    await rm(folder, { recursive: true, force: true });
  }
}

test("a check asked to end by SIGTERM writes its receipt and ends by that signal", async () => {
  const { status, signal, receipt, shot } = await sent("SIGTERM");
  assert.deepEqual([status, signal], [null, "SIGTERM"]);
  assert.equal(receipt.signal, "SIGTERM");
  assert.deepEqual(receipt.screenshots, [{ path: shot, sha256: sha("zh screenshot") }]);
});

test("an interrupted check ends with status 130, no receipt and the image left", async () => {
  // An interrupt is the driver's: it kills its browser and exits, and the check closes nothing.
  const { status, signal, receipt, left } = await sent("SIGINT");
  assert.deepEqual([status, signal], [130, null]);
  assert.equal(receipt, null);
  assert.deepEqual(left, ["player-zh.png"]);
});
