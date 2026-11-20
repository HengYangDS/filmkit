## Context

The capability `build-time` states that a build starts at its whole narration's record and that its time counts commands that ran together once. This Change answers finding 8 of the whole-edition trial; its proposal states why and what changes, its spec the behavior. A mark such as [S1] names an entry under Sources.

What the engine holds, read at `db7a837` with the staged Change `name-the-pause-that-fits` [S2]: `narration.converge` runs each narration as a child, `python -m filmkit.narration.narrate`, which writes the record `narrate` when it ends; the convergence opens no run of its own. `durations.build_start` takes the start of the latest `narrate` record, and `counted` keeps the completed records that started at or after it. `durations.running` counts the seconds during which at least one counted command ran.

## Goals / Non-Goals

**Goals:**

- The sum and the time of a converged edition's build hold everything its convergence took.
- An edition narrated without a convergence reads the figures it reads today.

**Non-Goals:**

- A record of each narration of a convergence. Its phases state their sum.
- Any check on a duration.

## Decisions

Each decision states what it rests on, what was considered, why the option taken was chosen, and where it applies.

1. **The convergence is a command of the build and records its own run.**
   - **Rests on:** every command of a build writes a duration record when it ends; the convergence, an engine command since 0.24.0 that a film runs for an edition whose takes are refused, writes none [S2] [S3]. Neither the sample film's narration task nor the trial's called it: the trial ran it by hand for the English edition. In the trial the English edition's convergence held 343 s: a first narration, a judgment, a round of candidates, a second narration and judgment; its duration records show the last narration, 41.0 s [S1].
   - **Considered:** (a) each narration of a convergence keeping a record of its own under a numbered name, which leaves the judgments and the candidates uncounted and a folder of records whose number differs from run to run; (b) one record, `converge`, opened by the command, with its narrations, judgments, candidates and count as phases.
   - **Chosen because:** (b). The command a build ran is the convergence; what it ran inside is its own.
   - **Applies to:** `narration/converge.py`: the command's run is opened in `main`, inside the block that answers a request to end, and is told that it failed where the edition ends unsettled or refused. The phases are `narration`, `judgment`, `candidates` and `count`. The refusals that come before the run's first effect (a receipt that is not the edition's own, a declaration the count cannot read, a request an earlier run left started, a former run's record that cannot be read) are made before the run is opened and write no duration record, as a narration's are: a refusal that did no work would otherwise replace the record of the run that narrated the standing build. `converge()` takes from those checks the reserve and the former run's record, which `left` alone reads; its one caller is the command's own `main`, so its changed signature is stated here and in no Changelog entry.
2. **A build starts at the convergence that ran its narration, and that narration is counted once.**
   - **Rests on:** `build_start` and `counted` read records by their start and name [S2]. A convergence runs its narrations as its children, one after another, so each starts and ends within the convergence's own span.
   - **Considered:** (a) the child narration told by its parent not to write `narrate`, which removes the one record that says a whole narration ran and changes what a narration writes by who called it; (b) a rule for any record that lies inside another, which would also leave out a command of the same edition that ran beside a longer one on purpose; (c) the build's start moved to the start of the `converge` record whose span holds the latest `narrate` record's start, and that `narrate` record listed as inside the convergence and left out of the sum.
   - **Chosen because:** (c). It is decided by two names and one comparison of times, and a film that narrates without a convergence meets no change.
   - **Applies to:** `durations.py`: `build_start`, `counted` and the printed lines. A convergence that did not complete is left out of the sum as every command that did not, and the narration it ran is then counted, so that a sum never reads less than it read before this Change; a command that started between such a convergence's start and its narration's is then counted too, where it was listed as earlier. The time of the build needs no change: it counts overlapping seconds once already.

## Risks / Trade-offs

- A convergence that a kill ends where it stands writes no record, as every command; the narration it ran last then starts the build. One that is asked to end writes a record that says it did not complete. → As every command; the next convergence writes its own.
- A sum grows for a film that converges, against its earlier builds. → It grows to what the build took; the Changelog says so.
- A command's record is its latest run, so a convergence run again after a miss replaces the record of the run that narrated. → The rule of every duration record; a budget is read from a build that ran through.
- A run's span is its wall-clock start and its monotonic seconds, so a clock set during a convergence can put its narration's start outside the span. → The build then starts at the narration, as before this Change.

## Sources

- [S1] The whole-edition trial's report, `build/evidence/faster-films-less-by-hand/whole-edition-trial/report.md` in this repository's local evidence, finding 8 and the section on time.
- [S2] The engine at `db7a837` with the staged steps of `name-the-pause-that-fits`: `src/filmkit/narration/converge.py`, `narration/narrate.py`, `durations.py`.
- [S3] `openspec/specs/build-time/spec.md`: "Each heavy command records how long it took", "A build starts at its whole narration's record", "A build's time counts commands that ran together once".
