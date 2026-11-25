## ADDED Requirements

### Requirement: Each run of a node writes one run record, for its edition or for the film

Each run of a node SHALL write, when it ends, one run record: for an edition's node at `build/evidence/records/editions/<code>/<node>.json`, for a film-wide node at `build/evidence/records/film/<node>.json`, replacing the node's previous record. A run that a signal ends where it stands SHALL write none. A record SHALL bind each record its owner writes as an output by digest and copy none of that record's fields.

#### Scenario: A gate's run is recorded

- **WHEN** `filmkit build check-sound:zh` runs the sound gate after measuring the soundtrack
- **THEN** `build/evidence/records/editions/zh/check-sound.json` names the soundtrack, the timeline, the assembly record and the declaration's tables the gate reads among its inputs and `sound-gates.json` among its outputs, each with its size, modification time and SHA-256, and states no finding

#### Scenario: A refused run is recorded as refused

- **WHEN** a node's owner refuses with "check-sound: …"
- **THEN** the node's record states the outcome `refuse` and that line as its refusal

#### Scenario: A run that a signal ends where it stands

- **WHEN** a node's run holds no narration process and no renderer and is sent SIGTERM
- **THEN** no run record is written or replaced

### Requirement: A narration of part of an edition writes a partial record

A narration of chosen segments or of its checks alone SHALL write, in place of the node's record, a partial record of the node's outputs as they stand after it, its outcome and its time. A partial record SHALL never make its node fresh, and SHALL make it stale where the outputs it states differ from those the node's record states.

#### Scenario: A retake is accounted for and leaves the narration stale

- **WHEN** `python -m filmkit.narration.narrate --language zh --ids 24` ends
- **THEN** a partial record of `narrate` binds the takes folder as it stands, the plan reports the narration stale as changed by a partial run, and `filmkit verify` refuses for the narration's staleness alone, naming no take as changed

### Requirement: A film is built by its targets

`filmkit build [TARGET…]` SHALL visit each target and every node upstream of it, by its inputs or by what it waits for, one at a time in the derived order, judge each again at its turn and run it only where it is stale. A node that refuses or fails SHALL stop every node downstream of it while the others go on, and the command SHALL then exit with one line for each refusal and failure, 2 where a node failed and 1 otherwise. It SHALL write no tracked file.

#### Scenario: A second build runs nothing

- **WHEN** `filmkit build sound:zh` runs twice with nothing changed between the runs
- **THEN** the second run runs no node and exits 0

#### Scenario: A change reaches its readers alone

- **WHEN** a hearing is recorded in the declaration's `narration` table after a whole build and `filmkit build all` runs
- **THEN** `check` and the nodes that read the `narration` table run again and pass, `check-sound` among them, all light; until `key-outputs-by-their-inputs` retires the picture gate's own binding of the whole declaration, `check-picture` of each edition runs again too, and both pictures of each edition after it

#### Scenario: A refusal stops what follows it

- **WHEN** `check-sound:zh` refuses during `filmkit build sound:all`
- **THEN** no node downstream of it runs, `check-sound:en` runs, and the command exits 1 with the Chinese gate's line

### Requirement: A refusal stands until what its node reads changes

`filmkit build` SHALL not run a node whose last run refused while nothing it reads has changed since, but the narration, which no build runs; that refusal SHALL stand as the node's, in its own line, and hold every node downstream of it.

#### Scenario: A refusal stands until what its node reads changes

- **WHEN** `check-sound:zh` refused, nothing it reads has changed since, and `filmkit build render-picture:zh` runs
- **THEN** it runs no node, holds the render and exits 1 with the gate's line; once an input of the gate changes, the gate runs again

### Requirement: Light work that can run now runs first, outside any heavy invocation

