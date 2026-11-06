/* The frame audit's wrapped labels (wrapped_labels): every label a frame paints on more than one line, read from the
 * film's own layout records (window.__filmLayout.texts), and the rules its lines break at rest.
 *
 * The lines of a label share its scene and the whole text the composition registers with each of them (`whole`). A
 * piece of one size whose vertical centre lies within a line's band, widened by a quarter of the band's height, and
 * which reaches the line across within half an em stands on that line, so a mark hung at a line's end or a word
 * revealed after the others joins it; a text painted twice in one place is one piece. Lines are read top to bottom
 * and their pieces left to right. Lines that follow each other, each below the last within 2.6 times the taller one's
 * height and overlapping it across, and whose texts joined without whitespace equal the whole, are one place of the
 * label, so the same name standing in two places is two labels. A line spans its pieces' extent, less the blank half
 * of full-width punctuation at either end of a CJK line (layout.mjs). A label is judged at the first frame in which
 * every one of its lines stands at 0.9 opacity or more, by the film's declared rules (filmkit.picture.gates names them
 * in FILMKIT_WRAPPING) or the defaults:
 *   - within the lines of one size, a line other than the last spans at least `line_share` of the widest of them, and
 *     the last at least `last_share`;
 *   - an English label, one without a Han character: within the lines of one size, a line other than the last ends on
 *     no lead word, and lines holding three or more words leave more than one word on the last; a name over its
 *     smaller gloss is thus two blocks, not one broken phrase;
 *   - a Chinese label, one with a Han character: no line after the first opens on closing punctuation. */
import { readFileSync } from "node:fs";

import { CJK, CLOSING, HUNG, OPENING } from "./layout.mjs";

/* The words an English line may not end on, as they lead the phrase that follows them: articles, prepositions,
 * coordinating and subordinating conjunctions, determiners, possessives, wh-words and auxiliaries. A film declares
 * more in its `lead_words`. */
export const LEAD_WORDS = new Set(
  (
    "a an the of in on at by to for with from into onto over under about after before between through without " +
    "within against per via as than like and or but nor if because although though while unless until since " +
    "whether its their his her our your my this that these those each every any no some which who whose whom what " +
    "when where why how is are was were be been can will would should may must not"
  ).split(" "),
);
/* The marks that close what precedes them, which a Chinese line may not open on. */
export const CLOSES = /^[，。、；：！？）》」』”’…]/u;
/* The rules a film declares in [picture.wrapping], with their defaults. */
export const WRAPPING = Object.freeze({ line_share: 0.8, last_share: 0.6, lead_words: [] });

/* Every line stands at this opacity or more when its label is at rest. */
const REST = 0.9;
/* A piece stands on a line whose band, widened by this share of its height, holds its vertical centre, and which it
 * reaches across within this share of its em, a word space (layout.mjs). */
const BAND = 0.25,
  JOIN = 0.5;
/* The next line of a label follows within this many times the taller line's height, a line counting at least 10 px,
 * and overlaps the last one within 4 px across. */
const REACH = 2.6,
  LEAST = 10,
  ACROSS = 4;
/* Pieces this share of their em apart, with no space of their own between them, are two words. */
const WORD_SPACE = 0.25;
const HAN = /\p{Script=Han}/u;

const squeeze = (v) => v.replace(/\s+/gu, "");
const sameSize = (a, b) => Math.abs((a.size ?? 0) - (b.size ?? 0)) < 0.5;
const middle = (v) => (v.top + v.bottom) / 2;
/* A line's span, less the blank half of a full-width mark hung at either end of a CJK line. */
const width = (v) =>
  v.right -
  v.left -
  (CJK.test(v.text) ? HUNG * v.em * (CLOSING.test(v.text) + OPENING.test(v.text)) : 0);
/* The share of the widest line of its block that each line spans, to three places, as it is judged and reported. */
const sharesOf = (block) => {
  const widest = Math.max(...block.map(width));
  return block.map((l) => +(widest > 0 ? width(l) / widest : 1).toFixed(3));
};
/* A painted word without the punctuation around it, and its form for comparison. */
const word = (v) => v.replace(/^[^\p{L}\p{N}'’]+|[^\p{L}\p{N}'’]+$/gu, "");
const bare = (v) => word(v).toLowerCase().replaceAll("’", "'");
/* The words of a text: its runs between spaces that hold a letter or a digit. */
const wordsOf = (v) => v.split(/\s+/u).filter((w) => /[\p{L}\p{N}]/u.test(w));

/** The rules of the declaration that FILMKIT_WRAPPING names, a JSON object of `line_share`, `last_share` and
 * `lead_words`, or the defaults without one. */
