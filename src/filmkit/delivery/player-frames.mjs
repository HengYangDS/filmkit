/** What a player paints while it switches films, as a screencast of the real browser shows it.
 *
 * player-read.mjs watches each switch from before its click until it settles. Each frame is sampled on a grid over the
 * box of the page's film, less its bottom, where the browser's own controls lie, and judged against the frames before
 * and after the switch and the delivered cover: a frame within COVER levels of the cover and NEARER levels nearer to
 * it than to both of those paints the cover, and a frame whose samples nearly all lie within SPREAD levels of their
 * median colour, while neither of those does, paints one flat colour where the film should be. On the essentials
 * films the cover frames lay 0.9 to 1.1 levels from the cover and the films' own frames 14 to 15, and the films'
 * frames held 93 to 98% of their samples in the ground, so a film's own frames, however close to its title card or its
 * ground, stay nearer the frames around the switch. player-verdict.mjs judges what a switch painted. */
import { inflateSync } from "node:zlib";

/* The grid's columns and rows, and the share of the box's height above the browser's controls. */
const COLUMNS = 64,
  ROWS = 36,
  FREE = 0.85;
/* A cover frame lies within COVER levels of the cover and NEARER levels nearer to it than to the frames around the
 * switch; a flat frame holds FLAT of its samples within SPREAD levels of their median colour. */
const COVER = 8,
  NEARER = 3,
  FLAT = 0.995,
  SPREAD = 10;
/* The screencast's largest frame, in pixels, and how long its first frame may take, in milliseconds. */
const CAST = { maxWidth: 800, maxHeight: 500 },
  FIRST = 2000;

const paeth = (a, b, c) => {
  const p = a + b - c,
    pa = Math.abs(p - a),
    pb = Math.abs(p - b),
    pc = Math.abs(p - c);
  return pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
};

/** Decode a PNG buffer, 8-bit and non-interlaced RGB or RGBA, into RGBA pixels; RGB pixels are opaque. */
export function decodePng(bytes) {
  if (!bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])))
    throw Error("Not a PNG");
  let width = 0,
    height = 0,
    channels = 0;
  const data = [];
  for (let at = 8; at + 8 <= bytes.length;) {
    const length = bytes.readUInt32BE(at),
      type = bytes.toString("latin1", at + 4, at + 8),
      body = bytes.subarray(at + 8, at + 8 + length);
    if (type === "IHDR") {
      [width, height] = [body.readUInt32BE(0), body.readUInt32BE(4)];
      channels = { 2: 3, 6: 4 }[body[9]] ?? 0;
      if (body[8] !== 8 || !channels || body[12] !== 0)
        throw Error("Only 8-bit non-interlaced RGB or RGBA PNG is decoded");
    } else if (type === "IDAT") data.push(body);
    else if (type === "IEND") break;
    at += 12 + length;
  }
  const raw = inflateSync(Buffer.concat(data)),
    stride = width * channels;
  if (!channels || raw.length !== (stride + 1) * height)
    throw Error("PNG pixel data does not match its header");
  const pixels = new Uint8Array(width * height * 4);
  let line = new Uint8Array(stride),
    above = new Uint8Array(stride);
  for (let y = 0; y < height; y++) {
    const start = y * (stride + 1),
      filter = raw[start];
    if (filter > 4) throw Error(`Unknown PNG filter ${filter}`);
    for (let x = 0; x < stride; x++) {
      const a = x < channels ? 0 : line[x - channels],
        b = above[x],
        c = x < channels ? 0 : above[x - channels];
      const predicted =
        filter === 0
          ? 0
          : filter === 1
            ? a
            : filter === 2
              ? b
              : filter === 3
                ? (a + b) >> 1
                : paeth(a, b, c);
      line[x] = (raw[start + 1 + x] + predicted) & 255;
    }
    for (let x = 0, i = 0, o = y * width * 4; x < width; x++, i += channels, o += 4) {
      pixels[o] = line[i];
      pixels[o + 1] = line[i + 1];
      pixels[o + 2] = line[i + 2];
      pixels[o + 3] = channels === 4 ? line[i + 3] : 255;
    }
    [line, above] = [above, line];
  }
  return { width, height, data: pixels };
}

/** The RGB samples of a decoded image on the grid over a box, [x, y, width, height] in its pixels, less the box's
 * bottom; a sample outside the image is null. */