Before it runs any node, `filmkit build` SHALL refuse a stale `narrate`, naming `filmkit narrate` with the edition; and heavy work that will run while a light node with no stale heavy or GPU node upstream of it is stale or did not pass, naming `filmkit build` with those light nodes. A node whose refusal stands, and every node downstream of it, SHALL count as no work that will run. A closure with no heavy work that will run SHALL run. A node's class is its measured class, else its expected class.

#### Scenario: Narration is not built

- **WHEN** the Chinese script changed after its narration and `filmkit build all` runs
- **THEN** it runs nothing and names `filmkit narrate --edition zh`

#### Scenario: Light work first

- **WHEN** the sample holds the records of its source check and its narration alone and `filmkit build all` runs
- **THEN** it runs nothing and names `filmkit build` with the light nodes that can run now, the sound chain, the stages and the cover check among them

#### Scenario: The light invocation runs

- **WHEN** the invocation that refusal names runs
- **THEN** it runs those nodes, outside any heavy node, and a refusal of `check-sound` is met there

#### Scenario: Light steps after a heavy node

- **WHEN** `render-picture:zh` is stale, every light node that can run now is fresh and passed, and the heavy nodes of `picture:zh` that will run are measured, their last seconds summing to at most 1,800 s
- **THEN** `filmkit build picture:zh` runs the render and then `validate-picture:zh`, which follows it

### Requirement: Heavy nodes of several names share an invocation only when measured

`filmkit build` SHALL refuse heavy nodes of more than one name that will run, unless each has a measured class and their last seconds sum to at most 1,800 s, and print the invocations to run in order, one name each, with class and last seconds. A heavy node will run where it is stale or behind, never where it is waiting. An unmeasured node expected light SHALL run as light and record its measured class.

#### Scenario: Unmeasured heavy work, one invocation each

- **WHEN** every light node of the sample that can run now is fresh and passed, its heavy nodes have no record, and `filmkit build all` runs
- **THEN** it runs nothing and prints one invocation for each heavy node name, in the derived order

#### Scenario: Measured heavy work within 30 minutes

- **WHEN** every heavy node of the sample is stale and measured, and their last seconds sum to 220 s
- **THEN** `filmkit build all` runs them all in one invocation

### Requirement: A target names a node, a group or all

The plan and the build SHALL take as a target a node, or one of the groups `sound`, `audit`, `picture` and `package`, for one edition or for `all`; the film-wide node `check`; or `all`, which holds every node but `narrate`. A target that names none of these SHALL be refused in one line naming the groups and nodes.

#### Scenario: A group's target

- **WHEN** `filmkit plan picture:zh --json` runs
- **THEN** it lists `render-picture:zh`, `render-picture-uncaptioned:zh`, `validate-picture:zh`, `validate-picture-uncaptioned:zh`, `compare-pictures:zh`, the qualification where the film qualifies Chinese, and every node upstream of them

#### Scenario: An unknown group

- **WHEN** `filmkit build pictures:zh` runs
- **THEN** it is refused in one line that names the groups and nodes, and no node runs

### Requirement: A heavy node waits for the gates on its inputs

A render of either picture and a package of an edition SHALL wait for that edition's sound gate and cover check; a render of either picture SHALL also wait for every edition's picture gate and geometry check, and, where the film declares drafts, every edition's draft; and every heavy or GPU node SHALL wait for the film's `check`. A wait SHALL bind none of the gate's bytes, and a wait on a node the table lacks SHALL be dropped when the table loads.

#### Scenario: A refused sound gate holds the render

- **WHEN** `check-sound:zh` refused, a thought under the film's thought line that the owner did not hear clear
- **THEN** the plan reports `render-picture:zh` and `package-film:zh` waiting and not ready, naming `check-sound:zh`, and while nothing the gate reads changes, `filmkit build render-picture:zh` runs nothing and exits 1 with the gate's line

#### Scenario: Another edition's geometry holds the render

- **WHEN** `geometry-check:en` refused
- **THEN** the plan reports `render-picture:zh` waiting and not ready, naming `geometry-check:en`

