/** Exercise the player page's script, src/filmkit/delivery/player-page.js, in a stand-in document whose videos load,
 * seek, play and paint as Chrome Headless Shell 152 does: a video shows its poster until its first frame decodes, a
 * video without a poster paints black from its metadata until then, a seek keeps the last frame until the sought one
 * decodes, a hidden video paints nothing, a transparent one without a frame shows what lies beneath, and a later video
 * of the screen paints over an earlier one. Each test steps the stand-in's clock one animation frame at a time and
 * records what the screen shows. */
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const SCRIPT = fileURLToPath(new URL("../../src/filmkit/delivery/player-page.js", import.meta.url));
/* One animation frame, and how long a film takes to load its metadata and to decode a frame after a load or a seek,
 * in milliseconds; every film lasts DURATION seconds. */
const FRAME = 1000 / 60,
  METADATA = 30,
  DECODE = 50,
  DURATION = 60;
const camel = (name) => name.replace(/-(\w)/g, (_, letter) => letter.toUpperCase());

class Element {
  constructor(page, tag, attributes = {}, text = "") {
    Object.assign(this, { page, tag, text, parent: null, children: [], listeners: {}, style: {} });
    this.attributes = new Map(Object.entries(attributes));
    page.elements.push(this);
  }
  get id() {
    return this.getAttribute("id") ?? "";
  }
  set id(value) {
    this.setAttribute("id", value);
  }
  get textContent() {
    return this.text + this.children.map((child) => child.textContent).join("");
  }
  set textContent(value) {
    this.text = value;
    this.children = [];
  }
  get dataset() {
    const data = [...this.attributes].filter(([name]) => name.startsWith("data-"));
    return Object.fromEntries(data.map(([name, value]) => [camel(name.slice(5)), value]));
  }
  getAttribute(name) {
    return this.attributes.get(name) ?? null;
  }
  setAttribute(name, value) {
    this.attributes.set(name, String(value));
  }
  hasAttribute(name) {
    return this.attributes.has(name);
  }
  removeAttribute(name) {
    this.attributes.delete(name);
  }
  toggleAttribute(name, force) {
    if (force) this.attributes.set(name, "");
    else this.attributes.delete(name);
  }
  addEventListener(type, listener, options) {
    (this.listeners[type] ??= []).push({ listener, once: options?.once });
  }
  removeEventListener(type, listener) {
    this.listeners[type] = (this.listeners[type] ?? []).filter((v) => v.listener !== listener);
  }
  dispatch(type) {
    for (const { listener, once } of [...(this.listeners[type] ?? [])]) {
      if (once) this.removeEventListener(type, listener);
      listener.call(this, { type, target: this });
    }
  }
  click() {
    this.dispatch("click");
  }
  append(child) {
    child.parent = this;
    this.children.push(child);
  }
  after(node) {
    node.parent = this.parent;
    this.parent.children.splice(this.parent.children.indexOf(this) + 1, 0, node);
  }
  remove() {
    this.parent?.children.splice(this.parent.children.indexOf(this), 1);
    this.parent = null;
  }
  replaceChildren() {
    this.children = [];
  }
  querySelector(tag) {
    return this.children.find((child) => child.tag === tag) ?? null;
  }
  cloneNode() {
    return new Element(this.page, this.tag, Object.fromEntries(this.attributes));
  }
  focus() {
    this.page.document.activeElement = this;
  }
  get connected() {
    let node = this;
    while (node.parent) node = node.parent;
    return node === this.page.body;
  }
}

/* A text track: its mode, its active cues and their cuechange listeners. */
class Track extends Element {
  constructor(page, attributes) {
    super(page, "track", attributes);
    this.cues = { mode: "hidden", activeCues: [], listeners: {} };
    for (const name of ["addEventListener", "removeEventListener", "dispatch"])
      this.cues[name] = Element.prototype[name].bind(this.cues);
  }
  cloneNode() {
    return new Track(this.page, Object.fromEntries(this.attributes));
  }
}

