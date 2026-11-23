/** Exercise the parts of the delivered-player and cover checks that need no browser: the delivery members, binding
 * verification, PNG decoding and the cover comparison, and how the read clicks the films and covers of a files list,
 * against a stand-in browser. */
import { boundFilm, SAMPLE_FILM } from "./film.mjs";
import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { crc32, deflateSync } from "node:zlib";

import {
  bindingProblems,
  changedMembers,
  compareImages,
  coverReport,
  decodePng,
  deliveryMembers,
  digestFile,
  seekPoints,
} from "../../src/filmkit/delivery/player-check.mjs";
import { openFileLinks } from "../../src/filmkit/delivery/player-read.mjs";
import { PAGE, RECORD } from "../../src/filmkit/picture/stage-contract.mjs";

const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
// The editions last 27:16 and 24:36: a binding names each edition's runtime by its code.
const FILM = SAMPLE_FILM;
const binding = (destination = "/delivery") => ({
  destination,
  film: FILM,
  members: deliveryMembers(FILM).map((path) => ({ path, sha256: sha(path) })),
});

const chunk = (type, body) => {
  const head = Buffer.alloc(8),
    tail = Buffer.alloc(4);
  head.writeUInt32BE(body.length);
  head.write(type, 4, "latin1");
  tail.writeUInt32BE(crc32(Buffer.concat([head.subarray(4), body])));
  return Buffer.concat([head, body, tail]);
};
const paeth = (a, b, c) => {
  const p = a + b - c,
    pa = Math.abs(p - a),
    pb = Math.abs(p - b),
    pc = Math.abs(p - c);
  return pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
};
/** Encode 8-bit RGB or RGBA pixels as a PNG, filtering row y with filter y % 5 so every filter type is exercised. */
function encodePng(width, height, channels, pixels, { depth = 8, interlace = 0 } = {}) {
  const stride = width * channels,
    rows = [];
  for (let y = 0; y < height; y++) {
    const filter = y % 5,
      line = pixels.subarray(y * stride, (y + 1) * stride);
    const above = y ? pixels.subarray((y - 1) * stride, y * stride) : new Uint8Array(stride),
      row = Buffer.alloc(stride + 1);
    row[0] = filter;
    for (let x = 0; x < stride; x++) {
      const a = x < channels ? 0 : line[x - channels],
        b = above[x],
        c = x < channels ? 0 : above[x - channels];
      row[x + 1] = line[x] - [0, a, b, (a + b) >> 1, paeth(a, b, c)][filter];
    }
    rows.push(row);
  }
  const header = Buffer.alloc(13);
  header.writeUInt32BE(width);
  header.writeUInt32BE(height, 4);
  header.set([depth, channels === 4 ? 6 : 2, 0, 0, interlace], 8);
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk("IHDR", header),
    chunk("IDAT", deflateSync(Buffer.concat(rows))),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}
const pattern = (width, height, channels) =>
  Uint8Array.from({ length: width * height * channels }, (_, i) => (i * 37 + (i >> 3) * 91) & 255);
const opaque = (rgb) =>
  Uint8Array.from({ length: (rgb.length / 3) * 4 }, (_, i) =>
    i % 4 === 3 ? 255 : rgb[(i >> 2) * 3 + (i % 4)],
  );

test("the delivery has the entry page and twelve members per language", () => {
  const edition = (code) =>
    [
      `sample-reel-${code}-uhd.mp4`,
      `sample-reel-${code}-1080p-captioned.mp4`,
      `sample-reel-${code}-uhd-uncaptioned.mp4`,
      `sample-reel-${code}-1080p-uncaptioned.mp4`,
      "sample-reel-cover.png",
      "sample-reel-cover.jpg",
      `sample-reel-${code}.srt`,
      `sample-reel-${code}.vtt`,
      `sample-reel-${code}-transcript.md`,
      "chapters.json",
      "chapters.ffmeta",
      "index.html",
    ].map((name) => `${code}/${name}`);
  assert.deepEqual(deliveryMembers(FILM), ["index.html", ...edition("zh"), ...edition("en")]);
  assert.equal(new Set(deliveryMembers(FILM)).size, 25);
});

