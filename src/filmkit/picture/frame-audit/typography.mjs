/* The frame audit's text-layout measures: how the settled names and marks of each voiced frame line up.
 *
 * A frame's paints (headless-composition.mjs) give a text's anchor, size and baseline exactly and its extent as the
 * headless canvas estimates it, a CJK character as wide as its size and a Latin one about half of it; a mark's path is
 * exact. Text settled at 0.85 opacity or more and the settled marks of the content band, below the head band and above
 * the caption band, are read. Runs of one alignment, size and baseline that follow each other join into lines; a
 * line's ink rises 0.74 of its size above its baseline and falls 0.18 below it when it holds a CJK character, and 0.72
 * and 0.2 otherwise. A container is a closed outline or panel at least 40 by 24 px, a card one that runs along its
 * box; each line stands in its innermost container or in none. Lines of one size and container stacked within 1.6
 * times their size form a block, and within three times it a column of items. The measures:
 *   ragged_rows      names of one size side by side whose baselines differ by more than 3.5 px and less than half
 *                    their size, in the same innermost container, or in none and within 300 px of each other; an
 *                    item of a list, set on the list's pitch or led by a marker, is not in a row with a name beside
 *                    the list;
 *   ragged_columns   the lines of one block, or the items stacked in one column, whose shared edge differs by more
 *                    than 3 px, and the lines of a left-aligned block centred under or over a mark that stand more
 *                    than 4 px off its axis;
 *   crammed_lines    a line stacked under another of its block with less than 7 px clear between their inks;
 *   off_card_centre  a name alone in a card no taller than three times its size, more than 4 px off the card's
 *                    centre or middle;
 *   uneven_pitch     three or more like marks on one centre line at uneven pitch while the names under them keep
 *                    equal gaps, the trace of spacing by name width;
 *   touching_marks   a name whose ink comes within 3 px of a mark, measured on the mark's path.
 * Each measure's findings are joined over consecutive voiced frames into runs per scene and texts, and a run of 1 s or
 * more is kept with its start, its end, its texts and the offsets of its worst frame. The first four rest on exact
 * anchors, sizes and baselines; uneven_pitch and touching_marks rest on the estimated extents of Latin text. */
import { HEAD, VISIBLE } from "./marks.mjs";

/* Text and marks at this opacity or more have settled; fades in and out are not judged. */
const SETTLED = 0.85;
/* The frame audit's content band (composition.mjs): below the head band, above the caption band. */
const BAND = [HEAD, 950];
/* A run must last this long, so a passing build-up or a fade is not a defect. */
const RUN_SECONDS = 1;
/* The characters the headless canvas sets a full size wide, and the ink of a line above and below its baseline. */
const CJK = /[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]/u;
const INK = { cjk: [0.74, 0.18], latin: [0.72, 0.2] };
/* Full-width punctuation sets its mark in one half of its em, so a CJK line that ends in a closing mark, or starts
 * with an opening one, may hang that half past its edge for its ink to line up. */
const CLOSING = /[、，。；：！？）」』”》】]$/u,
  OPENING = /^[（「『“《【]/u,
  HUNG = 0.5;
/* Names hold letters; a lone check, cross or question mark is a mark, as a drawn one is. */
const LETTER = /\p{L}/u;
const GLYPH = /^[✓✔✗✘✕×?？]$/u;
/* Runs of one line follow each other within half the size, a word space. */
const JOIN = 0.5;

/* ragged_rows: the reviewers see baselines 4 px apart in a row; past half the size, two names stand on two rows. */
const ROW_STEP = 3.5,
  ROW_REACH = 300;
/* Blocks and columns: a line follows another overlapping it by a third of the narrower; a block's lines follow at up
 * to 1.6 times their size and a column's items at 0.9 to three times it. Items beyond a block's leading make a list,
 * read from every visible name, lit or dimmed. */
const SHARE = 0.3,
  LEADING = 1.6,
  PITCH = [0.9, 3];
/* ragged_columns: edges set by one layout agree within 1 px, inks within 3 px; 3 px apart they are seen. The left
 * edges of two stacked left-aligned lines nearly meet within three quarters of the larger size. */
