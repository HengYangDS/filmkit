## ADDED Requirements

### Requirement: The release record stands at the film's root

The release record SHALL stand at `release.json` in the film's root, beside `VERSION`. The loader SHALL refuse a film that holds `content/release.json`, naming the move, with every other refusal of the load.

#### Scenario: A record at its former place

- **WHEN** a film holds `content/release.json` and its declaration names a missing cover
- **THEN** the engine refuses the load naming both, the first as "move it to release.json"

### Requirement: Encoded streams are compared within one encoder version, and before encoding across versions

The release record SHALL state each film's FFmpeg version and each drawn UHD picture's drawn-frame digest. `filmkit verify --release` SHALL compare encoded audio and pictures only under the recorded version; under another, the audio through the soundtrack's bytes and each drawn picture through its digest, naming both versions. A derived picture, and any picture of a record without a version, SHALL be compared by decoded frames against the floor.

#### Scenario: A rebuild under another FFmpeg

- **WHEN** a film released under FFmpeg 9.1 is rebuilt under another version from byte-equal soundtracks and pictures drawn to the recorded frame digests
- **THEN** the comparison names both versions for the audio and the pictures, states them compared before encoding, and passes

#### Scenario: A soundtrack that differs across versions

- **WHEN** a film is rebuilt under another FFmpeg and one edition's soundtrack differs from its recorded bytes
- **THEN** the comparison refuses, naming the soundtrack

#### Scenario: Under the recorded version

- **WHEN** the running FFmpeg is the version the record states
- **THEN** each film's audio and picture are compared as the reproduction standard states

#### Scenario: A record from before this rule

- **WHEN** a release record states no FFmpeg version and no drawn-frame digest
- **THEN** the comparison reports the recorded encoder as unknown, compares the audio through the soundtrack's bytes and each film's picture by decoded frames against its floor

#### Scenario: A derived uncaptioned picture across versions

- **WHEN** an edition's uncaptioned picture was derived from its captioned one and the film is rebuilt under another FFmpeg
- **THEN** its uncaptioned films are compared by decoded frames against their floors, and its captioned films through the drawn-frame digest

## MODIFIED Requirements

### Requirement: A release record is written from the reviewed, delivered build

`filmkit release` SHALL write the release manifest and stage every asset it names, under its release name, with the checksums file. It SHALL do so only from a build whose bound inputs the film verifier accepts, whose staged pictures are current, whose recorded reviews cover its current films, and whose members the film's own delivery folder holds. The first refusal SHALL stop it before any file is written.

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

- **WHEN** `release.json` exists and cannot be read as a release manifest
- **THEN** the command refuses in one line that names the file, and no file changes

#### Scenario: A dry run

- **WHEN** the command runs with `--dry-run` on a build it would record
- **THEN** it prints the manifest it would write and no file changes

### Requirement: A stated source is a file of the film that is neither its record nor generated

The command SHALL take as a declared source a file below the film's root that is neither the release manifest nor below the folder that holds what the engine generates, and that no link leads to either or outside the root. It SHALL refuse any other by name, before any file is written. It compares paths as they are spelled.

#### Scenario: The record itself

- **WHEN** `[release] sources` names `release.json`, with or without a manifest to replace
- **THEN** the command refuses in one line that says it is the release record itself, and no file changes

#### Scenario: A path below the generated folder

- **WHEN** `[release] sources` names a file below `build/`, or a link elsewhere below the film's root that leads to one
- **THEN** the command refuses in one line that names the path, and no file changes

#### Scenario: A link that leads outside the film

- **WHEN** `[release] sources` names a link below the film's root that leads to a file outside it
- **THEN** the command refuses in one line that names the path, and no file changes

### Requirement: A record's film-bound sources are stated at every run

The command SHALL take the film-bound sources from the declaration's `[release] sources` at every run and SHALL record, in sorted order and each once, the SHA-256 of each path it names. It SHALL take no source from the manifest it replaces. It SHALL refuse a declared path that the manifest's model does not list as a source's path, in words that name that model and print its pattern, and a declared source that is not a file.

#### Scenario: A run without its sources

- **WHEN** the declaration states no `[release] sources`, with or without a manifest to replace
- **THEN** the command refuses and names `[release] sources`, and no file changes

#### Scenario: A script changed since the last release

- **WHEN** a script changed since the last release and `[release] sources` names it
- **THEN** the script's entry in the written manifest holds its current SHA-256

#### Scenario: A stated set replaces the listed one

- **WHEN** the manifest the command replaces lists a path that `[release] sources` does not name
- **THEN** the written manifest lists exactly the declared paths and not that one

#### Scenario: A source that is gone

- **WHEN** `[release] sources` names a path that is not a file
- **THEN** the command refuses and names the path

#### Scenario: A path the manifest's model does not list

- **WHEN** `[release] sources` names a file as `.config/policy.toml` or `content/My Notes.md`, by an absolute path, or by a path that holds `./` or `..`
- **THEN** the command refuses in one line that names the manifest's model of a source's path, prints that model's pattern and names the path

### Requirement: A release is recorded only on records that verify

Recording a release SHALL run `filmkit verify` before it stages an asset or writes the manifest, a dry run included, and SHALL refuse with each of its lines when it refuses. A node that is stale, behind or without a record SHALL refuse it too.

#### Scenario: A soundtrack changed by no declared writer

- **WHEN** an edition's soundtrack is changed after the record of `assemble` by a command that is no declared writer of it, and the release is recorded
- **THEN** recording refuses, naming the soundtrack and the node, and no asset or manifest is written

#### Scenario: Both editions wrote the entry page

- **WHEN** the release is recorded after both editions' `package-metadata` replaced the entry page
- **THEN** recording proceeds as it does today
