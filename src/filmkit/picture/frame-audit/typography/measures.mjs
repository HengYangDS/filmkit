/* The frame audit's text-layout measures, each over one frame's layout (layout.mjs):
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
 *   touching_marks   a name whose ink comes within 3 px of a mark, measured on the mark's path. */
import {
  centre,
  holds,
  insidePath,
  LEADING,
  LETTER,
  like,
  markBeside,
  middle,
  PITCH,
  round,
  sameSize,
  spread,
  twins,
} from "./layout.mjs";

/* ragged_rows: the reviewers see baselines 4 px apart in a row; past half the size, two names stand on two rows. */
const ROW_STEP = 3.5,
  ROW_REACH = 300;
/* ragged_columns: edges set by one layout agree within 1 px, inks within 3 px; 3 px apart they are seen. The left
 * edges of two stacked left-aligned lines nearly meet within three quarters of the larger size. */
const EDGE_SAME = 1,
  EDGE_SEEN = 3,
  NEAR_MISS = 0.75;
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
 * part of the card. */
const CARD = [60, 30],
  CARD_OFF = 4,
  CARD_LINES = 3,
  CARD_PART = 0.3;
/* uneven_pitch: like marks at least 16 px on one centre line within 2 px, their pitch uneven by more than 6 px, under
 * names whose gaps agree within 4 px. A name stands under its mark within 60 px. */
const PITCH_MARK = 16,
  PITCH_LINE = 2,
  PITCH_UNEVEN = 6,
  GAPS_EVEN = 4,
  NAME_UNDER = 60;
/* touching_marks: a name keeps 3 px clear of any mark. */
const TOUCH = 3;

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

/* ragged_rows: neighbouring names of one size whose baselines step by more than the reviewers see and less than a
 * second row would, in one container or close by in none. An item of a list keeps its list's rows: a name on a list's
 * pitch, and a name led by a marker beside one that is not. */
export function raggedRows({ names, listed, lead }) {
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

/* ragged_columns. The lines of a block share the edge that their alignment, set in one run each, declares; two stacked
 * left-aligned lines outside a block, a name over its note or two items of one column, share their left edge when it
 * nearly meets; the items after a column of marks share their left edge, like marks before a column of items share
 * one edge, and like marks after left-aligned items share theirs. Lines whose em boxes agree within 1 px on any edge,
 * or whose inks do within 3 px, are aligned, and so is a hanging heading flush with the ink of the marks that lead the
 * items under it. */
export function raggedColumns(layout) {
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
export function crammedLines({ below }) {
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
export function offCardCentre({ lines, marks, glyphs, containers }) {
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
export function unevenPitch({ names, marks }) {
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
export function touchingMarks({ names, marks }) {
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