test("a binding names an absolute destination, the film and exactly its delivery members", () => {
  assert.deepEqual(bindingProblems(binding()), []);
  assert.deepEqual(bindingProblems(binding("Movies/sample-reel")), [
    "destination is not an absolute path",
  ]);
  const finderCopy = binding();
  finderCopy.members.push({ path: "zh/sample-reel-zh 2.srt", sha256: sha("copy") });
  assert.deepEqual(bindingProblems(finderCopy), ["unexpected members: zh/sample-reel-zh 2.srt"]);
  const short = binding();
  short.members = short.members.filter((member) => member.path !== "en/index.html");
  assert.deepEqual(bindingProblems(short), ["missing members: en/index.html"]);
  const twice = binding();
  twice.members.push(twice.members[0]);
  assert.deepEqual(bindingProblems(twice), ["duplicate members"]);
  const unhashed = binding();
  unhashed.members[3].sha256 = "abc";
  assert.deepEqual(bindingProblems(unhashed), [`${unhashed.members[3].path}: no SHA-256`]);
  const misnamed = { ...FILM, slug: "Sample Reel", runtimes: { zh: 0, en: 1476.5, fr: 60 } };
  assert.deepEqual(bindingProblems({ ...binding(), film: misnamed }), [
    "film names no file prefix",
    "film names no runtime for zh",
    "film names no runtime for en",
    "film names a runtime for no edition: fr",
  ]);
  // A binding of the former shape names one duration for the film and no editions, and is refused.
  assert.deepEqual(bindingProblems({ ...binding(), film: { slug: "sample-reel", duration: 60 } }), [
    "film names one duration for the whole film; a binding names each edition's runtime by its code",
    "film names no editions, each with its code, tag and members",
  ]);
  // The editions are the binding's: a film of three editions asks for each one's runtime and members.
  const three = boundFilm("sample-reel", [
    ...FILM.editions.map((e) => [e.code, e.tag, 60]),
    ["xb", "xb", 60],
  ]);
  assert.equal(deliveryMembers(three).length, 37);
  assert.deepEqual(
    bindingProblems({ ...binding(), film: { ...three, runtimes: { zh: 60, en: 60 } } }).slice(0, 2),
    [
      "film names no runtime for xb",
      `missing members: ${deliveryMembers(three)
        .filter((p) => p.startsWith("xb/"))
        .join(", ")}`,
    ],
  );
  // Another film's binding names its own members, so this delivery's are missing and unexpected.
  const other = boundFilm(
    "another",
    FILM.editions.map((e) => [e.code, e.tag, FILM.runtimes[e.code]]),
  );
  const another = { ...binding(), film: other };
  assert.deepEqual(
    bindingProblems(another).map((problem) => problem.split(":")[0]),
    ["missing members", "unexpected members"],
  );
  assert.deepEqual(bindingProblems({}), [
    "destination is not an absolute path",
    "film names no file prefix",
    "film names no editions, each with its code, tag and members",
  ]);
});

test("a delivery readback binds only when it matched its sources with nothing beside them", () => {
  assert.deepEqual(bindingProblems({ ...binding(), all_match: true, unexpected: [] }), []);
  assert.deepEqual(bindingProblems({ ...binding(), all_match: false, unexpected: [] }), [
    "the readback does not match its sources",
  ]);
  assert.deepEqual(
    bindingProblems({ ...binding(), all_match: false, unexpected: ["zh/sample-reel-zh 2.srt"] }),
    [
      "the readback does not match its sources",
      "unexpected entries at the destination: zh/sample-reel-zh 2.srt",
    ],
  );
});

