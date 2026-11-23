# build-time Specification

## Purpose

Record how long each heavy command of a build took and print a build's time from those records; and keep the build short by what the records settle: where a build starts, the render's worker count, what runs side by side, narration in several processes, and commands that end what they started when they end.

## Requirements

### Requirement: Each heavy command records how long it took

Each action of `filmkit.produce`, each narration, the geometry check and the cover check run from the command line, the verifier and the reproduction SHALL write, at its own end, a duration record for its edition: the command, when it started, its seconds, whether it completed, its phases' seconds and the settings it names. The record SHALL stand beside the edition's evidence and inside no record that another binds by SHA-256. With `--read-only` the verifier and reproduction SHALL write none.

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

#### Scenario: A reproduction that does not pass

- **WHEN** the reproduction's comparison of an edition holds a failing layer or a film that is still calibrating
- **THEN** that edition's duration record says that the reproduction did not complete, as a refused verification's does

#### Scenario: The two checks a build runs from the command line

- **WHEN** the geometry check or the cover check (`player-check cover`) is run from the command line on the Chinese edition's stage
- **THEN** the Chinese edition's duration record `geometry-check` or `player-check-cover` states the run, as not completed when the tool exits with a failure

#### Scenario: A tool run by hand

- **WHEN** another tool, such as `frame-audit` or `player-check players`, is run from the command line with arguments that name an edition
- **THEN** it writes no duration record, and the records of the build's checks stand as they were

#### Scenario: A check for no single edition of this film

- **WHEN** the geometry check is run with arguments that name no edition, both editions, or a stage outside this film's root
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

An edition's build SHALL start at its duration record named `narrate`, which only a narration of the whole edition that generates writes, or as "A build counts the convergence that narrated it" states. A narration of chosen segments SHALL be recorded as `narrate-<ids>` and a check-only narration as `narrate-checks`, with the ids after it when given; neither SHALL replace the whole narration's record or move the build's start. A build narrated otherwise SHALL name its start with `--since`.

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

#### Scenario: Two commands at once

- **WHEN** two commands of 170 s and 172 s, one of each edition, started half a second apart
- **THEN** the build's time holds 172.5 s for them, where the sum of their seconds holds 342 s

#### Scenario: Commands in a row

- **WHEN** every counted command ended before the next started
- **THEN** the build's time equals the sum of their seconds, whatever time passed between them

### Requirement: Independent checks run side by side

`check-picture` SHALL run its frame, motion and detail audits at the same time, and the verifier SHALL verify up to four films at the same time. Each SHALL write the reports, print the results in the order and refuse with the words it does when the same work runs in sequence.

#### Scenario: An audit that fails beside the others

- **WHEN** the motion audit exits with a failure while the frame and detail audits pass
- **THEN** `check-picture` refuses, naming the motion audit and its report

#### Scenario: The verifier's order

- **WHEN** the verifier verifies an edition's four films
- **THEN** its report lists them in the films' declared order whichever decode ends first

### Requirement: Narration divides its segments among processes

When more than one segment is to be generated, the narration SHALL generate them in several processes at the same time, each segment in one. The count SHALL be one process for every 16 GB of the host's memory, at least one and at most three, or the count `FILMKIT_NARRATION_PROCESSES` names. It SHALL then write one receipt in segment order. A value that is no positive whole number SHALL be refused before any step, and the narration's duration record SHALL state the count.

#### Scenario: Four segments and two processes

- **WHEN** four segments are to be generated on a host of 32 GB and the variable is unset
- **THEN** two processes narrate at the same time, each segment in one of them and the longest spoken text alone or with the shortest, and the receipt lists the four segments in their order

#### Scenario: The host's count

- **WHEN** the variable is unset on hosts of 8, 16, 32, 48 and 128 GB of memory
- **THEN** the narration uses 1, 1, 2, 3 and 3 processes, and 1 on a host whose memory cannot be read

#### Scenario: A count the variable names

- **WHEN** `FILMKIT_NARRATION_PROCESSES` is 2 on a host of 128 GB, or 1 on any host
- **THEN** the narration uses two processes, or stays in its own

#### Scenario: One segment to generate

- **WHEN** one segment is to be generated and the others are retained
- **THEN** it is generated in the narration's own process, and no other process starts

#### Scenario: A process that fails

- **WHEN** one of two processes fails
- **THEN** the other narrates its segments to the end, the narration is then refused, naming the failed process's segments, its exit status, its log and the last five lines the process wrote that are not empty, and the edition's receipt stays as it was

