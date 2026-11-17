## ADDED Requirements

### Requirement: Each heavy command records how long it took

Each action of `filmkit.produce`, each narration, each tool run from the command line for one edition, the verifier and the reproduction SHALL write, when it ends, a duration record for its edition: the command, when it started, its seconds, whether it completed, its phases' seconds and the settings it names. The record SHALL stand beside the edition's evidence and inside no record that another binds by SHA-256. With `--read-only` the verifier and the reproduction SHALL write none.

#### Scenario: A comparison's phases

- **WHEN** `compare-pictures` passes on a natively rendered pair
- **THEN** its duration record says that it completed and holds the seconds of its validation, its composition report, its sampled frames and its every-frame scan

#### Scenario: A command that is refused

- **WHEN** `package-film` refuses an edition
- **THEN** its duration record says that it did not complete and holds the seconds until the refusal

#### Scenario: A gate record keeps no duration

- **WHEN** `check-picture` passes an edition
- **THEN** the gate record holds no duration, and the duration record beside it holds the seconds of each audit

#### Scenario: The verifier's record

- **WHEN** the verifier verifies an edition's four films
- **THEN** its report states the seconds of each film's verification, and the one file it writes is the edition's duration record of the run, which no check reads and no record binds

#### Scenario: A read-only verification

- **WHEN** the verifier or the reproduction runs with `--read-only`
- **THEN** it writes no duration record

#### Scenario: A tool run for one edition

- **WHEN** the geometry check is run from the command line on the Chinese edition's stage
- **THEN** the Chinese edition's duration record of the geometry check states the run, as not completed when the tool exits with a failure

#### Scenario: A tool run for no single edition

- **WHEN** a tool is run from the command line with arguments that name no edition, or both
- **THEN** it writes no duration record

### Requirement: One command prints a build's durations

`python -m filmkit.durations` SHALL print each selected edition's duration records in the order the commands started and the sum of its build: the seconds of the commands that completed and started at or after its latest whole narration, or at or after the time `--since` names. It SHALL mark an earlier record, leave it out, and say what the sum covers. With `--json` it SHALL print the records. An edition without a record SHALL be named as having none.

#### Scenario: Two recorded commands

- **WHEN** an edition holds the duration records of `check-picture` and `render-picture` and none of a whole narration
- **THEN** the command lists both, the earlier first, with their seconds and phases, prints their sum, and says that every record counts because no whole narration is recorded

#### Scenario: A record of earlier work

- **WHEN** an edition holds a `repair-pictures` record that started before its latest whole narration
- **THEN** the record is listed as earlier, the sum leaves it out, and the sum's line says since when it counts and how many earlier records it leaves out

#### Scenario: A build that keeps its narration

- **WHEN** `--since` names the time a picture-only rebuild began
- **THEN** each edition's sum covers the commands that started at or after that time

#### Scenario: A value that is no time

- **WHEN** `--since` is `yesterday`
- **THEN** the command is refused, asking for an ISO 8601 time with its offset

#### Scenario: An edition that was never built

- **WHEN** an edition holds no duration record
- **THEN** the command says so for that edition and exits 0

### Requirement: A build starts at its whole narration's record

An edition's build SHALL start at its duration record named `narrate`, which only a narration of the whole edition that generates writes. A narration of chosen segments SHALL be recorded as `narrate-<ids>` and a check-only narration as `narrate-checks`, with the ids after it when given; neither SHALL replace the whole narration's record or move the build's start. A build narrated otherwise SHALL name its start with `--since`.

#### Scenario: A check-only narration within a build

- **WHEN** an edition is narrated whole and rendered, and `narrate --skip-generation` then runs
- **THEN** the check-only run is recorded as `narrate-checks`, the record `narrate` stands byte for byte, and the build's sum still counts the narration and the render

#### Scenario: Checks of chosen segments

- **WHEN** `narrate --skip-generation --ids 06,07` runs
- **THEN** its record is `narrate-checks-06-07`

#### Scenario: A build narrated by the synthesis command

- **WHEN** a build's segments are narrated by `filmkit.narration.synthesis --ids`, which writes no duration record, and checked by `narrate --skip-generation`
- **THEN** the build wrote no `narrate` record, and its durations are printed with `--since` naming its start

### Requirement: A build's time counts commands that ran together once

After the editions, `python -m filmkit.durations` SHALL print the time of the build: the seconds during which at least one counted command of the selected editions was running, beside the sum of those commands' seconds. Commands that ran at the same time SHALL count once in the build's time, and the time between commands not at all. A budget stated for a build SHALL be judged by the build's time.

