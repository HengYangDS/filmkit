# Design

## Context

See [proposal.md](proposal.md). The frame audit (`picture/frame-audit.mjs`) exercises every frame of an edition's composition headlessly. Each frame's paints carry exact anchors and mark geometry; a text's extent is the headless canvas's estimate, a CJK character as wide as its size and a Latin character about half of it, so the far edge of centred or right-aligned Latin text is approximate while its anchor, size and baseline are exact. `check-picture` refuses the findings that `picture/gates.py` lists in `FRAME_GATES`.

On 2026-11-03 independent typography reviews read the delivered DDWG 1.2.0 Chinese edition in three slices (79, 78 and 85 of 100), its English edition in two (the last scored 78), and both editions of the ETHOS v2 composition (70 and 72). A prototype of this audit, run headlessly over the same compositions, reported ten rows of names off one baseline in the Chinese DDWG edition, and the reviewers confirmed all ten; its stacked-line findings matched theirs, while its card-centre findings were column headings in tall cards, and its proximity findings measured an arc's bounding box rather than its stroke. After the films' typography repairs, the prototype reports at most four findings in either DDWG edition.

## Goals / Non-Goals

**Goals:**

- The frame audit measures how text lines up, from the exact geometry it already has, and reports each defect with the scene, its span, the texts and the measured offsets.
- `check-picture` refuses the text-layout defects the audit can measure without the estimated widths, so a film cannot render ragged rows or crammed lines.
- The engine's own sample film is aligned, and its review floors are the owner's 95.
- An editable install names the engine version it runs.

**Non-Goals:**

- Judging composition as a whole: a picture off the frame's centre, a label placed where its finished group will stand, or a heading that crowds its mark stay with the balance audits and the reviewers.
- Gating measures that rest on the estimated widths of Latin text; they are reported for the reviewers.
- Changing a film that does not adopt 0.7.0.

## Decisions

- **A text-layout module of the frame audit.** `picture/frame-audit/typography/` reads each exercised voiced frame's settled text (opacity 0.85 or more) and marks in the content band, below the head band and above the caption band. It joins fragments of one size on one baseline into lines, and lines into blocks by their leading. Its modules keep the repository's limit of 500 effective lines: `layout.mjs` reads a frame, `measures.mjs` holds the measures and `index.mjs` joins their findings into runs. Its measures, each joined over frames into runs of 1 s or more per scene and reported with start, end, texts and offsets:
  - `ragged_rows`: names of one size side by side whose baselines differ by more than 3.5 px and less than half their size, inside the same innermost card, or in no card and within 300 px of each other. Baselines are exact.
  - `ragged_columns`: the lines of one block, or the items stacked in one left-aligned column, whose shared edge differs by more than 3 px; for a left-aligned block centred under or over a mark, its axis more than 4 px off the mark's. Anchors are exact.
  - `crammed_lines`: a line stacked under another of its block with less than 7 px clear between their inks, the ink taken from the size and baseline (a CJK line 0.74 of its size above the baseline and 0.18 below, Latin 0.72 and 0.2).
  - `off_card_centre`: a name alone in a card no taller than three of its lines, more than 4 px off the card's centre or middle. The height limit leaves out headings at the top of tall cards.
  - `uneven_pitch`: three or more like marks on one centre line at uneven pitch while the names under them keep equal gaps, the trace of spacing by name width.
  - `touching_marks`: a name whose ink comes within 3 px of a mark's stroke, measured on the stroke's points rather than its bounding box.
- **What the gate refuses.** `FRAME_GATES` gains `ragged_rows`, `ragged_columns`, `crammed_lines` and `off_card_centre`, which rest on exact anchors, sizes and baselines. `uneven_pitch` and `touching_marks` depend on the estimated width of Latin text, which a real browser lays out differently, so they are reported in the gate record and judged by the reviewers.
- **Calibrated on the reviewed films.** Before release, the audit is run from source over the DDWG 1.2.0 and ETHOS v2 compositions as the reviewers saw them and as their typography repairs left them. The gated measures must find the reviewers' confirmed rows of their kinds and none of the automated findings the reviewers rejected, and must report nothing gated on the repaired compositions. The comparison is recorded with the release evidence; the engine's tests keep to the sample film and synthetic frames.
- **The sample film's checklist is aligned.** Its `text()` helper gains an `align` option, and the closing checklist sets each item left-aligned at one gap after its check, so the column has one left edge. `content/film.toml` raises `overall_minimum` and `dimension_minimum` to 95.
- **A version change rebuilds the editable install.** `pyproject.toml` declares `tool.uv.cache-keys = [{ file = "pyproject.toml" }, { file = "VERSION" }]`, so uv rebuilds an editable install when `VERSION` changes and its gate records name the engine that ran.
- **HyperFrames 0.9.8.** `RENDERER_VERSION` moves to 0.9.8, the newest stable release on 2026-11-03. It declares the same Chrome Headless Shell, 152.0.7977.30, and still pins undici 7.25.0, so the browser pin and the undici 7.30.1 override stay. Its fixes include preview and export frame alignment when a `set` fires inside a running tween and a wider `overlapping_gsap_tweens` lint, so the sample film's gate and render show whether the picture moved.

## Risks / Trade-offs

- [A gated measure refuses a layout a reviewer would accept] → Its limits are the reviewers' measured tolerances, and the calibration requires no rejected automated finding; a film with an intended offset sets the names apart in different cards or sizes.
- [The headless estimates differ from the browser] → The gated measures use exact anchors, sizes and baselines; the width-based measures only report.
- [A film adopting 0.7.0 meets new refusals] → ETHOS v2 and the essentials repair their typography before they adopt it; the DDWG 1.2.0 repair keeps 0.5.0 and is measured from source.
- [HyperFrames 0.9.8 changes frames] → The sample film's gate and render run on it before release, and each film keeps its reviewed renderer pin until it adopts 0.7.0 for its next render.

## Migration Plan

Implement and test the module and its gate; align the sample's checklist and raise its floors; add the cache keys; move the supply to HyperFrames 0.9.8; calibrate on the reviewed films; build and verify the sample film; record and date the release notes. A film adopting 0.7.0 raises its `filmkit` and `hyperframes` pins and passes `check-picture` with the new measures before it renders. To roll back, a film pins 0.6.0 again.
