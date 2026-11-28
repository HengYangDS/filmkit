---
subject: filmkit:film-layout
role: reference
state: active
relations:
  projects: ../openspec/specs/film-engine/spec.md
---

# A film's layout

Each film's repository holds its scripts, casts, pronunciations, pages, review policy and picture composition, and the engine reads them from the film it builds.

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

## The declaration

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

The fields and their refusals are specified in [`openspec/specs/`](../openspec/specs/): the film's parameters in `film-engine`, the other tables in the specifications of what reads them.
