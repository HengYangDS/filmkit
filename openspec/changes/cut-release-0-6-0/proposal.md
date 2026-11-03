# Proposal

## Why

Producing the DDWG 1.2.0 repair and the ETHOS v2 and DDWG essentials films on 0.5.0 turned up three gaps that each film owner filled by hand. HyperFrames has also published 0.9.6.

The first gap is in the picture gates. The frame audit reports its findings but exits 0 with them, and nothing stops a render whose audits found a gated defect, so a film owner kept a scratch script that read every audit and refused gated findings before each render. The audit also samples balance at only two instants of each thought, while the reviewers measure it through all speech. The DDWG round-27 review found English 06.2 standing 13% to 15% off the content centre for 5.2 s and covering under a tenth of the content band, between the two instants the audit samples.

The second gap is in thought retakes. A retake binds the SHA-256 of its thought's display text, not of the speech it was auditioned on. A pronunciation change that alters only the spoken text therefore leaves the retake bound, and synthesis narrates a seed chosen for other speech. In the ETHOS v2 production such a stale run-on retake surfaced only in assembly, as "A run-on take does not end naturally at its cut".

The third gap is in the review configuration. Since 0.3.0 a review round's prompt context names the film's concept contract and the reading occurrence plans, but nothing requires a film's prompt template to cite them or its dimensions to score concept fidelity. The ETHOS v2 film copied its review configuration from the first edition, written before 0.3.0, and lacked all three until its owner added them on 2026-11-03.

## What Changes

- The frame audit measures the lit picture in every voiced frame and reports each run of 2 s or more of speech in which it stands more than 12% off the content centre or covers less than a tenth of the content band.
- `python -m filmkit.produce check-picture --language <code>` runs the frame, sync and motion audits of the edition's current composition and timeline, writes a gate record that binds them, and refuses any gated finding.
- `render-picture` refuses an edition unless a passing gate record binds its current composition, timeline and engine version.
- A thought retake also binds the SHA-256 of the spoken text it was auditioned on. Synthesis refuses a retake whose thought now speaks other text and names the thought, and binding an audition's proposal records both texts. A retake bound before 0.6.0 keeps its text-only binding.
- A review round refuses to write prompts for a film that declares a concept contract unless its prompt template cites `{concepts}` and `{readings}` and its dimensions include `concept_fidelity`, and names each omission. The sample film scores concept fidelity.
- Raise HyperFrames to 0.9.6, set `RENDERER_VERSION` to it, and run `check-picture` in the sample film's picture task before each render.
- Record the changes under `Unreleased`, date them as `[0.6.0]`, and set `VERSION` and the README pin to 0.6.0.

## Capabilities

### New Capabilities

- `picture-gates`: an edition's picture is audited through all its speech, and a render waits until no gated finding remains.
- `narration-retakes`: a thought retake binds the text and the speech it was auditioned on.

### Modified Capabilities

- `concept-contract`: a film that declares a contract has it cited and scored in every review round.

## Impact

The Change touches these files:

- `src/filmkit/picture/frame-audit.mjs`, `src/filmkit/picture/frame-audit/`, `src/filmkit/picture/rules/balance.mjs` and the frame audit's tests;
- a new `src/filmkit/picture/gates.py`, with `src/filmkit/produce.py`, `src/filmkit/picture/rendering.py`, `src/filmkit/picture/sync_audit.py`, `src/filmkit/production.py`, `src/filmkit/tools.py` and their tests;
- `src/filmkit/narration/retakes.py`, `src/filmkit/narration/audition.py` and their tests;
- `src/filmkit/review/round.py`, its tests and the sample film's `content/film.toml`;
- `package.json`, `package-lock.json` and the sample film's tasks in `.config/mise/config.toml`;
- `README.md`, `NOTICE`, `CHANGELOG.md` and `VERSION`.

A film adopts 0.6.0 when it next renders. Its picture task must then run `check-picture` before each render, its composition must pass the continuous balance and cover runs, and it must raise its own `hyperframes` pin. A film with a concept contract must also cite it and the reading occurrence plans in its prompt template and score `concept_fidelity`; DDWG 1.2.0, ETHOS v2 and the essentials already do. Films that keep 0.5.0, such as the DDWG 1.2.0 repair, are not affected. In the 0.x series this is a minor release.
