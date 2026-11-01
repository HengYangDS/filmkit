# Changelog

All notable changes to filmkit are recorded here. The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/), and releases follow [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html). Until 1.0.0 the declaration format may change in a minor release.

## [Unreleased]

### Added

- `CONTRIBUTING.md`: how to prepare the tools, change the engine in an ETHOS Work Lane, verify a change, commit, and cut and publish a release.

### Changed

- The repository runs ETHOS 0.2.0-alpha.25, whose 500-line ceiling bounds JavaScript too. The frame rules and the reviewers' measures that the geometry check and the frame audit share now live in `src/filmkit/picture/rules/`, each audit keeps its entry and holds its parts in a folder of its name, and the picture tests are split by subject. The tools keep their names, invocations and output.
- The engine renders with HyperFrames 0.8.225 and narrates with mlx-audio 0.6.3 and MLX 0.32.4, drives the browser with puppeteer-core 25.16.0 and @puppeteer/browsers 3.2.6, and builds with Node 26.13.0, uv 0.13.6 and Pydantic 2.14.2. The browser build stays Chrome Headless Shell 152.0.7977.30. A new renderer and speech engine change the frames and narration a film renders, so a film keeps its current filmkit pin until it produces, narrates, reviews and accepts an edition on this engine; moving that pin is not a routine update.

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

[Unreleased]: https://github.com/HengYangDS/filmkit/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/HengYangDS/filmkit/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/HengYangDS/filmkit/releases/tag/v0.1.0
