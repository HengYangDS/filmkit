## 1. Baseline

- [x] 1.1 Build the sample film at v0.22.0 in the lane before any pin moves; done when
      `mise run sample:build` passes and its films are kept outside the lane for the comparison.
      `mise run sample:build` at bcf2f9f passed from 02:32:52 to 02:48:57; both editions verify
      pass; its 12 films were cloned outside the lane and set aside in the lane with
      `filmkit.review.round set-aside --unreviewed`.

## 2. Supply

- [x] 2.1 Pin `hyperframes` 0.9.46, `puppeteer-core` 25.17.0 and `gsap` 3.15.1, override `undici` to
      7.30.2 and refresh `package-lock.json`; done when `npm ls --all --include=dev` reports no
      problem, the lock moves only these packages, their dependencies and postcss, and OSV reports
      no advisory in it. The npm lock moved exactly devtools-protocol, gsap 3.15.1, hyperframes
      0.9.46, postcss 8.5.33, puppeteer-core 25.17.0, undici 7.30.2 and webdriver-bidi-protocol
      1.0.2, and dropped puppeteer-core's nested @puppeteer/browsers 3.2.6; 127 packages; OSV
      reports no advisory; `npm ls --all --include=dev` reports no problem.
- [x] 2.2 Set `RENDERER_VERSION` to 0.9.46 and the GSAP test to 3.15.1, keeping `BROWSER` and its
      digest; done when `mise run check` passes. HyperFrames 0.9.46 declares `CHROME_VERSION`
      152.0.7977.30 and `MACOS_12_CHROME_VERSION` 150.0.7871.124, as 0.9.9 did; `mise run check`
      passes: 189 Node tests, the Markdown check and 1138 Python tests.
- [x] 2.3 Build the sample film on the new inputs and compare it with the baseline; done when
      `mise run sample:build` passes and the comparison reports, for each film, its frame counts,
      differing frames and largest sampled channel difference. `mise run sample:build` on the new
      inputs passed; Built at v0.22.0 and again on these inputs, the sample film's twelve films
      decode to the same frames, 43,200 of 43,200, and the eight with sound to the same audio; the
      files differ only in the renderer version and the creation time their containers record. The
      comparison is `compare-films.py` over both builds' films.

## 3. Release

- [x] 3.1 Bring the README and `NOTICE` to the new versions, with `@puppeteer/browsers` 3.2.7, and
      prepare 0.22.1 in `VERSION`, the Changelog and the README's install line; done when
      `mise run check` passes. `VERSION` reads 0.22.1; the Changelog has the dated 0.22.1 section
      and links 0.21.3 to 0.22.1; the README's install line names `v0.22.1`; README and `NOTICE`
      name the new versions; `mise run check` passes: 189 Node tests and 1138 Python tests.

## Workflow follow-up

- Archive this Change and prove the archived head once.
- Publish the proposal, wait for GitHub's and GitLab's macOS review jobs, and land only after the
  film session has read the comparison; publish `dev` and `main` and observe GitLab's protected
  macOS job.
- Tag v0.22.1 through `ethos land --release`, publish the tag and the two Releases, read them back,
  and retire the lane.
