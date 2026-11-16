/* Ink drops: a line that loses part of its ink within one frame while the rest of it stays.
 *
 * The motion audit calls a pop a drawn piece that leaves whole. A line that is split in two or cut short at once
 * leaves no piece whole, and a viewer sees it open all the same: the ETHOS film's review round 20 (note zh-R20-02)
 * found a 55 px gap that opened in a path within one frame, three times, on a master that had passed the motion audit.
 *
 * For each draw call of a scene, the line of the composition that drew it, the pieces of its firm solid strokes are
 * matched by length from one frame to the next. A piece that leaves whole is the motion audit's to judge. A drop is
 * a piece replaced by shorter ones, DROP px or more of ink lost in one frame, while neither the frame before nor the
 * frame after loses ink in that call: a line that is drawn off gradually loses a little in every frame and is no
 * drop. A loss on the frame of a stage cut that the scene declares is the cut's, and is counted apart. */

/** The thresholds, in 1080p px: a piece shorter than PIECE is not followed; a drop loses DROP or more in one frame
 * (the reviewer's gap was 55 px; a stroke drawn off at the film's pace of 450 px/s loses 7.5 px a frame at 60 fps);
 * a neighbouring frame that loses more than CALM in the same call makes the loss part of a gradual change; and a
 * stroke below the opacity FIRM is not firm enough for its loss to read as a pop. */
export const INK = Object.freeze({ PIECE: 8, DROP: 30, CALM: 3, FIRM: 0.5 });

/** The lengths of a paint's pieces that the scan follows: the sub-paths of a firm solid stroke of a scene, PIECE px
 * or longer. Every other paint gives none. */
export function strokePieces(paint) {
  if (paint.kind !== "stroke" || !paint.scene || paint.dash?.length) return [];
  if ((paint.alpha ?? 1) < INK.FIRM) return [];
  const pieces = [];
  for (const sub of paint.subs ?? []) {
    let ink = 0;
    for (let i = 1; i < sub.length; i++)
      ink += Math.hypot(sub[i][0] - sub[i - 1][0], sub[i][1] - sub[i - 1][1]);
    if (ink >= INK.PIECE) pieces.push(ink);
  }
  return pieces;
}

const same = (a, b) => Math.abs(a - b) <= Math.max(2, 0.01 * a);

/** The ink one draw call lost between two frames by pieces that got shorter or split, given its pieces' lengths in
 * each: 0 when every piece of `before` stands in `now` or its pieces only left whole. */
export function partialLoss(before, now) {
  const left = [...now];
  const gone = before.filter((v) => {
    const k = left.findIndex((w) => same(v, w));
    if (k < 0) return true;
    left.splice(k, 1);
    return false;
  });
  if (!left.length || !gone.length) return 0;
  return gone.reduce((s, v) => s + v, 0) - left.reduce((s, v) => s + v, 0);
}

/** Follows the draw calls' pieces through consecutive frames `dt` seconds apart. `frame(t, pieces, cuts)` takes the
 * frame's pieces as a Map from a draw call's key, "<scene> <origin>", to its pieces' lengths, and a function that
 * gives the stage cuts the composition has declared so far, a Map from scene to a Set of times, which is asked only
 * when a call lost ink. `finish()` returns the frames followed, the
 * drops, each with the time of the frame that shows the loss, its scene, its origin, the ink lost and the ink the
 * call held before, and how many losses fell on a declared stage cut. */
export function inkDrops(dt) {
  let a = null,
    b = null,
    lossAB = new Map(),
    lossBefore = new Map(),
    frames = 0,
    atCuts = 0;
  const drops = [];
  const losses = (x, y) => {
    const out = new Map();
    for (const [key, before] of x) {
      const lost = partialLoss(before, y.get(key) ?? []);
      if (lost > 0) out.set(key, lost);
    }
    return out;
  };
  return {
    frame(t, pieces, cuts = () => new Map()) {
      frames++;
      if (b === null) {
        b = { t, pieces };
        return;
      }
      const lossBC = losses(b.pieces, pieces);
      if (a !== null)
        for (const [key, lost] of lossAB) {
          if (lost < INK.DROP || lossBefore.get(key) > INK.CALM || lossBC.get(key) > INK.CALM)
            continue;
          const [scene, origin = ""] = key.split(" ");
          const cut = [...(cuts().get(scene) ?? [])].some(
            (c) => c > b.t - dt - 1e-6 && c <= b.t + 1e-6,
          );
          if (cut) atCuts++;
          else {
            const held = a.pieces.get(key).reduce((s, v) => s + v, 0);
            drops.push({ t: b.t, scene, origin, lost: Math.round(lost), of: Math.round(held) });
          }
        }
      lossBefore = lossAB;
      lossAB = lossBC;
      a = b;
      b = { t, pieces };
    },
    finish() {
      return { frames, drops, at_cuts: atCuts };
    },
  };
}
