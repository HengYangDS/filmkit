# Changelog

All notable changes to filmkit are recorded here. The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/), and releases follow [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html). Until 1.0.0 the declaration format may change in a minor release.

## [Unreleased]

## [0.6.0] - 2026-11-03

### Added

- `python -m filmkit.produce check-picture --language zh|en` runs the frame, sync and motion audits of an edition's current composition and timeline. It writes `build/evidence/editions/<edition>/picture-gates.json`, which binds the composition, the timeline and the engine version and lists every gated finding, and refuses while one remains.
- The frame audit follows the lit picture through all speech. `off_centre_runs` and `thin_runs` report each run of 2 s or more of one scene's speech in which the picture stands more than 12% off the content centre or covers less than a tenth of the content band, with its start, end and worst value; both are gated.

### Changed

- `render-picture` refuses an edition without a passing gate record for its current composition, timeline and engine version. A film's picture task runs `check-picture` before each render, as the sample film's now does.
- The sample film's composition is reworked to pass the gate: each scene stands centred from its first word, names each thing on its words and changes within 3.5 s.
- A thought retake that `filmkit.narration.audition apply` binds records `spoken_sha256`, the SHA-256 of the spoken text its audition narrated. Binding refuses a proposal without spoken text or with speech its thought no longer says, and narration refuses a retake whose thought now speaks other text, naming the thought. A retake bound before 0.6.0 keeps its text-only binding.
- A review round refuses to write prompts for a film that declares a concept contract unless its reviewer prompt cites `{concepts}` and `{readings}` and its dimensions include `concept_fidelity`, and names each omission. The sample film scores concept fidelity.
- The engine renders with HyperFrames 0.9.6. The browser build stays Chrome Headless Shell 152.0.7977.30, and `package.json` keeps its `undici` override, because 0.9.6 still declares that build and pins `undici` 7.25.0. A new renderer can change the frames a film renders, so a film keeps its current filmkit pin until it produces, reviews and accepts an edition on a release that carries this one.
- The locks hold the newest releases their declared ranges admit; apart from HyperFrames, neither lock moves. OSV reports no advisory for any package either lock pins.

## [0.5.0] - 2026-11-03

### Added

- The README's "Whole endings" section explains why in-context takes from mlx-audio 0.6.4 can end inside their last syllable, how `filmkit.narration.audition` keeps their endings whole, and the upstream fix, Blaizzy/mlx-audio#1116. The command table lists `filmkit.narration.audition`.

### Changed

- The repository runs ETHOS 0.2.0-alpha.28.
- The engine renders with HyperFrames 0.9.5. The browser build stays Chrome Headless Shell 152.0.7977.30, and `package.json` keeps its `undici` override, because 0.9.5 still declares that build and pins `undici` 7.25.0. A new renderer can change the frames a film renders, so a film keeps its current filmkit pin until it produces, reviews and accepts an edition on a release that carries this one.
- The speech engine is mlx-audio 0.6.4. Its in-context path without streaming narrates the same takes as 0.6.3 from the same seeds, so a film that moves to it keeps its accepted takes.
- The locks hold the newest releases their declared ranges admit: `filelock` 4.2.7 in `uv.lock` and `semver` 7.8.6 in `package-lock.json`. OSV reports no advisory for any package either lock pins.

### Fixed

- The reviewer prompt names a coda, an inner pause cap or a thought boundary ratio that a script does not declare as "none declared", instead of raising `KeyError`.

## [0.4.0] - 2026-11-02

### Changed

- The repository runs ETHOS 0.2.0-alpha.27, and its CI workflow uses `jdx/mise-action` 5.2.5.
- The engine renders with HyperFrames 0.9.3. The browser build stays Chrome Headless Shell 152.0.7977.30, and `package.json` keeps its `undici` override, because 0.9.3 still pins 7.25.0. A new renderer can change the frames a film renders, so a film keeps its current filmkit pin until it produces, reviews and accepts an edition on a release that carries this one.
- The locks hold the newest releases their declared ranges admit: anyio 4.16.0 in `uv.lock`, and @hono/node-server 2.1.6, ansi-regex 6.5.0, hono 4.13.16, nanoid 3.3.20, postcss 8.5.32, tslib 2.9.1 and ws 8.22.1 in `package-lock.json`. OSV reports no advisory for any package either lock pins.

## [0.3.0] - 2026-11-02

### Added

