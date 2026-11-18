## Context

See [proposal.md](proposal.md). `filmkit.durations` opens a run for each command (`Run`), measures its phases and writes one record at the run's end: the command, the edition, when it started, its seconds, whether it completed, its phases and the settings it names [S3]. The durations command prints each edition's records in the order they started, the sum of its build and, last, the build's time. No record binds a duration record and no check reads one.

What a slower record meant could twice be said only from outside the records [S1] [S2]. The seconds of 18 November are the plainest case: a ticket's START and DONE lines hold the only readings of the load, 6.5 and 33.8, and the phases that grew three to four times are ones the change under test did not touch.

## Goals / Non-Goals

**Goals:**

- A reader of a build's durations sees, on the same lines, how busy the host was while each command ran.

**Non-Goals:**

- Explaining a duration. The load is one condition of the host; it proves no cause, and a build setting is still decided on a baseline repeated at like load (the draft's decision 24, "It does not replace (b)").
- A limit. No command starts, waits or refuses by the load; that is the host's queue's to decide, not the engine's.
- Every condition of the host. Its memory is decision 4's, which leaves it and says until when.

## Decisions

Each decision states what it rests on, what was considered, why the option taken was chosen, where it applies, what would reopen it, and its sources.

1. **A record states the 1-minute load average at its command's start and at its end.**
   - **Rests on:** the two cases above; `os.getloadavg` of the engine's Python, which returns the 1-, 5- and 15-minute averages and raises `OSError` where the load average cannot be obtained; 100,000 readings took 0.03 s on the host of these builds [S4].
   - **Considered:** (a) the load at the start alone, as the draft's title has it: the build of 18 November started at 6.5 and ended at 33.8, and its last commands ran under the second figure; (b) the start and the end, as the draft's decision says; (c) the load sampled through the run by a thread, which would say more of a long command and adds a thread to every command; (d) the 5- and 15-minute averages beside the 1-minute one: a command of seconds is not described by an average of minutes.
   - **Chosen because:** (b) brackets a command with two readings and no thread. For a command shorter than a minute both readings hold much of the same minute, which is still the host the command met.
   - **Applies to:** `durations.Run`: the reading at its start, and the record's `load_1m` with `start` and `end`, each to two decimals. Every command that writes a duration record gains it.
   - **Reopened when:** a long command's two readings are shown to miss what slowed it; (c) is then measured.
   - **Sources:** [S1] [S2] [S4].
2. **A host that states no load average writes its record with both readings null; the field always stands.**
   - **Rests on:** `os.getloadavg` is absent on a platform without it and raises `OSError` where the average cannot be obtained [S4]; a record of an earlier engine holds no such field.
   - **Considered:** (a) leaving the field out on such a host, which a reader cannot tell from an earlier engine's record; (b) the field with null readings; (c) refusing or warning, for a field no check reads.
   - **Chosen because:** (b) says that the engine asked and the host stated none.
   - **Applies to:** `durations.host_load` and the record.
   - **Reopened when:** not applicable.
   - **Sources:** [S4].
3. **The durations command prints the load beside the seconds, and the range beside the build's time.**
   - **Rests on:** the command's lines as they stand [S3]: seconds, then `earlier` or `not completed`, then the phases in round brackets and the settings in square ones; the last line states the build's time and the sum.
   - **Considered:** (a) the load among the settings in the square brackets: a setting is the command's, the load is the host's; (b) a column of its own before the seconds, which moves the place of the seconds that scripts read; (c) after the seconds and the state, before the phases, as `load 6.5 to 33.8`, and after the last line's closing bracket the lowest and highest load the counted commands state; (d) an arrow between the two figures, which no other line of the engine's output uses.
   - **Chosen because:** (c) puts the host beside the seconds it qualifies, changes no existing part of a line, and keeps the output in the characters it already uses. One figure is printed where both ends print alike or only one was stated. A record that states none prints as before, so a folder that mixes records of two engines reads without a gap, and the last line then says how many of its commands state none.
   - **Applies to:** `durations.lines`, `durations.build_time`. `--json` prints the records, the field among them.
   - **Reopened when:** a film's script that parses these lines is shown to break (the films' repositories were not searched: see Open Questions).
   - **Sources:** [S3].
4. **The host's memory is not recorded in this Change, and the load alone does not make two durations comparable.**
   - **Rests on:** the one recorded case that the load does not tell. On 18 November 2026 a build of the sample film held its ticket 894 s where the baseline of the same morning held 387 s, at 1-minute loads of 6.7 and 21.0 against 5.1 and 20.1 at their two ends. The day's retrospective reads the slower build as run with the host's swap full, the host's kills for memory having begun at 07:59 and the build at 08:14, and says that the load was the wrong measure [S6]. The two builds also differ in their supply and neither ticket read memory, so the case is that reading and not a measured pair. The other way round, the build of the afternoon ran three to four times slower with the swap at 10.8 and 11.2 GiB at its two ends and the load risen fivefold [S2]. On macOS the standard library states the page size and the count of physical pages and no swap or pressure reading; the two the host's own rule reads, `vm.swapusage` and `kern.memorystatus_vm_pressure_level`, come from `sysctl`, one child process of about 3 ms for both [S4]. The engine's lock does not hold `psutil`, the usual package for such readings [S3].
   - **Considered:** (a) the load alone, with the limit stated to the reader; (b) swap used and the kernel's pressure level beside the load, read at both ends of every command by one `sysctl` child on macOS and from `/proc` on Linux; (c) the same readings through a binding to the kernel's call, or through a package the lock would gain.
   - **Chosen because:** (a), for now. Memory belongs beside the load: a record with the load alone would have shown the 894 s build at its baseline's load. What is not known is which reading tells. Swap used is a stock that an idle process can hold: the same evening it stood at 35.2 GiB after a ticket's processes had ended, held, as the retrospective reads it, by an idle model of 26 GiB [S5]. The pressure level is the kernel's statement of the moment. Neither was read at 08:14, and a reading chosen without one build measured with it would repeat that morning's fault with another figure. Each way to take a reading has a cost that is decided apart: a child process at both ends of every command, a hand-written binding for one platform, or a dependency. A ticket's lines state the host's swap and its pressure level [S2], and since 19:08 CST of that day the ticket's own memory beside them [S5], so the next builds bring the pairs this decision lacks.
   - **Applies to:** the README's words on reading a duration, which say that a like load does not make two durations comparable. Nothing in the record.
   - **Reopened when:** the builds ticketed from 18 November 2026 19:08 CST are read against their duration records, at the next reading of the draft `decide-before-heavy-work` on 22 November 2026, by the engine's maintainer. A pair at a like load whose seconds differ, with one memory reading apart, admits that reading.
   - **Sources:** [S2] [S3] [S4] [S5] [S6].
