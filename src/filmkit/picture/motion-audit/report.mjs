/* What the motion audit makes of the frames it tracked: each reported mark traced to the scene line that drew it, the
 * rests, stills, dips, hitches, camera moves and type sizes, and the report they form. */
export const round = (v, n = 2) => +v.toFixed(n);

export function motionReport({
  film,
  markOf,
  segments,
  dt,
  fps,
  from,
  to,
  SEEN,
  FAINT,
  faintRuns,
  pops,
  jumps,
  doubles,
  snaps,
  frames,
  typeSizes,
  cameras,
}) {
  /* Trace each reported mark to the scene line that drew it: re-render its frame and take the call stack of the first
   * mark that matches. */
  function traceAt(t, match) {
    let traced;
    film.render(t, (paint) => {
      const mark = traced === undefined && markOf(paint);
      if (mark && match(mark)) traced = film.origin();
    });
    return traced ?? null;
  }
  const near = (a, b) =>
    Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]) + Math.abs(a[2] - b[2]) + Math.abs(a[3] - b[3]) <
    8;
  for (const e of pops)
    e.origin = traceAt(
      e.way === "in" ? e.t : e.t - dt,
      (v) =>
        v.scene === e.scene &&
        v.kind === e.kind &&
        (v.text ?? undefined) === e.text &&
        near(v.screen, e.screen),
    );
  for (const e of jumps)
    e.origin = traceAt(
      e.t,
      (v) =>
        v.scene === e.scene &&
        v.kind === e.kind &&
        (v.text ?? undefined) === e.text &&
        near(v.screen, e.screen),
    );
  for (const e of snaps)
    e.origin = traceAt(e.t, (v) => v.scene === e.scene && v.kind === e.kind && v.color === e.to);
  /* Double exposure: group frames into episodes, keep the largest frame of each and trace its overlapping marks. */
  const episodes = [];
  for (const d of doubles) {
    const last = episodes.at(-1);
    if (last && d.t - last.end <= 0.35) {
      last.end = d.t;
      last.frames++;
      if (d.area > last.peak.area) last.peak = d;
    } else episodes.push({ start: d.t, end: d.t, frames: 1, peak: d });
  }
  const cutTimes = segments.map((v) => v.voice_start);
  for (const e of episodes) {
    const atCut = cutTimes.some((c) => Math.abs(c - e.peak.t) < 0.5);
    const origins = new Set();
    for (const b of e.peak.boxes) {
      const o = traceAt(
        e.peak.t,
        (v) =>
          v.scene === b.scene &&
          v.kind === b.kind &&
          (v.text ?? undefined) === b.text &&
          near(v.screen, b.screen),
      );
      if (o) origins.add(`${b.rising ? "+" : "-"}${o}`);
    }
    e.summary = {
      start: round(e.start),
      end: round(e.end),
      frames: e.frames,
      area: e.peak.area,
      at_cut: atCut,
      origins: [...origins].slice(0, 6),
    };
  }

  /* Rests in the faint band longer than 0.7 s, each in the colour it entered the band in: residue or ghosts (a slow
   * fade crossing the band is reported too). */
  const rests = faintRuns
    .map((v) => ({ ...v, seconds: round(v.end - v.start + dt) }))
    .filter((v) => v.seconds >= 0.7)
    .map((v) => {
      const [scene, kind, text] = v.key.split("|");
      return {
        scene,
        kind,
        text,
        color: v.color,
        start: round(v.start),
        seconds: v.seconds,
        low: Math.round(v.low),
        high: Math.round(v.high),
      };
    });
  for (const v of rests)
    v.origin = traceAt(
      v.start + v.seconds / 2,
      (m) =>
        m.scene === v.scene &&
        m.kind === v.kind &&
        (m.text ?? "") === v.text &&
        m.level >= SEEN &&
        m.level < FAINT,
    );
  const restsByScene = Object.groupBy(rests, (v) => v.scene);
  /* Still stretches during speech: no mark moves faster than 2 px/s and ink changes little, for at least 2.5 s. */
  const still = [];
  let run = null;
  const quietFade = 400;
  for (const f of frames) {
    const quiet = f.motion < 2 && f.fade < quietFade;
    if (quiet && f.speaking)
      run = run ? { ...run, end: f.t } : { start: f.t, end: f.t, scene: f.speaking };
    else {
      if (run && run.end - run.start >= 2.5)
        still.push({ ...run, seconds: round(run.end - run.start) });
      run = null;
    }
  }
  if (run && run.end - run.start >= 2.5)
    still.push({ ...run, seconds: round(run.end - run.start) });
  /* Emptying dips during speech: the picture's weight falls below 40% of its maximum over the previous 2 s and stays
   * there for at least 0.3 s (a stage clears before the next stands). */
  const dips = [];
  {
    let dip = null;
    frames.forEach((f, i) => {
      const past = frames.slice(Math.max(0, i - Math.round(2 / dt)), i).map((g) => g.weight);
      const peak = past.length ? Math.max(...past) : f.weight;
      const low = f.speaking && peak > 20 && f.weight < 0.4 * peak;
      if (low)
        dip = dip
          ? { ...dip, end: f.t, floor: Math.min(dip.floor, f.weight / peak) }
          : { start: f.t, end: f.t, scene: f.speaking, floor: f.weight / peak };
      else {
        if (dip && dip.end - dip.start >= 0.3)
          dips.push({ ...dip, seconds: round(dip.end - dip.start), floor: round(dip.floor) });
        dip = null;
      }
    });
    if (dip && dip.end - dip.start >= 0.3)
      dips.push({ ...dip, seconds: round(dip.end - dip.start), floor: round(dip.floor) });
  }
  /* Hitches: a change, a gap of 0.25-1.0 s where nothing changes, then another change, inside one voiced thought. */
  const hitches = [];
  {
    const active = frames.map((f) => f.motion >= 6 || f.fade >= 2500);
    let i = 0;
    while (i < frames.length) {
      if (!active[i]) {
        i++;
        continue;
      }
      let j = i;
      while (j < frames.length && active[j]) j++;
      let k = j;
      while (k < frames.length && !active[k]) k++;
      const gap = (k - j) * dt;
      if (
        k < frames.length &&
        gap >= 0.25 &&
        gap <= 1.0 &&
        frames[j].speaking &&
        frames[j].speaking === frames[k].speaking
      )
        hitches.push({ t: round(frames[j].t), gap: round(gap), scene: frames[j].speaking });
      i = j;
    }
  }
  /* Camera framing per scene: the scale range and every reframe of more than 3% or 30 px. */
  const camera = Object.fromEntries(
    [...cameras].map(([id, list]) => {
      const ks = list.map((v) => v[1]);
      const moves = [];
      let anchor = list[0];
      for (const v of list) {
        if (
          Math.abs(v[1] / anchor[1] - 1) > 0.03 ||
          Math.hypot(v[2] - anchor[2], v[3] - anchor[3]) > 30
        ) {
          moves.push([round(anchor[0], 1), round(v[0], 1), round(v[1] / anchor[1], 2)]);
          anchor = v;
        }
      }
      return [
        id,
        {
          k: [round(Math.min(...ks)), round(Math.max(...ks))],
          reframes: moves.length,
          moves: moves.slice(0, 8),
        },
      ];
    }),
  );
  const sizes = [...typeSizes.values()].flat().sort((a, b) => a - b);
  const median = (v) => (v.length ? v[Math.floor(v.length / 2)] : null);
  const filmMedian = median(sizes);
  const type = Object.fromEntries(
    [...typeSizes].map(([id, list]) => {
      list.sort((a, b) => a - b);
      const q = (p) => list[Math.min(list.length - 1, Math.floor(p * list.length))];
      return [
        id,
        {
          p05: round(q(0.05), 1),
          median: round(median(list), 1),
          p95: round(q(0.95), 1),
          vs_film: round(median(list) / filmMedian, 2),
        },
      ];
    }),
  );
  const summary = {
    range: [from, to],
    fps,
    frames: frames.length,
    label_size_film_median: round(filmMedian ?? 0, 1),
    faint_rests: {
      count: rests.length,
      seconds: round(
        rests.reduce((n, v) => n + v.seconds, 0),
        1,
      ),
      by_scene: Object.fromEntries(
        Object.entries(restsByScene).map(([id, list]) => [
          id,
          {
            count: list.length,
            seconds: round(
              list.reduce((n, v) => n + v.seconds, 0),
              1,
            ),
          },
        ]),
      ),
    },
    pops: {
      in: pops.filter((v) => v.way === "in").length,
      out: pops.filter((v) => v.way === "out").length,
    },
    jumps: jumps.length,
    colour_snaps: snaps.length,
    double_exposure_frames: doubles.length,
    still_runs: still.length,
    dips: dips.length,
    hitches: hitches.length,
  };
  const report = {
    summary,
    faint_rests: rests.sort((a, b) => b.seconds - a.seconds),
    pops,
    jumps,
    colour_snaps: snaps,
    double_exposure: episodes.map((e) => e.summary),
    still,
    dips,
    hitches,
    camera,
    type,
  };
  return { report, summary };
}
