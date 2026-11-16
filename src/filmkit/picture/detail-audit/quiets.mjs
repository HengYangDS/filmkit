/* Strokes at rest in a quiet, and the tips that draw them.
 *
 * A composition advances a stroke that draws on in voice time, which rests in the quiet between two thoughts. A
 * stroke that has set off and is not whole there shows less than its thought said: the DDWG film's review round 41
 * (finding Z41-1) found a bracket that named three layers at three fifths of its way through the quiet after its
 * thought. The motion audit follows marks that move; a stroke that stops half made neither pops, halts nor races.
 *
 * The composition publishes, with each frame's layout, the strokes it draws by their tip (`draws`: each with its
 * `scene`, the cue `at` which it is keyed, the `share` of its way it has reached, 0 to 1, and the tip's peak `pace`
 * in px/s at 1080p). The audit reads them at the middle of every quiet between two thoughts of a segment, and
 * through the film for a tip at the pace at which a mark races. A composition that publishes none is not judged. */
import { VIEWER } from "../motion-audit/follow.mjs";

/** A share within EDGE of 0 or 1 is unmade or whole. */
export const EDGE = 1e-6;
/** The pace from which a drawing tip races, in 1080p px/s: the motion audit's line for a mark that moves faster than
 * a viewer follows (motion-audit/follow.mjs). */
export const TIP_RACE = VIEWER.RACE;

const units = (text) => text.replace(/[^\p{L}\p{N}]/gu, "").toLowerCase();

/** Each thought of the timeline with the times of its first and last word: its segment's id as `scene`, its number
 * from 1 as `index`, and its `start` and `end`. A thought takes the words that fill its utterance group's letters
 * and digits, as the frame audit reads them. */
export function thoughtsOf(timeline) {
  return timeline.segments.flatMap((segment) => {
    let k = 0;
    return segment.utterance_groups.flatMap((group, index) => {
      const need = units(group).length,
        first = k;
      let n = 0;
      while (k < segment.words.length && n < need) n += units(segment.words[k++].text).length;
      if (k === first) return [];
      return [
        {
          scene: segment.id,
          index: index + 1,
          start: segment.words[first].start,
          end: segment.words[k - 1].end,
        },
      ];
    });
  });
}

/** The quiets between consecutive thoughts of one segment: each named by the thought it follows, "<segment>.<n>",
 * from that thought's last word, `rest`, to the next thought's first, `resume`. */
export function quietsOf(thoughts) {
  const quiets = [];
  for (let i = 1; i < thoughts.length; i++) {
    const before = thoughts[i - 1],
      after = thoughts[i];
    if (before.scene !== after.scene || after.start <= before.end) continue;
    quiets.push({ id: `${before.scene}.${before.index}`, rest: before.end, resume: after.start });
  }
  return quiets;
}

/** The published strokes that stand part-drawn: set off and not whole. */
export const partDrawn = (draws) => draws.filter((d) => d.share > EDGE && d.share < 1 - EDGE);

/** Gathers the tips that race. `frame(draws)` takes one frame's published strokes; `finish()` returns one row for
 * each stroke, by its scene and cue, whose tip reached TIP_RACE while it drew, with its fastest pace. */
export function racingTips() {
  const fastest = new Map();
  return {
    frame(draws) {
      for (const d of partDrawn(draws)) {
        if (!(d.pace >= TIP_RACE)) continue;
        const key = `${d.scene}\u0000${d.at}`;
        if (!(fastest.get(key)?.pace >= d.pace))
          fastest.set(key, { scene: d.scene, cue: d.at, pace: Math.round(d.pace) });
      }
    },
    finish() {
      return [...fastest.values()].sort((a, b) => a.cue - b.cue);
    },
  };
}
