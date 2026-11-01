/* The frame rule is serialised into the page: it is self-contained, takes the film's ink level as its argument and
 * runs both in the real browser (geometry-check.mjs) and headlessly (frame-audit.mjs). */

/** Frame analysis: labels must stay apart, inside the safe area, and clear of shapes; shapes stay inside the
 * action-safe area. Dim marks still collide visually, so anything above 15% opacity counts. A frame that must paint
 * (during speech, or in a pause within a chapter) may not show bare ground: the brightest mark of a scene, at its ink
 * `level` (inkLevel), must rise at least 30 levels above the ground (steady scenes reach 150-225), so no stage or scene
 * change dims through an empty picture; on a chapter's first word it must reach 90, half a steady scene. The frame's
 * brightest level is returned with its findings, so a run of speech that stays below 90 for half a second, a picture
 * of faint placeholders only, is reported too. Marks of the head band (the running head and the Illustrative chip)
 * frame the picture rather than show it, so they never keep a frame from reading as bare ground. Labels end at least
 * 34 px above the caption band. Each finding carries its evidence: a label's bounds, the overlapping pair, the shape
 * and the part of it that collides (a fill's box or a stroke's first crossing segment), or a shape's first point
 * outside the action-safe area. */
export function analysis(level) {
  const SAFE = [96, 40, 1824, 920],
    ACTION_SAFE = [96, 54, 1824, 1026],
    VISIBLE = 0.15,
    LEVEL = 30,
    FIRST_WORD = 90,
    HEAD = 108;
  const inHead = (points) => points.length > 0 && points.every(([, y]) => y < HEAD);
  const intersects = (a, b, pad = 2) =>
    a[0] < b[2] - pad && b[0] < a[2] - pad && a[1] < b[3] - pad && b[1] < a[3] - pad;
  const contains = (outer, inner, pad = 1) =>
    outer[0] <= inner[0] + pad &&
    outer[1] <= inner[1] + pad &&
    outer[2] >= inner[2] - pad &&
    outer[3] >= inner[3] - pad;
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
  // The first segment of a stroke that enters a zone, as its two end points.
  const crossing = (subs, zone) => {
    for (const v of subs) {
      const k = v.findIndex((p, k) => k > 0 && crosses(v[k - 1], p, zone));
      if (k > 0) return [...v[k - 1], ...v[k]];
    }
    return null;
  };
  const pointsOf = (g) =>
    g.kind === "fill"
      ? [
          [g.box[0], g.box[1]],
          [g.box[2], g.box[3]],
        ]
      : g.subs.flat();
  return function inspectFrame(
    texts,
    shapes,
    { mustPaint = false, firstWord = false, scene = null } = {},
  ) {
    const findings = [];
    const brightest = Math.max(
      0,
      ...texts
        .filter(
          (v) =>
            v.scene &&
            !inHead([
              [v.bounds[0], v.bounds[1]],
              [v.bounds[2], v.bounds[3]],
            ]),
        )
        .map((v) => level(v.color, v.alpha)),
      ...shapes.filter((g) => g.scene && !inHead(pointsOf(g))).map((g) => level(g.color, g.alpha)),
    );
    if (mustPaint && brightest < LEVEL) findings.push({ kind: "bare_ground", scene, text: "" });
    if (firstWord && brightest < FIRST_WORD)
      findings.push({ kind: "faint_first_word", scene, text: "" });
    findings.brightest = brightest;
    for (const g of shapes) {
      if (g.alpha <= VISIBLE) continue;
      const point = pointsOf(g).find(
        ([x, y]) =>
          x < ACTION_SAFE[0] - 0.5 ||
          y < ACTION_SAFE[1] - 0.5 ||
          x > ACTION_SAFE[2] + 0.5 ||
          y > ACTION_SAFE[3] + 0.5,
      );
      if (point)
        findings.push({
          kind: `${g.kind}_outside_action_safe`,
          scene: null,
          text: "",
          shape: g.kind,
          point,
        });
    }
    const labels = texts.filter((v) => v.alpha > VISIBLE);
    labels.forEach((a, i) => {
      const [x0, y0, x1, y1] = a.bounds;
      if (
        a.role !== "caption" &&
        a.role !== "title" &&
        (x0 < SAFE[0] || y0 < SAFE[1] || x1 > SAFE[2] || y1 > SAFE[3])
      ) {
        findings.push({
          kind: "outside_safe_area",
          scene: a.scene,
          text: a.text,
          bounds: a.bounds,
        });
      }
      if (a.role !== "caption") {
        // An opaque fill painted between a shape and the label (its pill or card) hides the shape beneath it.
        const covers = shapes.filter(
          (g) => g.kind === "fill" && g.alpha > 0.9 && g.seq < a.seq && contains(g.box, a.bounds),
        );
        for (const g of shapes) {
          if (g.alpha <= VISIBLE || covers.some((f) => f.seq > g.seq)) continue;
          const zone = [
            x0 + 3 - g.width / 2,
            y0 + 3 - g.width / 2,
            x1 - 3 + g.width / 2,
            y1 - 3 + g.width / 2,
          ];
          const graphic =
            g.kind === "fill"
              ? intersects(g.box, a.bounds, 3) && !contains(g.box, a.bounds)
                ? g.box
                : null
              : crossing(g.subs, zone);
          if (graphic)
            findings.push({
              kind: `label_${g.kind}_collision`,
              scene: a.scene,
              text: a.text,
              shape: g.kind,
              bounds: a.bounds,
              graphic,
            });
        }
      }
      for (const b of labels.slice(i + 1)) {
        if (intersects(a.bounds, b.bounds))
          findings.push({
            kind: "label_overlap",
            scene: a.scene ?? b.scene,
            text: `${a.text} | ${b.text}`,
            pair: [a.text, b.text],
          });
      }
    });
    return findings;
  };
}
