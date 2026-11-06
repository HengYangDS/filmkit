/** Exercise how the delivered players' readback judges what it reads: where a page's links lead, the cues of a caption
 * file, the track a page embeds, the browser's own captions control, the sizes its files list names and each page's
 * verdict; and that a read which stops fails only its page. */
import test from "node:test";
import assert from "node:assert/strict";

import { readEntry, readPlayer } from "../../src/filmkit/delivery/player-read.mjs";
import {
  bare,
  cueProblems,
  embeddedText,
  entryProblems,
  fileProblems,
  linkProblems,
  parseCues,
  playerProblems,
  sizeLabel,
  verdict,
  versionProblems,
  visibleCaptionControls,
} from "../../src/filmkit/delivery/player-verdict.mjs";
import { deliveryMembers } from "../../src/filmkit/delivery/player-check.mjs";

const MEMBERS = deliveryMembers("sample-reel");

test("every link of a page leads to a delivery member, a sibling page or a place in the page", () => {
  assert.deepEqual(
    linkProblems(
      "zh/index.html",
      [
        "sample-reel-zh-uhd.mp4",
        "sample-reel-cover.png#top",
        "../en/index.html",
        "../index.html",
        "#transcript",
      ],
      MEMBERS,
    ),
    [],
  );
  assert.deepEqual(linkProblems("index.html", ["zh/index.html", "en/index.html"], MEMBERS), []);
  assert.deepEqual(
    linkProblems(
      "zh/index.html",
      [
        "sample-reel-en.vtt",
        "../../outside.html",
        "https://example.com/film.mp4",
        "",
        "en/index.html",
      ],
      MEMBERS,
    ),
    [
      "sample-reel-en.vtt resolves to zh/sample-reel-en.vtt, which is no delivery member",
      "../../outside.html leaves the delivery",
      "https://example.com/film.mp4 leaves the delivery",
      "a link has no target",
      "en/index.html resolves to zh/en/index.html, which is no delivery member",
    ],
  );
  // A member a browser would show as raw text is a download, never a link.
  assert.deepEqual(
    linkProblems(
      "zh/index.html",
      ["sample-reel-zh-transcript.md#top", "chapters.json", "chapters.ffmeta"],
      MEMBERS,
    ),
    [
      "sample-reel-zh-transcript.md#top opens raw text in a tab",
      "chapters.json opens raw text in a tab",
      "chapters.ffmeta opens raw text in a tab",
    ],
  );
  assert.deepEqual(linkProblems("zh/index.html", ["sample-reel-zh.srt"], MEMBERS), [
    "sample-reel-zh.srt opens raw text in a tab",
  ]);
});

test("a caption file's cues are read by their times and text, in SRT and WebVTT alike", () => {
  const srt =
    "1\n00:00:01,000 --> 00:00:02,000\nOne\n\n2\n00:00:03,250 --> 00:00:04,500\nTwo\nlines\n";
  const vtt =
    "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nOne\n\n00:00:03.250 --> 00:00:04.500\nTwo\nlines\n";
  const cues = [
    [1000, 2000, "One"],
    [3250, 4500, "Two\nlines"],
  ];
  assert.deepEqual(parseCues(srt), cues);
  assert.deepEqual(parseCues(vtt), cues);
  assert.deepEqual(parseCues("WEBVTT\n"), []);
  assert.deepEqual(parseCues("1\r\n01:00:00,001 --> 01:00:00,500\r\nOne\r\n"), [
    [3600001, 3600500, "One"],
  ]);
});

test("the track's cues must equal the SRT's, in number, times and text", () => {
  const srt = [
    [1000, 2000, "一"],
    [3000, 4000, "二"],
  ];
  assert.deepEqual(cueProblems(srt, srt), []);
  assert.deepEqual(cueProblems(srt.slice(1), srt), ["the track holds 1 cues, the SRT 2"]);
  assert.deepEqual(cueProblems([srt[0], [3000, 4000, "三"]], srt), [
    "cue 2 of the track is 3000-4000 三, in the SRT 3000-4000 二",
  ]);
});

