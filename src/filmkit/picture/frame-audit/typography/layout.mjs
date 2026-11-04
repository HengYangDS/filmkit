/* How the frame audit's text-layout measures read a voiced frame (measures.mjs).
 *
 * A frame's paints (headless-composition.mjs) give a text's anchor, size and baseline exactly and its extent as the
 * headless canvas estimates it, a CJK character as wide as its size and a Latin one about half of it; a mark's path is
 * exact. Text settled at 0.85 opacity or more and the settled marks of the content band, below the head band and above
 * the caption band, are read. Runs of one alignment, size and baseline that follow each other join into lines; a
 * line's ink rises 0.74 of its size above its baseline and falls 0.18 below it when it holds a CJK character, and 0.72
 * and 0.2 otherwise. A container is a closed outline or panel at least 40 by 24 px, a card one that runs along its
 * box; each line stands in its innermost container or in none. Lines of one size and container stacked within 1.6
 * times their size form a block, and within three times it a column of items. */
import { HEAD, VISIBLE } from "../marks.mjs";

/* Text and marks at this opacity or more have settled; fades in and out are not judged. */
const SETTLED = 0.85;
/* The frame audit's content band (composition.mjs): below the head band, above the caption band. */
const BAND = [HEAD, 950];
/* The characters the headless canvas sets a full size wide, and the ink of a line above and below its baseline. */
const CJK = /[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]/u;
const INK = { cjk: [0.74, 0.18], latin: [0.72, 0.2] };
/* Full-width punctuation sets its mark in one half of its em, so a CJK line that ends in a closing mark, or starts
 * with an opening one, may hang that half past its edge for its ink to line up. */
const CLOSING = /[、，。；：！？）」』”》】]$/u,
  OPENING = /^[（「『“《【]/u,
  HUNG = 0.5;
/* Names hold letters; a lone check, cross or question mark is a mark, as a drawn one is. */
export const LETTER = /\p{L}/u;
const GLYPH = /^[✓✔✗✘✕×?？]$/u;
/* Runs of one line follow each other within half the size, a word space. */
const JOIN = 0.5;

/* Blocks and columns: a line follows another overlapping it by a third of the narrower; a block's lines follow at up
 * to 1.6 times their size and a column's items at 0.9 to three times it. Items beyond a block's leading make a list,
 * read from every visible name, lit or dimmed. */
export const SHARE = 0.3,
  LEADING = 1.6,
  PITCH = [0.9, 3];
/* A mark leads or follows an item when it stands within 2.5 times the item's size of it, level with its ink, and is no
 * larger than 1.6 times the size. Like marks agree in kind and in size within 3 px. */
const MARK_REACH = 2.5,
  MARK_LEVEL = 0.45,
  MARK_SIZE = 1.6,
  LIKE_SIZE = 3;
/* Containers are closed outlines or panels at least 40 by 24 px, and narrower than the content band. */
const CONTAINER = [40, 24, 1700];

export const round = (v) => Math.round(v * 10) / 10;
export const spread = (values) => Math.max(...values) - Math.min(...values);
const overlap = (a, b) => Math.min(a.right, b.right) - Math.max(a.left, b.left);
const width = (v) => v.right - v.left;
export const middle = (v) => (v.inkTop + v.inkBottom) / 2;
export const centre = (v) => (v.left + v.right) / 2;
export const sameSize = (a, b) => Math.abs(a.size - b.size) <= 0.6;
const boxOf = (points) => {
  const xs = points.map((p) => p[0]),
    ys = points.map((p) => p[1]);
  return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
};
const extent = ([left, top, right, bottom]) => ({
  left,
  top,
  right,
  bottom,
  width: right - left,
  height: bottom - top,
  cx: (left + right) / 2,
  cy: (top + bottom) / 2,
});