#### Scenario: Two renders at once

- **WHEN** the two editions' renders, of 170 s and 172 s, started half a second apart
- **THEN** the build's time holds 172.5 s for them, where the sum of their seconds holds 342 s

#### Scenario: Commands in a row

- **WHEN** every counted command ended before the next started
- **THEN** the build's time equals the sum of their seconds, whatever time passed between them

### Requirement: The render's worker count comes from the host

Every render SHALL pass the renderer a worker count of the host's logical cores less two, never under 8 nor over 16, unless `FILMKIT_RENDER_WORKERS` names a positive whole number, which it then passes. A value that is no positive whole number SHALL be refused by the variable's name. The render receipt SHALL record the count.

#### Scenario: A host of 18 cores

- **WHEN** a picture is rendered on a host of 18 logical cores with the variable unset
- **THEN** the renderer command passes 16 workers and the receipt records 16

#### Scenario: A host of 10 cores

- **WHEN** a picture is rendered on a host of 10 logical cores with the variable unset
- **THEN** the renderer command passes 8 workers

#### Scenario: A count named for a measurement

- **WHEN** `FILMKIT_RENDER_WORKERS` is 12
- **THEN** the renderer command passes 12 workers and the receipt records 12

#### Scenario: A value that is no count

- **WHEN** `FILMKIT_RENDER_WORKERS` is `many`
- **THEN** the render is refused before the renderer starts, naming the variable

### Requirement: Independent checks run side by side

`check-picture` SHALL run its frame, motion and detail audits at the same time, and the verifier SHALL verify up to four films at the same time. Each SHALL write the reports, print the results in the order and refuse with the words it does when the same work runs in sequence.

#### Scenario: An audit that fails beside the others

- **WHEN** the motion audit exits with a failure while the frame and detail audits pass
- **THEN** `check-picture` refuses, naming the motion audit and its report

#### Scenario: The verifier's order

- **WHEN** the verifier verifies an edition's four films
- **THEN** its report lists them in the films' declared order whichever decode ends first

### Requirement: Narration divides its segments among processes

When more than one segment is to be generated, the narration SHALL generate them in several processes at the same time, each segment in one: two processes, or the count `FILMKIT_NARRATION_PROCESSES` names, where 1 keeps a single process. It SHALL then write one receipt in segment order, as a single process writes it. A value that is no positive whole number SHALL be refused before any step, and the narration's duration record SHALL state the count.

#### Scenario: Four segments and two processes

- **WHEN** four segments are to be generated and the variable is unset
- **THEN** two processes narrate at the same time, each segment in one of them and the longest spoken text alone or with the shortest, and the receipt lists the four segments in their order

#### Scenario: One segment to generate

- **WHEN** one segment is to be generated and the others are retained
- **THEN** it is generated in the narration's own process, and no other process starts

#### Scenario: A process that fails

- **WHEN** one of two processes fails
- **THEN** the other narrates its segments to the end, the narration is then refused, naming the failed process's segments, its exit status and its log, and the edition's receipt stays as it was

#### Scenario: A value that is no count

- **WHEN** `FILMKIT_NARRATION_PROCESSES` is `many`
- **THEN** the narration is refused before any segment is generated, naming the variable

#### Scenario: The narration's duration record

- **WHEN** an edition is narrated with the variable unset
- **THEN** its duration record states a count of 2 narration processes

### Requirement: No narration process outlives its narration

Each narration process SHALL lead a session of its own. A narration that is interrupted, is asked to end (SIGTERM) or fails while its processes run SHALL end every process's whole process group before it exits, and SHALL refuse, naming what stopped it. `narrate` SHALL likewise end its running step when it is interrupted or asked to end, and its duration record SHALL then say that it did not complete.

#### Scenario: A narration asked to end

- **WHEN** the synthesis is sent SIGTERM while two processes narrate
- **THEN** both processes, and whatever each had started, have ended when it exits, and its refusal names the request to end and the folder of the processes' logs

#### Scenario: A process that cannot be started

- **WHEN** the second of two processes cannot be started
- **THEN** the first is ended, and the narration refuses, naming the failure

#### Scenario: A request to end during a step of narrate

- **WHEN** `narrate` is sent SIGTERM during its narration step
- **THEN** it asks the step to end, waits for it, refuses, and its duration record says that it did not complete