test("members whose destination bytes changed or vanished are found", async () => {
  const destination = await mkdtemp(join(tmpdir(), "delivery-"));
  try {
    await mkdir(join(destination, "zh"));
    const members = [];
    for (const path of ["index.html", "zh/index.html", "zh/chapters.json"]) {
      await writeFile(join(destination, path), `body of ${path}`);
      members.push({ path, sha256: sha(`body of ${path}`) });
    }
    assert.equal(await digestFile(join(destination, "index.html")), sha("body of index.html"));
    assert.deepEqual(await changedMembers({ destination, members }), []);
    await writeFile(join(destination, "zh/index.html"), "edited");
    await rm(join(destination, "zh/chapters.json"));
    assert.deepEqual(await changedMembers({ destination, members }), [
      "zh/index.html",
      "zh/chapters.json",
    ]);
  } finally {
    await rm(destination, { recursive: true, force: true });
  }
});

test("PNG decoding reverses every scanline filter for RGB and RGBA", () => {
  for (const channels of [3, 4]) {
    const pixels = pattern(7, 10, channels),
      decoded = decodePng(encodePng(7, 10, channels, pixels));
    assert.deepEqual([decoded.width, decoded.height], [7, 10]);
    assert.deepEqual(decoded.data, channels === 4 ? pixels : opaque(pixels));
  }
});

test("PNG decoding refuses what it does not decode", () => {
  assert.throws(() => decodePng(Buffer.from("not a png at all")), /Not a PNG/);
  assert.throws(() => decodePng(encodePng(2, 2, 3, pattern(2, 2, 3), { depth: 16 })), /Only 8-bit/);
  assert.throws(
    () => decodePng(encodePng(2, 2, 3, pattern(2, 2, 3), { interlace: 1 })),
    /Only 8-bit/,
  );
  const cut = encodePng(4, 4, 4, pattern(4, 4, 4));
  const header = cut.subarray(16, 24);
  header.writeUInt32BE(5, 4);
  assert.throws(() => decodePng(cut), /does not match its header/);
});

test("the tracked cover decodes at UHD on the film's ground", async () => {
  const cover = decodePng(
    await readFile(
      new URL("../../examples/sample-film/assets/cover/sample-reel-cover-zh.png", import.meta.url),
    ),
  );
  assert.deepEqual([cover.width, cover.height], [3840, 2160]);
  for (const offset of [0, (1079 * 3840 + 1919) * 4, cover.data.length - 4])
    assert.deepEqual([...cover.data.subarray(offset, offset + 4)], [15, 21, 25, 255]);
});

test("cover comparison counts differing pixels and the largest channel difference", () => {
  const rgb = pattern(6, 5, 3),
    painted = decodePng(encodePng(6, 5, 4, opaque(rgb))),
    tracked = decodePng(encodePng(6, 5, 3, rgb));
  // The painted canvas is RGBA and the tracked cover RGB; opaque pixels with equal colour are identical.
  assert.deepEqual(compareImages(painted, tracked), {
    sizes: [
      [6, 5],
      [6, 5],
    ],
    differing_pixels: 0,
    max_difference: 0,
    identical: true,
  });
  const changed = { ...painted, data: Uint8Array.from(painted.data) };
  changed.data[0] = (changed.data[0] + 9) & 255;
  changed.data[4 * 7 + 3] = 200;
  assert.deepEqual(compareImages(changed, tracked), {
    sizes: [
      [6, 5],
      [6, 5],
    ],
    differing_pixels: 2,
    max_difference: 55,
    identical: false,
  });
  const wider = decodePng(encodePng(7, 5, 3, pattern(7, 5, 3)));
  assert.deepEqual(compareImages(wider, tracked), {
    sizes: [
      [7, 5],
      [6, 5],
    ],
    differing_pixels: null,
    max_difference: null,
    identical: false,
  });
});

test("a painting without a tracked cover is reported uncompared and does not pass", () => {
  const painted = encodePng(6, 5, 4, opaque(pattern(6, 5, 3))),
    tracked = encodePng(6, 5, 3, pattern(6, 5, 3));
  assert.deepEqual(coverReport(painted, null), {
    sha256: sha(painted),
    cover_sha256: null,
    sizes: [[6, 5], null],
    differing_pixels: null,
    max_difference: null,
    identical: false,
  });
  assert.deepEqual(coverReport(painted, tracked), {
    sha256: sha(painted),
    cover_sha256: sha(tracked),
    ...compareImages(decodePng(painted), decodePng(tracked)),
  });
});