/* A painted text: its anchor, size and baseline, its alignment read from where the anchor stands in its box, its box
 * and its ink, and the whole text, set and role its name is registered with (the text itself, none and a label when
 * the paint carries none). The box rises 0.8 of the size above an alphabetic anchor, 0.52 above a middle one and none above a top
 * one (headless-composition.mjs), which places the baseline. */
function textOf(paint) {
  const [x, y] = paint.subs[0][0],
    [left, top, right, bottom] = boxOf(paint.points.map(paint.toScreen)),
    size = paint.size * paint.scale;
  const mode = Math.abs(x - left) < 0.6 ? "left" : Math.abs(x - right) < 0.6 ? "right" : "centre";
  const rise = (y - top) / size;
  const baseline =
    Math.abs(rise - 0.8) < 0.05
      ? y
      : Math.abs(rise - 0.52) < 0.05
        ? y + 0.28 * size
        : y + 0.8 * size;
  const [above, below] = CJK.test(paint.text) ? INK.cjk : INK.latin;
  return {
    text: paint.text,
    scene: paint.scene,
    whole: paint.whole ?? paint.text,
    set: paint.set ?? null,
    role: paint.role ?? "label",
    size,
    mode,
    anchor: x,
    baseline,
    left,
    right,
    top,
    bottom,
    inkTop: baseline - above * size,
    inkBottom: baseline + below * size,
  };
}

/* Runs of one line: one scene, size, baseline and alignment, left- or right-aligned, each following the last within a
 * word space, as a phrase revealed word by word or a word set in another colour. A centred text is a line of its own.
 * A line of one run declares its alignment and its anchor; a line of several declares neither, since the runs were
 * placed by the composition's own measure. Its ink edges allow hung full-width punctuation. */
function linesOf(texts) {
  const sorted = [...texts].sort((a, b) => a.baseline - b.baseline || a.left - b.left);
  const lines = [];
  for (const t of sorted) {
    const line =
      t.mode !== "centre" &&
      lines.find(
        (l) =>
          l.scene === t.scene &&
          l.mode === t.mode &&
          sameSize(l, t) &&
          Math.abs(l.baseline - t.baseline) <= 0.6 &&
          t.left - l.right <= JOIN * t.size &&
          t.right > l.right,
      );
    if (!line) lines.push({ ...t, parts: [t] });
    // A text painted twice in one place, such as a glow under its face, is one run.
    else if (!line.parts.some((q) => q.text === t.text && Math.abs(q.anchor - t.anchor) < 0.5)) {
      line.parts.push(t);
      line.text += (t.left - line.right > 0.25 * t.size ? " " : "") + t.text;
      line.right = t.right;
      line.top = Math.min(line.top, t.top);
      line.bottom = Math.max(line.bottom, t.bottom);
      line.inkTop = Math.min(line.inkTop, t.inkTop);
      line.inkBottom = Math.max(line.inkBottom, t.inkBottom);
      if (line.mode === "right") line.anchor = t.anchor;
    }
  }
  for (const line of lines) {
    line.single = line.parts.length === 1;
    const hung = CJK.test(line.text) ? HUNG * line.size : 0;
    line.inkLeft = line.left + (OPENING.test(line.text) ? hung : 0);
    line.inkRight = line.right - (CLOSING.test(line.text) ? hung : 0);
  }
  return lines;
}

/* A painted mark: its screen subpaths, box and centre, half its stroke width on the screen, its closed subpaths, and
 * whether it is one card: a single closed outline or panel, at least a container's size, that runs along its box. */
