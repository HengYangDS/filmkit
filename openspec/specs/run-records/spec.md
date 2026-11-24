# run-records Specification

## Purpose

Keep one record of every run of a film's build: what each node read and wrote, by size, time and digest, with the engine, the outcome, the time taken and the host class measured; and read those records alone to say what is stale, what is ready and whether every byte they cite was written by a declared writer.

## Requirements

### Requirement: Each run of a build node writes one run record

Each command of an edition's build chain SHALL write, when it ends, one run record for its node and edition at `build/evidence/records/editions/<code>/<node>.json`, replacing the node's previous record, and none where its duration record is not written. It SHALL bind each record its owner writes as an output by digest and copy none of that record's fields.

#### Scenario: A gate's run is recorded

- **WHEN** `produce check-sound --language zh` ends after measuring the soundtrack
- **THEN** `build/evidence/records/editions/zh/check-sound.json` names the soundtrack, the timeline, the assembly record and the declaration among its inputs and `sound-gates.json` among its outputs, each with its size, modification time and SHA-256, and states no finding

#### Scenario: A refused run is recorded as refused

- **WHEN** an action's owner refuses and the command ends with "check-sound: …"
- **THEN** the node's record states the outcome `refuse` and that line as its refusal

#### Scenario: A run that writes no duration record writes no run record

- **WHEN** the geometry check runs with arguments that name no edition of the film
- **THEN** no run record is written or replaced

### Requirement: A run record and its duration record come from one measurement

A run record SHALL state the engine's version, the SHA-256 of the engine's `released.json` and the model snapshots its node declares. Its start, seconds, 1-minute load at both ends, phases and settings SHALL be taken from the measurement that writes the command's duration record, which is the run's own and no owner's record.

#### Scenario: One measurement, two records

- **WHEN** a chain command ends and writes both records
- **THEN** both state the same start, seconds, load, phases and settings

#### Scenario: A narration names its model

- **WHEN** a whole narration of an edition ends
- **THEN** its record names the voice, recognizer and aligner snapshots by repository and revision

### Requirement: A run of part of a node writes a partial record

A narration of chosen segments or of its checks alone, a stage written to another place or size than the node's, and a check whose arguments name other places SHALL write, in place of the node's record, a partial record of the node's outputs as they stand after it, its outcome and its time. A partial record SHALL never make its node fresh, and SHALL make it stale where the outputs it states differ from those the node's record states.

#### Scenario: A retake is accounted for and leaves the narration stale

- **WHEN** `narrate --language zh --ids 24` ends
- **THEN** a partial record of `narrate` binds the takes folder as it stands, the plan reports the narration stale as changed by a partial run, and `filmkit verify` refuses nothing for it

#### Scenario: A stage written elsewhere

- **WHEN** `produce stage-picture --language zh --output build/runtime/work/trial` ends
- **THEN** the node's run record is not replaced, a partial record states the node's outputs as they stand after it, and the plan leaves the node fresh, since the run changed none of them

### Requirement: A redo writes the records of the nodes it redoes

A command that is no node but runs a node's work again SHALL open that node's run inside its own, with the node's inputs and outputs, and write that node's run record and no second duration record. `repair-pictures` SHALL so write the records of each render and comparison it runs.

#### Scenario: A repaired picture verifies

- **WHEN** `repair-pictures --language zh` renders the captioned picture again and its comparison passes
- **THEN** the records of `render-picture` and `compare-pictures` bind the repaired picture and the new comparison, the repair's duration record counts its seconds once, and `filmkit verify` passes

### Requirement: Each node's inputs are what its run reads, stated once

Each node SHALL take its inputs from one function of paths, the owner's where the owner binds its inputs. When `FILMKIT_OPENS` names a file, every engine Python process SHALL record its opens, renames and child processes there and Node SHALL run in permission audit mode, publishing each access outside the node's declaration to that file; a check SHALL fail an undeclared read or write below the film's root.

