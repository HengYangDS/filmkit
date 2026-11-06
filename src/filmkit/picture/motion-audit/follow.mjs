/* Follow every mark of a scene across frames as a viewer sees it move, and find the motion a viewer sees as not smooth:
 * a mark that halts at speed or sets off at speed within one frame, a mark that races, and a mark that pops in or out
 * outside a stage cut. Speeds are in 1080p pixels per second, so a result does not depend on the frame rate.
 *
 * A mark is a paint of a scene at ink level VISIBLE or more: its scene, kind, words, line width, ink level and screen
 * box. A mark whose box and line width stand unchanged continues the mark that stood there. The other marks of each
 * group of like marks (scene, kind and words) continue the previous frame's by the assignment of least total miss, a
 * mark's miss being how far its four edges stand from where the previous mark's own edge velocities put them, and
 * leaving a mark unfollowed costing four times the turn. A pair is one mark when it moved whole, at the same line width
 * and nearly the same size with each axis's two edges shifting together, or when it grew, shrank or was redrawn, in
 * place or while it moved: once the shift both edges of each axis share is taken out the boxes overlap by half the
 * smaller box. Its motion is the centre's shift, or that shared shift, which moves within reach; a stroke drawn on may
 * grow at any pace, and a pair that holds one end of one of its drawn pieces exactly where it stood grows or turns from
 * that end and does not travel, however its box changes. A followed mark changes its velocity within one frame by no
 * more than the turn or its own speed, a mark too small to be seen grows into or shrinks from only a mark small across,
 * and a text whose words change continues a text that moved whole.
 *
 * A frame is a stage cut for a scene when a CUT share of the scene's firm marks, counted or weighed by their ink, vanish
 * or appear in it, or when the composition declares a cut of the scene in it; no mark is followed across a cut, and a
 * scene's first and last frames are cuts. A mark that appears or vanishes pops only by the pieces it brings or takes:
 * those that no like mark of the other frame holds in place, together at least POP across. */
import { leastCostAssignment } from "./assignment.mjs";

/** The viewer's thresholds: ink levels, pixels per second at 1080p, shares and pixels across. */
export const VIEWER = Object.freeze({
  // A mark is followed from this ink level, and a pop is a mark at FIRM or more.
  VISIBLE: 25,
  FIRM: 60,
  // A stage cut changes this share of a scene's firm marks.
  CUT: 0.35,
  // A mark at MOVING or more is moving, one under REST at rest, and one at RACE or more is faster than a viewer follows.
  MOVING: 60,
  REST: 1.5,
  RACE: 900,
  // No edge of a followed mark moves faster than REACH, and its velocity changes within one frame by at most TURN or
  // its own speed.
  REACH: 4500,
  TURN: 1200,
  // A halt after a step, or a start before one, under this share of its neighbour eases out or in.
  EASED: 0.5,
  // A move is judged on marks at least SEEN across, a pop is at least POP across, and a flow's mark at most DOT.
  SEEN: 6,
  POP: 12,
  DOT: 16,
});

const dims = (b) => [b[2] - b[0], b[3] - b[1]];
const across = (b) => Math.hypot(...dims(b));
const area = (b) => Math.max(1, b[2] - b[0]) * Math.max(1, b[3] - b[1]);
const centre = (b) => [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2];
const overlap = (a, b) =>
  Math.max(1, Math.min(a[2], b[2]) - Math.max(a[0], b[0])) *
  Math.max(1, Math.min(a[3], b[3]) - Math.max(a[1], b[1]));
const meets = (a, b) =>
  Math.min(a[2], b[2]) - Math.max(a[0], b[0]) >= -1 &&
  Math.min(a[3], b[3]) - Math.max(a[1], b[1]) >= -1;
const likeOf = (m) => `${m.scene}|${m.kind}|${m.text}`;
const groupBy = (list, key) => {
  const groups = new Map();
  for (const m of list) {
    const k = key(m);
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(m);
  }
  return groups;
};

