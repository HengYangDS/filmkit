/** Exercise the frame audit's text-layout measures on frames drawn on the headless canvas. */
import test from "node:test";
import assert from "node:assert/strict";

import { canvasStandIn } from "../../src/filmkit/picture/headless-composition.mjs";
import {
  frameFindings,
  TEXT_LAYOUT,
  textLayout,
} from "../../src/filmkit/picture/frame-audit/typography.mjs";

/* One frame's paints as the frame audit receives them: drawn on the headless canvas, each in scene 01. */
function paintsOf(draw) {
  const paints = [];
  draw(canvasStandIn((paint) => paints.push({ ...paint, scene: "01" })));
  return paints;
}
/* A name on its alphabetic baseline, centred on x unless aligned otherwise. */
function name(ctx, value, x, y, { size = 30, align = "center", alpha = 1 } = {}) {
  ctx.globalAlpha = alpha;
  ctx.font = `${size}px Sample`;
  ctx.textAlign = align;
  ctx.textBaseline = "alphabetic";
  ctx.fillText(value, x, y);
}
function stroke(ctx, path, width = 2) {
  ctx.globalAlpha = 1;
  ctx.lineWidth = width;
  ctx.beginPath();
  path();
  ctx.stroke();
}
function card(ctx, x, y, width, height) {
  ctx.globalAlpha = 1;
  ctx.beginPath();
  ctx.roundRect(x, y, width, height, 12);
  ctx.fill();
  stroke(ctx, () => ctx.roundRect(x, y, width, height, 12));
}
const check = (ctx, x, y) =>
  stroke(
    ctx,
    () => {
      ctx.moveTo(x, y - 12);
      ctx.lineTo(x + 10, y - 2);
      ctx.lineTo(x + 28, y - 22);
    },
    4,
  );
const ring = (ctx, x, y, r) => stroke(ctx, () => ctx.arc(x, y, r, 0, 2 * Math.PI));
const of = (findings, kind) => findings.filter((v) => v.kind === kind);
const kinds = (findings) => [...new Set(findings.map((v) => v.kind))].sort();
/* The runs of a frame drawn by `draw(ctx, t)` every thirtieth of a second for `seconds` of speech. */
function runsOf(seconds, draw) {
  const layout = textLayout(1 / 30);
  for (let k = 0; k / 30 < seconds - 1e-9; k++) {
    const t = k / 30;
    layout.frame({ t, speaking: { id: "01" }, paints: paintsOf((ctx) => draw(ctx, t)) });
  }
  return layout.finish();
}

test("names of one row on two baselines through 2 s of speech are one ragged row", () => {
  const runs = runsOf(3, (ctx, t) => {
    name(ctx, "Sources", 600, 500);
    name(ctx, "Films", 900, t < 2 ? 506 : 500);
  });
  assert.deepEqual(Object.keys(runs), TEXT_LAYOUT);
  assert.equal(runs.ragged_rows.length, 1);
  const [row] = runs.ragged_rows;
  assert.equal(row.scene, "01");
  assert.ok(Math.abs(row.start) < 1e-9 && Math.abs(row.end - 2) < 1e-6);
  assert.deepEqual(row.texts, ["Sources", "Films"]);
  assert.deepEqual(row.detail.baselines, [500, 506]);
  assert.ok(row.detail.gap > 0 && row.detail.gap < 300);
  for (const kind of TEXT_LAYOUT.filter((v) => v !== "ragged_rows"))
    assert.deepEqual(runs[kind], []);
});

test("a passing misalignment, a dimmed name and a speechless frame are not ragged rows", () => {
  const brief = runsOf(3, (ctx, t) => {
    name(ctx, "Sources", 600, 500);
    name(ctx, "Films", 900, t < 0.5 ? 506 : 500);
  });
  assert.deepEqual(brief.ragged_rows, []);
  // A name fading in is not yet settled, and two names 3 px apart are on one baseline as the reviewers see it.
  const draw = (ctx) => {
    name(ctx, "Sources", 600, 500);
    name(ctx, "Films", 900, 506, { alpha: 0.6 });
    name(ctx, "Packages", 600, 700);
    name(ctx, "Picture", 900, 703);
  };
  assert.deepEqual(frameFindings(paintsOf(draw)), []);
  // Speech pausing between two second-long stretches ends the run.
  const layout = textLayout(1 / 30);
  const ragged = paintsOf((ctx) => {
    name(ctx, "Sources", 600, 500);
    name(ctx, "Films", 900, 506);
  });
  for (let k = 0; k < 75; k++)
    layout.frame({ t: k / 30, speaking: k >= 25 && k < 30 ? null : { id: "01" }, paints: ragged });
  assert.deepEqual(
    layout.finish().ragged_rows.map((v) => [+v.start.toFixed(2), +v.end.toFixed(2)]),
    [[1, 2.5]],
  );
});