class Video extends Element {
  constructor(page, attributes) {
    super(page, "video", attributes);
    Object.assign(this, {
      readyState: 0,
      seeking: false,
      paused: true,
      ended: false,
      time: 0,
      frame: null,
      duration: NaN,
      currentSrc: "",
      error: null,
      muted: false,
      volume: 1,
      playbackRate: 1,
      defaultPlaybackRate: 1,
      preload: attributes.preload ?? "auto",
      token: 0,
      seeks: 0,
      pictureInPicture: false,
    });
  }
  get textTracks() {
    return this.children.filter((child) => child instanceof Track).map((child) => child.cues);
  }
  get src() {
    return this.getAttribute("src") ?? "";
  }
  set src(value) {
    this.setAttribute("src", value);
    this.load();
  }
  get currentTime() {
    return this.time;
  }
  set currentTime(value) {
    if (this.readyState < 1) return;
    const token = ++this.token,
      slow = this.page.slowSeek?.(this, this.seeks++) ?? 0;
    Object.assign(this, { time: Math.min(Math.max(value, 0), this.duration), seeking: true });
    this.readyState = 1;
    this.dispatch("seeking");
    this.page.after(DECODE + slow, () => {
      if (token !== this.token) return;
      Object.assign(this, { seeking: false, readyState: 4, frame: this.time, ended: false });
      this.dispatch("seeked");
      if (!this.paused) this.dispatch("playing");
    });
  }
  load() {
    const token = ++this.token,
      source = this.src || (this.querySelector("source")?.getAttribute("src") ?? "");
    Object.assign(this, { readyState: 0, seeking: false, ended: false, time: 0, frame: null });
    Object.assign(this, {
      currentSrc: source,
      error: null,
      playbackRate: this.defaultPlaybackRate,
    });
    if (!this.paused) this.paused = true;
    this.dispatch("emptied");
    if (!source) return;
    this.page.after(METADATA, () => {
      if (token !== this.token) return;
      if (this.page.failing.has(source)) {
        this.error = { code: 4 };
        return this.dispatch("error");
      }
      Object.assign(this, { readyState: 1, duration: DURATION });
      this.dispatch("loadedmetadata");
      this.page.after(DECODE, () => {
        if (token !== this.token) return;
        Object.assign(this, { readyState: 4, frame: this.time });
        this.dispatch("loadeddata");
      });
    });
  }
  play() {
    if (this.paused) {
      this.paused = false;
      this.dispatch("play");
      if (this.readyState >= 3 && !this.seeking) this.dispatch("playing");
    }
    return Promise.resolve();
  }
  pause() {
    if (this.paused) return;
    this.paused = true;
    this.dispatch("pause");
  }
  remove() {
    super.remove();
    this.pause();
  }
  cloneNode() {
    const copy = new Video(this.page, Object.fromEntries(this.attributes));
    if (copy.src) copy.load();
    return copy;
  }
  requestPictureInPicture() {
    this.pictureInPicture = true;
    return Promise.resolve();
  }
  /* A playing film moves on with the clock until it ends. */
  advance(seconds) {
    if (this.paused || this.seeking || this.readyState < 3 || !this.connected) return;
    this.time = Math.min(this.time + seconds * this.playbackRate, this.duration);
    this.frame = this.time;
    if (this.time < this.duration) return;
    this.ended = true;
    this.pause();
  }
  /* What the video paints where it stands, or null where it lets the screen beneath show. */
  get painting() {
    if (this.style.visibility === "hidden") return null;
    if (this.frame !== null) return `${this.currentSrc}@${this.frame.toFixed(3)}`;
    if (this.hasAttribute("poster")) return "poster";
    if (this.readyState >= 1) return "black";
    return this.style.background === "transparent" ? null : "ground";
  }
}

/* A player page as the engine renders it, with the script run on it; `options` set the location's hash, the films
 * that fail to load and a seek delay. */
