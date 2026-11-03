# Proposal

## Why

On 2026-11-03 the owner asked that the text in every film be aligned, tidy and beautiful. The audits find collisions, clipping, faint and unplaced names, too many names or sizes, and a picture off the content centre, but nothing measures how text lines up. DDWG 1.2.0 passed its round-28 review with composition and typography at 95 or more in both editions, yet a headless measurement of its composition found that, in the Chinese scene 01, the film's name stands 6 px below the part titles of its row. The sample film's closing checklist centres each item beside a left-aligned column of checks: four items stand 54 px from their checks and the widest 26 px, so their left edges are ragged.

Two smaller gaps came out of the 0.6.0 release. The gate record's engine version reads the installed package's metadata, and uv does not rebuild an editable install when only `VERSION` changes, so the sample film's gate records after the bump still named 0.5.0. The owner also raised every review floor to 95 on 2026-11-03, but the sample film still declares 90.

## What Changes

- The frame audit measures the settled text of each voiced frame outside the head and caption bands: names of one size in one row on one baseline, the lines and items of one column on one edge, stacked lines with room between them, a name centred in its card, like marks at an even pitch and names clear of marks. Each defect that lasts 1 s or more is reported per scene with its span, texts and measured offsets. `check-picture` refuses the measures that rest on exact anchors, sizes and baselines and records the two that rest on estimated widths.
- Independent reviews of the DDWG 1.2.0 films and the ETHOS v2 composition, made on 2026-11-03, set the cases: the gated measures report none of the automated findings the reviewers rejected, and nothing on the compositions their typography repairs produced.
- The sample film's checklist stands left-aligned beside its checks, and its review floors rise to 95.
- `tool.uv.cache-keys` names `VERSION`, so an editable install is rebuilt when the version changes and its gate records name the engine that ran.
- The renderer moves to HyperFrames 0.9.8, the newest stable release, with the same Chrome Headless Shell.
- Record the changes under `Unreleased`, date them as `[0.7.0]`, and set `VERSION` and the README pin to 0.7.0.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `picture-gates`: the frame audit also measures text alignment, and `check-picture` refuses its findings.
- `sample-film`: the sample's checklist is aligned and its review floors are 95.

## Impact

The Change touches these files:

- `src/filmkit/picture/frame-audit.mjs`, a new text-layout module under `src/filmkit/picture/frame-audit/`, `src/filmkit/picture/frame-audit/report.mjs`, `src/filmkit/picture/gates.py` and their tests;
- `src/filmkit/picture/rendering.py`, `package.json`, `package-lock.json` and `NOTICE` for HyperFrames 0.9.8;
- the sample film's `examples/sample-film/picture/film.js` and `examples/sample-film/content/film.toml`;
- `pyproject.toml`, `README.md`, `CHANGELOG.md` and `VERSION`.

A film adopts 0.7.0 when it next renders. Its composition must then pass the text-layout findings before `render-picture` starts. ETHOS v2 and the DDWG essentials adopt it before their renders. The DDWG 1.2.0 repair keeps 0.5.0 and is measured with this audit from source. In the 0.x series this is a minor release.
