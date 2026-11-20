## ADDED Requirements

### Requirement: A release record is written from the reviewed, delivered build

`filmkit.delivery.release` SHALL write the release manifest and stage every asset it names, under its release name, with the checksums file. It SHALL do so only from a build whose bound inputs the film verifier accepts, whose staged pictures are current, whose recorded reviews cover its current films, and whose members the film's own delivery folder holds. The first refusal SHALL stop it before any file is written.

#### Scenario: A reviewed and delivered build

- **WHEN** both editions are reviewed and delivered to the film's own folder, and the command runs
- **THEN** the release folder holds exactly every edition's films, captions, transcript, cover and review and the checksums file, each with the bytes the manifest records
- **AND** the manifest loads as a release manifest and states the film's version

#### Scenario: A bound input that moved

- **WHEN** an edition's soundtrack differs from the one its assembly record names
- **THEN** the command refuses in one line as the verifier words it, and no file changes

#### Scenario: A stale uncaptioned stage

- **WHEN** an edition's uncaptioned picture was derived and its staged document differs from the one its sources stage now
- **THEN** the command refuses in one line that names the edition and the uncaptioned picture, and no file changes

#### Scenario: An edition without a recorded review

- **WHEN** an edition has no production review record
- **THEN** the command refuses in one line that names the record, and no file changes

#### Scenario: A tracked manifest that is none

- **WHEN** `content/release.json` exists and cannot be read as a release manifest
- **THEN** the command refuses in one line that names the file, and no file changes

#### Scenario: A dry run

- **WHEN** the command runs with `--dry-run` on a build it would record
- **THEN** it prints the manifest it would write and no file changes

### Requirement: A release is recorded from what the film's own folder holds

The command SHALL compare every delivery member in the film's own delivery folder, as the host names that folder when the command runs, with the build's file, and SHALL refuse a member that is missing or holds other bytes, by its path.

#### Scenario: A build delivered only to a named folder

- **WHEN** the build was delivered to a folder named with `--destination` and the film's own folder holds an earlier build
- **THEN** the command refuses and names a member of the film's own folder that differs

#### Scenario: A delivery under the host's root

- **WHEN** the host names its delivery root, and the film's folder below it holds every member with the build's bytes
- **THEN** the command records the release

### Requirement: The release folder is not overwritten with other bytes unasked

The command SHALL refuse, naming the entries and `--replace`, a release folder that holds any entry other than an asset with the bytes the record would write; with `--replace` it SHALL replace the folder. It SHALL leave a folder that already holds exactly the record's assets, and otherwise stage the whole set beside the folder before it puts it in the folder's place. It SHALL write the manifest last. A release or staging path that is a link or no folder SHALL be refused by its path.

#### Scenario: A second run on the same build

- **WHEN** the command runs twice on one build
- **THEN** the second run's manifest and release folder hold the bytes the first run's held

#### Scenario: The films of the release before

- **WHEN** the release folder holds the last release's films and the command runs on a new build
- **THEN** the command refuses, names those films and `--replace`, and the folder and the manifest hold the bytes they held

#### Scenario: A record written again after its review was recorded again

- **WHEN** the folder holds this version's assets, an edition's review was recorded again, and the command runs with `--replace`
- **THEN** the folder holds exactly the new record's assets and the manifest names the new review's bytes

#### Scenario: A staging that fails

- **WHEN** the copy of an asset fails while the set is staged
- **THEN** the release folder and the manifest hold the bytes they held, and the next run stages again

#### Scenario: A path that is no folder

- **WHEN** the release folder's path, or the path of the folder the set is staged in, is a file or a link
- **THEN** the command refuses in one line that names the path, with `--replace` too, and nothing is staged or removed

### Requirement: A run that stops late is completed by the next run

A run that stops after it removed the release folder, or after it put the staged set in the folder's place and before it wrote the manifest, SHALL leave the tracked manifest as it was, and the next run SHALL complete the record without `--replace`.

#### Scenario: A run that stops before the staged set is in place

