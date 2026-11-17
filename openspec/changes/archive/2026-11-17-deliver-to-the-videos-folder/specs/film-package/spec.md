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

#### Scenario: The videos line as xdg-user-dirs writes it

- **WHEN** the `XDG_VIDEOS_DIR` line of `user-dirs.dirs` holds its value in double or in single quotes, as `$HOME/...` or as an absolute path, with or without a comment after it
- **THEN** that folder is the videos folder, and of several such lines the last counts

#### Scenario: A videos line that cannot be used

- **WHEN** that line holds a relative value, a value without quotes or anything else after the value than a comment
- **THEN** the videos folder is `~/Videos`, and the rule the readback records says that the file's line was not usable and gives the line

#### Scenario: A dry run

- **WHEN** the delivery runs with `--dry-run`
- **THEN** its report states the destination and the rule, and the destination is not created

### Requirement: A delivery refuses a destination that is not its own to empty

Before it reads a player or changes anything, and in a dry run too, the delivery SHALL refuse: an empty `--destination`; a `FILMKIT_DELIVERY_ROOT` that is no absolute path; a destination that is the film's root, holds it or lies inside it, however its path is spelled and whichever rule gave it; and one that is no folder, or holds entries other than `.DS_Store` and `.claude` and no entry page of an earlier delivery. The refusal SHALL name the folder, the rule that gave it and what was found.

#### Scenario: An empty destination

- **WHEN** the delivery runs at the film's root with `--destination ""`, as an unset variable in a script leaves it
- **THEN** it refuses, naming the empty value, and no file below the root is moved

#### Scenario: The film's root, by each rule

- **WHEN** the destination resolves to the film's root or to a folder that holds it: named by the caller, as `.` or through a symbolic link; given by `FILMKIT_DELIVERY_ROOT` where the film's checkout has the name of its delivery folder; or given by the videos folder where the film is checked out inside its delivery folder
- **THEN** the delivery refuses, naming that rule and the film's root, and nothing is read back, run or written

#### Scenario: A folder that holds the root or lies inside it

- **WHEN** the destination is a folder above the film's root, or a folder below it
- **THEN** the delivery refuses, naming the film's root

#### Scenario: The film's own tree under another spelling

- **WHEN** the destination names the film's root, a folder above it or a folder below it, one that does not exist yet among them, in another letter case on a volume that folds case, through a symbolic link above it, or by a second path to the same volume
- **THEN** the delivery refuses as it does for the spelling the root has, and no file of the film is moved

#### Scenario: A host's root that is no absolute path

- **WHEN** `FILMKIT_DELIVERY_ROOT` is a relative path or holds only blanks
- **THEN** the delivery refuses, naming the variable and its value, and fills no folder below the working directory

#### Scenario: A populated folder that no delivery filled

- **WHEN** the destination holds a user's files and folders and no `index.html`
- **THEN** the delivery refuses, naming how many entries it holds and the first of them, and the folder is unchanged

#### Scenario: A folder an earlier delivery filled

- **WHEN** the destination holds the `index.html` of an earlier delivery and an entry beside the members
- **THEN** the delivery fills it, and that entry is moved into the predecessors

#### Scenario: A dry run refuses the same

- **WHEN** any of these destinations is given with `--dry-run`
- **THEN** the dry run refuses as the delivery does
