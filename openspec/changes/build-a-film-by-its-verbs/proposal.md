## Why

The engine exposes stages, not a build. A film reaches it through 53 entry points (26 modules with a `main`, the 18 actions of `filmkit.produce` and the 9 Node tools of `filmkit.tools`) [S1, §3.3], and each film states the build order as task lines that `filmkit.adoption` polices [S1, §2.2]. The films session rebuilt the missing build outside the engine: 41 of the kit's scripts order builds, bind readiness and pin the engine [S1, §3.4]. The derivation makes R2b "the core contradiction and the condition for deleting the kit" [S1, §5.7].

R2a (`record-every-run`, 0.32.0) gave the engine what that release stands on: one record of every run, the node table as data, the plan and a records-only verification [S4]. This Change is the first half of the derivation's release R2b, "The verbs and the retirements" [S1, §5.7, row R2b]: the film is built, checked, verified, reviewed, delivered and released through the verbs of §5.3, and the commands those verbs replace retire. The owner adopted the derivation's architecture and recommendations at 21:56 on 23 November 2026: 「都按照你的建议。还有什么不确定的？」 [S3, D-37]. The second half, `key-outputs-by-their-inputs`, keys outputs by their inputs and retires the set-aside, the owners' own bindings and the verifier's re-asks; it follows this Change and goes before R3, in §5.7's order. R3, R4 and R6 each depend on both halves (design decision 1).

## What Changes

