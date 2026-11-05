## ADDED Requirements

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