#### Scenario: The sound gate's binding is one complete list

- **WHEN** the sound gate writes its record and the pre-render check judges it
- **THEN** both, and the node `check-sound`, read the one function that names the soundtrack, the timeline, the assembly record and the declaration

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

### Requirement: The order of nodes is derived from their paths and declared writers

The engine SHALL derive each edge from the paths and order the nodes with `graphlib.TopologicalSorter`. A path that several nodes write SHALL name each writer as one that rewrites it after named writers or one that replaces it whole. A node that reads such a path SHALL come after every writer of it but a rewriter that names the reader among the nodes it follows. A cycle, and a path two nodes write without that declaration, SHALL refuse the table when it loads, naming the nodes or the path.

#### Scenario: A rewritten timeline has one producer for its reader

- **WHEN** `refresh-captions` is declared to rewrite the timeline after `assemble`
- **THEN** `refresh-captions` follows `assemble`, and `check-sound` follows both

#### Scenario: A reader that a rewriter follows comes before it

- **WHEN** `refresh-captions` is declared to rewrite the selected narration after `select` and `assemble`, and `assemble` reads it
- **THEN** the table loads with `assemble` before `refresh-captions`, and `assemble`'s binding of the selected narration holds through the record of `refresh-captions`

#### Scenario: An undeclared second writer is refused

- **WHEN** a table holds two nodes that write one path with no declaration of how
- **THEN** loading the table refuses, naming the path and both nodes

### Requirement: A node applies to the editions it declares

A node SHALL state the editions it applies to, every edition by default, and the plan and `filmkit verify` SHALL neither list nor wait on a node of an edition it does not apply to.

#### Scenario: The renderer is qualified once a build

- **WHEN** a film's chain qualifies the renderer for one edition, its first declared one or the one `[picture] qualified_edition` names
- **THEN** the table holds no `qualify-renderer` of any other edition, and a plan of that build states every node fresh

### Requirement: A file several runs write is bound by its latest declared writer, in order

The latest standing record of a declared writer SHALL bind a path's current bytes. An earlier writer's binding, and the binding of a reader that a rewriter follows, SHALL hold only through a later run of a writer declared after it, which for a rewrite read the bytes so bound, or of a peer that replaces the file, where that later run's binding holds in turn. A run of a writer SHALL make every writer declared after it stale until it runs again, whatever the bytes.

#### Scenario: Both editions write the entry page

- **WHEN** `package-metadata` of the Chinese edition and then of the English edition each replace the entry page
- **THEN** the English record binds the page, the Chinese record's binding holds through it, and neither node is stale for the page

#### Scenario: An earlier writer runs again

- **WHEN** `assemble` runs again after `refresh-captions` and writes the bytes it wrote before
- **THEN** `refresh-captions` is stale as its output was replaced by an earlier writer's run, `check-sound` is behind and not ready, and `filmkit verify` lists both and exits 0

#### Scenario: A rewriter replaced carries no reader's binding

- **WHEN** `select` runs again after `refresh-captions` rewrote the selection that `assemble` read
- **THEN** `assemble` is stale for the selection, and `refresh-captions` as its output was replaced by an earlier writer's run

#### Scenario: A hand edit fails closed

- **WHEN** the entry page is edited after both packages wrote it
- **THEN** both `package-metadata` nodes are stale, naming the page as changed by no declared writer, and `filmkit verify` refuses

### Requirement: Bytes a rewriter carried forward from no declared writer fail closed

Bytes that a rewriter read after a run of a writer it follows, which no declared writer's run between the two wrote, SHALL be bytes that no declared writer accounts for, though the file equals the rewriter's record.

#### Scenario: A rewriter run again on its own output verifies

- **WHEN** the script is edited twice for its captions alone, and `refresh-captions` and `check-sound` run after each edit
- **THEN** `filmkit verify` refuses nothing, since each run of `refresh-captions` read what its own previous run wrote