function markOf(paint) {
  const subs = paint.subs.filter((sub) => sub.length);
  if (!subs.length) return null;
  const shut = (sub) =>
    sub.length > 2 &&
    (paint.kind === "fill" ||
      Math.hypot(sub[0][0] - sub.at(-1)[0], sub[0][1] - sub.at(-1)[1]) <= 2);
  const mark = {
    kind: paint.kind,
    scene: paint.scene,
    subs,
    shapes: subs.filter(shut),
    box: boxOf(subs.flat()),
    half: paint.kind === "stroke" ? (paint.lineWidth * paint.scale) / 2 : 0,
  };
  Object.assign(mark, extent(mark.box));
  mark.card =
    subs.length === 1 &&
    mark.shapes.length === 1 &&
    mark.width >= CONTAINER[0] &&
    mark.height >= CONTAINER[1] &&
    hugsBox(subs[0], mark.box);
  return mark;
}
/* A rectangle or rounded rectangle runs along its box for most of its length; a ring touches it at four points. */
function hugsBox(sub, [x0, y0, x1, y1]) {
  const on = ([x, y]) => [
    Math.abs(x - x0) < 0.6,
    Math.abs(x - x1) < 0.6,
    Math.abs(y - y0) < 0.6,
    Math.abs(y - y1) < 0.6,
  ];
  let total = 0,
    along = 0;
  for (let k = 1; k < sub.length; k++) {
    const length = Math.hypot(sub[k][0] - sub[k - 1][0], sub[k][1] - sub[k - 1][1]),
      a = on(sub[k - 1]),
      b = on(sub[k]);
    total += length;
    if (a.some((v, i) => v && b[i])) along += length;
  }
  return total > 0 && along >= 0.6 * total;
}
/* A lone glyph stands as a mark: its estimated box, its ink for its height. */
const glyphMark = (t) => ({
  kind: "glyph",
  scene: t.scene,
  subs: [],
  shapes: [],
  box: [t.left, t.inkTop, t.right, t.inkBottom],
  half: 0,
  card: false,
  ...extent([t.left, t.inkTop, t.right, t.inkBottom]),
});
/* Marks alike enough to be compared by their edges. */
export const like = (a, b) =>
  a.kind === b.kind &&
  Math.abs(a.width - b.width) <= LIKE_SIZE &&
  Math.abs(a.height - b.height) <= LIKE_SIZE;

