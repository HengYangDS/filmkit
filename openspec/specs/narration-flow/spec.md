# narration-flow Specification

## Purpose

Keep each thought's speech joined where its text is joined, and keep adjacent thoughts sounding like one continuous reading.

## Requirements

### Requirement: The heard pause at every word boundary is measured

For each pair of adjacent aligned words of a take or of a soundtrack, the measurement SHALL record the heard pause: the longest run of 10 ms frames at least 24 dB below the speech median between the middles of the two words. With it the measurement SHALL record the marks the text holds between the words, and whether the words switch between Chinese characters and Latin letters or digits.

#### Scenario: A pause inside a phrase at a script switch

- **WHEN** a take holds 0.49 s of quiet between 的 and Agent in 可以互相替换的 Agent
- **THEN** the measurement records a 490 ms pause at that boundary, with no mark and a script switch

#### Scenario: A pause at a comma

- **WHEN** a take pauses 0.34 s at a comma
- **THEN** the measurement records the pause with its mark

### Requirement: An unmarked pause above its limit refuses the narration

Selecting takes and assembling a soundtrack SHALL refuse a heard pause above its limit at a boundary whose text holds no mark. The limit is 0.2 s at a script switch and 0.4 s elsewhere, unless the film declares other limits in `[narration.flow]`. A refusal SHALL name the edition, the thought, both words and the pause. A film MAY declare an exception for one boundary, with its reason; an exception that no boundary matches SHALL be refused.

#### Scenario: A 0.49 s pause at a script switch

- **WHEN** the selected take of a thought holds a 0.49 s pause between 的 and Agent
- **THEN** selection refuses and names the edition, the thought, 的, Agent and 0.49 s

#### Scenario: A clause boundary without a comma

- **WHEN** an English take pauses 0.36 s between "commit" and "and"
- **THEN** selection does not refuse, and the listening plan lists the boundary

### Requirement: Auditions prefer fluent takes

An audition SHALL record each candidate's longest unmarked pause and SHALL NOT propose a take with an unmarked pause above its limit while another qualifying take of the thought has none.

#### Scenario: A fluent take and a halting take

- **WHEN** two candidates of a thought qualify and only one holds a 0.45 s pause at a script switch
- **THEN** the audition proposes the other take

### Requirement: Continuity between adjacent thoughts is recorded for listening

For each pair of adjacent thoughts in one part, the measurement SHALL record the ratio of their speaking rates, the step of their median pitch in semitones and the step of their level in decibels. The listening plan SHALL list the largest steps, together with the unmarked pauses of 0.15 s or more that stay within their limits, for human listening. These steps SHALL NOT refuse a soundtrack.

#### Scenario: A faster thought

- **WHEN** a thought is spoken 1.49 times as fast as the thought before it in the same part
- **THEN** the measurement records the ratio and the listening plan lists the step