- **WHEN** a run stops after it removed the release folder and before it renamed the staged set to it
- **THEN** no release folder stands, the staged set is whole beside its place, and the manifest holds the bytes it held
- **AND** the next run, without `--replace`, stages the set again and writes the manifest

#### Scenario: A run that stops before the manifest is written

- **WHEN** the release folder was replaced and the manifest's write fails
- **THEN** the folder holds the new record's assets and the manifest the bytes it held
- **AND** the next run, without `--replace`, leaves the folder and writes the manifest

### Requirement: A record keeps each film's floor

The command SHALL record for each film the PSNR floor that the manifest it replaces states for a film of that name, and no floor for a film that manifest does not name, and SHALL print each film's floor or that it has none.

#### Scenario: A film's next release

- **WHEN** the replaced manifest states 45.0 dB for each of an edition's four films
- **THEN** the written manifest states 45.0 dB for each of them

#### Scenario: A film's first record

- **WHEN** no manifest exists and the command writes one
- **THEN** the manifest states no floor and the command names each film as without one

### Requirement: A record's film-bound sources are stated at every run

The command SHALL require `--sources` at every run and SHALL record, in sorted order and each once, the SHA-256 of each path it names. It SHALL take no source from the manifest it replaces. It SHALL refuse a stated path that the manifest's model does not list as a source's path, in words that name that model and print its pattern, and a stated source that is not a file.

#### Scenario: A run without its sources

- **WHEN** the command runs without `--sources`, with or without a manifest to replace
- **THEN** the command line refuses and names the option, and no file changes

#### Scenario: A script changed since the last release

- **WHEN** a script changed since the last release and the command runs with `--sources` naming it
- **THEN** the script's entry in the written manifest holds its current SHA-256

#### Scenario: A stated set replaces the listed one

- **WHEN** the manifest the command replaces lists a path that `--sources` does not name
- **THEN** the written manifest lists exactly the named paths and not that one

#### Scenario: A source that is gone

- **WHEN** `--sources` names a path that is not a file
- **THEN** the command refuses and names the path

#### Scenario: A path the manifest's model does not list

- **WHEN** `--sources` names a file as `.config/policy.toml` or `content/My Notes.md`, by an absolute path, or by a path that holds `./` or `..`
- **THEN** the command refuses in one line that names the manifest's model of a source's path, prints that model's pattern and names the path

### Requirement: A stated source is a file of the film that is neither its record nor generated

The command SHALL take as a stated source a file below the film's root that is neither the release manifest nor below the folder that holds what the engine generates, and that no link leads to either or outside the root. It SHALL refuse any other by name, before any file is written. It compares paths as they are spelled.

#### Scenario: The record itself

- **WHEN** `--sources` names `content/release.json`, with or without a manifest to replace
- **THEN** the command refuses in one line that says it is the release record itself, and no file changes

#### Scenario: A path below the generated folder

- **WHEN** `--sources` names a file below `build/`, or a link elsewhere below the film's root that leads to one
- **THEN** the command refuses in one line that names the path, and no file changes

#### Scenario: A link that leads outside the film

- **WHEN** `--sources` names a link below the film's root that leads to a file outside it
- **THEN** the command refuses in one line that names the path, and no file changes

### Requirement: The command says which record it replaces

The command SHALL print the version of the manifest it replaces beside the version it writes, and SHALL refuse a film version the manifest cannot state, by name. Beside the versions it SHALL print each path the replaced manifest listed as a source that the run does not state, and each path the run states that the replaced manifest did not list, in a dry run too, and SHALL refuse nothing for either.

#### Scenario: A stated set that differs from the replaced list

- **WHEN** the manifest the command replaces lists one source that the run does not state, and the run states one that manifest did not list
- **THEN** the command's output names each of the two paths with what it is, in a dry run as in a run, and the record is written with the stated set

#### Scenario: The same version written again

- **WHEN** the manifest states version 1.0.2 and the command runs on a film whose `VERSION` is still 1.0.2
- **THEN** the record is written and the command's output says that it replaces a record of 1.0.2

#### Scenario: A pre-release version

- **WHEN** the film's `VERSION` holds a pre-release
- **THEN** the command refuses and says that a release manifest states three numbers
