## 1. Baseline

- [x] 1.1 Build the sample film on 0.23.0's supply in the lane before any pin moves; done when `mise run sample:build` passes and its artifacts and evidence are kept outside the lane. `mise run sample:build` passed on `bc96c78` on 18 November 2026 from 07:41:53 to 07:48:20, as one host ticket; both editions' gates pass; the build was cloned outside the lane.

## 2. Supply

- [x] 2.1 Pin `mlx-audio` 0.6.6 and `numpy` 2.5.5, refresh `uv.lock`, pin `hyperframes` 0.9.64 and `puppeteer-core` 25.18.1, refresh `package-lock.json`, set `RENDERER_VERSION` to 0.9.64, declare uv 0.13.9 and lock it with `mise lock`, and bring the README's and `NOTICE`'s version lines and the two comments that name mlx-audio 0.6.4 to the new versions; done when `mise run bootstrap` with its dependency checks passes and every command of `mise run check` passes, the suite with warnings as errors. On a clone of `bc96c78` with the moves, on 18 November 2026: the npm lock moved exactly hyperframes and puppeteer-core, 2 of 129, with no install script among them and no advisory by `npm audit`; the uv lock moved seven packages and added four, 59 in all, and PyPI lists no advisory for any of the eleven; `mise lock` changed only uv's entries and kept `lockfile_version = 3`; `mise run bootstrap` passed, and every command of `mise run check` passed with the suite run with warnings as errors (1,609 Python tests).
- [ ] 2.2 Build the sample film on the new supply and compare it with the baseline; done when `mise run sample:build` passes and the comparison reports, for each edition, each take's length and whether its samples are equal, and for each film its frame counts, identical frames and lowest PSNR.

## 3. Documents

- [ ] 3.1 Say in the README's "Whole endings" which mlx-audio release carries the upstream repair and what the sample film's takes showed, and record the moves in the Changelog; done when the Markdown check and the proof's prose gate pass.
- [ ] 3.2 Prepare 0.23.1 in `VERSION`, the Changelog's dated section and the README's install line; done when every command of `mise run check` passes on that head.