#### Scenario: A gate run again leaves the render fresh

- **WHEN** `check` and `check-sound:zh` run again after a whole build and pass with records that differ from their last, and no input of `render-picture:zh` or `package-film:zh` changed
- **THEN** `render-picture:zh` and `package-film:zh` are fresh and do not run

#### Scenario: No draft declared

- **WHEN** the film declares no drafts
- **THEN** the table loads and no render waits for a draft

#### Scenario: Narration waits for the words check

- **WHEN** a picture module changes after a whole build
- **THEN** `check` is stale, the narration of each edition is waiting for it and not stale, and once `check` passes the narration is fresh

### Requirement: A node held by a gate is waiting, not behind

The plan SHALL state a node `waiting` when it is fresh by its own record, no node upstream of it by its inputs is stale or behind, and a gate it waits for, directly or through a node upstream of it, is not fresh and passed; and `behind` only when a node upstream of it by its inputs is stale or behind. It SHALL name, for a waiting node, each gate it waits for with that gate's state. A waiting node SHALL not be ready, and `filmkit verify` SHALL refuse it.

#### Scenario: An English retake

- **WHEN** an English thought is retaken and `check-picture:en` is stale after its sound is built again
- **THEN** the plan states `render-picture:zh` and the Chinese nodes after it waiting, naming `check-picture:en`, and `filmkit build all` counts none of them as heavy work that will run

#### Scenario: An edit that only the source check reads

- **WHEN** a source that only `check` reads changes after a whole build
- **THEN** `check` is stale and every other node is waiting or fresh, none behind

### Requirement: A film-wide node is recorded for the film

A node SHALL state whether it runs once for the film or once for each edition it applies to. A film-wide node's record SHALL stand at `build/evidence/records/film/<node>.json`, and the plan and verification SHALL judge it as they judge an edition's node. The film's source check SHALL be such a node, named `check`.

#### Scenario: The source check's record

- **WHEN** `filmkit check` passes
- **THEN** `build/evidence/records/film/check.json` names every source it read among its inputs, and its verdict and each edition's occurrence plan among its outputs

#### Scenario: A render waits for the source check

- **WHEN** `check` refused
- **THEN** the plan reports `render-picture:zh` not ready, whatever the state of the nodes upstream of it

### Requirement: A node binds the tables of the declaration it reads

A node SHALL bind each top-level table of the film's declaration that its run reads, each by the SHA-256 of its canonical JSON, and no other part of the declaration. When `FILMKIT_OPENS` names a file, the check of what each run opens SHALL also fail a read of a table that the node does not declare, and SHALL report each table a node declares that its run did not read, beyond the film's identity and editions, which every run reads as the engine loads.

#### Scenario: A hearing recorded reaches the readers of the narration table

- **WHEN** a record of the owner's hearing is added to the declaration's `narration` table after a whole build
- **THEN** the nodes that declare the `narration` table are stale, no render and no package is stale by a table of the declaration, and until `key-outputs-by-their-inputs` `check-picture` is stale through its owner's binding of the whole declaration

#### Scenario: An undeclared table

- **WHEN** a node's run reads the declaration's `review` table and the node does not declare it
- **THEN** the check fails, naming the node and the table

#### Scenario: A table declared and not read

- **WHEN** a node declares the declaration's `picture` table and its run does not read it
- **THEN** the check reports the table under the node

#### Scenario: The player's colours

- **WHEN** the declaration's `player` table is edited after a whole build
- **THEN** of the nodes that bind tables, only the two packages of each edition are stale by a table of the declaration

### Requirement: A node that encodes binds the host's encoders

A node that runs FFmpeg, ffprobe or ExifTool SHALL state the version of each among its pins, and SHALL be stale where the host's version differs from its record's.

#### Scenario: An FFmpeg upgrade

