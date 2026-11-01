/* The frame audit's measures of what a frame's picture shows: the seats and containers of its firm marks, its balance
 * and cover at the reviewers' instants, the runs of speech over too little of it, and the extent each scene paints. */
import { BALANCE_BAND, bandCover, pictureOffset } from "../rules/balance.mjs";
import { fillShare, litLevel, strokeShare } from "../rules/ink.mjs";
import { containerFill, FRAME, seatMarks } from "../seat-marks.mjs";
import { emptyBox, growBox, HEAD, inHead, pointsOf, spanOf, VISIBLE } from "./marks.mjs";

/* The content band between the head band (top 10%) and the caption band (bottom 12%). */
const BAND = [108, 950];

export function compositionMeasures({ film, step, thoughts }) {
  const isLit = litLevel(film.palette);
  const marks = [],
    extents = {},
    drawn = {};
  /* The firm graphics of the content band, each with its box, its kind and, for a stroke, its segments, as the seat
   * check and the container check read them (src/filmkit/picture/seat-marks.mjs). */
  function bandShapes(f) {
    const shapes = [];
    const closed = (sub) =>
      sub.length > 2 && Math.hypot(sub[0][0] - sub.at(-1)[0], sub[0][1] - sub.at(-1)[1]) <= 2;
    // A frame is a filled panel or a closed outline at least FRAME in size.
    const large = (pts) => {
      const [x0, y0, x1, y1] = spanOf(pts);
      return x1 - x0 >= FRAME[0] && y1 - y0 >= FRAME[1];
    };
    for (const g of f.sceneGraphics) {
      if (g.alpha <= 0.35) continue;
      const pts = pointsOf(g);
      if (!pts.length) continue;
      const box = spanOf(pts);
      if (box[3] < BAND[0] || box[1] > BAND[1]) continue;
      const segs =
        g.kind === "fill" ? null : g.subs.flatMap((sub) => sub.slice(1).map((q, k) => [sub[k], q]));
      const frame =
        g.kind === "fill" ? large(pts) : g.subs.some((sub) => closed(sub) && large(sub));
      const kind = g.kind === "fill" ? "fill" : g.subs.some(closed) ? "closed" : "open";
      shapes.push({ box, segs, kind, frame });
    }
    return shapes;
  }
  const writtenOf = (f) => f.layout.texts.filter((v) => v.scene && v.alpha > 0.35);
  /* MARKS: the seat check's marks of each voiced frame, with whether a legible name stands at each. */
  function seats(f) {
    if (!f.speaking) return;
    for (const row of seatMarks(bandShapes(f), writtenOf(f), f.legible))
      marks.push(
        `${f.t.toFixed(3)}\t${f.speaking.id}\t${row.box.map(Math.round).join("\t")}\t${row.named ? 1 : 0}`,
      );
  }
  /* Containers: a group's frame or bracket whose contents fill less than half of it while it stands through more than a
   * second of speech fills in like a form; a container grows with its members instead. Runs are kept per container, by its kind
   * and its box to 4 px, and end when it leaves, fills or the speech pauses. */
  const UNDERFILLED = 0.5,
    FORM_SECONDS = 1;
  /* A container that holds a group: any bracket, or a frame of at least 60,000 px², about 300 by 200; smaller frames are
   * cards and icons whose glyph need not fill them. */
  const GROUP_AREA = 60000;
  const holdsGroup = (row) =>
    row.kind === "bracket" || (row.box[2] - row.box[0]) * (row.box[3] - row.box[1]) >= GROUP_AREA;
  const containerRuns = new Map(),
    underfilled = [];
  function closeContainer(key) {
    const run = containerRuns.get(key);
    containerRuns.delete(key);
    if (run && run.frames * step > FORM_SECONDS) underfilled.push(run);
  }
  function containers(f) {
    const seen = new Set();
    if (f.speaking)
      for (const row of containerFill(bandShapes(f), writtenOf(f), f.legible)) {
        const box = row.box.map((v) => Math.round(v / 4) * 4),
          key = `${row.kind}:${box}`;
        if (row.fill >= UNDERFILLED || !holdsGroup(row) || seen.has(key)) continue;
        seen.add(key);
        const run = containerRuns.get(key) ?? {
          scene: f.speaking.id,
          kind: row.kind,
          box,
          start: f.t,
          frames: 0,
          least: 1,
        };
        run.frames++;
        run.end = f.t + step;
        run.least = Math.min(run.least, row.fill);
        containerRuns.set(key, run);
      }
    for (const key of [...containerRuns.keys()]) if (!seen.has(key)) closeContainer(key);
  }
  /* Every lit point of the frame, as the reviewers' gray frame shows it: lit strokes and fills at their worst share of a
   * cell, and lit text, whose glyph strokes cover about half of a cell. */
  const TEXT_SHARE = 0.5;
  const litPoints = (f) => [
    ...f.graphics
      .filter((g) =>
        isLit(g.color, g.alpha, g.kind === "fill" ? fillShare(g.box) : strokeShare(g.width)),
      )
      .flatMap(pointsOf),
    ...f.layout.texts
      .filter((v) => isLit(v.color, v.alpha, TEXT_SHARE))
      .flatMap((v) => [
        [v.bounds[0], v.bounds[1]],
        [v.bounds[2], v.bounds[3]],
      ]),
  ];
  /* Composition: the extent of the scene's firm marks and legible names stays balanced on the content centre, and at
   * the reviewers' instants, two seconds into each thought and 70% through it, the box around the firm marks and legible
   * names of the content band (the head band and the caption band excluded) covers a share of the frame, and the box
   * around every lit mark and legible name of the reviewers' band stands within their limits of its centre. */
  function pictureBalance(f) {
    if (!f.speaking) return;
    // The head band's marks (the running head and the Illustrative chip) frame the picture rather than show it.
    const firm = f.sceneGraphics
        .filter((g) => g.alpha > 0.35 && !inHead(pointsOf(g)))
        .flatMap(pointsOf),
      named = f.legible
        .filter((v) => v.bounds[3] >= HEAD)
        .flatMap((v) => [
          [v.bounds[0], v.bounds[1]],
          [v.bounds[2], v.bounds[3]],
        ]);
    const picture = emptyBox();
    for (const point of [...firm, ...named]) growBox(picture, point);
    const thought = thoughts.find((v) => v.start <= f.t && f.t <= v.end);
    if (thought)
      for (const [name, at] of [
        ["two", thought.start + 2],
        ["late", thought.start + 0.7 * (thought.end - thought.start)],
      ]) {
        if (!(f.t <= at && at < f.t + step) || at > thought.end) continue;
        const band = emptyBox();
        for (const point of [...firm, ...named])
          if (!(point[1] < BAND[0] || point[1] > BAND[1])) growBox(band, point);
        (thought.areas ??= {})[name] =
          band[2] > band[0] ? ((band[2] - band[0]) * (band[3] - band[1])) / (1920 * 1080) : 0;
        const lit = emptyBox();
        for (const point of litPoints(f))
          if (point[1] >= BALANCE_BAND[0] && point[1] <= BALANCE_BAND[1]) growBox(lit, point);
        (thought.covers ??= {})[name] = lit[2] > lit[0] ? bandCover(lit) : 0;
        if (lit[2] > lit[0]) (thought.offsets ??= {})[name] = pictureOffset(lit);
      }
    if (thought && picture[2] > picture[0]) {
      thought.box ??= emptyBox();
      growBox(thought.box, [picture[0], picture[1]]);
      growBox(thought.box, [picture[2], picture[3]]);
    }
  }
  /* Sparse runs, as the Chinese review measured them: the box around every mark of visible ink in the content band,
   * through each voiced frame; a run of 1.5 s or more of speech whose box covers less than 4% of the band is reported per
   * scene, with its start, end and least cover. On the delivered round-16 film, the review's runs (18.2, 21.4, 16.2,
   * 14.1, 07.1, 12.5 and 25.8) appear when visible ink is 45 levels above the ground in the 480x270 gray frame; a thin
   * stroke counts at its worst share of a cell. */
  const VISIBLE_LIFT = 45,
    SPARSE_COVER = 0.04,
    SPARSE_SECONDS = 1.5,
    isVisible = litLevel(film.palette, { lift: VISIBLE_LIFT });
  const sparseRuns = [];
  let sparseRun = null;
  function sparseSpeech(f) {
    const box = emptyBox();
    if (f.speaking) {
      const points = [
        ...f.graphics
          .filter((g) =>
            isVisible(
              g.color,
              g.alpha,
              g.kind === "fill" ? fillShare(g.box) : strokeShare(g.width),
            ),
          )
          .flatMap(pointsOf),
        ...f.layout.texts
          .filter((v) => v.role !== "caption" && isVisible(v.color, v.alpha, TEXT_SHARE))
          .flatMap((v) => [
            [v.bounds[0], v.bounds[1]],
            [v.bounds[2], v.bounds[3]],
          ]),
      ];
      for (const point of points)
        if (point[1] >= BALANCE_BAND[0] && point[1] <= BALANCE_BAND[1]) growBox(box, point);
    }
    const cover = box[2] > box[0] ? bandCover(box) : 0;
    if (f.speaking && cover < SPARSE_COVER) {
      if (
        sparseRun &&
        Math.abs(sparseRun.end - f.t) < step * 1.5 &&
        sparseRun.scene === f.speaking.id
      ) {
        sparseRun.end = f.t + step;
        sparseRun.least = Math.min(sparseRun.least, cover);
      } else {
        closeSparse();
        sparseRun = { scene: f.speaking.id, start: f.t, end: f.t + step, least: cover };
      }
    } else closeSparse();
  }
  function closeSparse() {
    if (sparseRun && sparseRun.end - sparseRun.start >= SPARSE_SECONDS) sparseRuns.push(sparseRun);
    sparseRun = null;
  }
  /* The marks and labels the frame's scene paints above 15% opacity, each with its scene and the points it covers. */
  const visibleOf = (f) => [
    ...f.sceneGraphics.filter((g) => g.alpha > VISIBLE).map((g) => [g.scene, pointsOf(g)]),
    ...f.layout.texts
      .filter((v) => v.scene && v.alpha > VISIBLE)
      .map((v) => [
        v.scene,
        [
          [v.bounds[0], v.bounds[1]],
          [v.bounds[2], v.bounds[3]],
        ],
      ]),
  ];
  /* BOUNDS: every frame a scene is drawn contributes its painted extent, so a scale keeps all of it in frame; each
   * speaking scene's extent and its mean share of the frame are kept for scale planning, from its own paints only, since
   * the outgoing scene holds over the first syllables of the next until the cut. */
  function paintedExtent(f) {
    const visible = visibleOf(f);
    for (const [scene, points] of visible) {
      drawn[scene] ??= emptyBox();
      for (const point of points) growBox(drawn[scene], point);
    }
    if (!f.speaking) return;
    const e = (extents[f.speaking.id] ??= { box: emptyBox(), frames: 0, area: 0 }),
      frame = emptyBox();
    for (const [scene, points] of visible)
      if (scene === f.speaking.id) for (const point of points) growBox(frame, point);
    if (frame[2] > frame[0]) {
      growBox(e.box, [frame[0], frame[1]]);
      growBox(e.box, [frame[2], frame[3]]);
      e.frames++;
      e.area += ((frame[2] - frame[0]) * (frame[3] - frame[1])) / (1920 * 1080);
    }
  }
  function finish() {
    for (const key of [...containerRuns.keys()]) closeContainer(key);
    closeSparse();
  }
  return {
    seats,
    containers,
    pictureBalance,
    sparseSpeech,
    paintedExtent,
    finish,
    marks,
    extents,
    drawn,
    sparseRuns,
    underfilled,
  };
}