/* A whole move: nearly the same size (2 px or 5%), each axis's two edges shifting together within 2 px or a fifth of
 * the axis's shift. Its motion is the centre's shift. */
function wholeMove(p, c) {
  const [pw, ph] = dims(p.screen),
    [cw, ch] = dims(c.screen);
  if (Math.abs(cw - pw) > Math.max(2, 0.05 * pw) || Math.abs(ch - ph) > Math.max(2, 0.05 * ph))
    return null;
  const [cx, cy] = centre(c.screen),
    [px, py] = centre(p.screen),
    d = [cx - px, cy - py];
  const together = (k) =>
    Math.abs(c.screen[k] - p.screen[k] - (c.screen[k + 2] - p.screen[k + 2])) <=
    Math.max(2, 0.2 * Math.abs(d[k]));
  return together(0) && together(1) ? d : null;
}

/* Whether two marks hold one end of one of their drawn pieces exactly where it stood: a mark drawn on, or turned, from
 * that end. Pieces are compared in their order, as a composition draws them. */
const anchored = (p, c) =>
  p.ends.some((ends, i) =>
    ends.some((a, k) => {
      const b = c.ends[i]?.[k];
      return b !== undefined && Math.abs(a[0] - b[0]) <= 0.01 && Math.abs(a[1] - b[1]) <= 0.01;
    }),
  );

/* A growth: a mark that grows, shrinks or is redrawn, in place or while it moves. Once the shift both edges of each axis
 * share is taken out the boxes overlap by half the smaller box. Its motion is that shared shift. */
function growth(p, c) {
  const d = [0, 1, 2, 3].map((k) => c.screen[k] - p.screen[k]);
  const shared = (a, b) =>
    Math.sign(a) === Math.sign(b) ? Math.sign(a) * Math.min(Math.abs(a), Math.abs(b)) : 0;
  const s = [shared(d[0], d[2]), shared(d[1], d[3])];
  const moved = [p.screen[0] + s[0], p.screen[1] + s[1], p.screen[2] + s[0], p.screen[3] + s[1]];
  if (!meets(moved, c.screen)) return null;
  return overlap(moved, c.screen) >= 0.5 * Math.min(area(moved), area(c.screen)) - 4 ? s : null;
}

/** A follower of the marks of successive frames, dt seconds apart. `frame(t, marks, declared)` takes each frame's
 * marks, each {scene, kind, text, width, level, screen, pieces}, in order, `pieces` the boxes and `ends` the first and
 * last points of the drawn subpaths of a stroke or fill, and the scenes whose stage cut the composition declares in
 * that frame; `finish()` returns what it found: the halts, starts, races and pops, each with its time, mark and speeds,
 * and for each scene the fastest glide (a text, or a mark more than DOT across) and flow (a smaller mark) with their
 * times. */
