/** Exercise how the readback judges what a player paints through a switch: the grid it samples over the film's box,
 * the frames that paint the cover or one flat colour, a switch whose frames were not read, and the screencast it
 * watches the switch with, on a stand-in page. */
import test from "node:test";
import assert from "node:assert/strict";
import { crc32, deflateSync } from "node:zlib";

import {
  coverSamples,
  distance,
  flat,
  paintedFrames,
  samplesOf,
  watchScreen,
} from "../../src/filmkit/delivery/player-frames.mjs";

/* An image of one colour with a block of another, as decoded RGBA pixels. */
function image(width, height, ground, block = null) {
  const data = new Uint8Array(width * height * 4);
  for (let y = 0; y < height; y++)
    for (let x = 0; x < width; x++) {
      const { x: bx, y: by, w, h, color } = block ?? {};
      const inside = block && x >= bx && x < bx + w && y >= by && y < by + h;
      data.set([...(inside ? color : ground), 255], (y * width + x) * 4);
    }
  return { width, height, data };
}
const GROUND = [15, 21, 25],
  INK = [201, 120, 92];
/* A film's frame, the ground with a mark on a tenth of it, and the cover, a bright card over its upper half, each the
 * size of the film's box. */
const filmFrame = (shift = 0) =>
  image(80, 45, GROUND, { x: 10 + shift, y: 10, w: 24, h: 15, color: INK });
const COVER = image(80, 45, GROUND, { x: 0, y: 0, w: 80, h: 22, color: [236, 230, 218] });
const BOX = [0, 0, 80, 45];
const frame = (at, picture) => ({ at, samples: samplesOf(picture, BOX) });

test("the grid samples the box above the controls, and a sample outside the image is not compared", () => {
  const samples = samplesOf(filmFrame(), BOX);
  assert.equal(samples.length, 64 * 36);
  assert.deepEqual(samples[0], GROUND);
  // The box's bottom 15% holds the browser's controls, so the grid stops short of it.
  const controls = image(10, 100, GROUND, { x: 0, y: 86, w: 10, h: 14, color: INK });
  assert.ok(samplesOf(controls, [0, 0, 10, 100]).every((p) => p.join() === GROUND.join()));
  const half = samplesOf(filmFrame(), [40, 0, 80, 45]);
  assert.equal(half.filter((p) => p === null).length, 32 * 36);
  assert.ok(Number.isFinite(distance(half, samplesOf(filmFrame(), BOX))));
  assert.equal(distance([null], [GROUND]), Infinity);
});

test("a frame is flat when nearly all its samples lie near one colour", () => {
  assert.equal(flat(samplesOf(image(80, 45, GROUND), BOX)), true);
  assert.equal(flat(samplesOf(image(80, 45, [0, 0, 0]), BOX)), true);
  assert.equal(flat(samplesOf(filmFrame(), BOX)), false);
  assert.equal(flat([null, null]), false);
});

test("a switch that keeps the film on the screen paints neither the cover nor a flat frame", () => {
  const frames = [frame(-30, filmFrame()), frame(10, filmFrame()), frame(40, filmFrame(1))];
  frames.push(frame(300, filmFrame(1)));
  assert.deepEqual(paintedFrames(frames, coverSamples(COVER)), { frames: 4, cover: [], flat: [] });
});

test("a switch that shows the poster or bare ground is caught with each frame's time", () => {
  const frames = [
    frame(-30, filmFrame()),
    frame(17, COVER),
    frame(34, COVER),
    frame(51, image(80, 45, GROUND)),
    frame(68, image(80, 45, [0, 0, 0])),
    frame(300, filmFrame()),
  ];
  assert.deepEqual(paintedFrames(frames, coverSamples(COVER)), {
    frames: 6,
    cover: [17, 34],
    flat: [51, 68],
  });
});

