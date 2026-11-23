## ADDED Requirements

### Requirement: The film's declaration states the credits' length once

The film's declaration SHALL state `credits_duration`, the length of the credits in whole seconds, once for both editions, and the engine SHALL take the credits' length from it alone. A declaration that omits it, or states no whole number of seconds, SHALL be refused with the field named.

#### Scenario: A declaration without the credits

- **WHEN** `content/film.toml` states no `credits_duration`
- **THEN** the engine refuses the declaration, naming `credits_duration`

#### Scenario: Both editions take the declared credits

- **WHEN** the declaration states `credits_duration = 3`
- **THEN** each edition's assembly lays out its credits from 3 s

## MODIFIED Requirements

### Requirement: Each script declares its edition

Each edition's script SHALL declare the edition's title, author, language, frame rate, chapters and pronunciation contract, and SHALL NOT declare `duration` or `credits_duration`, which the narration and the film's declaration state. The engine SHALL refuse, before any work, scripts that disagree on the film's author or chapter count, that declare a frame rate other than 60 fps, or that declare either key. The two editions MAY differ in length.

#### Scenario: Scripts that disagree refuse before work

- **WHEN** the editions' scripts declare different authors or chapter counts, or a frame rate other than 60 fps
- **THEN** the engine refuses when it loads and names the value

#### Scenario: A script that declares a duration

- **WHEN** a script declares `duration`
- **THEN** the engine refuses when it loads with one line that names the script and the key and says to remove it, since an edition lasts as long as its narration

#### Scenario: A script that declares the credits

- **WHEN** a script declares `credits_duration`
- **THEN** the engine refuses when it loads with one line that names the script and the key and says to state the credits in the film's declaration instead

#### Scenario: Editions of different lengths

- **WHEN** the Chinese edition's narration gives a runtime of 1636 s and the English edition's 1476 s
- **THEN** the engine refuses neither edition for the difference
