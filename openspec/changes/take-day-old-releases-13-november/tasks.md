## 1. Supply

- [x] 1.1 Narrate the sample film on the old locks and keep each edition's `narration-receipt.json`,
      `alignment.json`, `asr.json` and recordings aside with their sha256; done when both editions'
      files are kept. At 07:48 both editions narrated on the old locks; the six files are kept with
      their SHA-256, and the 28 recordings beside them.
- [x] 1.2 Move the uv and npm locks, the exact Python pins Pydantic and coverage, and the exact npm
      pins @puppeteer/browsers and prettier to the releases at least 24 hours old, keeping mlx-audio
      at 0.6.4; done when `mise run check:dependencies` and `mise run check` pass and OSV reports no
      advisory. At cutoff 2026-11-11T23:49:22Z uv moved 13 of 54 packages, the ten transitive moves
      plus Pydantic 2.14.3 with `pydantic-core` 2.50.4 and coverage 7.17.2, and npm moved 5 of 128
      transitively plus the two exact pins, leaving puppeteer-core its own @puppeteer/browsers
      3.2.6. OSV reports no advisory in either lock; `mise run bootstrap` with its
      `check:dependencies` and `mise run check` pass (Node tests, the Markdown check with prettier
      3.10.0 reformatting nothing, and 1,102 Python tests).
- [x] 1.3 Synthesize every take of the sample film again, narrate and build it; done when every
      take's `wav_sha256` and recording equal the baseline, `alignment.json` and `asr.json` are
      byte-identical and `mise run sample:build` passes. With the recordings moved aside, the eight
      takes were synthesized again under transformers 5.22.2, sentencepiece 0.2.3 and miniaudio
      1.73: `wav_sha256` is equal for 8 of 8 and all 28 recordings are byte-identical,
      `alignment.json` and `asr.json` are byte-identical in both editions, and the receipts differ
      only in each take's wall-clock `elapsed`. @puppeteer/browsers 3.2.7 installed
      chrome-headless-shell 152.0.7977.30 with its pinned SHA-256. `mise run sample:build` passed
      from 07:56:09 to 08:03:51, and both editions verify.
- [x] 1.4 Move `[supply] mise_version` to Mise 2026.11.7 and generate both pipelines again; done
      when `ethos lane project --check --json` reports both projections conforming. The check
      reports both conforming; only the workflow's Mise line changed. The official Mise 2026.11.7
      macOS archive, whose digest equals the API's and `SHASUMS256.txt`, lists `http:ethos`
      0.2.0-beta.9, node 26.13.0, python 3.12.16 and uv 0.13.7 under `MISE_LOCKED=1`, and the lock's
      bytes are unchanged. GitLab's macOS jobs run the Mise of their runner's guest, last observed
      at 2026.10.25 on 2026-11-02; its current version is not observed, because the job log does not
      print it.

## 2. Release

- [ ] 2.1 Prepare 0.21.1 in `VERSION`, the Changelog and the README's install line; done when the
      repository check passes.

## Deferred

- HyperFrames 0.9.35, puppeteer-core 25.17.0, GSAP 3.15.1 and the undici 8.x override stay pinned
  because they render the picture. Owner: the film session. Next action: open the picture-supply
  lane after DDWG round 39; that lane is accepted only by rendering the sample film and the three
  films' compositions before and after the move and comparing frames, and any changed pixel is
  explained or the move is held. Review date: 2026-11-14.

## Workflow follow-up

- Archive this Change and prove the archived head once.
- Publish the proposal, wait for GitHub's and GitLab's macOS review jobs, land and publish `dev` and
  `main`, and observe GitLab's protected macOS job.
- Tag v0.21.1 through `ethos land --release`, publish the tag and the two Releases, and retire the
  lane.
