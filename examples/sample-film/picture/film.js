/* Sample reel: how a film is rebuilt from its sources, in four scenes over three chapters. */
"use strict";
const film = window.FILM;
const canvas = document.getElementById("picture");
const ctx = canvas.getContext("2d", { alpha: false });
const resolution = Number(document.getElementById("film").dataset.width) / 1920;
/* The film's colours; the geometry check reads the ground and the ink from P. */
const P = {
  ground: "#0F1519",
  panel: "#1E2932",
  line: "#63758B",
  ink: "#ECE8DF",
  muted: "#9BA8B1",
  accent: "#7DB7D8",
  done: "#9CCB8F",
};
const en = film.edition === "en";
const L = (zh, english) => (en ? english : zh);
/* Scene names use two sizes; captions, cards and credits keep their own. */
const LABEL = 38;
const NOTE = 28;
const CAPTION = en ? 34 : 36;
/* A scene stands from this long before its voice, so it is whole on the first word; a chapter
 * card leaves before the scene arrives. */
const LEAD = 0.6;
const CARD_GONE = 0.7;
const FADE = 0.45;
const creditStart = film.duration - film.credits_duration;

const clamp = (q) => Math.max(0, Math.min(1, q));
const ease = (q) => {
  q = clamp(q);
  return q * q * (3 - 2 * q);
};
const ramp = (t, start, duration = FADE) => ease((t - start) / duration);

/* What the frame shows, published for the checks: one record per painted text, in paint order. */
let layout = { texts: [] };
let sceneId = null;

/* Any text with a Chinese character is set in Noto Sans CJK SC, Latin-only text in IBM Plex Sans. */
const CHINESE = /[\u3000-\u303f\u3400-\u9fff\uf900-\ufaff\uff00-\uffef]/u;
const family = (value, bold) =>
  CHINESE.test(value) ? (bold ? "SampleBold" : "Sample") : bold ? "SampleLatinBold" : "SampleLatin";

/* Paint one text and record its bounds, colour, opacity, role and scene. `align` starts the text at x, centres it on
 * x or ends it there. */
function text(
  value,
  x,
  y,
  { size, bold = false, color = P.ink, alpha = 1, role = "label", align = "center" },
) {
  if (alpha <= 0) return;
  ctx.font = `${bold ? "700 " : ""}${size}px ${family(value, bold)}`;
  ctx.textAlign = align;
  ctx.textBaseline = "alphabetic";
  const metrics = ctx.measureText(value);
  const left = align === "left" ? x : align === "right" ? x - metrics.width : x - metrics.width / 2;
  ctx.globalAlpha = alpha;
  ctx.fillStyle = color;
  ctx.fillText(value, x, y);
  ctx.globalAlpha = 1;
  layout.texts.push({
    text: value,
    bounds: [
      left - 2,
      y - metrics.actualBoundingBoxAscent - 2,
      left + metrics.width + 2,
      y + metrics.actualBoundingBoxDescent + 2,
    ],
    color,
    alpha,
    role,
    scene: sceneId,
    placed: true,
    size,
  });
}

/* A card: a filled panel with an outline. */
function card(x, y, width, height, alpha, outline = P.line) {
  if (alpha <= 0) return;
  ctx.globalAlpha = alpha;
  ctx.fillStyle = P.panel;
  ctx.beginPath();
  ctx.roundRect(x, y, width, height, 12);
  ctx.fill();
  ctx.strokeStyle = outline;
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.roundRect(x, y, width, height, 12);
  ctx.stroke();
  ctx.globalAlpha = 1;
}

/* A straight line, dashed when `dash` is given. */
function line(points, alpha, { color = P.line, width = 3, dash = [] } = {}) {
  if (alpha <= 0) return;
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.setLineDash(dash);
  ctx.beginPath();
  ctx.moveTo(...points[0]);
  for (const point of points.slice(1)) ctx.lineTo(...point);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.globalAlpha = 1;
}

/* A card's outline alone, as the narration lights or marks it. */
function outline(x, y, width, height, alpha, color) {
  if (alpha <= 0) return;
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = color;
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.roundRect(x, y, width, height, 12);
  ctx.stroke();
  ctx.globalAlpha = 1;
}

/* When a segment's voice says the words that its script marks as the anchor `id`: the start of the first of them.
 * Each anchor is read from the segment's own `anchors` (filmkit.narration.anchors); an id the script does not mark
 * there is refused. */
function cue(s, id) {
  const anchor = s.anchors?.[id];
  if (!anchor) throw Error(`Segment ${s.id} marks no anchor ${id}`);
  return anchor.start;
}

/* Something named appears as the narration names it. */
const shown = (t, at) => ramp(t, at, 0.35);
/* A card's tag: the kind of file or the step it stands for, set small at its top left from the moment the card
 * stands until the narration names the card, so no card waits empty for its name. */
const TAG = { dx: 22, dy: 34 };
function tag(value, x, y, alpha) {
  text(value, x + TAG.dx, y + TAG.dy, { size: NOTE, color: P.muted, alpha, align: "left" });
}