const EDGE_SAME = 1,
  EDGE_SEEN = 3,
  NEAR_MISS = 0.75;
/* A mark leads or follows an item when it stands within 2.5 times the item's size of it, level with its ink, and is no
 * larger than 1.6 times the size. Like marks agree in kind and in size within 3 px. */
const MARK_REACH = 2.5,
  MARK_LEVEL = 0.45,
  MARK_SIZE = 1.6,
  LIKE_SIZE = 3;
/* A left-aligned block of two or three lines is centred on a mark within 6 px, the mark standing within twice the
 * block's size above or below it; its lines stand off the mark's axis by more than 4 px. */
const AXIS_CENTRED = 6,
  AXIS_REACH = 2,
  AXIS_OFF = 4,
  AXIS_LINES = 3;
/* crammed_lines: the lines of a block keep 7 px clear between their inks. */
const CRAMMED = 7;
/* off_card_centre: a card at least 60 by 30 px, no taller than three times its name's size, holds the name within 4 px
 * of its centre and middle. A mark no larger than 30% of the card that touches its border, such as a folded corner, is
 * part of the card. Containers stay narrower than the content band. */
const CARD = [60, 30],
  CARD_OFF = 4,
  CARD_LINES = 3,
  CARD_PART = 0.3,
  CONTAINER = [40, 24, 1700];
/* uneven_pitch: like marks at least 16 px on one centre line within 2 px, their pitch uneven by more than 6 px, under
 * names whose gaps agree within 4 px. A name stands under its mark within 60 px. */
const PITCH_MARK = 16,
  PITCH_LINE = 2,
  PITCH_UNEVEN = 6,
  GAPS_EVEN = 4,
  NAME_UNDER = 60;
/* touching_marks: a name keeps 3 px clear of any mark. */
const TOUCH = 3;

const round = (v) => Math.round(v * 10) / 10;
const spread = (values) => Math.max(...values) - Math.min(...values);
const overlap = (a, b) => Math.min(a.right, b.right) - Math.max(a.left, b.left);
const width = (v) => v.right - v.left;
const middle = (v) => (v.inkTop + v.inkBottom) / 2;
const centre = (v) => (v.left + v.right) / 2;
const sameSize = (a, b) => Math.abs(a.size - b.size) <= 0.6;
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
 * and its ink. The box rises 0.8 of the size above an alphabetic anchor, 0.52 above a middle one and none above a top
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
const like = (a, b) =>
  a.kind === b.kind &&
  Math.abs(a.width - b.width) <= LIKE_SIZE &&
  Math.abs(a.height - b.height) <= LIKE_SIZE;

