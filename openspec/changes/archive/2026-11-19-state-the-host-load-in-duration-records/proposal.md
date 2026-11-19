## Why

A duration record states how long a command took and nothing of the host it ran on, so a slower build cannot be told from a busier host by the records alone. Twice in two days what a slower build's seconds meant could be said only from outside its records:

- On 17 November 2026 three builds of the sample film, on heads whose diffs do not touch the steps that grew, took 335.9 s, 468.7 s and 692.1 s; the first reading was a suspected regression, and the host's 1-minute load of 8, 25 and 21 to 36 was found afterwards, outside the records.
- On 18 November 2026 a build of the sample film held its host ticket 729 s where the day's baseline had held 387 s. `package-film` took 37.1 s against 9.8 s, the qualification's every-frame scan 39.1 s against 13.9 s and `compare-pictures` 87.9 s against 20.0 s, phases the change under test did not touch. The load rose from 6.5 to 33.8 during it. That stands in the ticket's own two lines and in no duration record; the baseline, which that build's record calls quiet, ended at a load of 20.1 by its own ticket.

This is decision 24 of the draft `decide-before-heavy-work`, admitted here as a Change of its own.

## What Changes

- Each duration record states the host's 1-minute load average at its command's start and at its end, as `load_1m` with `start` and `end`. A host that states no load average leaves both null.
- `python -m filmkit.durations` prints a record's load beside its seconds, `load 6.5 to 33.8`, as one figure where both ends print alike, and beside the build's time the lowest and the highest load its counted commands state. A record that states none, an earlier engine's or such a host's, prints as before.
- No check reads the load and no record binds it. It changes no verdict.
- The host's memory is not recorded, and the README says that a like load does not make two durations comparable. The load alone would not have told one build of 18 November 2026 from its baseline: 894 s against 387 s at like loads, on a host that was short of memory. `design.md`, decision 4, says why the reading waits and the day it is decided.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `build-time`: one requirement is added, on the load a duration record states and where the durations command prints it.

## Impact

- `src/filmkit/durations.py` and its tests. Every command that writes a duration record gains the field with no change of its own.
- A film: nothing to adopt. Its records gain the field with its next build on this engine, and a script that reads the durations command's lines finds the load between a command's seconds and its phases, and after the last line's closing bracket.
- Out of scope: the host's memory beside its load, until a build is read with a memory reading beside its seconds (decision 4; read again on 22 November 2026); any limit, gate or budget that reads the load.

`tasks.md` is the sole progress ledger.