export function samplesOf(image, [x, y, width, height]) {
  const samples = [];
  for (let row = 0; row < ROWS; row++)
    for (let column = 0; column < COLUMNS; column++) {
      const px = Math.floor(x + ((column + 0.5) * width) / COLUMNS),
        py = Math.floor(y + ((row + 0.5) * height * FREE) / ROWS),
        inside = px >= 0 && py >= 0 && px < image.width && py < image.height,
        o = (py * image.width + px) * 4;
      samples.push(inside ? [image.data[o], image.data[o + 1], image.data[o + 2]] : null);
    }
  return samples;
}

/** The mean absolute difference of two frames' samples per channel, in levels, over the samples both hold. */
export function distance(a, b) {
  let sum = 0,
    count = 0;
  a.forEach((p, k) => {
    const q = b[k];
    if (!p || !q) return;
    sum += Math.abs(p[0] - q[0]) + Math.abs(p[1] - q[1]) + Math.abs(p[2] - q[2]);
    count += 3;
  });
  return count ? sum / count : Infinity;
}

/** Whether a frame is one flat colour: FLAT of its samples within SPREAD levels of their median colour. */
export function flat(samples) {
  const held = samples.filter(Boolean);
  if (!held.length) return false;
  const median = [0, 1, 2].map(
    (k) => held.map((p) => p[k]).sort((a, b) => a - b)[held.length >> 1],
  );
  const near = held.filter((p) => p.every((v, k) => Math.abs(v - median[k]) <= SPREAD));
  return near.length >= FLAT * held.length;
}

/** What a switch painted, from its frames' times after the click (`at`, in ms) and samples, in order, and the cover's
 * samples: how many frames were read, and the times of those that painted the cover or one flat colour. The last
 * frame before the click and the last frame read are the film's frames around the switch. */
export function paintedFrames(frames, cover) {
  const before = frames.findLast((frame) => frame.at < 0),
    after = frames.at(-1);
  const read = { frames: frames.length, cover: [], flat: [] };
  if (!before || after === before) return { ...read, unread: true };
  const flatAround = flat(before.samples) || flat(after.samples);
  for (const { at, samples } of frames.filter((frame) => frame.at >= 0)) {
    const near = Math.min(distance(samples, before.samples), distance(samples, after.samples)),
      fromCover = distance(samples, cover);
    if (fromCover <= COVER && fromCover + NEARER < near) read.cover.push(Math.round(at));
    else if (!flatAround && flat(samples)) read.flat.push(Math.round(at));
  }
  return read;
}

/** The cover's samples on the grid over the whole of it, as the poster fills the film's box. */
export const coverSamples = (image) => samplesOf(image, [0, 0, image.width, image.height]);

/** Start a screencast of the page and return, once its first frame has come, `stop()`, which ends it and resolves what
 * the switch painted in the box of the page's film, judged against `cover`, the cover's samples, with each frame's time
 * after `clicked`, a Date.now() the caller sets just before its click. A page that sends no frame within FIRST ms is
 * watched all the same, and a switch without a frame before its click reads as not watched. */
export async function watchScreen(page, cover) {
  const client = await page.createCDPSession(),
    frames = [];
  const box = await page.$eval("#film", (video) => {
    const r = video.getBoundingClientRect();
    return [r.x + window.scrollX, r.y + window.scrollY, r.width, r.height];
  });
  let first;
  const started = new Promise((resolve) => {
    first = resolve;
    setTimeout(resolve, FIRST);
  });
  client.on("Page.screencastFrame", ({ data, metadata, sessionId }) => {
    frames.push({ data, metadata });
    first();
    client.send("Page.screencastFrameAck", { sessionId }).catch(() => {});
  });
  await client.send("Page.startScreencast", { format: "png", everyNthFrame: 1, ...CAST });
  await started;
  const watching = { clicked: Date.now() };
  watching.stop = async () => {
    await client.send("Page.stopScreencast").catch(() => {});
    await client.detach().catch(() => {});
    const sampled = frames.map(({ data, metadata }) => {
      const image = decodePng(Buffer.from(data, "base64")),
        scale = image.width / metadata.deviceWidth,
        [x, y, width, height] = box;
      const placed = [x - metadata.scrollOffsetX, y - metadata.scrollOffsetY - metadata.offsetTop];
      const inFrame = [placed[0] * scale, placed[1] * scale, width * scale, height * scale];
      return {
        at: metadata.timestamp * 1000 - watching.clicked,
        samples: samplesOf(image, inFrame),
      };
    });
    return paintedFrames(sampled, cover);
  };
  return watching;
}