test("names in different containers, or one standing in a list, are not one row", () => {
  // Boxes drawn as one path hold one name each; without them the names would make a ragged row.
  const names = (ctx) => {
    name(ctx, "Sources", 600, 500);
    name(ctx, "Films", 900, 506);
  };
  assert.deepEqual(kinds(frameFindings(paintsOf(names))), ["ragged_rows"]);
  const boxed = paintsOf((ctx) => {
    stroke(ctx, () => {
      ctx.roundRect(520, 140, 160, 90, 8);
      ctx.roundRect(520, 440, 160, 90, 8);
      ctx.roundRect(820, 440, 160, 90, 8);
    });
    names(ctx);
  });
  assert.deepEqual(of(frameFindings(boxed), "ragged_rows"), []);
  // An item of a list, dimmed items included, keeps its list's rows; a label beside the list is not one of them.
  const listed = paintsOf((ctx) => {
    name(ctx, "First item", 400, 500, { align: "left" });
    name(ctx, "Second item", 400, 572, { align: "left", alpha: 0.6 });
    name(ctx, "A label", 900, 505);
  });
  assert.deepEqual(of(frameFindings(listed), "ragged_rows"), []);
  // A name led by a marker is an item even alone.
  const led = paintsOf((ctx) => {
    ctx.beginPath();
    ctx.arc(385, 489, 6, 0, 2 * Math.PI);
    ctx.fill();
    name(ctx, "First item", 400, 500, { align: "left" });
    name(ctx, "A label", 900, 505);
  });
  assert.deepEqual(of(frameFindings(led), "ragged_rows"), []);
});

test("the lines of a block and the items of a column share their edge", () => {
  // Two left-aligned lines of one block start 5 px apart.
  const block = frameFindings(
    paintsOf((ctx) => {
      name(ctx, "The first line", 600, 500, { align: "left" });
      name(ctx, "the second line", 605, 538, { align: "left" });
    }),
  );
  assert.deepEqual(kinds(block), ["ragged_columns"]);
  assert.deepEqual(block[0].texts, ["The first line", "the second line"]);
  assert.deepEqual(block[0].detail, { edge: "left", edges: [600, 605] });
  // A name over its note, a size smaller, indented 10 px.
  const note = frameFindings(
    paintsOf((ctx) => {
      name(ctx, "Agent", 150, 500, { align: "left" });
      name(ctx, "Checks the task first", 140, 540, { align: "left", size: 24 });
    }),
  );
  assert.deepEqual(note[0].detail, { edge: "left", edges: [150, 140] });
  // Items centred beside a left-aligned column of checks stand at ragged distances from them; set left-aligned one
  // gap after their checks, under a heading flush with the checks, they share one edge.
  const items = ["录音", "音轨", "打包记录"];
  const centred = frameFindings(
    paintsOf((ctx) =>
      items.forEach((v, i) => {
        check(ctx, 870, 440 + 45 * i);
        name(ctx, v, 980, 440 + 45 * i, { size: 28 });
      }),
    ),
  );
  assert.deepEqual(kinds(centred), ["ragged_columns"]);
  assert.deepEqual(centred[0].detail, { edge: "after marks", edges: [952, 952, 924] });
  const aligned = paintsOf((ctx) => {
    name(ctx, "核对成片的结果", 868, 400, { size: 28, align: "left" });
    items.forEach((v, i) => {
      check(ctx, 870, 440 + 45 * i);
      name(ctx, v, 924, 440 + 45 * i, { size: 28, align: "left" });
    });
  });
  assert.deepEqual(frameFindings(aligned), []);
});