- **One `filmkit` command with ten verbs**: `supply`, `check`, `edit`, `narrate`, `plan`, `build`, `verify`, `review`, `deliver`, `release`. `plan` and `verify` are R2a's; the others wrap the owners that already do the work: the supply, the narration's convergence, the script edits, the review round, the delivery folder and the release record.
- **`filmkit build [TARGET…]`** runs, one at a time in the derived order, each node of R2a's table that the targets need and that is stale at its turn, each writing its run record. A target names a node, one of the derivation's nodes as a group of the table's nodes (`sound`, `audit`, `picture`, `package`), or `all`, for one edition or all.
- **A heavy node waits for the gates `preflight` held it behind**, stated once in the table as waits: a render and a package wait for their edition's sound gate (with the owner's hearing) and cover check, a render for every edition's picture gate, geometry check and declared draft, and every heavy or GPU node for the film's `check`. A wait orders and gates; it binds none of the gate's bytes.
- **Light work that can run now runs first, outside any heavy invocation**; `build` never runs narration (GPU); heavy nodes of more than one kind share one invocation only when every one is measured and their last seconds sum to at most 30 minutes, as host rules 2 and 7 ask; otherwise `build` prints the invocations to run, one host ticket each.
- **`filmkit check`**, a film-wide node of the table: the declaration, the concept contract, the register (Vale at the engine's pinned version), the readings, the anchors and what the picture reads over each edition's derived timeline, the film's npm and Python pins and its picture template. `--read-only` writes nothing, for the gates: each film's `film-sources` and the engine's own `sample-sources`.
- **Retired** (**BREAKING** for a film's tasks, gates and tests): `filmkit.produce`, the command line of `filmkit.tools`, `preflight` and `admitted` with the readiness receipt, `filmkit.durations` with its duration records and its sum, `filmkit.adoption` with its R1 bridge, `filmkit.delivery.media_server`, and the `main` of every module a verb now runs. Each question `preflight` asked goes to the node that owns its answer: the thought clarity line, with the owner's hearing, and the caption reading rate to the sound gate; the geometry record's coverage to the geometry check; the cover, the draft and the stages to their own nodes; the words to `check`.
- **The declaration holds what task lines and release lanes held**: `[picture] gate_row_gaps`, `[picture] native_uncaptioned` and `[release] sources`, beside R2a's `qualified_edition`.
- **A node binds only the tables of the declaration it reads**, so that recording the owner's hearing of a take makes the sound gate run again and no render, once `key-outputs-by-their-inputs` retires the picture gate's own binding of the whole declaration; until then a hearing also reruns that gate and both pictures of each edition.
- **A node that encodes binds the host's FFmpeg and ExifTool versions**; the release record states each film's encoder version, and reproduction compares encoded streams within one encoder version and, across versions, before encoding (the soundtrack's bytes, the UHD picture), naming both versions (derivation §8, finding 2).
- **`release.json` moves to the film's root**; the loader refuses `content/release.json`, naming the move.
- **`filmkit.api` and one test entry** (`filmkit/picture/testing.mjs`: `openComposition`, `openModules`, `derivedTimeline`): the only engine names a film's tests import.
- **The sample builds with `filmkit check`, `filmkit narrate` and `filmkit build`**; the README becomes one page.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `run-records`: `filmkit build`, targets and groups, waits, the scheduling under host rules 2, 3 and 7, the film-wide `check` node, the declaration bound by its tables, host tools' versions as pins, verification that requires every node fresh and passing, no duration record.
- `film-engine`: one console command with ten verbs; the source check and its read-only mode; `filmkit.api` and the test entry; the Node tools run by the engine's nodes only; two picture keys that task lines held.
- `sound-gates`: the thought clarity line, with the owner's hearing, and the caption reading rate, moved from `render-preflight`.
- `render-preflight`: retired; each requirement moves to the capability that owns its answer.
- `edition-readiness`: retired into the plan's readiness and the waits.
- `build-time`: duration records and their sum retired; the process rules stay.
- `engine-distribution`: the adoption command retired; its surviving questions are `filmkit check`'s.
- `film-package`: the release record at the film's root, its sources from the declaration; verification by verb; reproduction across FFmpeg versions.
- `review-rounds`: commands renamed to `filmkit review`; a round prepared on a build that verifies whole; the set-aside guard's words.
- `sample-film`: the sample's build by the verbs; its durations read from the plan.
- `narration-convergence`, `narration-anchors`, `runtime-fit`, `final-film-scan`, `caption-text`, `caption-equivalence`, `formal-register`, `picture-gates`: commands renamed to the verbs and nodes, and `render-preflight`'s draft, register and geometry rules moved in; no rule changes.

## Impact

- **Base:** the engine's release that holds R2a (`record-every-run`, 0.32.0) and the hearing Change (`hear-a-take-as-a-listener-does`), both released first. Version: the next minor after them, presumably 0.34.0 (the derivation numbered R2b 0.33.0 before the hearing Change took a release).
- **Engine:** `src/filmkit/graph/` (`cli.py`, `chain.py`, `nodes.py`, `runs.py`, `plan.py`, `verify.py`, `records.py`, `opens.py`, a new `build.py`); new `src/filmkit/check.py`, `src/filmkit/api.py`, `src/filmkit/picture/testing.mjs`; `soundtrack/gates.py`, `narration/narrate.py`, `narration/converge.py`, `narration/fitting.py`, `delivery/reproduction.py`, `delivery/release.py`, `delivery/verification.py`, `declared_sources.py`, `film.py`, `tools.py`; deleted `produce.py`, `preflight.py`, `durations.py`, `adoption.py`, `delivery/media_server.py`; `system/gates.toml` (`sample-sources`); README, CHANGELOG, the sample's tasks in `.config/mise/config.toml`. Sizes, with their search patterns, in the design.
- **Films** (each adopts in its own lane, after rebuilding and comparing under its own reproduction standard): delete the build chain's task lines (28 lines of `filmkit.produce` and 4 of `filmkit.tools` in each film, read 24 November); move `content/release.json` to `release.json` and rewrite its two links (`README.md`, `CONTRIBUTING.md`); declare `gate_row_gaps = true` and `[release] sources`; change the gates `film-media` and `film-reproduction` to `filmkit verify --technical-only` and `--release`, and add `film-sources` (`filmkit check --read-only`) to the proof sets once its first hosted run passes; make their tests import `filmkit.api` and the test entry only. The films pin 0.22.3, so a film's first adoption also carries 0.23 to 0.33 [S1, §5.7].
- **ETHOS:** `filmkit plan --json` keeps R2a's fields and gains the state `waiting`, with the gates each waiting node is held by; `filmkit build`'s refusal prints the invocations for host tickets. The release note lists the states, and a reader treats a state it does not know as not ready. ETHOS reads the plan and needs no change; the derivation leaves the JSON's shape to the engine (F7).
- **The kit:** the engine-owned needs of §3.4 that this release absorbs (the ordered build, readiness, the portable check, the pin questions) leave the kit when a film adopts; its release-asset scripts read `release.json` at the root for a film that adopted this release.
- **Later releases:** R3, R4 and R6 depend on this Change and on `key-outputs-by-their-inputs` (design decision 1).

Out of scope: outputs keyed by their inputs, the set-aside's retirement, the owners' own binding keys and the verifier's re-asks (`key-outputs-by-their-inputs`); findings and exceptions in the run record, one picture runtime, the font checks in `filmkit check` and `filmkit supply --runtime` (R3); the narration lock and the merge of `judge` and `audition` (R4); the entry page from the declaration and the static player check (R6); parallel runs of nodes.

Owner: the engine's maintainer.

## Sources

Numbered as in the design.

- **[S1]** `build/evidence/engine-derivation/derivation-2026-11-23.md` in the engine's repository: §1, §2.1, §2.2, §3.1 to §3.5, §5.1, §5.1.1, §5.3, §5.4, §5.5, §5.7 (rows R2b to R6), §6, §8.
- **[S3]** `build/evidence/owner-words.md` in the engine's repository, item D-37 (2026-11-23 21:56).
- **[S4]** The Change `record-every-run` (R2a): its proposal, design and spec `run-records`.