function openPage(options = {}) {
  const page = { elements: [], timers: [], frames: [], now: 0, shown: [], failing: new Set() };
  Object.assign(page, options);
  page.after = (ms, callback) => page.timers.push({ at: page.now + ms, callback });
  const element = (tag, attributes, text) => new Element(page, tag, attributes, text);
  page.body = element("body");
  page.screen = element("div", { class: "screen" });
  page.body.append(page.screen);
  const film = new Video(page, {
    id: "film",
    controls: "",
    preload: "metadata",
    poster: "cover.png",
  });
  film.append(element("source", { src: "1080p-captioned.mp4", type: "video/mp4" }));
  film.append(new Track(page, { kind: "metadata", default: "" }));
  page.screen.append(film);
  film.load();
  const version = (captioned, uncaptioned, pressed, name) =>
    element(
      "button",
      { "data-captioned": captioned, "data-uncaptioned": uncaptioned, "aria-pressed": pressed },
      name,
    );
  page.versions = [
    version("1080p-captioned.mp4", "1080p-uncaptioned.mp4", "true", "观看版 · 1080p"),
    version("uhd.mp4", "uhd-uncaptioned.mp4", "false", "超高清 4K · 2160p"),
  ];
  const on = "：开";
  page.captions = element(
    "button",
    { id: "captions", "aria-pressed": "true", "data-on": on, "data-off": "：关" },
    "字幕",
  );
  page.captions.append(element("span", { "aria-hidden": "true" }, on));
  page.status = element("p", {
    id: "playback-status",
    "data-unplayable": "这个浏览器播放不了当前的编码。",
  });
  page.thoughts = [3, 20, 40].map((at) =>
    element("p", { "data-from": String(at) }, `thought ${at}`),
  );
  page.times = [element("button", { "data-time": "40" }, "0:40")];
  page.details = element("details");
  page.link = element("a", { href: "#transcript" });
  for (const node of [...page.versions, page.captions, page.status, page.details, page.link])
    page.body.append(node);
  for (const node of [...page.thoughts, ...page.times]) page.details.append(node);
  const lists = {
    "[data-captioned]": page.versions,
    "#transcript p[data-from]": page.thoughts,
    "[data-time]": page.times,
    'a[href="#transcript"]': [page.link],
  };
  page.document = {
    activeElement: null,
    pictureInPictureElement: null,
    getElementById: (id) => page.elements.find((v) => v.id === id && v.connected) ?? null,
    querySelectorAll: (selector) => lists[selector],
    querySelector: (selector) => ({ "#transcript details": page.details })[selector],
  };
  page.film = () => page.document.getElementById("film");
  page.videos = () => page.screen.children;
  /* Step the clock one animation frame at a time for `ms` and record what the screen shows in each frame. */
  page.run = (ms) => {
    for (const end = page.now + ms; page.now < end - 1e-9;) {
      const next = page.now + FRAME;
      for (
        let due;
        (due = page.timers.filter((v) => v.at <= next).sort((a, b) => a.at - b.at)[0]);
      ) {
        page.timers.splice(page.timers.indexOf(due), 1);
        page.now = due.at;
        due.callback();
      }
      for (const video of page.elements.filter((v) => v instanceof Video))
        video.advance((next - page.now) / 1000);
      page.now = next;
      const callbacks = page.frames.splice(0);
      for (const callback of callbacks) callback(page.now);
      const top = [...page.videos()].reverse().find((v) => v.painting !== null);
      page.shown.push(top ? top.painting : "ground");
    }
  };
  const context = vm.createContext({
    document: page.document,
    location: { hash: page.hash ?? "" },
    requestAnimationFrame: (callback) => page.frames.push(callback),
  });
  vm.runInContext(readFileSync(SCRIPT, "utf8"), context, { filename: SCRIPT });
  page.run(200);
  return page;
}

/* Stand the film at a time, paused or playing, and forget what the screen showed so far. */
function standAt(page, time, playing = false) {
  page.film().currentTime = time;
  page.run(100);
  if (playing) page.film().play();
  page.run(200);
  page.shown = [];
}

