---
subject: filmkit:verbs
role: reference
state: active
relations:
  projects: ../openspec/specs/film-engine/spec.md
---

# The verbs

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

## Targets and run records

A target is `<node>:<code>`, `<node>:all`, a group (`sound`, `audit`, `picture`, `package`) or `all`. Every node's run writes its run record below `build/evidence/records/`, which binds its inputs, outputs, tools and the declaration's tables it reads; `plan` and `build` judge each node by it.
