/* What the follower found (follow.mjs), as the motion report lists it: each frame's halts, starts, races, pops, jumps
 * and dash snaps, and each stretch over the pace line by its fastest mark (pace.mjs), traced to the composition line
 * that drew their marks, a jump by its heaviest mark; the findings they form, one for each run of frames of one kind,
 * scene and line, and one for each pace stretch; and each scene's fastest glide and flow. */
import { round } from "./report.mjs";

const KINDS = {
  halts: "halt",
  starts: "start",
  races: "race",
  pops: "pop",
  jumps: "jump",
  dash_snaps: "dash",
  paces: "pace",
};
/* What a finding of each kind measures over its events: a pop its way and highest ink, and whether a declared cut that
 * keeps its stage brought it; a jump its longest shift and the marks it moved; a dash snap the gap shares it stepped
 * from and to; a pace stretch its fastest mark's speed, when it was fastest (`at`) and whether it glides or flows, with
 * the stretch's own start, end and frames and the most marks it held over the line at once; any other its highest
 * speed. */
const MEASURES = {
  pop: (events) => ({
    way: events[0].way,
    level: Math.max(...events.map((e) => e.level)),
    ...(events.some((e) => e.declared_cut) ? { declared_cut: true } : {}),
  }),
  jump: (events) => {
    const { shift, distance, marks } = events.reduce((a, e) => (e.distance > a.distance ? e : a));
    return { shift, distance, marks };
  },
  dash: (events) => ({ gaps: [events[0].gaps[0], events.at(-1).gaps[1]] }),
  pace: (events) => {
    const peak = events.reduce((a, e) => (e.speed > a.speed ? e : a));
    return {
      start: round(Math.min(...events.map((e) => e.start)), 3),
      end: round(Math.max(...events.map((e) => e.end)), 3),
      at: peak.t,
      speed: peak.speed,
      move: peak.move,
      marks: Math.max(...events.map((e) => e.marks)),
      frames: events.reduce((n, e) => n + e.frames, 0),
    };
  },
};
const speedOf = (events) => ({ speed: Math.max(...events.map((e) => e.from ?? e.to ?? e.speed)) });

/* Trace each event to the line that drew its mark: render its frame again and take the origin of the paint of its
 * scene, kind and words whose box stands nearest the event's, edge by edge, so a mark is told from another of its kind
 * around the same centre. A pop-out's mark stands in the frame before it. */
function traceAll(film, markOf, dt, found) {
  const frames = new Map();
  for (const [list, kind] of Object.entries(KINDS))
    for (const e of found[list]) {
      const t = kind === "pop" && e.way === "out" ? e.t - dt : e.t,
        key = t.toFixed(6);
      if (!frames.has(key)) frames.set(key, { t, events: [] });
      frames.get(key).events.push(e);
    }
  for (const { t, events } of frames.values()) {
    const best = events.map(() => Infinity);
    film.render(t, (paint) => {
      const mark = markOf(paint);
      if (!mark?.scene) return;
      let traced;
      events.forEach((e, i) => {
        if (e.scene !== mark.scene || e.kind !== mark.kind || e.text !== (mark.text ?? "")) return;
        const distance = mark.screen.reduce((n, v, k) => n + Math.abs(v - e.box[k]), 0);
        if (distance >= best[i]) return;
        best[i] = distance;
        traced ??= film.origin();
        e.origin = traced;
        e.module = film.module(traced);
      });
    });
  }
}

/* The findings of one list: its events of one scene and line, and for a pop one way, in runs of consecutive frames. */
function findingsOf(list, kind, dt) {
  const runs = new Map(),
    findings = [];
  for (const e of list) {
    const key = [e.scene, e.origin, e.way].join("|"),
      run = runs.get(key);
    if (run && e.t - run.end <= 1.5 * dt) {
      run.end = e.t;
      run.events.push(e);
    } else {
      const next = {
        kind,
        scene: e.scene,
        origin: e.origin,
        module: e.module,
        start: e.t,
        end: e.t,
        events: [e],
      };
      runs.set(key, next);
      findings.push(next);
    }
  }
  return findings.map(({ events, ...finding }) => ({
    ...finding,
    frames: new Set(events.map((e) => e.t)).size,
    ...(MEASURES[kind] ?? speedOf)(events),
    paints: [...new Set(events.flatMap((e) => e.paints ?? [e.kind]))],
    texts: [...new Set(events.flatMap((e) => e.texts ?? [e.text]).filter(Boolean))],
  }));
}

/** The motion report's `followed` section and its summary counts, from what the follower found. */
export function followedReport({ film, markOf, dt, found }) {
  traceAll(film, markOf, dt, found);
  const rows = (list) =>
    list.map(({ box, ...e }) => ({
      ...e,
      t: round(e.t, 3),
      origin: e.origin ?? null,
      module: e.module ?? null,
      box: box.map((v) => round(v, 1)),
      ...Object.fromEntries(
        ["from", "to", "speed", "level"].filter((k) => k in e).map((k) => [k, Math.round(e[k])]),
      ),
    }));
  const followed = Object.fromEntries(Object.keys(KINDS).map((list) => [list, rows(found[list])]));
  followed.findings = Object.entries(KINDS)
    .flatMap(([list, kind]) => findingsOf(followed[list], kind, dt))
    .sort((a, b) => a.start - b.start || a.scene.localeCompare(b.scene));
  followed.speeds = Object.fromEntries(
    Object.entries(found.speeds).map(([scene, kinds]) => [
      scene,
      Object.fromEntries(
        Object.entries(kinds).map(([kind, { speed, t }]) => [
          kind,
          { speed: Math.round(speed), t: round(t, 3) },
        ]),
      ),
    ]),
  );
  const summary = Object.fromEntries(
    Object.keys(KINDS).map((list) => [list, followed[list].length]),
  );
  return { followed, summary };
}