/* The middle source stands with the scene and the two beside it arrive together on a word of the film's first
 * sentence, so the row opens from its centre and stays centred, and the picture moves under that sentence: three
 * cards that stood from the scene's start left it still for the whole of it. Each card is tagged with its kind of
 * file; the three light as one when the narration names them, and each is named, then explained, as its words are
 * said. */
const SOURCES = [
  [L("脚本", "Script"), "script", L("要说的话", "What is said"), "what-is-said", ".json"],
  [
    L("参考录音", "Reference"),
    "reference",
    L("旁白的嗓音", "The narrator’s voice"),
    "voice",
    ".wav",
  ],
  [
    L("画面合成", "Composition"),
    "composition",
    L("每一帧画什么", "Every frame"),
    "every-frame",
    ".js",
  ],
];

function sourcesScene(s, t, alpha) {
  text(L("一部影片的源文件", "A film’s sources"), 960, 382, {
    size: NOTE,
    color: P.muted,
    alpha,
  });
  const lit = alpha * shown(t, cue(s, "sources"));
  SOURCES.forEach(([name, nameId, note, noteId, kind], i) => {
    const x = 350 + i * 440;
    const here = alpha * (i === 1 ? 1 : shown(t, cue(s, "film")));
    card(x, 472, 340, 170, here);
    outline(x, 472, 340, 170, lit, P.accent);
    const named = shown(t, cue(s, nameId));
    tag(kind, x, 472, here * (1 - named));
    text(name, x + 170, 547, { size: LABEL, alpha: alpha * named });
    text(note, x + 170, 602, {
      size: NOTE,
      color: P.muted,
      alpha: alpha * shown(t, cue(s, noteId)),
    });
  });
}

const STAGES = [
  [L("旁白", "Narration"), "narration"],
  [L("音轨", "Soundtrack"), "soundtrack"],
  [L("字幕", "Captions"), "captions"],
  [L("画面", "Picture"), "picture"],
  [L("成片", "Films"), "films"],
];

/* The build's five stages stand in a row from its first scene, each tagged with its step; the stages before `from` are
 * named already, those up to `to` are named as the narration names them, and the rest are named in the next scene. The
 * first scene shows what keeps a rebuild's voice the same, the second that the build stays offline. */
function buildScene(s, t, alpha, from, to) {
  text(L("构建的步骤", "Build steps"), 960, 382, { size: NOTE, color: P.muted, alpha });
  STAGES.forEach(([name, id], i) => {
    const x = 206 + i * 312;
    card(x, 492, 260, 140, alpha);
    const named = i < from ? 1 : i < to ? shown(t, cue(s, id)) : 0;
    tag(L(`步骤 ${i + 1}`, `Step ${i + 1}`), x, 492, alpha * (1 - named));
    text(name, x + 130, 576, { size: LABEL, alpha: alpha * named });
  });
  if (from === 0) {
    const seed = alpha * shown(t, cue(s, "fixed-seed"));
    text(L("固定的种子", "A fixed seed"), 336, 682, { size: NOTE, color: P.muted, alpha: seed });
    const same = alpha * shown(t, cue(s, "same-voice"));
    text(L("声音都一样", "The same voice"), 336, 732, { size: NOTE, color: P.done, alpha: same });
    return;
  }
  const offline = alpha * shown(t, cue(s, "offline"));
  line(
    [
      [176, 452],
      [1744, 452],
      [1744, 672],
      [176, 672],
      [176, 452],
    ],
    offline,
    { color: P.accent, width: 2, dash: [14, 10] },
  );
  text(L("不联网", "Offline"), 960, 437, { size: NOTE, color: P.accent, alpha: offline });
  const kept = alpha * shown(t, cue(s, "build-folder"));
  text(L("所有文件都留在构建目录", "Everything stays in the build folder"), 960, 732, {
    size: NOTE,
    color: P.muted,
    alpha: kept,
  });
}

/* What the check covers, as the narration lists it. */
const CHECKED = [
  [L("录音", "Recordings"), "recordings"],
  [L("音轨", "Soundtrack"), "soundtrack"],
  [L("字幕", "Captions"), "captions"],
  [L("画面", "Picture"), "picture"],
  [L("打包记录", "Packages"), "packages"],
];
/* Each check stands from x 870 to 898, and its item starts one gap after it, so the items share one left edge. */
const CHECK_LEFT = 870;
const CHECK_RIGHT = 898;
const ITEM_LEFT = CHECK_RIGHT + 26;

/* Each film beside its sources, and between them what the check covers; each item is marked as it is said to match,
 * and the check completes when everything does. */