/* The film and time of each frame the screen showed, and whether every one was a film's frame. */
const framesOf = (page) =>
  page.shown.map((v) => /^(.*)@(\d+\.\d+)$/.exec(v)).map((m) => m && [m[1], Number(m[2])]);
function onlyFilm(page) {
  const odd = page.shown.filter((v) => !v.includes("@"));
  assert.deepEqual(odd, [], `the screen showed ${[...new Set(odd)].join(", ")} during the switch`);
  return framesOf(page);
}

test("captions turned off on a paused film keep its frame and its time", () => {
  const page = openPage();
  standAt(page, 20);
  page.captions.click();
  page.run(500);
  const frames = onlyFilm(page);
  assert.deepEqual(
    [...new Set(frames.map(([film]) => film))],
    ["1080p-captioned.mp4", "1080p-uncaptioned.mp4"],
  );
  assert.ok(frames.every(([, time]) => time === 20));
  const film = page.film();
  assert.deepEqual(
    [film.currentSrc, film.currentTime, film.paused],
    ["1080p-uncaptioned.mp4", 20, true],
  );
  assert.equal(page.videos().length, 1);
  assert.equal(page.captions.getAttribute("aria-pressed"), "false");
  assert.equal(page.status.textContent, "观看版 · 1080p · 字幕：关");
  assert.equal(film.textTracks[0].mode, "hidden");
});

test("a version chosen while the film plays takes over at the time the film has reached", () => {
  const page = openPage();
  standAt(page, 10, true);
  const clicked = page.film().currentTime;
  page.versions[1].click();
  page.run(800);
  const frames = onlyFilm(page);
  // The film plays on: no frame steps back by more than two frames or forward by more than one, and the time moves
  // with the clock.
  for (let k = 1; k < frames.length; k++) {
    const step = frames[k][1] - frames[k - 1][1];
    assert.ok(step > -2 / 60 && step < 2 / 60 + 1e-9, `frame ${k} steps ${step.toFixed(3)} s`);
  }
  const switched = frames.findIndex(([film]) => film === "uhd.mp4");
  assert.ok(switched > 0 && frames.slice(switched).every(([film]) => film === "uhd.mp4"));
  const film = page.film();
  assert.deepEqual([film.currentSrc, film.paused, page.videos().length], ["uhd.mp4", false, 1]);
  assert.ok(
    Math.abs(film.currentTime - (clicked + 0.8)) < 0.05,
    `${film.currentTime} after ${clicked}`,
  );
  assert.equal(page.versions[1].getAttribute("aria-pressed"), "true");
});

test("a film slower to seek than the lead is aimed further ahead and still plays on", () => {
  const page = openPage({
    slowSeek: (video, seek) => (video.id !== "film" && seek === 0 ? 400 : 0),
  });
  standAt(page, 10, true);
  const clicked = page.film().currentTime;
  page.captions.click();
  page.run(2000);
  const frames = onlyFilm(page);
  assert.ok(frames.every(([, time], k) => !k || time > frames[k - 1][1] - 2 / 60));
  assert.equal(page.film().currentSrc, "1080p-uncaptioned.mp4");
  assert.ok(Math.abs(page.film().currentTime - (clicked + 2)) < 0.05);
});

test("a second switch, a seek and a pause during a switch end on the film and time they name", () => {
  const page = openPage();
  standAt(page, 20);
  page.captions.click();
  page.run(FRAME);
  page.versions[1].click();
  page.run(500);
  onlyFilm(page);
  assert.deepEqual([page.film().currentSrc, page.film().currentTime], ["uhd-uncaptioned.mp4", 20]);
  assert.equal(page.videos().length, 1);
  // A time button while a switch is under way plays the chosen film from that time.
  standAt(page, 10, true);
  page.captions.click();
  page.run(2 * FRAME);
  page.times[0].click();
  page.run(800);
  onlyFilm(page);
  assert.equal(page.film().currentSrc, "uhd.mp4");
  assert.ok(Math.abs(page.film().currentTime - 40.8) < 0.1, `${page.film().currentTime}`);
  // A pause while a switch is under way leaves the chosen film paused where the film was paused.
  page.versions[0].click();
  page.run(2 * FRAME);
  page.film().pause();
  const paused = page.film().currentTime;
  page.run(500);
  onlyFilm(page);
  assert.deepEqual(
    [page.film().currentSrc, page.film().paused, page.film().currentTime],
    ["1080p-captioned.mp4", true, paused],
  );
});

