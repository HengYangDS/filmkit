## ADDED Requirements

### Requirement: A delivery's destination is the caller's, the host's or the platform's videos folder

The delivery SHALL fill, in this order: the folder `--destination` names; the film's declared delivery folder below the root `FILMKIT_DELIVERY_ROOT` names; that folder below the user's videos folder, `~/Movies` on macOS and elsewhere the XDG videos directory. The engine SHALL name no other folder of a host. The delivery's readback and the command's summary SHALL state the destination and the rule that gave it.

#### Scenario: A folder the caller names

- **WHEN** the delivery runs with `--destination` naming a folder while `FILMKIT_DELIVERY_ROOT` is set
- **THEN** it fills that folder, and its readback states that folder and the rule `--destination`

#### Scenario: A host's delivery root

- **WHEN** the delivery runs without `--destination` on a host whose `FILMKIT_DELIVERY_ROOT` names a folder
- **THEN** it fills the film's declared delivery folder below that root, and its readback states the rule `FILMKIT_DELIVERY_ROOT`

#### Scenario: The videos folder on macOS

- **WHEN** the delivery runs on macOS with neither
- **THEN** it fills the film's declared delivery folder below `~/Movies`, and nothing below `~/Documents`

#### Scenario: The XDG videos directory

- **WHEN** the delivery runs elsewhere with neither
- **THEN** the videos folder is `XDG_VIDEOS_DIR` of the environment, else the `XDG_VIDEOS_DIR` line of `user-dirs.dirs` below `XDG_CONFIG_HOME` or `~/.config`, else `~/Videos`

#### Scenario: A dry run

- **WHEN** the delivery runs with `--dry-run`
- **THEN** its report states the destination and the rule, and the destination is not created