test("seek points sit two seconds in, at the middle and four seconds before the end", () => {
  assert.deepEqual(seekPoints(1500), [2, 750, 1496]);
});

test("each film and cover link is clicked, the tab it opens is closed, and a player that left is opened again", async () => {
  const home = "file:///delivery/zh/index.html",
    tabs = [],
    closed = [],
    visits = [];
  let address = home;
  // A stand-in browser looks for the new tab once the click has happened, and gives up at once.
  const browser = {
    targets: () => [...tabs],
    waitForTarget: async (found, { timeout }) => {
      await new Promise((resolve) => setTimeout(resolve));
      const tab = tabs.find(found);
      if (!tab) throw Error(`Waiting for target failed: ${timeout}ms exceeded`);
      return tab;
    },
  };
  // A link with a target opens its file in a new tab; one without takes the player there.
  const link = (href, target) => ({
    click: async () => {
      const url = new URL(href, home).href,
        page = async () => ({ close: async () => closed.push(url) });
      if (target) tabs.push({ type: () => "page", url: () => url, page });
      else address = url;
    },
  });
  const page = {
    browser: () => browser,
    url: () => address,
    $$: async () => [
      link("sample-reel-zh-uhd.mp4", "_blank"),
      link("sample-reel-cover.png"),
      link("data:,"),
    ],
    goto: async (url) => visits.push((address = url)),
  };
  const files = [
    { target: "sample-reel-zh-uhd.mp4", embedded: false },
    { target: "sample-reel-cover.png", embedded: false },
    { target: "chapters.json", embedded: true },
  ];
  assert.deepEqual(await openFileLinks(page, files), [
    {
      name: "sample-reel-zh-uhd.mp4",
      address: "file:///delivery/zh/sample-reel-zh-uhd.mp4",
      stayed: true,
    },
    { name: "sample-reel-cover.png", address: null, stayed: false },
  ]);
  // The film's tab is closed, the download is not clicked, and the player is opened again after the cover took it.
  assert.deepEqual(
    [closed, visits, address],
    [["file:///delivery/zh/sample-reel-zh-uhd.mp4"], [home], home],
  );
});

test("the player check refuses a malformed invocation before opening a browser", () => {
  const tool = fileURLToPath(
    new URL("../../src/filmkit/delivery/player-check.mjs", import.meta.url),
  );
  for (const args of [
    [],
    ["players", "binding.json"],
    ["cover", "stage", "cover.png"],
    ["--x"],
    ["play"],
  ]) {
    const result = spawnSync(process.execPath, [tool, ...args], { encoding: "utf8" });
    assert.equal(result.status, 2, args.join(" "));
    assert.equal(result.stdout, "", args.join(" "));
    assert.ok(
      result.stderr.includes("Usage: python -m filmkit.tools player-check"),
      args.join(" "),
    );
  }
});

test("the cover check refuses a stage whose record and page disagree before it paints", async () => {
  const tool = fileURLToPath(
    new URL("../../src/filmkit/delivery/player-check.mjs", import.meta.url),
  );
  const stage = await mkdtemp(join(tmpdir(), "cover-stage-"));
  try {
    // A restaging cut short: the record states the UHD frame, the page another.
    await writeFile(
      join(stage, RECORD),
      JSON.stringify({ width: 3840, height: 2160, duration: 60, fps: 60 }),
    );
    await writeFile(
      join(stage, PAGE),
      '<div id="film" data-width="1920" data-height="1080" data-duration="60"></div>',
    );
    const painting = join(stage, "painting.png");
    const args = [tool, "cover", stage, join(stage, "cover.png"), painting];
    const result = spawnSync(process.execPath, args, { encoding: "utf8" });
    assert.equal(result.status, 1);
    assert.equal(result.stdout, "");
    assert.equal(
      result.stderr,
      `player-check: The stage's page ${join(stage, "index.html")} states a width of 1920 where ` +
        "its record states 3840; run stage-picture again\n",
    );
    await assert.rejects(readFile(painting), { code: "ENOENT" });
  } finally {
    await rm(stage, { recursive: true, force: true });
  }
});

