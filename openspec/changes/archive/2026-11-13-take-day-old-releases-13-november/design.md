## Context

See [proposal.md](proposal.md). filmkit narrates with Qwen3-TTS through mlx-audio, which reaches
transformers, sentencepiece and miniaudio. The sample film binds its takes to its casts' seeds, and
its narration receipts record each take's `wav_sha256`, so a reproduced narration is a byte-level
comparison, not a judgement. A take is named by the fingerprint of its request, which names no
library version, so narrating again over retained recordings reuses them instead of synthesizing
them.

## Goals / Non-Goals

**Goals:**

- Take every release at least 24 hours old that the locks and exact pins allow, except the narration
  engine and the picture renderer.
- Show that the sample film's takes, alignment and recognition are byte-identical before and after
  the moves.
- Run the hosted GitHub jobs with the latest stable Mise.
- Ship the moves as release 0.21.1.

**Non-Goals:**

- Moving mlx-audio to 0.6.5, whose decode changes need sample-film evaluation and a narration batch
  per film.
- Moving HyperFrames, puppeteer-core, GSAP or the undici override, which change the picture and move
  in a picture-supply release.
- The Mise that GitLab's macOS runner provides, which its guest owns.
- Changing any source, test, film or runner declaration.

## Decisions

- Measure the baseline in the lane on the old locks with `mise run sample:supply` once and
  `mise run sample:narrate`, and keep each edition's `narration-receipt.json`, `alignment.json` and
  `asr.json` and its recordings aside.
- After the moves, move the lane's recordings aside so that every take is synthesized again,
  narrate, and require every take's `wav_sha256` and recording equal to the baseline and
  `alignment.json` and `asr.json` byte-identical; a receipt's wall-clock `elapsed` is not compared.
  Then `mise run sample:build` proves the rest end to end.
- Take the exact npm pins @puppeteer/browsers, which only installs the pinned browser build, and
  prettier, which formats Markdown, after `mise run check` passes without reformatting; leave
  puppeteer-core its own @puppeteer/browsers.
- Move only `[supply] mise_version` and let the native projection regenerate the workflow.
- Version 0.21.1 is a patch: no declaration, command or output changes.

## Risks / Trade-offs

- [A moved dependency changes a take, a word time or a transcript] → The comparison fails; the lane
  stops, and the move that changed it is held back with its evidence.
- [Mise 2026.11.7 changes the hosted bootstrap] → The proposal's hosted runs qualify it before
  landing; restoring the 2026.10.25 parameter rolls it back.

## Migration Plan

Baseline, move the locks, compare, build the sample film, move the Mise parameter, run the gates,
prove the archived head, publish the proposal, land, publish `dev` and `main`, tag v0.21.1 and
publish its Releases. To roll back, revert the lane's commits; the previous locks return.