#### Scenario: A value that is no count

- **WHEN** `FILMKIT_NARRATION_PROCESSES` is `many`
- **THEN** the narration is refused before any segment is generated, naming the variable

#### Scenario: The work an earlier run left

- **WHEN** a synthesis for a receipt begins, to divide its segments or to narrate one in its own process
- **THEN** the logs and receipts that an earlier run's processes left for that receipt are removed first, and this run's stay after it ends, whether it passes or fails

#### Scenario: A segment a process generated

- **WHEN** a process generated a segment in this run
- **THEN** the narration reports the segment as generated, with that process's number, and a segment retained from an earlier run as reused

#### Scenario: Each process's seconds

- **WHEN** one of two processes ends after two seconds and the other at once
- **THEN** the narration prints for each process the seconds until that process ended, and not the slower one's for both

#### Scenario: A receipt outside the film's root

- **WHEN** the synthesis is given a receipt or a recordings folder outside the film's root
- **THEN** it refuses before any segment is planned or generated, naming the option and the root, and writes nothing

#### Scenario: The root spelled another way

- **WHEN** the synthesis is given an absolute receipt or recordings folder that reaches a place below the film's root through another spelling of the root, as `/tmp` spells `/private/tmp` on macOS, or a place below a folder that is linked into the root
- **THEN** it takes the place as inside the root, by its path from the root

#### Scenario: A receipt that names no file

- **WHEN** the synthesis is given `.`, an empty value or a folder as its receipt, or the root itself or a file as its recordings folder
- **THEN** it refuses in words before any segment is planned, naming the option and what the value is, and writes nothing

#### Scenario: The narration's duration record

- **WHEN** an edition is narrated with the variable unset on a host of 128 GB
- **THEN** its duration record states a count of 3 narration processes

### Requirement: No narration process and no renderer outlives its command

Each narration process SHALL lead a session of its own, as each renderer does. A command that is interrupted, is asked to end (SIGTERM), is hung up on (SIGHUP) without ignoring it, or fails while its narration processes or its renderer run SHALL end each one's whole process group before it exits, also when further requests arrive meanwhile, and SHALL say what stopped it. `narrate` SHALL likewise end its running step, and its duration record SHALL then say that it did not complete.

#### Scenario: A narration asked to end

- **WHEN** the synthesis is sent SIGTERM while two processes narrate
- **THEN** both processes, and whatever each had started, have ended when it exits, and its one line names the request to end and the folder of the processes' logs

#### Scenario: A hang-up

- **WHEN** the synthesis is sent SIGHUP while two processes narrate, and does not ignore it
- **THEN** both processes, and whatever each had started, have ended when it exits, and its one line names the hang-up

#### Scenario: A hang-up under nohup

- **WHEN** the synthesis ignores SIGHUP, as under nohup, and is sent it while two processes narrate
- **THEN** the narration and both processes go on

#### Scenario: A process that cannot be started

- **WHEN** the second of two processes cannot be started
- **THEN** the first is ended, and the narration refuses, naming the failure

#### Scenario: A render asked to end

- **WHEN** a command that runs a renderer is sent SIGTERM while a renderer that ignores SIGTERM runs
- **THEN** the renderer's process group is sent SIGTERM once and killed after the grace, the renderer has ended when the command exits, and the command's one line names the request

#### Scenario: A renderer that exits and leaves a worker

- **WHEN** a renderer exits, with status 0 or with another, while a process it started still runs
- **THEN** that process has ended when the run of the renderer returns, and the run reports the renderer's own exit status

#### Scenario: A narration process that ended long before

- **WHEN** a narration is asked to end after one of its two processes has ended and been waited for
- **THEN** only the process that still runs is sent a signal, and no process that has since been given the other's number

#### Scenario: A second interrupt during the grace

- **WHEN** a command that runs a renderer is interrupted, and interrupted again while it waits out the renderer's grace
- **THEN** the renderer is still killed after the grace, and has ended when the command exits

#### Scenario: A request to end during a step of narrate

- **WHEN** `narrate` is sent SIGTERM during its narration step
- **THEN** it asks the step to end, waits for it, says what stopped it, and its duration record says that it did not complete

### Requirement: A command that is asked to end ends once, in one line