/* Whether a box lies within a container: within its box, and for a ring within its outline. */
function holds(container, v) {
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
function insidePath(sub, [x, y]) {
  let inside = false;
  for (let i = 0, j = sub.length - 1; i < sub.length; j = i++) {
    const [xi, yi] = sub[i],
      [xj, yj] = sub[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}
/* A card's panel and its outline, or an outline lit over it, are one card. */
const twins = (a, b) => a.box.every((v, i) => Math.abs(v - b.box[i]) <= 1.5);

/* The distance from a segment to a box, 0 when it enters the box. */
function segmentToBox([ax, ay], [bx, by], box) {
  const [x0, y0, x1, y1] = box;
  if (enters([ax, ay], [bx, by], box)) return 0;
  const pointToBox = (x, y) => Math.hypot(Math.max(x0 - x, 0, x - x1), Math.max(y0 - y, 0, y - y1));
  const dx = bx - ax,
    dy = by - ay,
    length = dx * dx + dy * dy;
  const pointToSegment = (x, y) => {
    const q = length ? Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / length)) : 0;
    return Math.hypot(ax + q * dx - x, ay + q * dy - y);
  };
  return Math.min(
    pointToBox(ax, ay),
    pointToBox(bx, by),
    pointToSegment(x0, y0),
    pointToSegment(x1, y0),
    pointToSegment(x0, y1),
    pointToSegment(x1, y1),
  );
}
/* Liang-Barsky: does the segment enter the box? */
function enters([ax, ay], [bx, by], [x0, y0, x1, y1]) {
  let lo = 0,
    hi = 1;
  const dx = bx - ax,
    dy = by - ay;
  for (const [p, q] of [
    [-dx, ax - x0],
    [dx, x1 - ax],
    [-dy, ay - y0],
    [dy, y1 - ay],
  ]) {
    if (p === 0) {
      if (q < 0) return false;
      continue;
    }
    const r = q / p;
    if (p < 0) lo = Math.max(lo, r);
    else hi = Math.min(hi, r);
    if (lo > hi) return false;
  }
  return true;
}

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
function frameLayout(paints) {
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

/* ragged_rows: neighbouring names of one size whose baselines step by more than the reviewers see and less than a
 * second row would, in one container or close by in none. An item of a list keeps its list's rows: a name on a list's
 * pitch, and a name led by a marker beside one that is not. */
function raggedRows({ names, listed, lead }) {
  const found = [];
  const level = (a, b) => Math.abs(a.baseline - b.baseline) < Math.min(a.size, b.size) / 2;
  for (const a of names)
    for (const b of names) {
      if (a.scene !== b.scene || a.right >= b.left || !sameSize(a, b)) continue;
      const offset = Math.abs(a.baseline - b.baseline),
        gap = b.left - a.right;
      if (offset <= ROW_STEP || !level(a, b) || listed.has(a) || listed.has(b)) continue;
      if (Boolean(lead.get(a)) !== Boolean(lead.get(b))) continue;
      if (a.container !== b.container || (!a.container && gap > ROW_REACH)) continue;
      // Only neighbours: a name of the row standing between them is compared with each instead.
      const between = names.some(
        (c) =>
          c !== a &&
          c !== b &&
          c.scene === a.scene &&
          sameSize(c, a) &&
          c.left >= a.right - 1 &&
          c.right <= b.left + 1 &&
          level(c, a) &&
          level(c, b),
      );
      if (between) continue;
      found.push({
        kind: "ragged_rows",
        scene: a.scene,
        texts: [a.text, b.text],
        severity: offset,
        detail: { baselines: [round(a.baseline), round(b.baseline)], gap: round(gap) },
      });
    }
  return found;
}

/* The mark that leads a line, just before it and level with its ink, or the mark that follows it. */
function markBeside(line, marks, side) {
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

/* ragged_columns. The lines of a block share the edge that their alignment, set in one run each, declares; two stacked
 * left-aligned lines outside a block, a name over its note or two items of one column, share their left edge when it
 * nearly meets; the items after a column of marks share their left edge, like marks before a column of items share
 * one edge, and like marks after left-aligned items share theirs. Lines whose em boxes agree within 1 px on any edge,
 * or whose inks do within 3 px, are aligned, and so is a hanging heading flush with the ink of the marks that lead the
 * items under it. */
function raggedColumns(layout) {
  const { names, below, blocks, columns, lead } = layout,
    marks = [...layout.marks, ...layout.glyphs],
    found = [];
  const within = (group, edge, limit) => spread(group.map(edge)) <= limit;
  const aligned = (group) =>
    [(l) => l.left, (l) => l.right, centre].some((edge) => within(group, edge, EDGE_SAME)) ||
    [
      (l) => l.inkLeft,
      (l) => l.inkRight,
      (l) => (l.inkLeft + l.inkRight) / 2,
      (l) => (lead.get(l) ? lead.get(l).left - lead.get(l).half : l.left),
    ].some((edge) => within(group, edge, EDGE_SEEN));
  const note = (group, detail, severity) =>
    found.push({
      kind: "ragged_columns",
      scene: group[0].scene,
      texts: group.map((l) => l.text),
      severity,
      detail,
    });

  for (const block of blocks) {
    if (!block.every((l) => l.single && l.mode === block[0].mode) || aligned(block)) continue;
    const anchors = block.map((l) => l.anchor);
    if (spread(anchors) > EDGE_SEEN)
      note(block, { edge: block[0].mode, edges: anchors.map(round) }, spread(anchors));
  }
  // A name over its note, or the items of one column: two stacked left-aligned lines whose left edges nearly meet.
  for (const [l, b] of below) {
    if (sameSize(l, b) && b.baseline - l.baseline <= LEADING * l.size) continue;
    if (!l.single || !b.single || l.mode !== "left" || b.mode !== "left" || aligned([l, b]))
      continue;
    const offset = Math.abs(l.left - b.left);
    if (b.baseline - l.baseline > PITCH[1] * l.size || offset <= EDGE_SEEN) continue;
    if (offset <= NEAR_MISS * Math.max(l.size, b.size))
      note([l, b], { edge: "left", edges: [round(l.left), round(b.left)] }, offset);
  }
  for (const column of columns) {
    const leads = column.map((l) => lead.get(l));
    if (leads.every(Boolean)) {
      const marksAligned = [(m) => m.left, (m) => m.cx, (m) => m.right].some((edge) =>
        within(leads, edge, EDGE_SAME),
      );
      const lefts = column.map((l) => l.left);
      if (marksAligned) {
        if (
          !within(column, (l) => l.left, EDGE_SEEN) &&
          !within(column, (l) => l.inkLeft, EDGE_SEEN)
        )
          note(column, { edge: "after marks", edges: lefts.map(round) }, spread(lefts));
      } else if (
        leads.every((m) => like(m, leads[0])) &&
        [(l) => l.left, centre].some((edge) => within(column, edge, EDGE_SAME)) &&
        !within(leads, (m) => m.left, EDGE_SEEN)
      )
        note(
          column,
          { edge: "marks before", edges: leads.map((m) => round(m.left)) },
          spread(leads.map((m) => m.left)),
        );
    }
    const trailing = column
      .map((l) => [l, markBeside(l, marks, "trail")])
      .filter(([l, m]) => m && l.mode === "left");
    if (
      trailing.length >= 2 &&
      trailing.every(([, m]) => like(m, trailing[0][1])) &&
      within(trailing, ([l]) => l.left, EDGE_SAME) &&
      !within(trailing, ([, m]) => m.left, EDGE_SEEN)
    )
      note(
        trailing.map(([l]) => l),
        { edge: "marks after", edges: trailing.map(([, m]) => round(m.left)) },
        spread(trailing.map(([, m]) => m.left)),
      );
  }
  // A left-aligned block of two or three lines centred on a mark just above or below it.
  for (const first of names) {
    if (first.mode !== "left") continue;
    const previous = [...below].find(([, b]) => b === first)?.[0];
    if (previous && previous.mode === "left" && Math.abs(previous.left - first.left) <= EDGE_SAME)
      continue;
    const block = [first];
    for (let b = below.get(first); b && block.length < AXIS_LINES; b = below.get(b)) {
      const last = block.at(-1);
      if (b.mode !== "left" || Math.abs(b.left - first.left) > EDGE_SAME) break;
      if (b.baseline - last.baseline > LEADING * Math.max(b.size, last.size)) break;
      block.push(b);
    }
    if (block.length < 2) continue;
    const box = {
      left: first.left,
      right: Math.max(...block.map((l) => l.right)),
      top: first.inkTop,
      bottom: block.at(-1).inkBottom,
    };
    const reach = AXIS_REACH * first.size;
    const mark = layout.marks.find(
      (m) =>
        !m.card &&
        m.scene === first.scene &&
        Math.abs(m.cx - centre(box)) <= AXIS_CENTRED &&
        ((box.top - m.bottom >= -1 && box.top - m.bottom <= reach) ||
          (m.top - box.bottom >= -1 && m.top - box.bottom <= reach)),
    );
    if (!mark) continue;
    const offsets = block.map((l) => centre(l) - mark.cx),
      worst = Math.max(...offsets.map(Math.abs));
    if (worst > AXIS_OFF)
      note(block, { edge: "axis", axis: round(mark.cx), offsets: offsets.map(round) }, worst);
  }
  return found;
}

/* crammed_lines: a line under another of its block, the two inks less than 7 px apart. */
function crammedLines({ below }) {
  const found = [];
  for (const [a, b] of below) {
    if (b.baseline - a.baseline > 2 * Math.max(a.size, b.size)) continue;
    const clear = b.inkTop - a.inkBottom;
    if (clear >= 0 && clear < CRAMMED)
      found.push({
        kind: "crammed_lines",
        scene: a.scene,
        texts: [a.text, b.text],
        severity: CRAMMED - clear,
        detail: { clear: round(clear) },
      });
  }
  return found;
}

/* off_card_centre: a card holding one name and nothing else, no taller than three times the name's size, holds it on
 * its centre, as its anchor gives a centred name, and on its middle, as its ink gives it. */
function offCardCentre({ lines, marks, glyphs, containers }) {
  const found = [];
  for (const card of containers) {
    if (!card.card || card.width < CARD[0] || card.height < CARD[1]) continue;
    const held = lines.filter((l) => l.scene === card.scene && holds(card, l));
    if (held.length !== 1 || !LETTER.test(held[0].text)) continue;
    const [name] = held;
    if (card.height > CARD_LINES * name.size) continue;
    const part = (m) =>
      twins(m, card) ||
      (m.width <= CARD_PART * card.width &&
        m.height <= CARD_PART * card.height &&
        (m.left - card.left <= 1.5 ||
          card.right - m.right <= 1.5 ||
          m.top - card.top <= 1.5 ||
          card.bottom - m.bottom <= 1.5));
    if ([...marks, ...glyphs].some((m) => m.scene === card.scene && holds(card, m) && !part(m)))
      continue;
    const dx = name.mode === "centre" ? name.anchor - card.cx : 0,
      dy = middle(name) - card.cy;
    if (Math.abs(dx) > CARD_OFF || Math.abs(dy) > CARD_OFF)
      found.push({
        kind: "off_card_centre",
        scene: card.scene,
        texts: [name.text],
        severity: Math.max(Math.abs(dx), Math.abs(dy)),
        detail: { offset: [round(dx), round(dy)], card: card.box.map(round) },
      });
  }
  return found;
}

/* uneven_pitch: like marks on one centre line, each over a name, the names evenly gapped and the marks not. */
function unevenPitch({ names, marks }) {
  const found = [],
    groups = [];
  const candidates = marks
    .filter((m) => !m.card && m.width >= PITCH_MARK && m.height >= PITCH_MARK)
    .sort((a, b) => a.cy - b.cy || a.cx - b.cx);
  for (const m of candidates) {
    const group = groups.find(
      (g) =>
        g.scene === m.scene && like(g.marks[0], m) && Math.abs(g.marks[0].cy - m.cy) <= PITCH_LINE,
    );
    if (group) group.marks.push(m);
    else groups.push({ scene: m.scene, marks: [m] });
  }
  for (const group of groups) {
    const byX = [];
    for (const m of group.marks.sort((a, b) => a.cx - b.cx))
      if (!byX.length || m.cx - byX.at(-1).cx > 8) byX.push(m);
    if (byX.length < 3) continue;
    const pitch = byX.slice(1).map((m, i) => m.cx - byX[i].cx);
    if (spread(pitch) <= PITCH_UNEVEN) continue;
    const under = byX.map((m) =>
      names.find(
        (l) =>
          l.scene === m.scene &&
          Math.abs(centre(l) - m.cx) <= AXIS_CENTRED &&
          l.inkTop - m.bottom >= -1 &&
          l.inkTop - m.bottom <= NAME_UNDER,
      ),
    );
    if (under.some((l) => !l)) continue;
    const gaps = under.slice(1).map((l, i) => l.left - under[i].right);
    if (spread(gaps) <= GAPS_EVEN)
      found.push({
        kind: "uneven_pitch",
        scene: group.scene,
        texts: under.map((l) => l.text),
        severity: spread(pitch),
        detail: { pitch: pitch.map(round), gaps: gaps.map(round) },
      });
  }
  return found;
}

/* touching_marks: the nearest mark to a name's ink, measured on the mark's path, less half a stroke's width. A path
 * that enters the ink is a collision, which the label rules judge, and a name set on a panel is held by it. */
function touchingMarks({ names, marks }) {
  const found = [];
  for (const l of names) {
    const ink = [l.left, l.inkTop, l.right, l.inkBottom];
    let best = null;
    for (const m of marks) {
      const reach = m.half + TOUCH;
      if (
        m.scene !== l.scene ||
        m.left - reach > ink[2] ||
        m.right + reach < ink[0] ||
        m.top - reach > ink[3] ||
        m.bottom + reach < ink[1]
      )
        continue;
      if (m.kind === "fill" && m.shapes.some((s) => insidePath(s, [centre(l), middle(l)])))
        continue;
      let distance = Infinity;
      for (const sub of m.subs) {
        const path = m.kind === "fill" && sub.length > 2 ? [...sub, sub[0]] : sub;
        for (let k = 1; k < path.length && distance > 0; k++)
          distance = Math.min(distance, segmentToBox(path[k - 1], path[k], ink));
      }
      const clear = distance - m.half;
      if (distance > 0 && clear < TOUCH && (!best || clear < best.clear)) best = { clear, m };
    }
    if (best)
      found.push({
        kind: "touching_marks",
        scene: l.scene,
        texts: [l.text],
        severity: TOUCH - best.clear,
        detail: { clear: round(best.clear), mark: best.m.box.map(round) },
      });
  }
  return found;
}

/** The text-layout findings of one frame's paints, each with its measure, scene, texts, severity and offsets. */
export function frameFindings(paints) {
  const layout = frameLayout(paints);
  return [
    ...raggedRows(layout),
    ...raggedColumns(layout),
    ...crammedLines(layout),
    ...offCardCentre(layout),
    ...unevenPitch(layout),
    ...touchingMarks(layout),
  ];
}

/** The measures the frame audit reports, in its order. */
export const TEXT_LAYOUT = [
  "ragged_rows",
  "ragged_columns",
  "crammed_lines",
  "off_card_centre",
  "uneven_pitch",
  "touching_marks",
];

/** Joins each voiced frame's findings, sampled every `step` seconds, into runs. `frame(f)` reads the frame audit's
 * frame: its time, whether it is voiced and its paints; a frame without speech ends every run. `finish()` returns, for
 * each measure, its runs of 1 s or more, each with its scene, start, end, texts and the offsets of its worst frame. */
export function textLayout(step) {
  const open = new Map(),
    runs = Object.fromEntries(TEXT_LAYOUT.map((kind) => [kind, []]));
  const close = (id) => {
    const run = open.get(id);
    open.delete(id);
    // Within half a step: the gate's step, a thirtieth of a second to seven places, makes 30 frames 0.999999 s.
    if (run.end - run.start >= RUN_SECONDS - step / 2) runs[run.kind].push(run);
  };
  return {
    frame(f) {
      const seen = new Set();
      for (const v of f.speaking ? frameFindings(f.paints) : []) {
        const id = [v.kind, v.scene, v.detail.edge ?? "", ...v.texts].join("\u0000"),
          run = open.get(id);
        if (seen.has(id)) {
          if (v.severity > run.severity)
            Object.assign(run, { severity: v.severity, detail: v.detail });
          continue;
        }
        seen.add(id);
        if (run && Math.abs(run.end - f.t) < step / 2) {
          run.end = f.t + step;
          if (v.severity > run.severity)
            Object.assign(run, { severity: v.severity, detail: v.detail });
          continue;
        }
        if (run) close(id);
        open.set(id, { ...v, start: f.t, end: f.t + step });
      }
      for (const id of [...open.keys()]) if (!seen.has(id)) close(id);
    },
    finish() {
      for (const id of [...open.keys()]) close(id);
      for (const list of Object.values(runs))
        list.sort((a, b) => a.start - b.start || a.texts.join().localeCompare(b.texts.join()));
      return runs;
    },
  };
}