5. **The capability gains one requirement, and none is restated.**
   - **Rests on:** `build-time` holds three requirements on duration records and their command, the first at 497 of the 500 characters a requirement may hold [S3]; a requirement that a delta modifies is restated whole with its scenarios.
   - **Considered:** (a) the load written into each of the three, restating sixteen scenarios; (b) one added requirement that owns what a record states of the host and where the command prints it.
   - **Chosen because:** (b) gives the load one owner in the specification and leaves the three as they stand.
   - **Applies to:** the delta `specs/build-time/spec.md`.
   - **Reopened when:** not applicable.
   - **Sources:** [S3].

## Risks / Trade-offs

- A load average is read as a cause. → The README says what it is: a condition of the host, beside which a duration is read; a build setting is decided on a repeated baseline.
- The 1-minute average lags: a command of seconds that starts as the host turns busy states the calmer minute before. → Both ends are stated, and the build's last line gives the range over all its commands.
- A host that is short of memory can state a load like a quiet morning's, and a reader then takes two durations for comparable. → The README says that a like load does not make them so; decision 4 names the case and the day it is read again.

## Open Questions

- Whether a film's or the kit's script parses the durations command's lines in a way the load disturbs. The kit reads the last line's "was running for … s", which stands unchanged before the added clause; the films' repositories were not searched.

## Sources

Read or measured on 18 November 2026. Paths under `build/evidence/` are the canonical checkout's local evidence.

- **[S1] The draft `decide-before-heavy-work`:** `openspec/changes/decide-before-heavy-work/design.md`, decision 24 (the three builds of 17 November 2026 with their seconds and loads, and its options (a) to (c)), and the last paragraph of its `proposal.md`, which names this slice as the draft's next.
- **[S2] The build of 18 November 2026 and its baseline:** `build/evidence/draw-pictures-natively/native/result.md` (the phases' seconds of both builds, and the ticket's readings: swap used 10.8 and 11.2 GiB, load 6.5 and 33.8), `sample-durations.txt` and `tickets.txt` beside it (held 729 s, 14:30:29 to 14:42:38 CST); `build/evidence/take-mlx-audio-0-6-6-and-hyperframes-0-9-64/baseline-tickets.txt` (the baseline of 07:41:53 to 07:48:20 CST: held 387 s, load 5.14 at its start and 20.09 at its end).
- **[S3] The engine at `3f7051e`:** `src/filmkit/durations.py`, the capability `openspec/specs/build-time/spec.md` (the requirements "Each heavy command records how long it took", "One command prints a build's durations" and "A build's time counts commands that ran together once"), and `uv.lock`, which names no `psutil`. Each requirement's characters and scenarios are counted in `build/evidence/state-the-host-load-in-duration-records/build-time-requirements.txt`.
- **[S4] What the host offers:** `build/evidence/state-the-host-load-in-duration-records/load-probe.py` with `load-probe.txt`: Python 3.12.16 on macOS 27.2.1, the standard library's words on `os.getloadavg`, the names `os.sysconf` knows there, 100,000 readings in 0.03 s, and one `sysctl` child for both memory readings in 0.002 to 0.003 s. That `os.getloadavg` is absent on some platforms is the standard library's statement of its availability, not tried here.
- **[S5] The swap's rise of 18 November 2026:** `build/evidence/retrospectives/2026-11-18.md`, Part 4, "Failures traced to their cause" (swap used from 8.8 to 34.5 GiB in thirteen minutes of a ticket; the host's keeper read another application's process at 62 to 65 GB resident; swap used stood at 35.2 GiB after the ticket's processes had ended, held by an idle model of 26 GiB; the ticket tool records its ticket's process tree beside the host's swap since 19:08 CST).
- **[S6] The build that the load does not tell:** `build/evidence/take-mlx-audio-0-6-6-and-hyperframes-0-9-64/baseline-tickets.txt` and `moved-tickets.txt` (held 387 s from 07:41:53 CST at loads 5.14 and 20.09; held 894 s from 08:14:33 CST at loads 6.65 and 21.00; the second is the build on the moved supply), and `build/evidence/retrospectives/2026-11-18.md`, Part 2, "Failures traced to their cause", items 1 and 4 (the host's kills for memory from 07:59:41 CST; "Durations of today's builds are not comparable").
