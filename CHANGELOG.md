# Changelog

All notable changes to filmkit are recorded here. The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/), and releases follow [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html). Until 1.0.0 the declaration format may change in a minor release.

## [Unreleased]

## [0.10.0] - UNRELEASED

### Added

- `review.round prompts` writes a film's first production review: `--previous` is optional, and the template field `{previous_review}` cites the previous round's review files and findings, or states that no earlier production review exists. A template that cites `{previous}` and `{findings}` itself keeps working with `--previous` and is refused without it. `{clarity}` states the declared clarity floors. The sample film's prompt cites both.
- `review.round set-aside --unreviewed --consumer <dir>` sets aside a build nobody reviewed, such as a preview the owner watched, in the layout, manifest, move and readback of a reviewed round, bound by the consumer folder's byte-identical copies of each edition's two films and labelled `round-<n>` or by `--label`. Every set-aside takes `--language` for one edition, and `--without-picture` names the editions whose rendered picture stays; named alone it keeps both, as before.
- `review.measurement` records each edition's voice clarity, the median cepstral peak prominence over the loud frames of its soundtrack and of each segment's voice, computed as the reviewers' prompts state it, each value to 0.01 dB beside the floor a film declares for the edition in `[review] clarity_minimum_db`. On the six current soundtracks of the three films it keeps the reviewers' tool's frames and its medians, 17.35 to 19.64 dB, within 4e-15 dB. The sample film declares 18 and 17 dB.
- `check-picture` refuses an opening whose frames before the first word show the title the script declares for less than 1 s, in texts at 3:1 or more, and each run of 0.7 s or more in which a text holding a letter or a digit shows below 4.5:1 against the ground, its colour composited at its opacity. The frame audit writes a trace of every text of every frame, whatever its role, for both measures (`TEXTS`). On the current compositions of DDWG, ETHOS v2 and the essentials film both measures pass both editions, each opening on its title for 2.40–4.00 s; the ETHOS composition that lost its title signature (`28a177a`) shows none, and the DDWG composition before its legibility repair holds 143 Chinese and 145 English texts at rest below 4.5:1, among them every dimmed level its round-30 review measured.
- `produce preflight` reports at once every stale or missing input of an edition's render, by the owner that would refuse it later, and refuses while one remains: a stage that is not the current UHD picture, a tracked cover other than the one the stage paints, an earlier film package record, a draft still scan that is missing, failing or bound to another timeline or composition, a failing concept check, and a picture gate record that has not passed on the current inputs.

### Changed

- The still scan records the composition it judged beside the film and the timeline, and with `--language` judges the edition's draft against its timeline into `build/evidence/editions/<edition>/draft-stills.json`, which the pre-render check reads. A film's draft tooling moves to it; a record written by 0.9.0 binds no composition and is reported as stale.
- `filmkit.review.round` keeps its command and options; its prompts move to `filmkit.review.prompts`, its set-aside to `filmkit.review.set_aside` and the files every step reads to `filmkit.review.files`, so a script that imported them from `filmkit.review.round` imports them from their owners.

## [0.9.0] - 2026-11-04

### Added

- `check-picture` gates the sync audit's continuity. It refuses each seat, a mark that stands in speech for more than 0.6 s before a name is legible at it, and each run of a thought's speech longer than 1 s with no legible name, naming each with its thought and time. It lists each thought that keeps the previous picture for more than 1 s in the gate record without refusing it, since a deliberate index may stay while the first new name arrives.
- The seat check judges a dashed closed outline on its own where a link or a touch joins it to a larger mark: only a name within its reach, or a mark or text inside it, names it. The canvas stand-in records whether each stroke is dashed. The dashed box at the end of the link in ETHOS v2's 09.1, which stood 5–6 s before its seal and name, was judged with the card and the Agent the link joins, a mark that counted as named in every frame because its box held the Agent's inner dot.
- The sync audit lists the caption cues that labels repeat. `check-picture` refuses a cue of three or more words that one label legible during the cue holds exactly, in order, and records a cue at least 80% of whose words labels drawn during it repeat, and a cue that is itself one quotation, since the narration then reads out what the picture shows. The frame audit's `caption_echoes`, never gated, is retired.
- The frame audit reports `mixed_case`, the names of one set or of one row of one size, anywhere across the frame, that begin in both cases, and `check-picture` refuses it. A name counts once by its whole text; a CJK name, a quotation and a name whose first word holds a later capital are not judged. The frame audit reads a name's whole text, set and role from the record a composition publishes with each text.
- Packaging writes the edition's language into each film's chapter track in place, because FFmpeg tags that track English in every edition, and refuses a film any of whose tracks, the attached cover aside, carries another language.
- The concept check reads each edition's release synopsis, comment and description and the text its player page shows outside its scripts and styles, and refuses a counterexample there as in the narration.

