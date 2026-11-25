# Film Kit

Film Kit rebuilds a narrated explainer film, an edition in each language the film declares, from the film's tracked sources. It narrates each script with a local speech model, assembles one soundtrack per edition, times the captions, draws the picture on a native canvas with and without its captions, packages a UHD master and a 1080p viewing film with FFmpeg, and verifies every film against the inputs it binds. After one supply step the build is offline.

The engine carries no film's content. Each film's repository holds its scripts, casts, pronunciations, pages, review policy and picture composition, and the engine reads them from the film it builds. The [DDWG introduction films](https://github.com/HengYangDS/data-department-work-guidelines-film) are built with it.

## Requirements

- An Apple-silicon Mac: the speech models run on MLX.
- [Mise](https://mise.jdx.dev), which installs the film's locked Node, CPython and uv, and [Vale](https://vale.sh) at the version the engine's record states; the register check refuses any other.
- FFmpeg with libx264, ExifTool and rsync 3, from Homebrew: `brew install ffmpeg exiftool rsync`.
- Network access for `filmkit supply` alone, which installs the browser build of the checks, the pinned CMUdict and the three speech models; `HF_ENDPOINT` names a Hugging Face mirror where the hub is unreachable.

## Installing the engine in a film

A film pins a release tag in its Python project and locks it:

```toml
[project]
dependencies = ["filmkit"]

[tool.uv.sources]
filmkit = { git = "https://github.com/HengYangDS/filmkit", tag = "v0.33.0" }
```

Its `package.json` declares the npm packages the engine runs, `@napi-rs/canvas`, `puppeteer-core` and `@puppeteer/browsers`, each at the version the engine's own `package.json` names under `dependencies`, the one source of those versions; `filmkit check` names a package the film holds at another version.

## A film's layout

A film is the folder that holds `content/film.toml`. The engine builds the film that `FILMKIT_ROOT` names or, when it is unset, the nearest film at or above the working directory.

| Path                                                        | What it holds                                                                            |
| ----------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `content/film.toml`                                         | The declaration: file prefix, editions, fonts, player colours, review policy and release |
| `content/<code>/film-script.json`                           | An edition's script                                                                      |
| `content/<code>/voice-reference.json`                       | The edition's cast: its reference recording, seeds and retakes                           |
| `content/<code>/pronunciation.json`                         | The edition's pronunciation                                                              |
| `picture/index.html`, `picture/film.js`, `picture/film.css` | The picture composition                                                                  |
| `release.json`                                              | The release record, which `filmkit release` writes                                       |
| `build/`                                                    | Everything the engine writes; keep it out of version control                             |

The declaration states the film's file prefix (`slug`), `author`, `delivery_folder`, `entry`, `source_manifest` and `credits_duration`, optionally a concept contract (`concepts`), and these tables:

| Table               | What it declares                                                                                                                                        |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `[editions.<code>]` | Each edition, in the film's order: the summary its player shows and its caption terms                                                                   |
| `[picture]`         | The fonts, the capture, the drafts, the geometry's row gaps, the editions rendered natively uncaptioned, and the wrapping, motion and detail exceptions |
| `[player]`          | The player page's colours                                                                                                                               |
| `[review]`          | The reviewer prompt, the floors, the scored dimensions, the clarity floors and their exceptions                                                         |
| `[pronunciation]`   | What every edition's pronunciation shares                                                                                                               |
| `[narration]`       | The narration's flow and terms and the owner's hearings                                                                                                 |
| `[captions]`        | The caption cues above the reading rate that the film keeps                                                                                             |
| `[register]`        | The forms the film keeps against the register style                                                                                                     |
| `[release]`         | The film-bound sources its release records                                                                                                              |

The fields and their refusals are specified in [`openspec/specs/`](openspec/specs/): the film's parameters in `film-engine`, the other tables in the specifications of what reads them.

## The verbs

Run in a film's folder. A refusal is one line on standard error, and the command exits 1. A command that cannot finish exits 2: a tool the host lacks is named in one line, any other fault shows its traceback.

| Verb                                                             | What it does                                                                                                                              |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `filmkit supply`                                                 | Installs and checks the pinned browser build, dictionary and speech models                                                                |
| `filmkit check [--read-only]`                                    | Asks every question of the film's sources at once; with `--read-only` it writes no file                                                   |
| `filmkit edit --edits FILE [--dry-run]`                          | Applies exact edits to the scripts and casts                                                                                              |
| `filmkit narrate [--edition CODE\|all] [--rounds N] [--takes N]` | Narrates each edition until every thought holds an accepted take; refused while the plan calls the narration not ready                    |
| `filmkit plan [TARGET...] [--json]`                              | Prints each node's state, reasons, host class, last seconds and readiness; writes nothing                                                 |
| `filmkit build [TARGET...]`                                      | Makes the targets fresh from the run records, `all` where none is named                                                                   |
| `filmkit verify [--technical-only] [--release]`                  | Hashes every recorded file and judges every node; then checks the delivered films, or compares the build with the release; writes nothing |
| `filmkit review prepare\|record\|set-aside`                      | Prepares a review round, records its reviews, or sets a reviewed build's packages aside                                                   |
| `filmkit deliver [--to DIR] [--dry-run]`                         | Fills the film's delivery folder once the records, the films and the reviews verify                                                       |
| `filmkit release [--replace] [--dry-run]`                        | Records the release of the delivered build from the sources `[release] sources` declares, and stages its assets                           |

A target is `<node>:<code>`, `<node>:all`, a group (`sound`, `audit`, `picture`, `package`) or `all`. Every node's run writes its run record below `build/evidence/records/`, which binds its inputs, outputs, tools and the declaration's tables it reads; `plan` and `build` judge each node by it.

A film is built by `filmkit check`, `filmkit narrate --edition all`, then `filmkit build all`. The narration is GPU work. `filmkit build all` first names the light build to run outside any host ticket, then each heavy invocation to run as the child of its own ticket; heavy nodes share one invocation once measured within 30 minutes. `filmkit verify --technical-only` then verifies the delivered films.

## A film's tests

A film's tests import only `filmkit.api` and one Node module, `filmkit.api.TEST_ENTRY` (`filmkit/picture/testing.mjs`), which opens the composition and the film's own modules headlessly.

## The sample film

`examples/sample-film` is a film of two editions whose text is written for the engine's tests. Its tasks run the verbs in its folder: `mise run sample:supply`, `sample:check`, `sample:narrate`, `sample:build` and `sample:verify`.

## Specifications and changes

What the engine guarantees is specified in [`openspec/specs/`](openspec/specs/); each change is proposed, designed and archived in [`openspec/changes/`](openspec/changes/). The [Changelog](CHANGELOG.md) states what each release changes and what a film changes to adopt it, and [CONTRIBUTING.md](CONTRIBUTING.md) how the engine is developed.