test("the browser's own caption controls count only where they are shown", () => {
  const button = (style) => ({
    attributes: ["pseudo", "-webkit-media-controls-toggle-closed-captions-button", "style", style],
  });
  const tree = (style) => ({
    nodeName: "#document",
    children: [
      { attributes: ["id", "film"], shadowRoots: [{ children: [{ children: [button(style)] }] }] },
    ],
  });
  assert.equal(visibleCaptionControls(tree("display: none;")), 0);
  assert.equal(visibleCaptionControls(tree("")), 1);
  assert.equal(visibleCaptionControls({ children: [] }), 0);
});

test("a track embedded as a data URL gives back its text, and a file name gives none", () => {
  const vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n字幕 “quoted”\n";
  const base64 = `data:text/vtt;charset=utf-8;base64,${Buffer.from(vtt).toString("base64")}`;
  assert.equal(embeddedText(base64), vtt);
  assert.equal(embeddedText(`data:text/vtt,${encodeURIComponent(vtt)}`), vtt);
  assert.equal(embeddedText("sample-reel-zh.vtt"), null);
});

test("sizes are named in decimal units, as the engine writes them", () => {
  assert.deepEqual(
    [404, 999, 1000, 13_005, 251_500, 999_600, 262_800_000, 1_500_000_000].map(sizeLabel),
    ["404 B", "999 B", "1 KB", "13 KB", "252 KB", "1 MB", "263 MB", "1.5 GB"],
  );
});

test("each file the list names carries the size of the delivered member it leads to", () => {
  const sizes = new Map([
    ["zh/sample-reel-zh.vtt", 13_005],
    ["zh/sample-reel-zh-uhd.mp4", 262_800_000],
  ]);
  const entries = [
    { target: "sample-reel-zh.vtt", text: "字幕 · WebVTT · 13 KB" },
    { target: "sample-reel-zh-uhd.mp4", text: "影片 · 4K UHD · MP4 · 251 MB" },
    { target: "sample-reel-zh.srt", text: "字幕 · SRT · 13 KB" },
  ];
  assert.deepEqual(fileProblems("zh/index.html", entries, sizes), [
    "影片 · 4K UHD · MP4 · 251 MB names another size than zh/sample-reel-zh-uhd.mp4's 263 MB",
    "字幕 · SRT · 13 KB leads to zh/sample-reel-zh.srt, which was not read",
  ]);
});

test("a page passes when none of its checks found a problem", () => {
  assert.deepEqual(verdict("zh/index.html", []), {
    page: "zh/index.html",
    verdict: "pass",
    problems: [],
  });
  assert.deepEqual(verdict("en/index.html", ["the track is not showing on the UHD film"]), {
    page: "en/index.html",
    verdict: "fail",
    problems: ["the track is not showing on the UHD film"],
  });
});