- **WHEN** the host's FFmpeg moves from 9.1 to another version after a whole build
- **THEN** every render and `package-film` of each edition are stale with both versions named, and `check-picture`, which runs no encoder, stays fresh

### Requirement: A run record states its own measurement

A run record SHALL state the engine's version, the SHA-256 of the engine's `released.json`, the model snapshots and host tools its node declares, and its start, seconds, 1-minute load at both ends, phases and settings. No other record of a run's duration SHALL be written, and `filmkit plan` SHALL print each listed node's last seconds, their sum and their span from the first start to the last end.

#### Scenario: A narration names its model

- **WHEN** a whole narration of an edition ends
- **THEN** its record names the voice, recognizer and aligner snapshots by repository and revision

#### Scenario: No duration record

- **WHEN** `filmkit build check-sound:zh` ends
- **THEN** no file is written below `build/evidence/editions/zh/durations/`

#### Scenario: A build's seconds

- **WHEN** `filmkit plan` runs after the sample was built
- **THEN** it prints each node's last seconds, their sum and their span

### Requirement: Verification requires every node fresh and passing, and every byte accounted for

`filmkit verify` SHALL hash every input and output of every standing record and write no file. It SHALL exit with status 1, naming each path or node, for bytes that no record of a declared writer accounts for; for a node that size and time call fresh whose digests differ; for a node of the table without a record; and for a node that is stale, behind or waiting, or whose outcome is not `pass`.

#### Scenario: A change that keeps size and time is caught

- **WHEN** a timeline's bytes are changed and its size and modification time restored
- **THEN** the plan still reports its readers fresh, and `filmkit verify` names the timeline and every node that binds it, and exits 1

#### Scenario: A whole build verifies

- **WHEN** every node of the sample's table and `check` have run and passed, the Chinese uncaptioned picture rendered natively and a repair run
- **THEN** `filmkit verify` exits 0

#### Scenario: An edited script refuses

- **WHEN** a script changes after a whole build
- **THEN** `filmkit verify` names the readers of the script as stale and exits 1

#### Scenario: A build without records refuses

- **WHEN** no run record stands
- **THEN** `filmkit verify` names every node as without a record and exits 1

## MODIFIED Requirements

### Requirement: A redo writes the records of the nodes it redoes

A command that is no node but runs a node's work again SHALL open that node's run inside its own, with the node's inputs and outputs, and write that node's run record. The repair (`python -m filmkit.picture.repair`) SHALL so write the records of each render and comparison it runs.

#### Scenario: A repaired picture verifies

- **WHEN** `python -m filmkit.picture.repair --language zh` renders the captioned picture again and its comparison passes
- **THEN** the records of `render-picture` and `compare-pictures` bind the repaired picture and the new comparison, and `filmkit verify` passes on a build whose other nodes are fresh

### Requirement: Freshness compares size and time first and hashes only on change

A node SHALL be fresh when its record passed, binds the running engine and pins and the inputs of the way it recorded, and every input and output has its recorded size and time or else its recorded SHA-256, a path several runs write judged by its latest declared writer. It SHALL be stale otherwise, each reason named; behind when a node upstream of it by its inputs is stale, behind, failed or unrecorded; and waiting as "A node held by a gate is waiting, not behind" states.

#### Scenario: A touched file is hashed once and stays fresh

- **WHEN** a script's modification time changes and its bytes do not
- **THEN** the plan hashes that script once, finds its digest unchanged and reports every node that reads it fresh

#### Scenario: An edited script makes its readers stale

- **WHEN** a script's bytes change
- **THEN** every node that reads the script is stale with that input named, and every node after them by its inputs is behind

#### Scenario: The uncaptioned picture's inputs follow its way

- **WHEN** the Chinese uncaptioned picture was rendered with `--native` and the English one derived
- **THEN** the Chinese record states the way `native` and binds its own stage, the English states `derived` and binds the captioned picture, and each is judged by its own way's inputs

