# narration-endings Specification

## Purpose

Keep each thought's spoken ending whole from its take to the delivered soundtrack, and measure delivered endings where a listener hears the voice stop.

## Requirements

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

### Requirement: A take's onset after digital silence is released at a thought join

At a complete-thought join, the assembly SHALL release to digital silence the sound that follows digital silence after the thought's last aligned word and lasts at most 0.1 seconds before the join's native quiet, so the join leaves its digital silence only into quiet, and SHALL record the samples it released. Speech, the aligned words, the designed quiet and every timing SHALL stay unchanged; a longer sound, or one an aligned word covers, keeps its samples.

#### Scenario: A take's onset between digital silence and the native quiet

- **WHEN** a take that follows digital silence opens with a 40 ms low-frequency onset from −30 dBFS before the join's native quiet
- **THEN** the assembly releases the onset and records its samples, the review's quiet edges find no edge above −45 dBFS where the join leaves its digital silence, and the speech samples are bit-identical

#### Scenario: Sound that is no onset

- **WHEN** the sound after the digital silence lasts longer than 0.1 seconds before the native quiet, or the thought's last aligned word still covers it
- **THEN** the join keeps every sample before its native quiet and records no released samples

#### Scenario: A join without digital silence

- **WHEN** no digital silence lies between the thought's last aligned word and the join's native quiet
- **THEN** the join keeps every sample before its native quiet

### Requirement: A take's onset where a join's digital silence ends its native quiet is released

Where a join's digital silence ends within 0.1 seconds of the end of its native quiet, the assembly SHALL release the sound the silence is left into when that sound meets heard quiet within 0.1 seconds and before the next thought's first aligned word, and SHALL record the samples. Speech, the aligned words, the designed quiet and every timing SHALL stay unchanged.

#### Scenario: A take's onset after the silence that ends the native quiet

- **WHEN** a join's native quiet ends with its digital silence and the next take opens with a 40 ms low-frequency onset from −30 dBFS that falls into heard quiet before the next word
- **THEN** the assembly releases the onset and records its samples, the review's quiet edges find no edge above −45 dBFS where the join leaves its digital silence, and the speech samples are bit-identical

#### Scenario: Sound after the silence that is no onset

- **WHEN** the next word begins at the silence, the sound after it lasts longer than 0.1 seconds before heard quiet, or the next word begins inside it
- **THEN** the join keeps that sound's samples and records no released samples

### Requirement: A clip heard from its first sample begins in its released onset

When a recording offers its clip no heard quiet before its first aligned word, the assembly SHALL release its sound before its first 10 ms heard as quiet if that sound lasts at most 0.1 seconds and ends by the first word, begin the clip there and record the samples, and refuse the recording otherwise. The audition SHALL propose a take that opens its recording only when the assembly would begin its clip in quiet, and record its first 10 ms level and whether its onset is releasable.

#### Scenario: A recording that opens on a take's onset

- **WHEN** a recording opens with a 40 ms onset that falls into heard quiet before its first word, 0.09 seconds in
- **THEN** the assembly releases the onset and begins the clip in it, and the audition accepts the take although its first 10 ms are heard

#### Scenario: Speech from the first sample

- **WHEN** a recording is heard from its first sample into its first word, or its sound before heard quiet lasts longer than 0.1 seconds
- **THEN** the assembly refuses it, and the audition does not propose the take

#### Scenario: A recording that begins in quiet

- **WHEN** a recording begins in heard quiet, or offers heard quiet before its first word after an onset
- **THEN** the assembly releases nothing and begins the clip where it began before