#### Scenario: A hand edit that a rewriter carried forward fails closed

- **WHEN** the timeline is edited by hand after `assemble` and before `refresh-captions` rewrites it
- **THEN** `assemble` and `refresh-captions` are stale, naming the timeline as changed by no declared writer, and `filmkit verify` refuses

### Requirement: Freshness compares size and time first and hashes only on change

A node SHALL be fresh when its record passed, binds the running engine and pins and the inputs of the way it recorded, and every input and output has its recorded size and time or else its recorded SHA-256, a path several runs write judged by its latest declared writer. It SHALL be stale otherwise, each reason named, and behind when a node upstream is stale, failed or unrecorded.

#### Scenario: A touched file is hashed once and stays fresh

- **WHEN** a script's modification time changes and its bytes do not
- **THEN** the plan hashes that script once, finds its digest unchanged and reports every node that reads it fresh

#### Scenario: An edited script makes its readers stale

- **WHEN** a script's bytes change
- **THEN** every node that reads the script is stale with that input named, and every node after them is behind

#### Scenario: The uncaptioned picture's inputs follow its way

- **WHEN** the Chinese uncaptioned picture was rendered with `--native` and the English one derived
- **THEN** the Chinese record states the way `native` and binds its own stage, the English states `derived` and binds the captioned picture, and each is judged by its own way's inputs

### Requirement: Each node's host class is measured as the host rules measure it

Each run SHALL record its CPU time over its wall time, every waited-for descendant included, and its process tree's summed `%cpu` sampled every five seconds. A node SHALL be `gpu` where it declares model work, else `heavy` where this run or its previous record measured over two cores by either measure, else `light`. A node without a record SHALL be `unmeasured`.

#### Scenario: Heavy stays heavy

- **WHEN** a node's previous record measured heavy and its next run measures light
- **THEN** its next record's class is `heavy`, beside the raw measures of that run

#### Scenario: A cleared build forgets nothing silently

- **WHEN** `build/` is cleared
- **THEN** the plan states every node as `unmeasured` with its expected class, never as `light`

### Requirement: The plan states what is stale and ready, and changes nothing

`filmkit plan [TARGET…] [--json]` SHALL report, for each node asked for and every node upstream of it, in the derived order: its state and reasons, its class, its expected class, its last seconds, and whether it is ready, which needs every node upstream fresh with a passing outcome and every declared input present. It SHALL run no node and write no file.

#### Scenario: ETHOS reads the plan

- **WHEN** `filmkit plan render-picture:zh --json` runs on a sample whose sound is fresh and whose picture gate is stale
- **THEN** the JSON names `check-picture:zh` stale and ready, `light` with its seconds, and `render-picture:zh` behind, `heavy`, and not ready

#### Scenario: A plan leaves the build as it found it

- **WHEN** a plan runs while a node's input has a new modification time and its old bytes
- **THEN** no file below `build/` is created, changed or removed

### Requirement: Verification refuses only bytes that no declared writer accounts for

`filmkit verify` SHALL hash every input and output of every standing record, write no file, and exit with status 1 only for bytes that no record of a declared writer accounts for, and for a node that size and time call fresh whose digests differ, naming each path and node. A node stale for another reason SHALL be listed and refuse nothing.

#### Scenario: A change that keeps size and time is caught

- **WHEN** a timeline's bytes are changed and its size and modification time restored
- **THEN** the plan still reports its readers fresh, and `filmkit verify` names the timeline and every node that binds it, and exits 1

#### Scenario: A whole build of the sample verifies

- **WHEN** the sample's chain has run, the Chinese uncaptioned picture rendered with `--native`, a repair run, and a script then edited
- **THEN** `filmkit verify` lists the readers of the script as stale and exits 0

#### Scenario: A build without records verifies

- **WHEN** no run record stands
- **THEN** `filmkit verify` reports that it checked no record and exits 0