test("the cover check refuses a folder that is no whole stage before it paints", async () => {
  const tool = fileURLToPath(
    new URL("../../src/filmkit/delivery/player-check.mjs", import.meta.url),
  );
  const stage = await mkdtemp(join(tmpdir(), "cover-stage-"));
  try {
    const painting = join(stage, "painting.png");
    const refused = (said) => {
      const args = [tool, "cover", stage, join(stage, "cover.png"), painting];
      const result = spawnSync(process.execPath, args, { encoding: "utf8" });
      assert.equal(result.status, 1, result.stderr);
      assert.equal(result.stdout, "");
      assert.equal(result.stderr, `player-check: The stage's ${said}; run stage-picture again\n`);
    };
    // A page alone states no frame: the record is absent.
    await writeFile(
      join(stage, PAGE),
      '<div id="film" data-width="3840" data-height="2160" data-duration="60"></div>',
    );
    refused(`record ${join(stage, "stage.json")} is absent`);
    // A record that states no rate.
    await writeFile(
      join(stage, RECORD),
      JSON.stringify({ width: 3840, height: 2160, duration: 60 }),
    );
    refused(`record ${join(stage, "stage.json")} states no whole positive fps`);
    // A whole record beside a page that holds no film element.
    await writeFile(
      join(stage, RECORD),
      JSON.stringify({ width: 3840, height: 2160, duration: 60, fps: 60 }),
    );
    await writeFile(join(stage, PAGE), "<!doctype html><title>no film</title>");
    refused(`page ${join(stage, "index.html")} holds no film element`);
    await assert.rejects(readFile(painting), { code: "ENOENT" });
  } finally {
    await rm(stage, { recursive: true, force: true });
  }
});

/** The cover check run on a folder: its status, its output and its error text. */
function paintedFrom(stage) {
  const tool = fileURLToPath(
    new URL("../../src/filmkit/delivery/player-check.mjs", import.meta.url),
  );
  const args = [tool, "cover", stage, join(stage, "cover.png"), join(stage, "painting.png")];
  return spawnSync(process.execPath, args, { encoding: "utf8" });
}

test("the cover check refuses a stage whose record holds no JSON before it paints", async () => {
  const stage = await mkdtemp(join(tmpdir(), "cover-stage-"));
  try {
    await writeFile(join(stage, RECORD), "{");
    await writeFile(
      join(stage, PAGE),
      '<div id="film" data-width="3840" data-height="2160" data-duration="60"></div>',
    );
    const result = paintedFrom(stage);
    const said = `player-check: The stage's record ${join(stage, "stage.json")} holds no JSON (`;
    assert.equal(result.status, 1, result.stderr);
    assert.equal(result.stdout, "");
    assert.ok(result.stderr.startsWith(said), result.stderr);
    assert.ok(result.stderr.endsWith("); run stage-picture again\n"), result.stderr);
    assert.equal(result.stderr.split("\n").length, 2, result.stderr);
    await assert.rejects(readFile(join(stage, "painting.png")), { code: "ENOENT" });
  } finally {
    await rm(stage, { recursive: true, force: true });
  }
});

test("the cover check refuses a stage without its page before it paints", async () => {
  const stage = await mkdtemp(join(tmpdir(), "cover-stage-"));
  try {
    await writeFile(
      join(stage, RECORD),
      JSON.stringify({ width: 3840, height: 2160, duration: 60, fps: 60 }),
    );
    const result = paintedFrom(stage);
    assert.equal(result.status, 1, result.stderr);
    assert.equal(result.stdout, "");
    assert.equal(
      result.stderr,
      `player-check: The stage's page ${join(stage, "index.html")} is absent; ` +
        "run stage-picture again\n",
    );
    await assert.rejects(readFile(join(stage, "painting.png")), { code: "ENOENT" });
  } finally {
    await rm(stage, { recursive: true, force: true });
  }
});