export function readWrapping(path = process.env.FILMKIT_WRAPPING) {
  if (!path) return WRAPPING;
  const declared = { ...WRAPPING, ...JSON.parse(readFileSync(path, "utf8")) };
  for (const share of ["line_share", "last_share"])
    if (!(declared[share] > 0 && declared[share] <= 1))
      throw RangeError(`${share} is not a share in (0, 1]: ${declared[share]}`);
  return declared;
}

/* A piece's em on the screen: the font size it was painted at, as the frame audit gives it, or its registered size. */
const emOf = (p) => p.em ?? p.size ?? 0;

/* A line's text: its pieces left to right, a space between two that stand a word space apart with none of their own. */
function joined(pieces) {
  let text = "";
  pieces.forEach((p, k) => {
    const gap = k ? p.bounds[0] - pieces[k - 1].bounds[2] : 0;
    if (k && gap >= WORD_SPACE * emOf(p) && !/\s$/u.test(text) && !/^\s/u.test(p.text)) text += " ";
    text += p.text;
  });
  return text.trim();
}

/* A text painted twice in one place, such as a lit copy over a dim one, is one piece, at its higher opacity. */
function distinct(pieces) {
  const kept = new Map();
  for (const p of pieces) {
    const key = [p.text, Math.round(p.bounds[0]), Math.round(p.bounds[1])].join("\u0000");
    if (!kept.has(key) || p.alpha > kept.get(key).alpha) kept.set(key, p);
  }
  return [...kept.values()];
}

/* The lines of one label's pieces, each with its pieces, text, size, em, band, extent across and lowest opacity.
 * Pieces are taken left to right, so each line grows rightwards from its first piece. */
function linesOf(pieces) {
  const lines = [];
  const sorted = distinct(pieces).sort(
    (a, b) => a.bounds[0] - b.bounds[0] || a.bounds[1] - b.bounds[1],
  );
  for (const p of sorted) {
    const [left, top, right, bottom] = p.bounds,
      height = bottom - top,
      centre = (top + bottom) / 2,
      reach = JOIN * emOf(p);
    const line = lines.find(
      (l) =>
        sameSize(l, p) &&
        centre >= l.top - BAND * l.height &&
        centre <= l.bottom + BAND * l.height &&
        left <= l.right + reach &&
        right >= l.left - reach,
    );
    if (!line) {
      lines.push({ size: p.size, em: emOf(p), top, bottom, height, left, right, alpha: p.alpha });
      lines.at(-1).pieces = [p];
      continue;
    }
    line.pieces.push(p);
    line.em = Math.max(line.em, emOf(p));
    line.left = Math.min(line.left, left);
    line.right = Math.max(line.right, right);
    line.alpha = Math.min(line.alpha, p.alpha);
    // A taller piece widens the band; a comma's low ink does not move it.
    if (height > line.height) {
      line.top = Math.min(line.top, top);
      line.bottom = Math.max(line.bottom, bottom);
      line.height = line.bottom - line.top;
    }
  }
  for (const l of lines) {
    l.pieces.sort((a, b) => a.bounds[0] - b.bounds[0]);
    l.text = joined(l.pieces);
  }
  return lines.sort((a, b) => middle(a) - middle(b));
}

/* The places of a label: runs of lines that follow each other and whose texts joined equal the whole. */
function placesOf(lines, whole) {
  const target = squeeze(whole),
    used = new Set(),
    places = [];
  const follows = (l, last) =>
    middle(l) > middle(last) &&
    middle(l) - middle(last) <= REACH * Math.max(l.height, last.height, LEAST) &&
    l.right >= last.left - ACROSS &&
    l.left <= last.right + ACROSS;
  lines.forEach((first, i) => {
    let text = squeeze(first.text);
    if (used.has(i) || !text || !target.startsWith(text)) return;
    const run = [i];
    while (text !== target) {
      const last = lines[run.at(-1)];
      const next = lines.findIndex(
        (l, j) =>
          !used.has(j) &&
          !run.includes(j) &&
          follows(l, last) &&
          target.startsWith(text + squeeze(l.text)),
      );
      if (next < 0) break;
      run.push(next);
      text += squeeze(lines[next].text);
    }
    if (text !== target || run.length < 2) return;
    for (const j of run) used.add(j);
    places.push(run.map((j) => lines[j]));
  });
  return places;
}

/** The wrapped labels of one frame's layout records: each place of a name a scene registers as a label and paints on
 * two or more lines, with its scene, its whole text and its lines top to bottom. A record may carry the `em` its text
 * was painted at; otherwise its `size` stands for it. */