From a first request to end that arrives while its narration processes, its renderer or a step of `narrate` run, until they have ended and it has exited, a command SHALL take every further request, at whatever interval, without ending early or cutting their ending short. It SHALL then write one line on standard error that names the request, with no traceback, or drop the line where that stream takes none, and SHALL exit with 143 after SIGTERM and 129 after a hang-up, or die by the interrupt.

#### Scenario: A second request to end, at any interval

- **WHEN** the synthesis, or a command that runs a renderer, is sent SIGTERM twice, the second from 0 to 10,000 microseconds after the first
- **THEN** every narration process or the renderer has ended when the command exits, and the command writes its one line and exits with 143

#### Scenario: A request to the group, which narrate relays

- **WHEN** SIGTERM is sent to the process group of `narrate` while its narration step runs two processes, so that the step gets the request from the group and again from `narrate`
- **THEN** both processes have ended, the step and `narrate` each write their one line, and `narrate` exits with 143

#### Scenario: The exit status names the request

- **WHEN** the synthesis is interrupted, sent SIGTERM, or sent SIGHUP without ignoring it, while its processes narrate
- **THEN** it dies by the interrupt, for which a shell reports 130, or exits with 143 or 129, and its one line names an interrupt, a request to end or a hang-up

#### Scenario: A hang-up whose terminal is gone

- **WHEN** the synthesis writes to a terminal that has closed and is sent SIGHUP while two processes narrate
- **THEN** both processes have ended when it exits, and it exits with 129 although its line cannot be written

#### Scenario: A line that no stream takes

- **WHEN** a command that acted on a request has standard error on a pipe that, as `select` answers, takes no write within a second, as a full one that nobody reads, or was started without standard error
- **THEN** it writes no line, at once where it has no standard error and after at most a second otherwise, waits for no reader, and ends with the status of its request

#### Scenario: Requests while the command unwinds

- **WHEN** a command has acted on SIGTERM, has ended what it held, and is sent SIGTERM, an interrupt and a hang-up before it has exited
- **THEN** it exits with 143 and its one line names the request to end

### Requirement: A command that a signal ends where it stands writes no duration record

A command that SIGTERM or a hang-up ends by its default action, since it holds no narration process, no renderer and no step of `narrate`, SHALL write no duration record, and the record that an earlier run of that command wrote SHALL stand as it was. A command that unwinds, by a refusal, by an interrupt or by a request it takes, SHALL write its record, which says that it did not complete.

#### Scenario: A duration record after an interrupt and after SIGTERM

- **WHEN** a production action that holds no child of the kinds above is interrupted, run again and sent SIGTERM
- **THEN** the interrupted run's record says that it did not complete, and the second run writes none and leaves that record as it was

### Requirement: Outside those waits a request to end has its usual effect

While a command holds no narration process, no renderer and no step of `narrate`, it SHALL take no request to end: SIGTERM and a hang-up SHALL end it by their default action, and an interrupt SHALL end `filmkit.produce`, the steps of `narrate` and the synthesis with one line that names it, by the interrupt itself.

#### Scenario: SIGTERM during a check that runs tools

- **WHEN** a command that holds no child of the kinds above is sent SIGTERM or SIGHUP
- **THEN** it ends at once by that signal, with no line, as a command before this Change did, and the tools it had started run on to their own end

### Requirement: A tool that a command waits for is asked to end before it is killed

A tool whose wait an interrupt cuts short SHALL be asked to end and waited for, and killed only when it has not ended after 20 s. While the tool is being ended, a further request to end SHALL be deferred until the tool has ended or been killed.

#### Scenario: An interrupt during a check that runs a tool

- **WHEN** a terminal's interrupt reaches a command and the tool it runs, and the tool takes a second to close what it started
- **THEN** the tool ends by its own handling of the interrupt, and the command waits for it, writes its one line and dies by the interrupt

#### Scenario: An interrupt of the command alone

- **WHEN** an interrupt reaches a command and not the tool it waits for
- **THEN** the command asks the tool to end, the tool closes what it started and is not killed, and the command then writes its one line and dies by the interrupt

#### Scenario: A further request while a tool is being ended

- **WHEN** a command is interrupted while it waits for a tool that takes a second to close what it started, and is sent SIGTERM, a hang-up or a second interrupt in that second
- **THEN** the tool closes what it started, and only then does the command end: by the signal itself after SIGTERM or a hang-up, and with its one line after a second interrupt

#### Scenario: An interrupt of the command alone during audits that run side by side

