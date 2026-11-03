# filmkit

filmkit rebuilds a narrated bilingual explainer film, a Chinese and an English edition, from the film's tracked sources. It narrates each edition's script with a local speech model, assembles one soundtrack per edition at a single program level, times the captions, renders the picture with HyperFrames, packages a UHD master and a captioned 1080p film with FFmpeg, and verifies every film against the inputs it binds. The build is offline after one supply step.

The engine carries no film's content. Each film's repository holds its scripts, casts, pronunciation contract, pages, review policy and picture composition, and the engine reads them from the film it builds. The [DDWG introduction films](https://github.com/HengYangDS/data-department-work-guidelines-film) are built with it.

## Requirements

- An Apple-silicon Mac: the speech models run on MLX, and the 1080p films are encoded with VideoToolbox.
- [Mise](https://mise.jdx.dev), which installs the film's locked Node, CPython and uv.
- FFmpeg with VideoToolbox, ExifTool and rsync 3, from Homebrew: `brew install ffmpeg exiftool rsync`.
- Network access for the supply step only. It installs the browser build that the renderer pins and the three speech models; `HF_ENDPOINT` names a Hugging Face mirror where the hub is unreachable.

## A film's layout

A film is the folder that holds `content/film.toml`. The engine builds the film that `FILMKIT_ROOT` names or, when it is unset, the nearest film at or above the working directory, and it finds the film's npm packages in the nearest `node_modules` at or above the film.

| Path                                                        | What it holds                                                                               |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `content/film.toml`                                         | The declaration: the film's file prefix, editions, fonts and review policy                  |
| `<sources>/film-script.json`                                | An edition's script, in the sources folder that the declaration names for it                |
| `<sources>/voice-reference.json`                            | The edition's cast: the narrator's reference recording, its text, the seeds and any retakes |
| `<sources>/narration.md`                                    | The edition's narration: its segment texts joined by blank lines                            |
| `<sources>/player.html`                                     | The template of the edition's player page                                                   |
| `picture/index.html`, `picture/film.js`, `picture/film.css` | The picture composition: the renderer document's template, its script and its style         |
| `content/release.json`                                      | The published release that `filmkit.delivery.reproduction` compares a rebuild with          |
| `build/`                                                    | Everything the engine writes; keep it out of version control                                |

Every other file is named by the declaration, a script or a cast: the entry page, the source manifest, the concept contract, the covers, the fonts, the pronunciation contract, the reviewer prompt, the listening-plan readings and the reference recordings.

## The declaration

| Field                            | Meaning                                                                                                                                                                |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `slug`                           | The prefix of every delivered file, in lowercase words joined by hyphens                                                                                               |
| `documents_folder`               | The folder in `~/Documents` that a delivery fills                                                                                                                      |
| `entry`                          | The template of the page that leads to each edition's player                                                                                                           |
| `source_manifest`                | The commit and digests of the document the film explains                                                                                                               |
| `concepts`                       | The concept contract (optional): what each concept the film names means in its source, and the words each edition uses for it                                          |
| `[editions.zh]`, `[editions.en]` | Each edition's `sources` folder, its 16:9 `cover` and the `caption_terms` that stay on one caption line                                                                |
| `[picture] fonts`                | The font files the picture stages below `fonts/`, in order                                                                                                             |
| `[review]`                       | The reviewer `prompt`, the listening-plan `readings` (optional), the verifier's `overall_minimum` and `dimension_minimum`, and the scored `dimensions` in record order |

Each script declares the edition's title, author, language, duration, frame rate, credits duration, chapters, release metadata, pause policy and pronunciation contract, and its segments, each split into utterance groups that end at sentence punctuation. Both editions declare the same duration, author and chapter count, at 60 fps. The engine refuses a declaration or a script that differs from this contract before any work, naming each failing field. [`examples/sample-film`](examples/sample-film) is a complete film to follow.

A new film names its covers before they exist. It narrates and stages its picture without them; `filmkit.tools player-check cover <stage> <cover> <painting>` paints each edition's cover from the staged picture, reports a painting with no tracked cover as uncompared and fails, and the painting is then tracked as the cover. Packaging refuses an edition whose cover is missing, naming its field.

## Concepts and readings

A film can make its words checkable before anything is narrated. Narration runs both checks first, including a dry run, and refuses on either, naming every failure.

- **Concepts.** The concept contract that `concepts` names is a TOML file of `[[concept]]` entries. Each has an `id`, the source `term`, its `essence` in one sentence, a `source` with the `path` of a document the source manifest pins and a `quote` from it, and a `zh` and an `en` table with the edition's `rendering`, the other `forms` the narration may use and the counterexamples to `avoid`. A segment lists the ids it states in `concepts`, the same in both editions, and must say each by its rendering or a form. No counterexample may appear in the narration, the titles, the caption terms or the text files below `picture/`. With `FILM_SOURCE_CHECKOUT` naming a clone of the source repository, every quotation must be in its document at the pinned commit. `python -m filmkit.concepts` runs the check alone.
- **Readings.** A pronunciation contract of `schema_version` 2 must declare, as `contextual-mandarin-word` targets, the reading of every Chinese character on the engine's watch list wherever the narration says it. A character that reads differently in ordinary words needs a declared word of two or more characters around each occurrence; one that reads differently only inside known words may be declared alone. Each declared reading must be a dictionary reading per character, or after a word's first character that reading in the neutral tone; where the dictionary reads an occurrence otherwise in context, the word records why in `dictionary_disagreement`. Declarations the narration no longer says are refused. Every Latin word in the Chinese narration and every English word with two or more capitals needs a declared spoken form. `python -m filmkit.narration.readings` runs the check alone and writes each edition's occurrence plan to `build/evidence/readings/`, with the text around every occurrence, which the reviewer prompt names beside the contract. With `--propose` it instead writes `build/evidence/readings/zh-proposals.json`: a proposed word and the dictionary's reading for each occurrence nothing declares yet, for the author to correct and declare.

A review round's prompts name the concept contract and the occurrence plans. For a film that declares a contract, `filmkit.review.round prompts` refuses to write them unless the reviewer prompt cites `{concepts}` and `{readings}` and the review's dimensions include `concept_fidelity`, and names each omission.

A film that declares neither, or keeps a version 1 pronunciation contract, narrates as before.

## The picture gate

`filmkit.produce check-picture --language zh|en` audits an edition's current picture before it renders: the frame audit over every frame of its timeline at one thirtieth of a second, the sync audit of its labels against their words, and the motion audit at 30 frames per second. Besides layout, legibility and collisions, the frame audit follows the lit picture through all speech and reports each stretch of 2 s or more in which it stands more than 12% off the content centre or covers less than a tenth of the content band. The command writes `build/evidence/editions/<edition>/picture-gates.json`, which binds the composition, the timeline and the engine version and lists every gated finding, and refuses while one remains. `render-picture` refuses an edition without a passing record for its current composition, timeline and engine version, so a film's picture task runs `check-picture` before each render.

## Installing the engine in a film

A film pins a release tag in its Python project and locks it:

```toml
[project]
dependencies = ["filmkit"]

[tool.uv.sources]
filmkit = { git = "https://github.com/HengYangDS/filmkit", tag = "v0.6.0" }
```

Its `package.json` declares the npm packages the engine runs, at these versions: `hyperframes` 0.9.8, the renderer, which the engine checks before it stages, renders or runs a tool; `gsap` 3.15.0, which each staged document loads; and `puppeteer-core` 25.16.0 and `@puppeteer/browsers` 3.2.6, which drive and install the browser build. It also overrides `undici` to 7.30.1, because HyperFrames 0.9.8 pins 7.25.0, which known advisories affect.

## Commands

Run each command at the film's root, for example from a Mise task, with `uv run python -m <command>`:

| Command                                                | What it does                                                                                                                                                                       |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `filmkit.supply`                                       | Installs the pinned browser build and speech models below `build/runtime/tool-cache/`                                                                                              |
| `filmkit.narration.narrate --language zh\|en`          | Narrates an edition from its cast's seeds, then aligns and transcribes it                                                                                                          |
| `filmkit.narration.audition audition\|apply`           | Auditions other seeds or run-on takes of chosen thoughts, then binds the chosen ones into the cast's retakes                                                                       |
| `filmkit.concepts`                                     | Checks the film's words against its concept contract                                                                                                                               |
| `filmkit.narration.readings [--language zh\|en]`       | Checks every declared reading and name, and writes the occurrence plans; `--propose` proposes Chinese declarations                                                                 |
| `filmkit.produce <action> --language zh\|en`           | Runs one production action: `select`, `assemble`, `refresh-captions`, `stage-picture`, `check-picture`, `render-picture`, `validate-picture`, `package-metadata` or `package-film` |
| `filmkit.tools <tool> [arguments]`                     | Runs a Node tool with the film's npm packages: `geometry-check`, `frame-audit`, `motion-audit` or `player-check`                                                                   |
| `filmkit.delivery.verification --language zh\|en\|all` | Verifies the films and every input they bind; `--technical-only` leaves out the review                                                                                             |
| `filmkit.delivery.documents_folder`                    | Delivers the reviewed editions to the film's Documents folder with rsync and reads them back                                                                                       |
| `filmkit.delivery.reproduction`                        | Compares a rebuild with the published release                                                                                                                                      |
| `filmkit.review.round <step>`                          | Prepares and records an independent review round                                                                                                                                   |

## Whole endings

The assembly refuses a thought whose take ends inside its last syllable. In-context narration with mlx-audio 0.6.4 can produce such takes: its decode counts a frame as valid only when the frame's first codebook id is above 0, while the reference tokenizer pads with −1 and counts every id above it. The reference's codes are decoded with the take's, so each frame with id 0 in either removes 80 ms from the end of the take, and a reference whose pauses encode to id 0 shortens every take narrated from it. The fix is proposed upstream as [Blaizzy/mlx-audio#1116](https://github.com/Blaizzy/mlx-audio/pull/1116).

Until a release carries it, `filmkit.narration.audition` keeps endings whole. Its targets file names each thought the assembly refused and a phrase the take must contain. An audition narrates other seeds of each target and proposes a take that still ends naturally; a run-on target is narrated on into the next thought and cut in the quiet between, so the trim falls on the words cut away. `apply` binds the proposals into the cast's retakes, and narration then records only the retaken thoughts again. A retake that `apply` binds keeps the SHA-256 of the spoken text its audition narrated, and narration refuses one whose thought now speaks other text, so a changed reading is auditioned again instead of narrated from a seed chosen for other speech.

## The sample film

`examples/sample-film` is a one-minute bilingual film that the engine's tests load and that builds end to end:

```sh
mise run bootstrap
mise run sample:supply
mise run sample:build
```

The build writes only below `examples/sample-film/build/`. Its text is written for this repository and is no film's source.

Packaging refuses to extend films bound to other inputs. A film sets a reviewed round's films aside with `filmkit.review.round set-aside`; to rebuild the unreviewed sample after a change, first delete each edition's two films below `build/artifacts/film/<edition>/` and its `build/evidence/editions/<edition>/film-package.json`.

## Development

`mise run bootstrap` prepares the locked Python and npm environments, and `mise run check` runs the Node and Python suites and the Markdown format check. The repository is governed by [ETHOS](https://github.com/HengYangDS/ethos); its portable proof runs in GitHub Actions and GitLab CI, and the sample film's build stays a local acceptance because it needs the speech models and the browser build. [CONTRIBUTING.md](CONTRIBUTING.md) explains how to change, verify and release the engine, and [CHANGELOG.md](CHANGELOG.md) records each release.

## License

The code is licensed under the [MIT License](LICENSE). [NOTICE](NOTICE) names the sample film's reference recordings, under CC BY 4.0, its fonts, under the SIL Open Font License, and the third-party software and models that a build installs.
