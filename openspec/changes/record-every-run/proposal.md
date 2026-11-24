## Why

The engine knows every dependency of a film's build, yet states none of them once. About twenty kinds of record each bind their inputs by SHA-256 with their own key shapes, and about a dozen functions each judge their own record stale [S1, §3.1]. Readiness (`preflight`, `admitted`), the durations sum, the verifier's re-asking and the set-aside each re-derive what one record of every run would state. Two of those binding lists are already kept twice: the sound gate's at `soundtrack/gates.py:71-75` and `preflight.py:202-206`, the picture gate's at `picture/gates.py:387-395` and `picture/rendering.py:405-411`.

At 21:56 on 23 November 2026 the owner adopted the engine's re-derived architecture and its decision 1: an engine-owned record core, ordered by the standard library's `graphlib.TopologicalSorter`, with doit reading the engine's records through `uptodate` as the named alternative [S3, D-37; S1, §4.1, §5, §6]. This Change is that architecture's release R2a (0.32.0): the one record kind and `filmkit plan --json`, beside today's stages, retiring nothing [S1, §5.7]. R2b (0.33.0) then retires the records and checks this Change leaves standing.

## What Changes

- **One record of every run.** Each command of an edition's build chain writes, when it ends, one run record at `build/evidence/records/editions/<code>/<node>.json`: each input's and output's path, size, modification time and SHA-256; the engine's version, the digest of its `released.json` and the node's model pins; the outcome and the command's refusal line; the seconds, phases, settings and 1-minute load that its duration record states, from the same measurement; and the host class measured as host rule 3 measures it. Every existing record and check stays; the run record binds each as an output by its digest and copies none of its fields. A run of part of a node (a retake, a stage written elsewhere) writes a partial record that accounts for what it wrote and leaves the node stale.
- **A node table, as data.** `filmkit.graph` declares each command of the chain as a node with its inputs and outputs. The edges are derived from the paths; `graphlib` orders the nodes and refuses a cycle. A file that several runs write declares each writer as one that rewrites it or one that replaces it whole, and the latest declared writer's record binds its bytes in that declared order, so a later legitimate writer leaves the earlier records standing, an earlier writer's rerun makes every later writer stale whatever the bytes, and bytes no declared writer accounts for fail closed. `repair-pictures` writes the records of the renders and comparison it runs, and the uncaptioned picture records whether it was derived or rendered. Where an owner binds its inputs today, that list becomes a function of paths that the owner's record and the node both read, completed to what the run reads, and a check holds each node's reads and writes to its declaration: an audit hook in every engine Python process and Node's permission audit mode, which records and refuses nothing, both off unless `FILMKIT_OPENS` is set.
- **`filmkit plan [TARGET…] [--json]`.** For each node asked for and every node upstream: fresh, stale with its reasons, or behind a stale node; its host class as measured, or unmeasured with its expected class; its last seconds; and whether it is ready. Freshness compares sizes and times first and hashes only what changed. The plan runs nothing and writes nothing.
- **`filmkit verify`.** Re-hashes every input and output that any run record binds; it refuses only bytes that no declared writer accounts for and changes that kept size and time, and lists every other stale node. A review round's preparation and a release's record run it first and refuse when it refuses.
- **A `filmkit` console command** with these two verbs; R2b adds the rest of the derivation's verbs to it [S1, §5.3].

Nothing a film declares, runs or commits changes, and no delivered byte changes. A film adopting this release does nothing; its commands write the new records beside the old ones. The one new refusal is `filmkit verify`'s, before a review round and a release, which fires only when a file below `build/` was changed by no declared writer or changed while keeping its size and time. The sound gate's and picture gate's records gain the keys of the inputs they read and did not bind, the assembly record and the declaration, so their bytes change once and their checks refuse what they let through before.

Out of scope, each R2b's [S1, §5.7]: the other verbs (`check`, `build`, `review`, `deliver`, `release`), outputs keyed by their inputs, the retirement of `preflight`, `admitted`, `durations`, `set-aside`, `adoption`, `produce`, `tools` and the verifier's re-asks, findings and exceptions in the run record, and `filmkit.api`. The one exception model is R3's, and the narration lock with per-thought freshness is R4's.

## Capabilities

### New Capabilities

- `run-records`: one record of every run of a build node; the node table with derived edges; freshness by size and time, then digest; host classes measured by host rule 3; `filmkit plan` and `filmkit verify`.

### Modified Capabilities

- `review-rounds`: a round is prepared only on records that verify.
- `film-package`: a release is recorded only on records that verify.

## Impact

- **Base:** R1, `treat-languages-as-equals` (0.31.0), built and released first; this Change reads the edition places that R1 derives from the code and moves none of them [S4].
- **Engine:** new package `src/filmkit/graph/` (`records.py`, `nodes.py`, `host.py`, `plan.py`, `cli.py`); `durations.py` (its run opens and closes the node's run); the owners whose binding lists become functions of paths: `soundtrack/gates.py`, `picture/gates.py`, `picture/rendering.py`, `preflight.py`, `picture/equivalence.py`; `review/round.py` and `delivery/release.py` (verify first); `filmkit/__init__.py`, `tools.py` and `picture/renderer.py` (the recorder, off by default); `pyproject.toml` (`[project.scripts]`).
- **Tests:** new `tests/graph/`; `tests/test_durations.py`, `tests/review/test_round.py` and `tests/delivery/test_release.py` gain scenarios; the owners' tests pass unchanged.
- **Size:** core about 500 lines and adapters about 300, by the derivation's estimate [S1, §5.7], not yet measured.
- **Films:** none. `filmkit plan --json` is the seam ETHOS's host admission may read [S1, §5.4].

Owner: the engine's maintainer.

## Sources

Numbered as in the design.

- **[S1]** `build/evidence/engine-derivation/derivation-2026-11-23.md` in the engine's repository, revision 2: §2.1, §3.1, §4.1, §4.4, §5, §5.1, §5.1.1, §5.3, §5.4, §5.7 (row R2a), §7.
- **[S3]** `build/evidence/owner-words.md` in the engine's repository, item D-37 (2026-11-23 21:56).
- **[S4]** The draft Change `treat-languages-as-equals` beside this one: its proposal, design (decision 1, Non-Goals) and tasks.