test("a film that shows its own title card or bare ground at the switch is not taken for a flash", () => {
  // The film's own title card is the cover's picture: the frames around the switch are as near to it.
  const titled = [frame(-30, COVER), frame(20, COVER), frame(300, COVER)];
  assert.deepEqual(paintedFrames(titled, coverSamples(COVER)).cover, []);
  // A film that stands on bare ground at the switch keeps doing so.
  const bare = image(80, 45, GROUND);
  const quiet = [frame(-30, bare), frame(20, bare), frame(300, filmFrame())];
  assert.deepEqual(paintedFrames(quiet, coverSamples(COVER)).flat, []);
});

test("a switch whose frames were not read around it is not judged as clean", () => {
  assert.equal(paintedFrames([frame(10, filmFrame())], coverSamples(COVER)).unread, true);
  assert.equal(paintedFrames([frame(-10, filmFrame())], coverSamples(COVER)).unread, true);
  assert.equal(paintedFrames([], coverSamples(COVER)).unread, true);
});

/* A PNG of decoded RGBA pixels, every scanline unfiltered. */
function png({ width, height, data }) {
  const chunk = (type, body) => {
    const head = Buffer.alloc(8),
      tail = Buffer.alloc(4);
    head.writeUInt32BE(body.length);
    head.write(type, 4, "latin1");
    tail.writeUInt32BE(crc32(Buffer.concat([head.subarray(4), body])));
    return Buffer.concat([head, body, tail]);
  };
  const header = Buffer.alloc(13);
  header.writeUInt32BE(width);
  header.writeUInt32BE(height, 4);
  header.set([8, 6, 0, 0, 0], 8);
  const row = (y) => [
    Buffer.from([0]),
    Buffer.from(data.subarray(y * width * 4, (y + 1) * width * 4)),
  ];
  const rows = Buffer.concat(Array.from({ length: height }, (_, y) => row(y)).flat());
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk("IHDR", header),
    chunk("IDAT", deflateSync(rows)),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}

/* A 160 x 90 cast of a page whose film's box stands at (20, 15), showing a picture there, scrolled down `scroll`. */
function castOf(picture, scroll) {
  const cast = image(160, 90, [0, 0, 255]);
  for (let y = 0; y < 45; y++)
    for (let x = 0; x < 80; x++) {
      const from = (y * 80 + x) * 4;
      cast.data.set(picture.data.subarray(from, from + 4), ((15 - scroll + y) * 160 + 20 + x) * 4);
    }
  return cast;
}

test("the screencast is read in the film's box at each frame's scroll and timed from the click", async () => {
  const sent = [],
    listeners = {},
    clicked = Date.now();
  const cast = (at, picture, scrollOffsetY) =>
    listeners["Page.screencastFrame"]({
      data: png(castOf(picture, scrollOffsetY)).toString("base64"),
      metadata: {
        deviceWidth: 160,
        offsetTop: 0,
        scrollOffsetX: 0,
        scrollOffsetY,
        timestamp: (clicked + at) / 1000,
      },
      sessionId: at,
    });
  const client = {
    on: (type, listener) => (listeners[type] = listener),
    send: async (method, params) => {
      sent.push(method);
      if (method !== "Page.startScreencast") return;
      assert.deepEqual(params, { format: "png", everyNthFrame: 1, maxWidth: 800, maxHeight: 500 });
      // The page scrolls down 10 px after the first frame, so the box rises in the cast.
      cast(-40, filmFrame(), 0);
      cast(20, COVER, 10);
      cast(200, filmFrame(), 10);
    },
    detach: async () => sent.push("detach"),
  };
  const page = {
    createCDPSession: async () => client,
    $eval: async (selector, read) => {
      assert.equal(selector, "#film");
      return read({ getBoundingClientRect: () => ({ x: 20, y: 15, width: 80, height: 45 }) });
    },
  };
  globalThis.window = { scrollX: 0, scrollY: 0 };
  try {
    const watch = await watchScreen(page, coverSamples(COVER));
    watch.clicked = clicked;
    assert.deepEqual(await watch.stop(), { frames: 3, cover: [20], flat: [] });
    assert.deepEqual(sent, [
      "Page.startScreencast",
      "Page.screencastFrameAck",
      "Page.screencastFrameAck",
      "Page.screencastFrameAck",
      "Page.stopScreencast",
      "detach",
    ]);
  } finally {
    delete globalThis.window;
  }
});
