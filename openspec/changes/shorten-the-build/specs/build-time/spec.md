## ADDED Requirements

### Requirement: Each heavy command records how long it took

Each action of `filmkit.produce` and `narrate` SHALL write, when it ends, a duration record for its edition: the command, when it started, its seconds, whether it completed, the seconds of each phase it names and the settings it names. The record SHALL stand beside the edition's evidence, and no duration SHALL be written into a record that another record binds by SHA-256. The verifier, which writes nothing, and the reproduction SHALL state each film's seconds in their reports.

#### Scenario: A comparison's phases

- **WHEN** `compare-pictures` passes on a natively rendered pair
- **THEN** its duration record says that it completed and holds the seconds of its validation, its composition report, its sampled frames and its every-frame scan

#### Scenario: A command that is refused

- **WHEN** `package-film` refuses an edition
- **THEN** its duration record says that it did not complete and holds the seconds until the refusal

#### Scenario: A gate record keeps no duration

- **WHEN** `check-picture` passes an edition
- **THEN** the gate record holds no duration, and the duration record beside it holds the seconds of each audit

#### Scenario: The verifier's report

- **WHEN** the verifier verifies an edition's four films
- **THEN** its report states the seconds of each film's verification, and the verifier writes no file

### Requirement: One command prints a build's durations

`python -m filmkit.durations` SHALL print, for each selected edition, every duration record in the order the commands started, each with its phases, and the sum of the seconds of the commands that completed; with `--json` it SHALL print the records themselves. An edition without a record SHALL be named as having none.

#### Scenario: Two recorded commands

- **WHEN** an edition holds the duration records of `check-picture` and `render-picture`
- **THEN** the command lists both, the earlier first, with their seconds and phases, and prints their sum

#### Scenario: An edition that was never built

- **WHEN** an edition holds no duration record
- **THEN** the command says so for that edition and exits 0

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
