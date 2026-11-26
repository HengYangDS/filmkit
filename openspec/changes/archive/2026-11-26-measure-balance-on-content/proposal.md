## Why

The engine's balance rules measure the box of the lit picture, and a frame drawn across a stage centres that box whatever the stage holds. On the fused DDWG film's previews of chapters 5 to 9, measured on 25 November 2026, the box stood within 50 px in 99 to 100 % of frames while the content's mass, its rails left out, leaned left by a median of 58 to 158 px [S1, §14; S3]. At 19:41 the owner answered 「照建议改」 to the films session's recommendation that balance be measured on the content, "lit pixels with declared frame strokes excluded, mass and box", filmkit's balance rule the same way (D-69); his 「1 全按第 3 条改」 at 22:06 is read by the record as holding rule 3, its vertical limit included, to every stage (D-70) [S4].

## What Changes

- **A composition declares a frame stroke where it draws it**, by setting `window.__paintRole = "frame"` while it strokes the frame and `null` after, as it sets `window.__sceneId` around a scene; the audits record the role on each paint as they record the scene. A role of another value, or in effect while a fill, a text or `fillRect` paints, is an error of the frame audit. The renderer ignores the role.
- **Both measures leave declared frame strokes out**, and both weigh, by one rule, the paints of the scene being drawn, their runs keyed by that scene: titles, chapter cards and credits, which film.js draws outside every scene, and every caption are left out; a title drawn inside a scene is weighed with it. The reviewers' box, which the build-up, still and far runs read, keeps its paints as today but its declared frame strokes; the new vertical runs and the mass weigh scene paints alone. A film that declares no frame keeps every lit scene pixel in both. The frame report records each scene's declared frame strokes (`declared_frames`).
- **The mass audit.** `check-picture` gains a fourth audit, `mass-audit`, on the edition's uncaptioned stage: the renderer's native canvas, with the renderer's text renderer, draws the ground and the scene being drawn at 1920 × 1080 every 0.25 s, each frame is reduced to a 480 × 270 grey of full-range luma, the grey the prototype and the reviewers read, and the cells lit above 60 in the content band give the frame's mass centre. Per scene it reports each run of 1.5 s or more through which the mass stands more than 90 px off x 960 (`off_centre_mass`) and a summary (`mass_balance`).
- **The vertical.** The frame audit reports each still state of 2 s or more, its whole box still, whose centre stands more than 50 px above or below y 510 (`off_centre_vertical`).
- **The gate** refuses `off_centre_mass`, `off_centre_vertical` and a role error, records `mass_balance` and `declared_frames`, and binds the uncaptioned stage's record, so a render waits while the check is not fresh for that stage.
- **The content centre is stated once**, as `[960, 510]` in `rules/balance.mjs`.

Unchanged: the limits and gates of every box rule; every other measure of the frame audit, which keeps counting declared frame strokes and paints outside scenes as it does today (design decision 7); the renderer and every encoder. No picture, film or delivered byte changes; a picture that passed `check-picture` may now be refused by it.

Out of scope: the fused film's rules 1 and 2 (no camera move; rails only for ranks or rules), which are its composition's; recomposing any film but the sample; a declaration through which a film keeps a mass or vertical finding; and the `[960, 500]` centre of `off_balance`, whose move would change that rule's verdicts.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `picture-gates`: the declared frame stroke and what each measure does with it; the mass audit and its runs; the vertical still states; the gate on all three; `check-picture` reads and binds the uncaptioned stage.

## Impact

- **Engine:** `picture/headless-composition.mjs` (one function that records a paint's scene and role, which `picture/testing.mjs` also calls), `picture/frame-audit.mjs`, `frame-audit/composition.mjs` and `frame-audit/report.mjs` (the box without declared frame strokes, the role error, `declared_frames`, the vertical runs), `picture/rules/balance.mjs` (the centre, the mass and vertical runs), `picture/rules/ink.mjs` (the mass audit's lit grey), a new `picture/mass-audit.mjs`, `picture/native-canvas.mjs` (its stage opening exported, with the width to draw at), `tools.py` (the tool `mass-audit`), `picture/gates.py` (the audit, its gate, the stage's binding), `graph/chain.py` (the node `check-picture` reads the uncaptioned stage).
- **Tests:** new `tests/picture/frame-role.test.mjs`, `tests/picture/vertical-runs.test.mjs`, `tests/picture/mass-audit.test.mjs` and `tests/picture/test_mass_gates.py`; changes to `tests/picture/test_gates.py` and `tests/picture/gate_reports.py` (the fourth audit and its report), to the three fixtures that write passing gate records, `tests/picture/conftest.py`, `tests/picture/staged_inputs.py` and `tests/picture/test_uncaptioned.py` (the stage's binding), `tests/picture/rules/balance.test.mjs`, `tests/picture/native-canvas.test.mjs`, `tests/picture/sample-film.mjs` (the stage helper moved there), `tests/graph/test_nodes.py` and `tests/test_tools.py`. `tests/picture/frame-audit.test.mjs` and `tests/picture/headless-composition.test.mjs`, each within 39 effective lines of the 500 ceiling, are not changed (design decision 10).
- **Readers of the gate record:** `rendering.require_passing_gates` reads the record's bindings through `gates.current_bindings`, which gains the stage, so a render now refuses a stage staged again after its check; `review/motion.bound_report` reads the reports it read before. The new keys are otherwise additive.
- **Order of the build:** `check-picture` reads the output of `stage-picture-uncaptioned` and runs after it, and runs again when an input of that stage changes: the script, the assembly record, the soundtrack, the source manifest or the template.
- **Time:** one more audit, run beside the others, sampling every 0.25 s, at which 1.5 s and 2 s stay whole numbers of steps; its phase in the run record is held to the traced frame audit's phase of the same run (design decision 1). Measured alone on the fused film's preview of chapters 1 to 5 in Chinese (713 s): 14 to 15 s, against the frame audit's 21 to 29 s; not measured with the audits running together.
- **The sample film:** its picture is recomposed where it fails the new rules, most likely its opening scene (task 6.4), and its pictures' bytes change; it is the engine's test film, no film's source.
- **Films:** a film that adopts this release may be refused at `check-picture` where its content leans in mass or sits off y 510. The three released films cannot run this release's check before their December editions adopt an engine that stages them (design decision 9). Frozen films keep their pins and are not affected until they adopt.
- **Release:** a minor release, marked **Breaking:** in the CHANGELOG, after 0.34.2.

Owner: the engine's maintainer (the films session).

## Sources

Numbered as in the design.

- **[S1]** `build/runtime/work/fused-picture/design.md` beside the drafts, §14 with its decision block, rule 3 as corrected on 2026-11-26 at about 02:45 (its preimage `design.before-rule3-fix-2.md`).
- **[S2]** The engine at `5462d65` (tag `v0.34.2`), read on 2026-11-26, where every cited file stands as at `38d661c` (tag `v0.34.1`): the files the design cites; `openspec/specs/picture-gates/spec.md`; `CHANGELOG.md`.
- **[S3]** `build/runtime/work/fused-picture/balance79.json` and `fused-picture/tools/balance79.py`, the films session's measure of 2026-11-25, 19:25 to 19:37.
- **[S4]** `build/evidence/owner-words.md` in the engine's canonical checkout: D-69 (2026-11-25 19:41) and D-70 (22:06), with the record's readings, read on 2026-11-26.