function checkScene(s, t, alpha) {
  text(L("核对成片", "Checking the films"), 960, 382, { size: NOTE, color: P.muted, alpha });
  const complete = alpha * shown(t, cue(s, "everything"));
  for (const [x, kind, name, id] of [
    [330, ".mp4", L("成片", "Films"), "film"],
    [1290, ".json .wav .js", L("源文件", "Sources"), "sources"],
  ]) {
    card(x, 477, 300, 170, alpha);
    outline(x, 477, 300, 170, complete, P.done);
    const named = shown(t, cue(s, id));
    tag(kind, x, 477, alpha * (1 - named));
    text(name, x + 150, 575, { size: LABEL, alpha: alpha * named });
  }
  const matched = alpha * shown(t, cue(s, "match"));
  CHECKED.forEach(([name, id], i) => {
    const y = 492 + i * 45;
    text(name, ITEM_LEFT, y, {
      size: NOTE,
      align: "left",
      alpha: alpha * shown(t, cue(s, id)),
    });
    line(
      [
        [CHECK_LEFT, y - 12],
        [CHECK_LEFT + 10, y - 2],
        [CHECK_RIGHT, y - 22],
      ],
      matched,
      { color: P.done, width: 4 },
    );
  });
  text(L("完成", "Complete"), 960, 752, {
    size: LABEL,
    color: P.done,
    alpha: alpha * shown(t, cue(s, "complete")),
  });
}

const scenes = {
  "01": sourcesScene,
  "02": (s, t, alpha) => buildScene(s, t, alpha, 0, 3),
  "03": (s, t, alpha) => buildScene(s, t, alpha, 3, 5),
  "04": checkScene,
};

const segments = film.segments;
const opensChapter = (i) => i === 0 || segments[i - 1].chapter !== segments[i].chapter;
const continues = (i) => i + 1 < segments.length && !opensChapter(i + 1);
/* The time each segment's scene stands, and when it leaves. */
const sceneStart = (i) => segments[i].voice_start - LEAD;
const sceneEnd = (i) =>
  continues(i) ? sceneStart(i + 1) : i + 1 < segments.length ? segments[i + 1].start : creditStart;

function drawScene(i, t) {
  const s = segments[i];
  const fadeIn = i > 0 && !opensChapter(i) ? 1 : ramp(t, sceneStart(i));
  const fadeOut = continues(i) ? 1 : 1 - ramp(t, sceneEnd(i) - 0.5, 0.5);
  sceneId = s.id;
  window.__sceneId = s.id;
  scenes[s.id](s, t, Math.min(fadeIn, fadeOut));
  sceneId = null;
  window.__sceneId = null;
}

/* The film's title card, before the first scene. */
function titleCard(alpha, chapter) {
  text(L("示例影片", "Sample Reel"), 960, 470, { size: 84, bold: true, alpha, role: "title" });
  text(L("从源文件到成片", "From Sources to Film"), 960, 560, {
    size: 40,
    color: P.muted,
    alpha,
    role: "title",
  });
  if (chapter) text(chapter, 960, 680, { size: 32, color: P.accent, alpha, role: "title" });
}

/* A chapter card: its number and title, from the segment's start until the scene arrives. */
function chapterCard(i, t) {
  const s = segments[i];
  const alpha = ramp(t, s.start, 0.15) * (1 - ramp(t, s.voice_start - CARD_GONE - 0.25, 0.25));
  const number = String(s.chapter_index + 1).padStart(2, "0");
  if (i === 0) {
    titleCard(alpha, `${number}  ${s.chapter_title}`);
    return;
  }
  text(number, 960, 440, { size: 32, color: P.accent, alpha, role: "title" });
  text(s.chapter_title, 960, 540, { size: 64, bold: true, alpha, role: "title" });
}

function credits(t) {
  const alpha = ramp(t, creditStart, 0.4);
  titleCard(alpha, film.author);
  text(L("由 filmkit 重建", "Rebuilt with filmkit"), 960, 760, {
    size: 28,
    color: P.muted,
    alpha,
    role: "title",
  });
}

/* The caption of the moment: small, single-line, below the picture. */
function caption(t) {
  const cue = film.captions.find((v) => v.start <= t && t < v.end);
  if (!cue) return;
  const alpha = ramp(t, cue.start, 0.1) * (1 - ramp(t, cue.end - 0.1, 0.1));
  text(cue.display_text ?? cue.text, 960, 1000, { size: CAPTION, alpha, role: "caption" });
}

function drawAt(t) {
  layout = { texts: [], time: t };
  ctx.setTransform(resolution, 0, 0, resolution, 0, 0);
  ctx.globalAlpha = 1;
  ctx.fillStyle = P.ground;
  ctx.fillRect(0, 0, 1920, 1080);
  if (t >= creditStart) {
    credits(t);
  } else {
    const index = segments.findIndex((_, i) => sceneStart(i) <= t && t < sceneEnd(i));
    if (index >= 0) drawScene(index, t);
    const opening = segments.findIndex(
      (s, i) => opensChapter(i) && s.start <= t && t < s.voice_start - CARD_GONE,
    );
    if (opening >= 0) chapterCard(opening, t);
    caption(t);
  }
  window.__filmLayout = { time: t, texts: layout.texts };
}

window.renderFrame = (t) => drawAt(t + (film.render_offset || 0));
/* The cover: the title card on the ground, at the stage's frame. */
window.renderCover = () => {
  layout = { texts: [] };
  ctx.setTransform(resolution, 0, 0, resolution, 0, 0);
  ctx.fillStyle = P.ground;
  ctx.fillRect(0, 0, 1920, 1080);
  titleCard(1, film.author);
};
window.__filmScenes = scenes;
window.renderFrame(0);
