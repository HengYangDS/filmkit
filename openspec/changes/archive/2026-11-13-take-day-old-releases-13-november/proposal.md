## Why

The owner's direction is that every supply chain moves to its latest stable release once it is at
least 24 hours old. At a 24-hour floor on 13 November 2026, filmkit's uv lock trails ten transitive
releases and its npm lock five, two exact Python pins and six exact npm pins trail their releases,
and the hosted jobs install Mise 2026.10.25 while 2026.11.7 is the latest stable release. Each film
adopts a filmkit release only at its next edition, so the moves ship as a release of their own,
0.21.1, together with the ETHOS 0.2.0-beta.9 binding that is already under Unreleased.

## What Changes

- Move the uv lock to annotated-doc 0.0.6, click 8.5.1, filelock 4.2.10, markdown-it-py 4.3.0,
  miniaudio 1.73, regex 2026.11.9, sentencepiece 0.2.3, transformers 5.22.2, typer 0.29.1 and
  typing-inspection 0.4.5, and the exact pins to Pydantic 2.14.3 and coverage 7.17.2.
- Move the npm lock to @hono/node-server 2.1.7, @swc/helpers 0.5.24, ansi-regex 6.6.0, hono 4.13.18
  and ws 8.22.2, and the exact pins to @puppeteer/browsers 3.2.7 and prettier 3.10.0.
- Run the hosted GitHub jobs with Mise 2026.11.7 and generate both pipelines again.
- Keep mlx-audio at 0.6.4: 0.6.5 changes the Qwen3-TTS decode rule and the decoder's attention
  window, which would change every bound take, so it needs a planned narration change of its own.
- Keep HyperFrames, puppeteer-core, GSAP and the undici override where they are: they render the
  picture, so they move in a picture-supply release that compares the films' frames.
- Cut 0.21.1: `VERSION`, the dated Changelog section and the README's install line.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The film kit, its commands and its outputs behave as before, so `.openspec.yaml` sets
`skip_specs: true`.

## Impact

`uv.lock`, `pyproject.toml`, `package-lock.json`, `package.json`, `.config/ci/verification.toml`,
the generated `.github/workflows/ci.yml`, `VERSION`, `CHANGELOG.md` and `README.md`. transformers,
sentencepiece and miniaudio sit on the narration path, so acceptance includes the sample film's
takes re-synthesized bit for bit. `tasks.md` is the sole progress ledger.
