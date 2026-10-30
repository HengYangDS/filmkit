# filmkit

filmkit rebuilds a narrated bilingual explainer film, a Chinese and an English edition, from the film's tracked sources. It narrates each edition's script with a local speech model, assembles one soundtrack per edition at a single program level, times the captions, renders the picture with HyperFrames, packages a UHD master and a captioned 1080p film with FFmpeg, and verifies every film against the inputs it binds. The build is offline after one supply step.

The engine carries no film's content. Each film's repository holds its scripts, casts, pronunciation contract, pages, review policy and picture composition, and the engine reads them from the film it builds. The [DDWG introduction films](https://github.com/HengYangDS/ddwg-film) are built with it.

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

Every other file is named by the declaration, a script or a cast: the entry page, the source manifest, the covers, the fonts, the pronunciation contract, the reviewer prompt, the listening-plan readings and the reference recordings.

## The declaration

| Field                            | Meaning                                                                                                                                                                |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `slug`                           | The prefix of every delivered file, in lowercase words joined by hyphens                                                                                               |
| `documents_folder`               | The folder in `~/Documents` that a delivery fills                                                                                                                      |
| `entry`                          | The template of the page that leads to each edition's player                                                                                                           |
| `source_manifest`                | The commit and digests of the document the film explains                                                                                                               |
| `[editions.zh]`, `[editions.en]` | Each edition's `sources` folder, its 16:9 `cover` and the `caption_terms` that stay on one caption line                                                                |
| `[picture] fonts`                | The font files the picture stages below `fonts/`, in order                                                                                                             |
| `[review]`                       | The reviewer `prompt`, the listening-plan `readings` (optional), the verifier's `overall_minimum` and `dimension_minimum`, and the scored `dimensions` in record order |

Each script declares the edition's title, author, language, duration, frame rate, credits duration, chapters, release metadata, pause policy and pronunciation contract, and its segments, each split into utterance groups that end at sentence punctuation. Both editions declare the same duration, author and chapter count, at 60 fps. The engine refuses a declaration or a script that differs from this contract before any work, naming each failing field. [`examples/sample-film`](examples/sample-film) is a complete film to follow.

## Installing the engine in a film

A film pins a release tag in its Python project and locks it:

```toml
[project]
dependencies = ["filmkit"]

[tool.uv.sources]
filmkit = { git = "https://github.com/HengYangDS/filmkit", tag = "v0.1.0" }
```

Its `package.json` declares the npm packages the engine runs, at these versions: `hyperframes` 0.8.150, the renderer, which the engine checks before it stages, renders or runs a tool; `gsap` 3.15.0, which each staged document loads; and `puppeteer-core` 25.12.0 and `@puppeteer/browsers` 3.2.3, which drive and install the browser build.

## Commands

Run each command at the film's root, for example from a Mise task, with `uv run python -m <command>`:

| Command                                                | What it does                                                                                                                                                      |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `filmkit.supply`                                       | Installs the pinned browser build and speech models below `build/runtime/tool-cache/`                                                                             |
| `filmkit.narration.narrate --language zh\|en`          | Narrates an edition from its cast's seeds, then aligns and transcribes it                                                                                         |
| `filmkit.produce <action> --language zh\|en`           | Runs one production action: `select`, `assemble`, `refresh-captions`, `stage-picture`, `render-picture`, `validate-picture`, `package-metadata` or `package-film` |
| `filmkit.tools <tool> [arguments]`                     | Runs a Node tool with the film's npm packages: `geometry-check`, `frame-audit`, `motion-audit` or `player-check`                                                  |
| `filmkit.delivery.verification --language zh\|en\|all` | Verifies the films and every input they bind; `--technical-only` leaves out the review                                                                            |
| `filmkit.delivery.documents_folder`                    | Delivers the reviewed editions to the film's Documents folder with rsync and reads them back                                                                      |
| `filmkit.delivery.reproduction`                        | Compares a rebuild with the published release                                                                                                                     |
| `filmkit.review.round <step>`                          | Prepares and records an independent review round                                                                                                                  |

## The sample film

`examples/sample-film` is a one-minute bilingual film that the engine's tests load and that builds end to end:

```sh
mise run bootstrap
mise run sample:supply
mise run sample:build
```

The build writes only below `examples/sample-film/build/`. Its text is written for this repository and is no film's source.

## Development

`mise run bootstrap` prepares the locked Python and npm environments, and `mise run check` runs the Node and Python suites and the Markdown format check. The repository is governed by [ETHOS](https://github.com/HengYangDS/ethos); its portable proof runs in GitHub Actions and GitLab CI, and the sample film's build stays a local acceptance because it needs the speech models and the browser build. [CHANGELOG.md](CHANGELOG.md) records each release.

## License

The code is licensed under the [MIT License](LICENSE). [NOTICE](NOTICE) names the sample film's reference recordings, under CC BY 4.0, its fonts, under the SIL Open Font License, and the third-party software and models that a build installs.
