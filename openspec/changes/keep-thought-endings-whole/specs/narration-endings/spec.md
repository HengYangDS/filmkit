## Purpose

Keep each thought's spoken ending whole from its take to the delivered soundtrack, and measure delivered endings where a listener hears the voice stop.

## ADDED Requirements

### Requirement: A soundtrack never fades a thought that is still speaking

The assembly SHALL refuse an edition when a bound thought take does not end naturally, unless the film declares a release for that thought's join, and the refusal SHALL name every such thought. A take ends naturally when its final 30 ms are quiet, its final syllable dies away to heard quiet, and a voiced final syllable does not fall silent within 6 ms.

#### Scenario: A take that stops inside its last syllable refuses

- **WHEN** a bound thought take is still heard at its end and its join declares no release
- **THEN** the assembly refuses before it writes a soundtrack and names the thought

#### Scenario: A declared release is kept

- **WHEN** the film declares a release for that thought's join
- **THEN** the assembly proceeds and fades the thought over the declared seconds

#### Scenario: Natural endings assemble as before

- **WHEN** every bound thought take ends naturally
- **THEN** the assembly writes the same soundtrack bytes as before this requirement

### Requirement: Delivered endings are measured where the voice stops

The review's measurement of delivered endings SHALL take each thought's stop at the first run of digital silence after its last word begins, and SHALL judge a thought that the assembly released where its release begins.

#### Scenario: A voice that stops before its aligned end

- **WHEN** a thought's sound stops before the aligned end of its last word
- **THEN** the measurement judges the thought's ending at that stop, not at the aligned end

#### Scenario: A release that fades a voice at full level

- **WHEN** a released thought is voiced and within 6 dB of its speech median where its release begins
- **THEN** the measurement lists the thought as cut while voiced

### Requirement: A run-on reads into the next words with a word space

When a thought's spoken text ends in Latin text without a trailing space and the following thought begins with a Latin letter or digit, its run-on text SHALL begin with a space.

#### Scenario: An English thought that ends its segment

- **WHEN** an English thought that ends its segment is auditioned as a run-on
- **THEN** its run-on text begins with a space, so the thought's last word and the next thought's first word are separate words

#### Scenario: A Chinese thought

- **WHEN** a Chinese thought is auditioned as a run-on
- **THEN** its run-on text is the following thought's spoken text unchanged