export function wrappedLabels(records) {
  const pieces = new Map();
  for (const r of records) {
    if (!r.scene || (r.role ?? "label") !== "label" || !r.text?.trim() || r.whole == null) continue;
    if (!(r.alpha > 0)) continue;
    // A name painted whole on one line is not wrapped.
    if (squeeze(r.text) === squeeze(r.whole)) continue;
    const key = `${r.scene}\u0000${r.whole}`;
    pieces.set(key, [...(pieces.get(key) ?? []), r]);
  }
  return [...pieces.values()].flatMap((group) => {
    const { scene, whole } = group[0];
    return placesOf(linesOf(group), whole).map((lines) => ({ scene, whole, lines }));
  });
}

/* The lines of a label in blocks of one size, each line with its number in the label. */
function blocksOf(lines) {
  const blocks = [];
  lines.forEach((line, k) => {
    const block = blocks.at(-1);
    const entry = { ...line, number: k + 1 };
    if (block && sameSize(block[0], line)) block.push(entry);
    else blocks.push([entry]);
  });
  return blocks;
}

/** The rules a wrapped label's lines break (wrappedLabels), each named with its line: the share of the widest line of
 * its size a line spans under the declared shares, a lead word at the end of a line, one word left on the last line,
 * and a Chinese line opening on closing punctuation. */
export function labelBreaks({ whole, lines }, rules = WRAPPING) {
  const lead = new Set([...LEAD_WORDS, ...rules.lead_words.map(bare)]),
    chinese = HAN.test(whole),
    found = [];
  for (const block of blocksOf(lines)) {
    if (block.length < 2) continue;
    const shares = sharesOf(block),
      words = block.flatMap((l) => wordsOf(l.text)).length;
    block.forEach((line, k) => {
      const last = k === block.length - 1,
        share = shares[k],
        ending = wordsOf(line.text).at(-1);
      if (!last && share < rules.line_share)
        found.push(
          `line ${line.number} spans ${share} of the widest line of its size, under ${rules.line_share}`,
        );
      if (last && share < rules.last_share)
        found.push(
          `line ${line.number}, the last of its size, spans ${share} of the widest, under ${rules.last_share}`,
        );
      if (chinese) return;
      if (!last && ending && lead.has(bare(ending)))
        found.push(`line ${line.number} ends on the lead word "${word(ending)}"`);
      if (last && words >= 3 && wordsOf(line.text).length === 1)
        found.push(
          `line ${line.number} holds one of its block's ${words} words, "${word(ending)}"`,
        );
    });
  }
  if (chinese)
    lines.forEach((line, k) => {
      const mark = k ? CLOSES.exec(line.text)?.[0] : null;
      if (mark) found.push(`line ${k + 1} opens on "${mark}"`);
    });
  return found;
}

/** Follows the wrapped labels through the frames: `frame(f)` reads a frame audit frame's time, its layout records and
 * its paints, whose font size and scale give each record's em, and `finish()` returns, per scene, each label by its
 * lines, with when it was first seen and first at rest (null when it never rests), and at rest the sizes of its lines,
 * the share of the widest line of its size each spans and the rules its lines break. A label is judged once, at the
 * first frame it rests in; its lines read alike whenever they stand again. */
export function wrapLayout(rules = WRAPPING) {
  const labels = new Map();
  return {
    frame(f) {
      const t = +f.t.toFixed(3);
      // The frame audit gives each record the sequence number of its paint.
      const records = f.layout.texts.map((r) => {
        const paint = f.paints?.[r.seq - 1];
        return paint?.kind === "text" ? { ...r, em: paint.size * paint.scale } : r;
      });
      for (const label of wrappedLabels(records)) {
        const lines = label.lines.map((l) => l.text),
          key = lines.join("\u0000"),
          scene = labels.get(label.scene) ?? new Map();
        labels.set(label.scene, scene);
        if (!scene.has(key)) scene.set(key, { lines, seen: t, at: null, breaks: [] });
        const entry = scene.get(key);
        if (entry.at !== null || !label.lines.every((l) => l.alpha >= REST)) continue;
        Object.assign(entry, {
          at: t,
          sizes: label.lines.map((l) => l.size),
          shares: blocksOf(label.lines).flatMap(sharesOf),
          breaks: labelBreaks(label, rules),
        });
      }
    },
    finish() {
      const order = (a, b) =>
        a.seen - b.seen || a.lines.join("\n").localeCompare(b.lines.join("\n"));
      return Object.fromEntries(
        [...labels].map(([scene, entries]) => [scene, [...entries.values()].sort(order)]),
      );
    },
  };
}
