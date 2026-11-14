/* The rule on a row's names is serialised into the page: it is self-contained, takes the film's ink level as its
 * argument and runs in the real browser (geometry-check.mjs), where a name's box is the ink the browser paints. */

/** Row gaps: neighbouring names that stand on one row keep a clear gap of FLOOR em of the smaller face.
 *
 * The film reviews measure this on the delivered frames, as the ink gap between two text runs of one row band, and
 * their two lines agree on 1.5 em: one review holds a row's names to 1.5 em apart, 87 px of a 58 px face at UHD, and
 * the other names every pair up to 43 px apart at 1080p, 1.46 em of its 29.4 px face, and leaves alone every pair it
 * measured from 49 px, 1.66 em, on.
 *
 * A name is a scene's label whose whole text, the one it is registered with or its own, holds a letter, and each of
 * its painted runs that reads at LEGIBLE:1 or more is judged, a closing comma painted on its own included; a run that
 * ends in a joining mark (、 ， , ; ；) reads on into the run after it, so the two are one sentence, not neighbours. Two runs
 * stand on one row when the middles of their boxes are within LEVEL em of each other: the reviews' scripts take ink
 * 7 px apart in height at 1080p, a quarter of an em, as one row. A run's neighbour is the nearest run of its scene to
 * its right on its row; it is judged when it belongs to another name, so the runs and lines of one name and a term
 * with its qualifier are not neighbours; set in the same face, within FACE of its size, since a note beside a name is
 * its lead-in or qualifier; and at least JOIN em away, since runs under a word space apart read as one line, as the
 * reviews' scripts join ink closer than 16 px at 1080p. The gap is clear when no lit mark, a stroke or a fill at ink
 * INK or more or a text that is no name, stands between the two boxes: a link, an icon or a cross there separates the
 * names, as it splits the gap the reviews measure.
 *
 * A pair is judged while both names are at rest, each edge moving under REST px/s since the frame checked before, and
 * a pair that stands so for STAND seconds or more is a finding: its scene, both names, its tightest gap in px and in
 * em of the smaller face, when it first stood and how many checked frames show it. `see(texts, shapes, t, contrast)`
 * takes each checked frame's texts and shapes in turn, and `findings()` returns the pairs. A text's size on the screen
 * is its `shown`, or its `size` where the frame records none. */
export function rowGaps(level) {
  const FLOOR = 1.5,
    JOIN = 0.5,
    LEVEL = 0.25,
    FACE = 0.05,
    LEGIBLE = 3,
    INK = 40,
    REST = 1.5,
    STAND = 1;
  const pairs = new Map();
  let before = [],
    last = null;
  const face = (v) => v.shown ?? v.size;
  const whole = (v) => v.whole ?? v.text;
  const middle = (v) => (v.bounds[1] + v.bounds[3]) / 2;
  // A run of words that ends in a joining mark reads on into the run after it: one sentence set as two runs. A mark
  // painted on its own is a name's closing mark, which ends it.
  const continues = (v) => /\p{L}.*[、，,;；]\s*$/u.test(v.text);
  const meets = (a, b) => a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3];
  /* Liang-Barsky: does segment p-q enter rectangle r? */
  const crosses = ([x0, y0], [x1, y1], [rx0, ry0, rx1, ry1]) => {
    let a = 0,
      b = 1;
    const dx = x1 - x0,
      dy = y1 - y0;
    for (const [p, q] of [
      [-dx, x0 - rx0],
      [dx, rx1 - x0],
      [-dy, y0 - ry0],
      [dy, ry1 - y0],
    ]) {
      if (p === 0) {
        if (q < 0) return false;
        continue;
      }
      const r = q / p;
      if (p < 0) {
        if (r > b) return false;
        if (r > a) a = r;
      } else {
        if (r < a) return false;
        if (r < b) b = r;
      }
    }
    return true;
  };
  /* Whether a lit shape, or a text that is no name, stands in the zone between two names. */
  const marked = (zone, shapes, marks) =>
    marks.some((v) => meets(v.bounds, zone)) ||
    shapes.some(
      (g) =>
        level(g.color, g.alpha) >= INK &&
        (g.kind === "fill"
          ? meets(g.box, zone)
          : g.subs.some((sub) => sub.some((p, k) => k > 0 && crosses(sub[k - 1], p, zone)))),
    );
  return {
    see(texts, shapes, t, contrast) {
      const reach = last === null ? -1 : REST * (t - last) + 0.01;
      const still = (v) =>
        before.some(
          (u) =>
            u.scene === v.scene &&
            u.text === v.text &&
            u.bounds.every((x, k) => Math.abs(x - v.bounds[k]) <= reach),
        );
      const labels = texts.filter((v) => v.scene && v.role === "label"),
        named = (v) => /\p{L}/u.test(whole(v)),
        names = labels.filter((v) => named(v) && contrast(v.color, v.alpha) >= LEGIBLE),
        marks = labels.filter((v) => !named(v) && level(v.color, v.alpha) >= INK);
      for (const a of names) {
        // The nearest run to the right on a's row, a run that overlaps it aside: that is the overlap rule's.
        const gapTo = (v) => v.bounds[0] - a.bounds[2];
        const b = names
          .filter(
            (v) =>
              v !== a &&
              v.scene === a.scene &&
              gapTo(v) >= 0 &&
              Math.abs(middle(v) - middle(a)) <= LEVEL * Math.min(face(a), face(v)),
          )
          .sort((u, v) => gapTo(u) - gapTo(v))[0];
        if (!b || whole(a) === whole(b) || continues(a)) continue;
        const em = Math.min(face(a), face(b)),
          gap = gapTo(b);
        if (Math.abs(face(a) - face(b)) > FACE * em || gap < JOIN * em || gap >= FLOOR * em)
          continue;
        if (!still(a) || !still(b)) continue;
        const zone = [
          a.bounds[2],
          Math.max(a.bounds[1], b.bounds[1]),
          b.bounds[0],
          Math.min(a.bounds[3], b.bounds[3]),
        ];
        if (marked(zone, shapes, marks)) continue;
        const key = [a.scene, whole(a), whole(b)].join("\u0000"),
          found = pairs.get(key) ?? { scene: a.scene, pair: [whole(a), whole(b)], runs: [] },
          run = found.runs.at(-1);
        if (run && run.end === last) {
          run.end = t;
          run.frames++;
          if (gap / em < run.em) Object.assign(run, { gap, em: gap / em });
        } else found.runs.push({ start: last, end: t, frames: 2, gap, em: gap / em });
        pairs.set(key, found);
      }
      before = texts;
      last = t;
    },
    findings() {
      const round = (v, n) => Math.round(v * 10 ** n) / 10 ** n;
      return [...pairs.values()].flatMap(({ scene, pair, runs }) => {
        const stood = runs.filter((run) => run.end - run.start >= STAND - 1e-6);
        if (!stood.length) return [];
        const tightest = stood.reduce((a, run) => (run.em < a.em ? run : a));
        return [
          {
            kind: "row_gap",
            scene,
            text: pair.join(" | "),
            pair,
            gap: round(tightest.gap, 1),
            em: round(tightest.em, 2),
            floor: FLOOR,
            at: stood[0].start,
            frames: stood.reduce((n, run) => n + run.frames, 0),
          },
        ];
      });
    },
  };
}