export function follower(dt, v = VIEWER) {
  const reach = v.REACH * dt,
    unfollowed = 4 * v.TURN * dt;
  const found = { halts: [], starts: [], races: [], pops: [] },
    speeds = {};
  // Each start waits, by its track, for the step after it, which tells a start at speed from an eased one.
  let waiting = new Map(),
    previous = null,
    tracks = 0;
  const begin = (c) =>
    Object.assign(c, { track: ++tracks, age: 0, d: null, edges: null, speed: null, prior: null });
  const row = (t, m, extra) => ({
    t,
    scene: m.scene,
    kind: m.kind,
    text: m.text,
    box: m.screen,
    ...extra,
  });

  /* The motion of a pair of marks and its miss, or null where they cannot be one mark. */
  function candidate(p, c, motion) {
    const [small, large] = across(p.screen) < across(c.screen) ? [p, c] : [c, p];
    if (across(small.screen) < v.SEEN && Math.min(...dims(large.screen)) > 2 * v.SEEN) return null;
    const shift = motion(p, c);
    if (!shift || Math.hypot(...shift) > reach) return null;
    // A pair that holds one end of a drawn piece where it stood turns or grows from it: its box may flip as a piece
    // turns through that end, which is no motion of the mark.
    const d = anchored(p, c) ? [0, 0] : shift;
    if (p.d && Math.hypot(d[0] - p.d[0], d[1] - p.d[1]) > Math.max(v.TURN * dt, Math.hypot(...p.d)))
      return null;
    const edges = p.edges ?? [0, 0, 0, 0];
    const miss = [0, 1, 2, 3].reduce(
      (n, k) => n + Math.abs(c.screen[k] - p.screen[k] - edges[k]),
      0,
    );
    return { d, miss: miss + (p.width2 === c.width2 ? 0 : 0.5) };
  }

  /* Pair the marks of one group by the assignment of least total miss; a crowd too large to assign is paired greedily. */
  function pairUp(cur, old, motion, pairs, matched, used) {
    const rows = old.filter((p) => !used.has(p)),
      cols = cur.filter((c) => !matched.has(c));
    if (!rows.length || !cols.length) return;
    const options = rows.map((p) => cols.map((c) => candidate(p, c, motion)));
    const take = (i, j) => {
      used.add(rows[i]);
      matched.add(cols[j]);
      pairs.push([cols[j], rows[i], options[i][j].d]);
    };
    const r = rows.length,
      k = cols.length;
    if (r + k > 240) {
      const list = [];
      options.forEach((line, i) => line.forEach((o, j) => o && list.push([o.miss, i, j])));
      list.sort((a, b) => a[0] - b[0]);
      for (const [, i, j] of list) if (!used.has(rows[i]) && !matched.has(cols[j])) take(i, j);
      return;
    }
    // Rows are the previous marks, then one stand-in for each current mark; columns the current marks, then one
    // stand-in for each previous mark. A mark assigned a stand-in is left unfollowed.
    const cost = Array.from({ length: r + k }, (_, i) =>
      Array.from({ length: r + k }, (_, j) => {
        if (i < r && j < k) return options[i][j]?.miss ?? Infinity;
        if (i < r) return j - k === i ? unfollowed : Infinity;
        if (j < k) return i - r === j ? unfollowed : Infinity;
        return 0;
      }),
    );
    leastCostAssignment(cost).forEach((j, i) => {
      if (i < r && j < k && options[i][j]) take(i, j);
    });
  }

  function match(marks) {
    const pairs = [],
      matched = new Set(),
      used = new Set();
    const before = groupBy(previous, likeOf),
      now = groupBy(marks, likeOf);
    for (const [key, cur] of now) {
      const old = before.get(key) ?? [];
      for (const c of cur) {
        const p = old.find(
          (q) =>
            !used.has(q) &&
            q.width2 === c.width2 &&
            q.screen.every((x, k) => Math.abs(x - c.screen[k]) < 0.01),
        );
        if (!p) continue;
        used.add(p);
        matched.add(c);
        pairs.push([c, p, [0, 0]]);
      }
    }
    const motion = (p, c) => (p.width2 === c.width2 ? wholeMove(p, c) : null) ?? growth(p, c);
    for (const [key, cur] of now) pairUp(cur, before.get(key) ?? [], motion, pairs, matched, used);
    // A text whose words change continues a text of its scene that moved whole, as a counter does.
    const texts = (list, set) =>
      groupBy(
        list.filter((m) => m.kind === "text" && !set.has(m)),
        (m) => m.scene,
      );
    const oldTexts = texts(previous, used);
    for (const [scene, cur] of texts(marks, matched))
      pairUp(cur, oldTexts.get(scene) ?? [], wholeMove, pairs, matched, used);
    return { pairs, matched, used };
  }

  /* The scenes a frame cuts: those where a CUT share of the firm marks, counted or by ink, vanished or appeared. */
  function cuts(marks, matched, used) {
    const share = new Map();
    const add = (list, kept, side) => {
      for (const m of list) {
        if (m.level < v.FIRM) continue;
        const s = share.get(m.scene) ?? [
          [0, 0, 0, 0],
          [0, 0, 0, 0],
        ];
        const w = area(m.screen) * m.level;
        s[side][0] += 1;
        s[side][1] += w;
        if (!kept.has(m)) {
          s[side][2] += 1;
          s[side][3] += w;
        }
        share.set(m.scene, s);
      }
    };
    add(previous, used, 0);
    add(marks, matched, 1);
    return new Set(
      [...share]
        .filter(([, sides]) =>
          sides.some(([n, w, gone, ink]) => n && (gone / n >= v.CUT || ink / w >= v.CUT)),
        )
        .map(([scene]) => scene),
    );
  }

  function record(scene, t, speed, m) {
    const kind = m.kind !== "text" && Math.max(...dims(m.screen)) <= v.DOT ? "flow" : "glide";
    const best = (speeds[scene] ??= {})[kind];
    if (!best || speed > best.speed) speeds[scene][kind] = { speed, t };
  }

  function judge(t, c, p, d, next) {
    const speed = Math.hypot(...d) / dt;
    Object.assign(c, {
      track: p.track,
      age: p.age + 1,
      d,
      edges: [0, 1, 2, 3].map((k) => c.screen[k] - p.screen[k]),
      speed,
      prior: p.speed,
    });
    const start = waiting.get(p.track);
    if (start) {
      waiting.delete(p.track);
      if (speed * v.EASED <= start.to) found.starts.push(start);
    }
    if (across(c.screen) < v.SEEN || across(p.screen) < v.SEEN) return;
    const easedOut = p.prior !== null && p.speed < v.EASED * p.prior;
    if (p.speed !== null && p.speed >= v.MOVING && speed < v.REST && !easedOut)
      found.halts.push(row(t, c, { from: p.speed }));
    if (p.speed !== null && p.speed < v.REST && speed >= v.MOVING)
      next.set(c.track, row(t, c, { to: speed }));
    if (speed >= v.RACE) found.races.push(row(t, c, { speed }));
    if (speed >= v.REST) record(c.scene, t, speed, c);
  }

  function frame(t, raw, declared = []) {
    const marks = raw.map((m) => ({
      ...m,
      text: m.text ?? "",
      width2: Math.round((m.width ?? 0) * 2),
      pieces: m.pieces ?? [m.screen],
      ends: m.ends ?? [],
    }));
    if (previous === null) {
      marks.forEach(begin);
      previous = marks;
      return;
    }
    const { pairs, matched, used } = match(marks);
    const cut = cuts(marks, matched, used),
      next = new Map();
    for (const scene of declared) cut.add(scene);
    for (const [c, p, d] of pairs)
      if (cut.has(c.scene)) begin(c);
      else judge(t, c, p, d, next);
    // A start whose mark is not followed on, past a cut or out of the picture, stands as it was found.
    found.starts.push(...waiting.values());
    waiting = next;
    const before = new Set(previous.map((p) => p.scene)),
      after = new Set(marks.map((c) => c.scene));
    // The pieces of a mark that no like mark of the other frame holds in place, to 2 px: what it brings or takes.
    const near = (a, b) => a.every((x, k) => Math.abs(x - b[k]) <= 2);
    const brought = (m, others) => {
      const like = likeOf(m),
        standing = others.filter((o) => likeOf(o) === like && o.width2 === m.width2);
      return m.pieces.filter((a) => !standing.some((o) => o.pieces.some((b) => near(a, b))));
    };
    const pops = (list, kept, way, present, others) => {
      for (const m of list) {
        if (kept.has(m) || m.level < v.FIRM) continue;
        if (cut.has(m.scene) || !present.has(m.scene)) continue;
        if (brought(m, others).reduce((n, b) => n + across(b), 0) < v.POP) continue;
        found.pops.push(row(t, m, { way, level: m.level }));
      }
    };
    pops(marks, matched, "in", before, previous);
    pops(previous, used, "out", after, marks);
    for (const c of marks) if (!matched.has(c)) begin(c);
    previous = marks;
  }

  function finish() {
    found.starts.push(...waiting.values());
    waiting = new Map();
    for (const list of Object.values(found)) list.sort((a, b) => a.t - b.t);
    return { ...found, speeds };
  }
  return { frame, finish };
}