- **WHEN** an interrupt reaches `check-picture` and not the audits it runs side by side
- **THEN** the command writes its one line and dies by the interrupt, and the audits run on to their own end

#### Scenario: A tool that does not end when asked

- **WHEN** the tool ignores the request to end for longer than the grace
- **THEN** it is killed, and the command writes its one line and dies by the interrupt

#### Scenario: An interrupt in a script

- **WHEN** `sh` or `bash` runs a script whose command is interrupted
- **THEN** the shell ends the script and does not run its next line

### Requirement: A duration record states the host's load

Each duration record SHALL state the host's 1-minute load average at its command's start and at its end, each null on a host that states none. `python -m filmkit.durations` SHALL print a record's load beside its seconds, as one figure where both ends print alike, and after the build's time the lowest and highest load its counted commands state. A record that states no load SHALL print as it did. No check SHALL read the load and no record SHALL bind it.

#### Scenario: A command on a host that turns busy

- **WHEN** `package-film` starts at a 1-minute load of 6.52 and ends at 33.80
- **THEN** its duration record states `load_1m` with `start` 6.52 and `end` 33.8, and its line prints `load 6.5 to 33.8` after its seconds and before its phases

#### Scenario: A command that is refused

- **WHEN** a command that started at a load of 7.0 is refused at a load of 7.3
- **THEN** its record states both readings beside `completed` false, and its line prints the load after `not completed`

#### Scenario: Both ends alike

- **WHEN** a record states 10.18 at its start and 10.21 at its end
- **THEN** its line prints `load 10.2`

#### Scenario: A host that states no load average

- **WHEN** a command runs on a host without load averages, or one whose load average cannot be read
- **THEN** it writes its duration record with both readings null, completes as it would, and its line prints no load

#### Scenario: A record of an earlier engine

- **WHEN** an edition holds a duration record without `load_1m`
- **THEN** its line and the sum print as they did

#### Scenario: The range of a build

- **WHEN** a build's three counted commands state loads from 6.52 to 33.84, and a refused command and an earlier record state higher ones
- **THEN** the last line ends with the host's 1-minute load between 6.5 and 33.8 at their starts and ends

#### Scenario: Counted commands that state none

- **WHEN** two of a build's five counted commands state no load
- **THEN** the last line gives the range of the three that do and says that 2 of them state none

#### Scenario: A build without a stated load

- **WHEN** none of a build's counted commands states a load
- **THEN** the last line is as it was

### Requirement: A convergence records how long it took

`filmkit.narration.converge` SHALL write the duration record `converge` when it ends, with the seconds of its narrations, its judgments, its candidates and its count of the runtime as phases. The record SHALL say that the command completed only where the edition ends settled and is not refused. A convergence refused before its first effect SHALL write none.

#### Scenario: A convergence of two narrations

- **WHEN** a convergence narrates, judges, generates a round of candidates, narrates again and judges again
- **THEN** its record `converge` states its seconds and the phases `narration`, `judgment` and `candidates`, the first holding both narrations

#### Scenario: An edition left unsettled

- **WHEN** a convergence ends with a thought unsettled
- **THEN** its record says that the command did not complete

#### Scenario: A convergence refused before its first effect

- **WHEN** a convergence is refused for a declaration it cannot read, or for a request an earlier run left started, while a `converge` record stands from the run that narrated
- **THEN** no duration record is written and the standing one holds its bytes

### Requirement: A build counts the convergence that narrated it

Where an edition's latest whole narration started within the run of a convergence, the build SHALL start at that convergence's record `converge`. Where the convergence completed, the sum SHALL count it and list the narration as inside it without adding its seconds again. Where it did not complete, the sum SHALL leave the convergence out and count the narration.

#### Scenario: A converged edition

- **WHEN** a convergence of 343 s ran two narrations, the last of 41 s, and a render of 200 s followed
- **THEN** the build's sum holds 543 s, the narration's record is listed as inside the convergence, and the sum's line says that the build began at the convergence

#### Scenario: A convergence that did not complete

- **WHEN** a convergence of 343 s ran a narration of 41 s and ended with its edition refused by the assembly, and a render of 200 s followed
- **THEN** the convergence is listed as not completed and left out, and the build's sum holds 241 s: the narration and the render

#### Scenario: A narration after an earlier convergence

- **WHEN** an edition converged in an earlier build and is now narrated whole without a convergence
- **THEN** the build starts at that narration, and the earlier convergence's record is listed as earlier and left out