/* What a delivery holds for the Chinese player, and a read of a player that does all it should. */
const VTT = "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n一\n";
const CUES = [[1000, 2000, "一"]];
const EXPECTED = {
  code: "zh",
  slug: "sample-reel",
  duration: 60,
  chapters: [
    { title: "开始", start: 0 },
    { title: "构建", start: 20.25 },
  ],
  members: MEMBERS,
  sizes: new Map([
    ["zh/sample-reel-zh-transcript.md", 13_005],
    ["zh/chapters.json", 13_005],
    ["zh/chapters.ffmeta", 13_005],
    ["zh/sample-reel-zh.vtt", 13_005],
    ["zh/sample-reel-zh.srt", 13_005],
    ["zh/sample-reel-zh-uhd.mp4", 262_800_000],
  ]),
  vtt: VTT,
  srt_cues: CUES,
};
const version = (file, dimensions) => ({
  file,
  dimensions,
  duration: 60,
  width: dimensions[0],
  height: dimensions[1],
  error: null,
  kept_time: [20, 20.02],
  track_mode: "hidden",
  cue_at: 12.5,
  active_cue: "“先核对，",
  current_paragraph: "先核对，再放行。",
  seek_checks: [2, 30, 56].map((target) => ({ target, error: null, decoded_frames: 31 })),
});
const SHOWN = Array.from({ length: 4 }, () => ({
  target: "sample-reel-zh-uhd.mp4",
  text: "影片 · 超高清 4K · 画面内含字幕 · MP4 · 263 MB",
  embedded: false,
}));
const DOWNLOADS = [
  "sample-reel-zh-transcript.md",
  "chapters.json",
  "chapters.ffmeta",
  "sample-reel-zh.vtt",
  "sample-reel-zh.srt",
];
const FILES = [
  ...SHOWN,
  ...DOWNLOADS.map((target) => ({ target, text: `${target} · 13 KB`, embedded: true })),
];
const READ = {
  lang: "zh-CN",
  chapters: ["开始", "构建"],
  links: ["../en/index.html", "../index.html", "sample-reel-zh-uhd.mp4", "#transcript"],
  language_links: ["../en/index.html", "../index.html"],
  plain_downloads: [],
  files: FILES,
  saved: DOWNLOADS.map((name) => ({ name, state: "completed", same: true, navigated: false })),
  track: { kind: "metadata", srclang: "zh", label: "中文字幕", text: VTT },
  opening: { src: "sample-reel-zh-1080p-captioned.mp4", tracks: 1, mode: "hidden" },
  cues: CUES,
  native_caption_controls: 0,
  control_sweep: { controls: 14, shown: [] },
  editions: [version("-uhd.mp4", [3840, 2160]), version("-1080p-captioned.mp4", [1920, 1080])],
  chapter_jump: 20.25,
  transcript_chapters: 2,
  transcript_open: true,
  transcript_time: { time: 22.872, played: 22.9 },
};

test("a player that does what the delivery holds has no problem", () => {
  assert.deepEqual(playerProblems(READ, EXPECTED), []);
  // A read that stopped early is judged as far as it got.
  assert.deepEqual(playerProblems({ lang: "zh-CN", editions: [] }, EXPECTED), []);
});

test("a player that misses what the delivery holds names each problem", () => {
  const broken = {
    ...READ,
    lang: "en",
    chapters: ["开始"],
    links: ["sample-reel-zh.srt.bak"],
    language_links: [],
    plain_downloads: ["sample-reel-zh-uhd.mp4"],
    files: FILES.slice(0, 7),
    saved: [
      { name: "sample-reel-zh-transcript.md", state: "canceled", same: false, navigated: false },
      { name: "chapters.json", state: "completed", same: true, navigated: true },
    ],
    track: { kind: "captions", srclang: "zh", label: "", text: "WEBVTT\n" },
    opening: { src: "sample-reel-zh-uhd.mp4", tracks: 0, mode: "showing" },
    cues: [],
    native_caption_controls: 1,
    control_sweep: { controls: 14, shown: ["字幕"] },
    editions: [],
    chapter_jump: 3,
    transcript_chapters: 1,
    transcript_open: false,
    transcript_time: { time: 22.872, played: 40 },
  };
  assert.deepEqual(playerProblems(broken, EXPECTED), [
    "the page's language is en",
    "the chapter buttons differ from chapters.json",
    "sample-reel-zh.srt.bak resolves to zh/sample-reel-zh.srt.bak, which is no delivery member",
    "the language links do not lead to the other edition's player and the entry page",
    "the files list names 7 files, not 9",
    "sample-reel-zh-uhd.mp4 asks for a download, which a browser ignores on a file beside the page",
    "sample-reel-zh.vtt is no download the page holds",
    "sample-reel-zh.srt is no download the page holds",
    "sample-reel-zh-transcript.md saved canceled, not the delivered bytes",
    "chapters.json navigated away from the page",
    "chapters.ffmeta was not saved",
    "sample-reel-zh.vtt was not saved",
    "sample-reel-zh.srt was not saved",
    "the track is no hidden metadata track with a label in its language",
    "the track does not carry the delivered WebVTT",
    "the page opens on sample-reel-zh-uhd.mp4",
    "the film has 0 text tracks, not one",
    "the caption track is showing on the viewing film, not hidden",
    "the track holds 0 cues, the SRT 1",
    "the browser's own controls offer the track, so a viewer could double the captions",
    "a control shows the track: 字幕",
    "the second chapter does not play from its start",
    "the transcript does not head every chapter",
    "the transcript link does not open the transcript",
    "a transcript time of 22.872 s played from 40 s",
  ]);
});