- A concept contract: `concepts` in the declaration names a TOML file that states what each concept a film names means in its pinned source, quoting the passage, and which words each edition uses for it. `python -m filmkit.concepts` checks that each segment says the concepts it declares, the same in both editions, by their approved words; that no counterexample appears in the narration, titles, caption terms or picture sources; and, with a source clone, that each quotation is in its document at the pinned commit.
- A readings check for pronunciation contracts of schema version 2: every Chinese character on the engine's watch list must have a declared reading wherever the narration says it, each declared reading must be a dictionary reading, or in the neutral tone after a word's first character, and a reading the dictionary contradicts in context needs a recorded reason. Every name in either edition needs a declared spoken form. `python -m filmkit.narration.readings` writes each edition's occurrence plan for review, and with `--propose` the dictionary's word and reading for each occurrence nothing declares yet. The dictionary is `pypinyin` 0.55.0, a new dependency.
- The reviewer prompt context names the concept contract as `concepts` and the occurrence plans as `readings`.

### Changed

- Narration runs the concept and readings checks before any speech model loads, including a dry run, and refuses on either. A film that declares no concept contract and keeps a version 1 pronunciation contract narrates as before.

## [0.2.0] - 2026-11-01

### Added

- `CONTRIBUTING.md`: how to prepare the tools, change the engine in an ETHOS Work Lane, verify a change, commit, and cut and publish a release.

### Changed

- **Breaking:** the assembly refuses an edition whose bound thought take ends abruptly, naming every such thought, unless the film declares a release for that thought's join in `released_tail_seconds`. It judges each take by the criterion that auditions and the review already use. Before, it faded such a take over 60 ms where the silence after it began, which hid the cut but swallowed the last syllable. A film whose takes all end naturally assembles the same soundtrack as before.
- The repository runs ETHOS 0.2.0-alpha.25, whose 500-line ceiling bounds JavaScript too. The frame rules and the reviewers' measures that the geometry check and the frame audit share now live in `src/filmkit/picture/rules/`, each audit keeps its entry and holds its parts in a folder of its name, and the picture tests are split by subject. The tools keep their names, invocations and output.
- The engine renders with HyperFrames 0.8.225 and narrates with mlx-audio 0.6.3 and MLX 0.32.4, drives the browser with puppeteer-core 25.16.0 and @puppeteer/browsers 3.2.6, and builds with Node 26.13.0, uv 0.13.6 and Pydantic 2.14.2. The browser build stays Chrome Headless Shell 152.0.7977.30. A new renderer and speech engine change the frames and narration a film renders, so a film keeps its current filmkit pin until it produces, narrates, reviews and accepts an edition on this engine; moving that pin is not a routine update.

### Fixed

- The review's measure of delivered endings takes each thought's stop at the first digital silence after its last word begins, not after the word's aligned end, which the aligner can place after the voice has stopped, and judges a released thought on the 20 ms before the samples the assembly released. It had counted thoughts whose voice was cut and then faded as natural endings.
- A thought that ends in Latin text without a space, such as an English thought that ends its segment, is auditioned as a run-on that reads into the next thought after a word space, so the two thoughts' words stay apart.

### Security

- `package.json` overrides `undici` to 7.30.1. HyperFrames 0.8.225 pins 7.25.0, which 29 advisories affect, among them TLS certificate validation bypasses (GHSA-vmh5-mc38-953g, GHSA-w293-vg96-wgc3). The new browser driver also moves `zod` from 3.25.76 to 4.6.7, outside GHSA-mrhx-c7xc-m3w5.

## [0.1.1] - 2026-10-31

### Fixed

- A new film can name its covers before it paints them: the declaration loads without them, packaging refuses an edition whose cover is missing and names its field, and the cover check writes a painting that has no tracked cover yet and reports it as uncompared.

## [0.1.0] - 2026-10-30

### Added

- The engine that rebuilt the DDWG introduction films, from [ddwg-film](https://github.com/HengYangDS/ddwg-film) at `37549a9`: narration with a local speech model, soundtrack assembly, captions, picture staging and rendering with HyperFrames 0.8.150, packaging, verification, delivery and independent review rounds.
- The engine finds the film it builds from `FILMKIT_ROOT` or the working directory, and its npm packages in the nearest `node_modules`. It takes every film-specific value from `content/film.toml` and the files it names, now including the fonts the picture stages and the listening plan's readings, and each script names its pronunciation contract.
- `python -m filmkit.tools` runs the Node tools from a copy below the film with the film's npm packages. Staging, rendering and every tool refuse a renderer other than HyperFrames 0.8.150.
- A one-minute bilingual sample film that the tests load and the `sample:` Mise tasks build end to end.
- ETHOS governance, with the portable proof projected into GitHub Actions and GitLab CI.
- The MIT License for the code, with the sample film's recordings and fonts and the third-party software in `NOTICE`.

[Unreleased]: https://github.com/HengYangDS/filmkit/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/HengYangDS/filmkit/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/HengYangDS/filmkit/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/HengYangDS/filmkit/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/HengYangDS/filmkit/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/HengYangDS/filmkit/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/HengYangDS/filmkit/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/HengYangDS/filmkit/releases/tag/v0.1.0