test("marks beside a column of items share an edge", () => {
  // Crosses after left-aligned items of different lengths form a ragged column.
  const after = frameFindings(
    paintsOf((ctx) =>
      ["一个文件", "一张表", "一份报告"].forEach((v, i) => {
        name(ctx, v, 700, 400 + 60 * i, { align: "left" });
        name(ctx, "✗", 700 + 30 * v.length + 20, 400 + 60 * i, { align: "left" });
      }),
    ),
  );
  assert.deepEqual(kinds(after), ["ragged_columns"]);
  assert.deepEqual(after[0].detail, { edge: "marks after", edges: [840, 810, 840] });
  // Bullets hung on the left edges of centred items zig-zag.
  const before = frameFindings(
    paintsOf((ctx) =>
      ["Fresh facts", "The applicable policy", "Valid attestations"].forEach((v, i) => {
        const y = 400 + 60 * i,
          left = 700 - (v.length * 0.54 * 30 + 0.12 * 30) / 2;
        ctx.globalAlpha = 1;
        ctx.beginPath();
        ctx.arc(left - 18, y - 9, 5, 0, 2 * Math.PI);
        ctx.fill();
        name(ctx, v, 700, y);
      }),
    ),
  );
  assert.deepEqual(kinds(before), ["ragged_columns"]);
  assert.equal(before[0].detail.edge, "marks before");
});

test("lines aligned by hung punctuation, by a layout's measure or as separate labels are not ragged", () => {
  // A right-aligned CJK line ending in 、 hangs its empty half past the edge, so its ink meets the line under it.
  const hung = paintsOf((ctx) => {
    name(ctx, "局部、可逆、", 896, 300, { align: "right" });
    name(ctx, "不对外承诺的小事", 881, 340, { align: "right" });
  });
  assert.deepEqual(frameFindings(hung), []);
  // Lines revealed run by run were placed by the composition's own measure: a line still being revealed under a
  // whole one declares no edge.
  const runs = paintsOf((ctx) => {
    name(ctx, "局部", 731, 300, { align: "left" });
    name(ctx, "、可逆", 791, 300, { align: "left" });
    name(ctx, "不对外承诺", 641, 340, { align: "left" });
  });
  assert.deepEqual(frameFindings(runs), []);
  // Two centred labels close together on one baseline are two names: a rule under the second touches it alone.
  const pair = frameFindings(
    paintsOf((ctx) => {
      name(ctx, "Production failure", 1000, 500);
      name(ctx, "Permission or", 1262, 500);
      name(ctx, "compliance breach", 1262, 538);
      stroke(ctx, () => {
        ctx.moveTo(1160, 509);
        ctx.lineTo(1360, 509);
      });
    }),
  );
  assert.deepEqual(
    pair.map((v) => [v.kind, v.texts]),
    [["touching_marks", ["Permission or"]]],
  );
});

test("a left-aligned block centred on a mark stands off its axis", () => {
  const found = frameFindings(
    paintsOf((ctx) => {
      ring(ctx, 600, 400, 30);
      name(ctx, "研究员", 528, 480, { align: "left" });
      name(ctx, "拿数据做回测", 528, 516, { align: "left", size: 24 });
    }),
  );
  assert.deepEqual(kinds(found), ["ragged_columns"]);
  assert.deepEqual(found[0].detail, { edge: "axis", axis: 600, offsets: [-27, 0] });
});

test("a line whose ink comes within 7 px of the ink of the line above it is crammed", () => {
  const found = frameFindings(
    paintsOf((ctx) => {
      name(ctx, "A name", 600, 500);
      name(ctx, "its note", 600, 531.6);
    }),
  );
  assert.deepEqual(kinds(found), ["crammed_lines"]);
  assert.deepEqual(found[0].texts, ["A name", "its note"]);
  assert.deepEqual(found[0].detail, { clear: 4 });
  // 10 px clear is room enough.
  assert.deepEqual(
    frameFindings(
      paintsOf((ctx) => {
        name(ctx, "A name", 600, 500);
        name(ctx, "its note", 600, 537.6);
      }),
    ),
    [],
  );
});

test("a name alone in a small card stands on its centre; a heading at the top of a tall card does not", () => {
  const found = frameFindings(
    paintsOf((ctx) => {
      card(ctx, 500, 100, 300, 200);
      name(ctx, "Heading", 650, 140);
      card(ctx, 500, 600, 200, 70);
      name(ctx, "Name", 608, 642.8);
      card(ctx, 900, 600, 200, 70);
      name(ctx, "Centred", 1000, 642.8);
    }),
  );
  assert.deepEqual(kinds(found), ["off_card_centre"]);
  assert.deepEqual(found[0].texts, ["Name"]);
  assert.deepEqual(found[0].detail, { offset: [8, 0], card: [500, 600, 700, 670] });
  // A folded corner is part of its card; a second mark inside it is not, so the name no longer stands alone.
  const folded = paintsOf((ctx) => {
    card(ctx, 500, 600, 200, 70);
    stroke(ctx, () => {
      ctx.moveTo(680, 600);
      ctx.lineTo(700, 620);
    });
    name(ctx, "Name", 600, 630);
  });
  assert.equal(of(frameFindings(folded), "off_card_centre")[0].detail.offset[1], -12.8);
  const marked = paintsOf((ctx) => {
    card(ctx, 500, 600, 200, 70);
    ring(ctx, 530, 635, 10);
    name(ctx, "Name", 600, 630);
  });
  assert.deepEqual(of(frameFindings(marked), "off_card_centre"), []);
});

