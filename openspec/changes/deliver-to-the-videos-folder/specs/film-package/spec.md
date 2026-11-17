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

### Requirement: A delivery refuses a destination that is not its own to empty

Before it reads a player or changes anything, and in a dry run too, the delivery SHALL refuse: a `--destination` whose value is empty; a destination that, on resolved paths, is the film's root, holds it or lies inside it, whichever rule gave it; and one that is no folder, or that holds entries other than `.DS_Store` and `.claude` and no entry page of an earlier delivery. The refusal SHALL name the folder, the rule that gave it and what was found.

#### Scenario: An empty destination

- **WHEN** the delivery runs at the film's root with `--destination ""`, as an unset variable in a script leaves it
- **THEN** it refuses, naming the empty value, and no file below the root is moved

#### Scenario: The film's root, by each rule

- **WHEN** the destination resolves to the film's root or to a folder that holds it: named by the caller, as `.` or through a symbolic link; given by `FILMKIT_DELIVERY_ROOT` where the film's checkout has the name of its delivery folder; or given by the videos folder where the film is checked out inside its delivery folder
- **THEN** the delivery refuses, naming that rule and the film's root, and nothing is read back, run or written

#### Scenario: A folder that holds the root or lies inside it

- **WHEN** the destination is a folder above the film's root, or a folder below it
- **THEN** the delivery refuses, naming the film's root

#### Scenario: A populated folder that no delivery filled

- **WHEN** the destination holds a user's files and folders and no `index.html`
- **THEN** the delivery refuses, naming how many entries it holds and the first of them, and the folder is unchanged

#### Scenario: A folder an earlier delivery filled

- **WHEN** the destination holds the `index.html` of an earlier delivery and an entry beside the members
- **THEN** the delivery fills it, and that entry is moved into the predecessors

#### Scenario: A dry run refuses the same

- **WHEN** any of these destinations is given with `--dry-run`
- **THEN** the dry run refuses as the delivery does