test("a version must keep the time, keep the track hidden, mark its paragraph and decode", () => {
  assert.deepEqual(versionProblems(version("-uhd.mp4", [3840, 2160]), 60), []);
  const moved = {
    ...version("-uhd.mp4", [3840, 2160]),
    kept_time: [20, 0],
    track_mode: "showing",
    duration: 59.5,
    width: 1920,
    height: 1080,
    error: 4,
    active_cue: null,
    current_paragraph: null,
  };
  moved.seek_checks[1] = { target: 30, error: null, decoded_frames: 0 };
  assert.deepEqual(versionProblems(moved, 60), [
    "switching to -uhd.mp4 moved the time from 20 s to 0 s",
    "the caption track is showing on -uhd.mp4, not hidden",
    "no cue is active at 12.5 s on -uhd.mp4",
    "-uhd.mp4 lasts 59.5 s, not 60 s",
    "-uhd.mp4 is 1920x1080, not 3840x2160",
    "-uhd.mp4 reports media error 4",
    "-uhd.mp4 decodes nothing at 30 s",
  ]);
  const elsewhere = { ...version("-uhd.mp4", [3840, 2160]), current_paragraph: "另一段。" };
  assert.deepEqual(versionProblems(elsewhere, 60), [
    "the transcript's current paragraph at 12.5 s on -uhd.mp4 does not hold the active cue",
  ]);
  // A cue and its paragraph are compared by their letters and digits.
  assert.equal(bare("“先核对，” A-1"), "先核对A1");
});

test("the entry page leads to both players and nowhere outside the delivery", () => {
  const links = ["zh/index.html", "en/index.html"];
  assert.deepEqual(entryProblems({ links, language_links: links }, MEMBERS), []);
  assert.deepEqual(
    entryProblems(
      { links: ["zh/index.html", "fr/index.html"], language_links: ["zh/index.html"] },
      MEMBERS,
    ),
    [
      "fr/index.html resolves to fr/index.html, which is no delivery member",
      "the language links are zh/index.html, not zh/index.html, en/index.html",
    ],
  );
  assert.deepEqual(entryProblems({}, MEMBERS), []);
});

test("a read that stops fails its page and keeps what it read, and the other pages are still read", async () => {
  // A page that cannot be opened.
  const closed = { goto: async () => Promise.reject(Error("net::ERR_FILE_NOT_FOUND")) };
  assert.deepEqual(await readEntry(closed, "/nowhere", MEMBERS), {
    page: "index.html",
    verdict: "fail",
    problems: ["the read stopped: net::ERR_FILE_NOT_FOUND"],
  });
  // A player whose delivery holds no chapters is not judged beyond the stop.
  const binding = { film: { slug: "sample-reel", duration: 60 }, members: [] };
  const read = await readPlayer(closed, "/nowhere", "zh", binding, "/nowhere/player-zh.png");
  assert.equal(read.verdict, "fail");
  assert.deepEqual(read.editions, []);
  assert.match(read.problems[0], /^the read stopped: ENOENT/);
});