### Changed

- A frame counts as named by what it holds only through a text, a named mark or, once it holds a mark, a name within its reach, so a pictogram drawn in a tool's frame no longer names the frame.
- The transcript's title and headings, `chapters.json`, the chapter metadata and the films' title, comment, description and synopsis tags set quotation marks as the captions do. On the current inputs of DDWG, ETHOS v2 and the essentials film, only ETHOS v2's English edition changes: the part title “Done” in the transcript and the player's transcript, the chapter title One requirement’s life in the transcript, the player's transcript and chapters, `chapters.json` and the chapter metadata, the part title of the same name in both transcripts, and the quotes of the synopsis tag. Each film's Chinese films change one more thing: their chapter track's language, English until now.
- The sample film tags each card with its kind of file or its step until the narration names it, so no card waits empty for its name.
- On the ETHOS v2 composition its round-4 review judged, the new gates refuse 11 seats in each edition, the English unnamed speech of 03.7 and 11 English runs of mixed case in 07–09, and record two held pictures in each edition and 41 Chinese and 23 English cues mostly drawn as labels, among them the three English cues that review named. Its seat repair leaves the dashed stand-in of 09.1 and the two tool frames of 03.6 in each edition, which the repair did not address. The concept check refuses the Chinese player of `411dd65^` for 模型提升 and passes every film's current inputs.
- The supply moves to ETHOS 0.2.0-alpha.29 and uv 0.13.7, and the CI projection to `jdx/mise-action` 5.2.6.

## [0.8.1] - 2026-11-04

### Fixed

- A Chinese caption line keeps the closing quotes and brackets that follow its last mark, as an English one already does, so no cue begins with one: in 。” the quote ends the line that 。 ends. A brief cue that ends in such a mark takes the same early start as one that ends at the mark, and a passage that ends in a closing quote no longer leaves the quote alone as a line its timing cannot place. A passage without such a mark is set as before.
- The display copy of cues, subtitles and transcripts sets each straight double quote as a typographic one: an opening quote at the start of the text or after a space, an opening bracket or a dash, and a closing quote elsewhere. A cue's text, its timing and the waveform do not change. A film refreshes its captions with `produce refresh-captions` to take both. On the current timelines this moves three closing quotes in the Chinese captions of ETHOS v2 and one in those of the essentials film, sets the quotes of twelve and four of their English cues, and changes no DDWG cue and no cue's timing.

## [0.8.0] - 2026-11-04

### Added

- The headless audits measure text with the film's own fonts. `filmkit.picture.metrics` reads each `@font-face` rule of `picture/film.css` whose source is one of the film's `picture.fonts` and records the advance width of every character each face maps, and the canvas stand-in measures a text as the sum of its characters' advances at its size plus its letter spacing. `check-picture` names the table to the frame and motion audits in `FILMKIT_TEXT_METRICS`, and `python -m filmkit.tools frame-audit` and `motion-audit` name it when the caller names none. A family the stylesheet does not declare and a character its face does not map keep the estimate, and every text's height keeps it.
- The frame audit measures balance as the reviews since DDWG round 29 do, in every frame it exercises: the box of every paint brighter than grey 60 at full size within rows 120–919, and its horizontal offset from x 960. `off_centre_builds` reports each run of 1.5 s or more in which the box stands more than 90 px off, and `off_centre_settled` each run of 2 s or more in which it stands more than 50 px off while its edges keep still, unless the picture then grows from it.