### Requirement: Each node's inputs are what its run reads, stated once

Each node SHALL take its inputs from one function of paths, the owner's where the owner binds its inputs. When `FILMKIT_OPENS` names a file, every engine Python process SHALL record its opens, renames and child processes there and Node SHALL run in permission audit mode, publishing each access outside the node's declaration to that file; a check SHALL fail an undeclared read or write below the film's root.

#### Scenario: The sound gate's binding is one complete list

- **WHEN** the sound gate writes its record and the plan judges the node `check-sound`
- **THEN** both read the one function that names the soundtrack, the timeline, the assembly record, the selected narration and the declaration's tables the gate reads

#### Scenario: A read the table does not state fails the check

- **WHEN** a node's command, or a Python or Node process it starts, opens a file below the film's root that its inputs do not name
- **THEN** the check fails, naming the node, the process and the file

#### Scenario: Recording changes no run

- **WHEN** a node that starts the browser runs with `FILMKIT_OPENS` set
- **THEN** it reads, writes and reaches the network as it does without the variable, and its accesses outside its declaration are recorded, not refused

#### Scenario: A write through a rename is the target's

- **WHEN** a node's run writes a record through `repository.write`
- **THEN** the check counts the record's own path as written and the `.partial` sibling as no write

#### Scenario: What the engine reads as it starts is judged alike in every process

- **WHEN** a child of a node's run starts the engine, whose film loader validates every file the declaration names and whose modules read every script for the chapter count
- **THEN** the check reports those reads as the exemption `start-up` with the node, as a command's own start-up before its run opens is not recorded, and fails none of them

#### Scenario: A file looked for and not found

- **WHEN** a node's process opens for reading a file that does not stand
- **THEN** the check lets it through where the node would declare the file were it to stand, and otherwise fails it, naming the file as looked for

#### Scenario: What the check cannot see is named

- **WHEN** the check reports on a node whose run starts FFmpeg, ffprobe, ExifTool, `mdimport` or Chrome
- **THEN** it names the node as seen through those tools' arguments only

### Requirement: The plan states what is stale and ready, and changes nothing

`filmkit plan [TARGET…] [--json]` SHALL report, for each node a target names and every node upstream of it, in the derived order: its state and reasons, its class, its expected class, its last seconds, and whether it is ready, which needs every node upstream, by its inputs or by what it waits for, fresh with a passing outcome and every declared input present. It SHALL run no node and write no file.

#### Scenario: ETHOS reads the plan

- **WHEN** `filmkit plan render-picture:zh --json` runs on a sample whose sound is fresh and whose picture gate is stale
- **THEN** the JSON names `check-picture:zh` stale and ready, `light` with its seconds, and `render-picture:zh` behind, `heavy`, and not ready

#### Scenario: A plan leaves the build as it found it

- **WHEN** a plan runs while a node's input has a new modification time and its old bytes
- **THEN** no file below `build/` is created, changed or removed

## REMOVED Requirements

### Requirement: Each run of a build node writes one run record

**Reason**: it named the duration record and a run of the geometry check by hand, which retire.

**Migration**: "Each run of a node writes one run record, for its edition or for the film".

### Requirement: A run of part of a node writes a partial record

**Reason**: the stage of another place or size and the check of other places leave with `produce` and `filmkit.tools`.

**Migration**: "A narration of part of an edition writes a partial record".

### Requirement: A run record and its duration record come from one measurement

**Reason**: the duration record retires; the run record is the one record of a run's measurement.

**Migration**: "A run record states its own measurement"; `filmkit plan` prints the seconds that `python -m filmkit.durations` printed.

### Requirement: Verification refuses only bytes that no declared writer accounts for

**Reason**: verification now requires every node of the table recorded, fresh and passing, as R2a announced for R2b.

**Migration**: "Verification requires every node fresh and passing, and every byte accounted for".
