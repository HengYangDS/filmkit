# build-time Specification

## Purpose

Record how long each heavy command of a build took and print a build's time from those records; and keep the build short by what the records settle: where a build starts, the render's worker count, what runs side by side, narration in several processes, and commands that end what they started when they end.

## Requirements

### Requirement: Independent checks run side by side

`check-picture` SHALL run its frame, motion and detail audits at the same time, and the verifier SHALL verify up to four films at the same time. Each SHALL write the reports, print the results in the order and refuse with the words it does when the same work runs in sequence.

#### Scenario: An audit that fails beside the others

- **WHEN** the motion audit exits with a failure while the frame and detail audits pass
- **THEN** `check-picture` refuses, naming the motion audit and its report

#### Scenario: The verifier's order

- **WHEN** the verifier verifies an edition's four films
- **THEN** its report lists them in the films' declared order whichever decode ends first

### Requirement: No narration process and no renderer outlives its command

Each narration process SHALL lead a session of its own, as each renderer does. A command that is interrupted, is asked to end (SIGTERM), is hung up on (SIGHUP) without ignoring it, or fails while its narration processes or its renderer run SHALL end each one's whole process group before it exits, also when further requests arrive meanwhile, and SHALL say what stopped it. `narrate` SHALL likewise end its running step, and its run record SHALL then state the outcome `error`.

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
- **THEN** it asks the step to end, waits for it, says what stopped it, and its run record states the outcome `error`

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

### Requirement: Outside those waits a request to end has its usual effect

While a command holds no narration process, no renderer and no step of `narrate`, it SHALL take no request to end: SIGTERM and a hang-up SHALL end it by their default action, and an interrupt SHALL end `filmkit build`, the steps of `narrate` and the synthesis with one line that names it, by the interrupt itself.

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

### Requirement: A convergence records how long it took

`filmkit narrate` SHALL state in the convergence's record, `convergence.json` beside the receipt, its seconds and the seconds of its narrations, its judgments, its candidates and its count of the runtime as phases. The record SHALL say that the convergence completed only where the edition ends settled and is not refused. A convergence refused before its first effect SHALL write no record.

#### Scenario: A convergence of two narrations

- **WHEN** a convergence narrates, judges, generates a round of candidates, narrates again and judges again
- **THEN** its record states its seconds and the phases `narration`, `judgment` and `candidates`, the first holding both narrations

#### Scenario: An edition left unsettled

- **WHEN** a convergence ends with a thought unsettled
- **THEN** its record says that it did not complete

#### Scenario: A convergence refused before its first effect

- **WHEN** a convergence is refused for a declaration it cannot read, or for a request an earlier run left started, while the record of the run that narrated stands
- **THEN** no record is written and the standing one holds its bytes

### Requirement: Narration divides its segments among processes and records their count

When more than one segment is to be generated, the narration SHALL generate them in several processes at the same time, each segment in one. The count SHALL be one process for every 16 GB of the host's memory, at least one and at most three, or the count `FILMKIT_NARRATION_PROCESSES` names. It SHALL then write one receipt in segment order. A value that is no positive whole number SHALL be refused before any step, and the narration's run record SHALL state the count among its settings.

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

#### Scenario: The narration's run record

- **WHEN** an edition is narrated with the variable unset on a host of 128 GB
- **THEN** its run record states a count of 3 narration processes