test("a switch while the chosen film already shows completes it first", () => {
  const page = openPage();
  standAt(page, 20);
  page.captions.click();
  // Stop as soon as the chosen film shows beside the shown one, before the shown one leaves.
  for (
    let k = 0;
    k < 60 && page.videos().every((v) => v.style.visibility === "hidden" || v.id === "film");
    k++
  )
    page.run(FRAME);
  page.captions.click();
  page.run(500);
  onlyFilm(page);
  assert.deepEqual([page.film().currentSrc, page.film().currentTime], ["1080p-captioned.mp4", 20]);
  assert.equal(page.videos().length, 1);
});

test("the chosen film keeps the volume, mute, rate, focus and picture-in-picture, and the old one is let go", () => {
  const page = openPage();
  standAt(page, 20, true);
  const old = page.film();
  Object.assign(old, { muted: true, volume: 0.4, playbackRate: 1.5 });
  old.focus();
  page.document.pictureInPictureElement = old;
  page.captions.click();
  page.run(800);
  const film = page.film();
  assert.notEqual(film, old);
  assert.deepEqual(
    [film.muted, film.volume, film.playbackRate, film.paused],
    [true, 0.4, 1.5, false],
  );
  assert.equal(page.document.activeElement, film);
  assert.equal(film.pictureInPicture, true);
  assert.equal(film.hasAttribute("poster"), false);
  assert.deepEqual([old.connected, old.paused, old.src, old.currentSrc], [false, true, "", ""]);
});

test("near the end a playing film ends and the chosen film shows its last frame", () => {
  const page = openPage();
  standAt(page, 59.62, true);
  page.versions[1].click();
  page.run(800);
  onlyFilm(page);
  assert.deepEqual([page.film().currentSrc, page.film().currentTime], ["uhd.mp4", 60]);
});

test("a chosen film that fails to load is shown with the message that it cannot play", () => {
  const page = openPage({ failing: new Set(["uhd.mp4"]) });
  standAt(page, 20);
  page.versions[1].click();
  page.run(300);
  assert.equal(page.film().currentSrc, "uhd.mp4");
  assert.equal(page.status.textContent, "这个浏览器播放不了当前的编码。");
  assert.equal(page.videos().length, 1);
});

test("the shown film's active cue marks its thought, and a time button plays from its time", () => {
  const page = openPage({ hash: "#transcript" });
  assert.equal(page.details.open, true);
  const cue = (track, startTime) => {
    track.activeCues = startTime === null ? [] : [{ startTime }];
    track.dispatch("cuechange");
  };
  const current = () =>
    page.thoughts.filter((p) => p.hasAttribute("aria-current")).map((p) => p.text);
  const before = page.film().textTracks[0];
  cue(before, 21);
  assert.deepEqual(current(), ["thought 20"]);
  cue(before, null);
  assert.deepEqual(current(), ["thought 20"]);
  page.captions.click();
  page.run(500);
  // The film let go no longer marks a thought; the chosen film's track does.
  cue(before, 41);
  assert.deepEqual(current(), ["thought 20"]);
  cue(page.film().textTracks[0], 41);
  assert.deepEqual(current(), ["thought 40"]);
  page.times[0].click();
  page.run(100);
  assert.deepEqual([page.film().currentTime > 40, page.film().paused], [true, false]);
  page.details.open = false;
  page.link.click();
  assert.equal(page.details.open, true);
  page.film().error = { code: 4 };
  page.film().dispatch("error");
  assert.equal(page.status.textContent, "这个浏览器播放不了当前的编码。");
});