### Changed

- `check-picture` refuses `off_centre_builds`, and lists `off_centre_settled` in the gate record without refusing it, because whether a still state is a finished composition or a build-up held for its next part only the stage's intent tells.
- `check-picture` refuses `uneven_pitch` and `touching_marks` too. Measured with the film's widths, they report nothing on the repaired DDWG and ETHOS v2 compositions, and on the DDWG composition its third re-check judged they keep the touches the drafts showed real and drop the ones they showed clear.
- The gate record binds the SHA-256 of `picture/film.css` and of each declared font, and `render-picture` refuses a record measured with other fonts.
- The measures that already read text extents, such as the round-16 cover runs, read the film's widths too, so a film that passed 0.7.0 can be refused by this release before its next render.
- The engine renders with HyperFrames 0.9.9. The browser build stays Chrome Headless Shell 152.0.7977.30, and `package.json` keeps its `undici` override, because 0.9.9 still declares that build and pins `undici` 7.25.0. A new renderer can change the frames a film renders, so a film keeps its current filmkit pin until it produces, reviews and accepts an edition on a release that carries this one.
- The locks hold the newest releases their declared ranges admit; apart from HyperFrames, neither lock moves. OSV reports no advisory for any package either lock pins.

## [0.7.0] - 2026-11-04

### Added

- The frame audit measures how text lines up, from the exact anchors, sizes and baselines of each voiced frame's settled names and marks. `ragged_rows` reports names of one size side by side on baselines more than 3.5 px apart; `ragged_columns` reports the lines of a block or the items of a column off their shared edge or axis; `crammed_lines` reports stacked lines with less than 7 px between their inks; `off_card_centre` reports a name alone in a small card off its centre; `uneven_pitch` reports like marks at uneven pitch under names at equal gaps; and `touching_marks` reports a name within 3 px of a mark's stroke. Each lasts 1 s or more and is reported per scene with its span, texts and offsets.

### Changed

- `check-picture` refuses `ragged_rows`, `ragged_columns`, `crammed_lines` and `off_card_centre`, and records `uneven_pitch` and `touching_marks` in the gate record without refusing them, because they rest on the headless estimate of Latin text widths.
- The sample film's closing checklist stands left-aligned beside its checks, and its review floors are 95, as the owner set for every film on 2026-11-03.
- The engine renders with HyperFrames 0.9.8. The browser build stays Chrome Headless Shell 152.0.7977.30, and `package.json` keeps its `undici` override, because 0.9.8 still declares that build and pins `undici` 7.25.0. A new renderer can change the frames a film renders, so a film keeps its current filmkit pin until it produces, reviews and accepts an edition on a release that carries this one.
- The locks hold the newest releases their declared ranges admit; apart from HyperFrames, neither lock moves. OSV reports no advisory for any package either lock pins.

### Fixed

- An editable install is rebuilt when `VERSION` changes, so the gate records of a bumped engine name the version that ran: `pyproject.toml` declares `tool.uv.cache-keys` for itself and `VERSION`.

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

[Unreleased]: https://github.com/HengYangDS/filmkit/compare/v0.10.0...HEAD
[0.10.0]: https://github.com/HengYangDS/filmkit/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/HengYangDS/filmkit/compare/v0.8.1...v0.9.0
[0.8.1]: https://github.com/HengYangDS/filmkit/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/HengYangDS/filmkit/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/HengYangDS/filmkit/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/HengYangDS/filmkit/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/HengYangDS/filmkit/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/HengYangDS/filmkit/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/HengYangDS/filmkit/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/HengYangDS/filmkit/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/HengYangDS/filmkit/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/HengYangDS/filmkit/releases/tag/v0.1.0
