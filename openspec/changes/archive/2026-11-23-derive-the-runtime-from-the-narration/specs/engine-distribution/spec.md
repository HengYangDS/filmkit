## ADDED Requirements

### Requirement: The command reads what a film states of its runtime and credits

The command SHALL report, reading the files as text, each edition's script that declares `duration` or `credits_duration`, each edition's cast that declares `runtime_fit`, and each line of the film's review prompt that cites the runtime's field without saying "This edition", each with what to do instead. A declaration that states no `credits_duration` SHALL be reported once, by the question that reports the declaration's problems, in one line that says to declare the credits' length there.

#### Scenario: A film that has not adopted the release

- **WHEN** both scripts declare `duration` and `credits_duration`, a cast declares `runtime_fit` and the review prompt says "Each edition: exactly {duration} s"
- **THEN** one run names each key with its file and what to do instead, and the prompt's line with its number and the wording to use, and the command exits with a failure

#### Scenario: A declaration without the credits

- **WHEN** the declaration states no `credits_duration`
- **THEN** the command names it once, in one line that says to declare the credits' length there

#### Scenario: A prompt line that cites the runtime in other words

- **WHEN** a line of the review prompt cites the runtime's field, with a format or without one, and does not say "This edition"
- **THEN** the command names the line, whatever else it says, and a line that only escapes the field's braces is not named

#### Scenario: A film that holds what the release asks

- **WHEN** no script or cast declares a withdrawn key, the declaration states its credits and every line of the review prompt that cites the runtime says "This edition"
- **THEN** the question reports no finding