test("a touching mark is measured on the stroke, not its box", () => {
  const found = frameFindings(
    paintsOf((ctx) => {
      // A name inside an empty ring stands in its box but well clear of its stroke.
      ring(ctx, 600, 500, 60);
      name(ctx, "Inside", 600, 510);
      // A name 2 px under a rule.
      stroke(ctx, () => {
        ctx.moveTo(1100, 300);
        ctx.lineTo(1300, 300);
      });
      name(ctx, "Touching", 1200, 324.6);
    }),
  );
  assert.deepEqual(kinds(found), ["touching_marks"]);
  assert.deepEqual(found[0].texts, ["Touching"]);
  assert.deepEqual(found[0].detail, { clear: 2, mark: [1100, 300, 1300, 300] });
  // A name set on a panel, however tight, is held by it, and a stroke that crosses a name is a collision, judged by
  // the label rules.
  const held = paintsOf((ctx) => {
    ctx.globalAlpha = 1;
    ctx.beginPath();
    ctx.roundRect(610, 486, 180, 32, 8);
    ctx.fill();
    name(ctx, "On a panel", 700, 510);
    stroke(ctx, () => {
      ctx.moveTo(1100, 690);
      ctx.lineTo(1300, 690);
    });
    name(ctx, "Crossed", 1200, 700);
  });
  assert.deepEqual(frameFindings(held), []);
});

test("an uneven pitch is reported only when the names under the marks keep equal gaps", () => {
  // Names 36, 100.8 and 68.4 px wide with 100 px between them centre their marks at uneven pitch.
  const row = (texts, centres) =>
    frameFindings(
      paintsOf((ctx) =>
        texts.forEach((v, i) => {
          ring(ctx, centres[i], 450, 20);
          name(ctx, v, centres[i], 511.6);
        }),
      ),
    );
  const spaced = row(["Ax", "Bxxxxx", "Cxxx"], [400, 568.4, 753]);
  assert.deepEqual(kinds(spaced), ["uneven_pitch"]);
  assert.deepEqual(spaced[0].texts, ["Ax", "Bxxxxx", "Cxxx"]);
  assert.deepEqual(spaced[0].detail, { pitch: [168.4, 184.6], gaps: [100, 100] });
  // The same marks over names of one width leave uneven gaps, and an even pitch is tidy.
  assert.deepEqual(row(["Ax", "Bx", "Cx"], [400, 568.4, 753]), []);
  assert.deepEqual(row(["Ax", "Bxxxxx", "Cxxx"], [400, 568.4, 736.8]), []);
});

test("baselines are read from alphabetic, middle and top anchors alike", () => {
  // A name 6 px low, anchored by its middle, and another on the row's baseline, anchored by its top.
  const found = frameFindings(
    paintsOf((ctx) => {
      name(ctx, "Sources", 600, 500);
      ctx.textBaseline = "middle";
      ctx.fillText("Films", 900, 506 - 0.28 * 30);
      ctx.textBaseline = "top";
      ctx.fillText("Picture", 1200, 500 - 0.8 * 30);
    }),
  );
  assert.deepEqual(
    found.map((v) => [v.kind, v.texts, v.detail.baselines]),
    [
      ["ragged_rows", ["Sources", "Films"], [500, 506]],
      ["ragged_rows", ["Films", "Picture"], [506, 500]],
    ],
  );
});

test("a run keeps the offsets of its worst frame", () => {
  // The same row twice in one frame, and its step growing through the run.
  const runs = runsOf(2, (ctx, t) => {
    name(ctx, "Sources", 600, 300);
    name(ctx, "Films", 900, 305);
    name(ctx, "Sources", 600, 600);
    name(ctx, "Films", 900, t < 1 ? 607 : 609);
  });
  assert.equal(runs.ragged_rows.length, 1);
  assert.deepEqual(runs.ragged_rows[0].detail.baselines, [600, 609]);
});