/* Whether a box lies within a container: within its box, and for a ring within its outline. */
export function holds(container, v) {
  if (
    v.left < container.left - 1 ||
    v.right > container.right + 1 ||
    v.top < container.top - 1 ||
    v.bottom > container.bottom + 1
  )
    return false;
  return (
    container.card ||
    [
      [v.left, v.top],
      [v.right, v.top],
      [v.left, v.bottom],
      [v.right, v.bottom],
    ].every((p) => insidePath(container.outline, p))
  );
}
export function insidePath(sub, [x, y]) {
  let inside = false;
  for (let i = 0, j = sub.length - 1; i < sub.length; j = i++) {
    const [xi, yi] = sub[i],
      [xj, yj] = sub[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}
/* A card's panel and its outline, or an outline lit over it, are one card. */
export const twins = (a, b) => a.box.every((v, i) => Math.abs(v - b.box[i]) <= 1.5);

/* Chains of lines, each linked to the line `link` gives for it. */
function chainsOf(lines, link) {
  const next = new Map();
  for (const l of lines) {
    const b = link(l);
    if (b) next.set(l, b);
  }
  const followed = new Set(next.values()),
    chains = [];
  for (const first of lines) {
    if (followed.has(first) || !next.has(first)) continue;
    const chain = [first];
    for (let l = next.get(first); l; l = next.get(l)) chain.push(l);
    chains.push(chain);
  }
  return chains;
}

/* The line stacked under each line: the nearest below it in its scene and container that overlaps it. */
function stacked(names) {
  const below = new Map();
  for (const l of names) {
    let best = null;
    for (const other of names)
      if (
        other !== l &&
        other.scene === l.scene &&
        other.container === l.container &&
        other.baseline > l.baseline + 0.6 &&
        overlap(l, other) > SHARE * Math.min(width(l), width(other)) &&
        (!best || other.baseline < best.baseline)
      )
        best = other;
    if (best) below.set(l, best);
  }
  return below;
}

/* The settled texts and marks of a frame's content band: its lines and names, its containers, the innermost container
 * of each line, the line stacked under each, its blocks and columns, and the names that stand in a list. */
export function frameLayout(paints) {
  const texts = [],
    shown = [],
    marks = [];
  for (const paint of paints) {
    if (!paint.scene || paint.alpha <= VISIBLE) continue;
    if (paint.kind === "text") {
      if (!paint.text.trim()) continue;
      const t = textOf(paint);
      if (t.top < BAND[0] || t.bottom > BAND[1]) continue;
      shown.push(t);
      if (paint.alpha >= SETTLED) texts.push(t);
    } else if (paint.alpha >= SETTLED && (paint.kind === "stroke" || paint.kind === "fill")) {
      const mark = markOf(paint);
      if (mark && mark.bottom >= BAND[0] && mark.top <= BAND[1]) marks.push(mark);
    }
  }
  const glyph = (t) => GLYPH.test(t.text.trim());
  const glyphs = texts.filter(glyph).map(glyphMark);
  const lines = linesOf(texts.filter((t) => !glyph(t)));
  // Every closed subpath of a mark is a container, so boxes drawn as one path stay apart.
  const containers = [];
  for (const mark of marks)
    for (const outline of mark.shapes) {
      const box = boxOf(outline),
        shape = { scene: mark.scene, box, outline, card: hugsBox(outline, box), ...extent(box) };
      if (shape.width < CONTAINER[0] || shape.height < CONTAINER[1] || shape.width >= CONTAINER[2])
        continue;
      if (!containers.some((c) => c.scene === shape.scene && twins(c, shape)))
        containers.push(shape);
    }
  const innermost = (line) =>
    containers
      .filter((c) => c.scene === line.scene && holds(c, line))
      .sort((a, b) => a.width * a.height - b.width * b.height)[0] ?? null;
  const namesOf = (all) => {
    const found = all.filter((l) => LETTER.test(l.text));
    for (const l of found) l.container = innermost(l);
    return found;
  };
  const names = namesOf(lines),
    below = stacked(names);
  const step = (a, b) => (b.baseline - a.baseline) / a.size;
  const linked = (map, least, most) => (l) => {
    const b = map.get(l);
    return b && sameSize(l, b) && step(l, b) >= least && step(l, b) <= most ? b : null;
  };
  const blocks = chainsOf(names, linked(below, 0, LEADING)),
    columns = chainsOf(names, linked(below, PITCH[0], PITCH[1]));
  // A list's items stand on its own pitch; a dimmed item still belongs to it, so lists are read from every shown name.
  const shownNames = namesOf(linesOf(shown.filter((t) => !glyph(t))));
  const runOf = (q) => [q.scene, q.text, round(q.anchor), round(q.baseline)].join("\u0000");
  const inList = new Set(
    chainsOf(shownNames, linked(stacked(shownNames), LEADING + 1e-9, PITCH[1]))
      .flat()
      .flatMap((l) => l.parts.map(runOf)),
  );
  const listed = new Set(names.filter((l) => l.parts.some((q) => inList.has(runOf(q)))));
  const lead = new Map(names.map((l) => [l, markBeside(l, [...marks, ...glyphs], "lead")]));
  return { lines, names, marks, glyphs, containers, below, blocks, columns, listed, lead };
}

/* The mark that leads a line, just before it and level with its ink, or the mark that follows it. */
export function markBeside(line, marks, side) {
  let best = null;
  for (const m of marks) {
    if (
      m.scene !== line.scene ||
      m.width > MARK_SIZE * line.size ||
      m.height > MARK_SIZE * line.size
    )
      continue;
    if (Math.abs(m.cy - middle(line)) > MARK_LEVEL * line.size) continue;
    const gap = side === "lead" ? line.left - m.right : m.left - line.right;
    if (gap < -1 || gap > MARK_REACH * line.size) continue;
    if (!best || (side === "lead" ? m.right > best.right : m.left < best.left)) best = m;
  }
  return best;
}
