## MODIFIED Requirements

### Requirement: The dry run allocates the gaps as the assembly does

`python -m filmkit.soundtrack.fit` SHALL decode, shape and design the edition's selected recordings and allocate its designed gaps by the steps that `assemble` runs, and SHALL report for the script's pause policy the speech with its thought pauses, the designed gaps, the closing quiet, the runtime the assembly would give, the seconds of the rounding's fraction that the gaps and the credits take, and the allocation's verdict. It SHALL write nothing but the assembly's decode work files.

#### Scenario: The dry run agrees with the assembly

- **WHEN** `fit` and then `assemble` run on the same selected recordings and script
- **THEN** the runtime, the gaps, the closing quiet and the credits that `fit` reports for the script's policy equal, to the sample, those the timeline and the assembly receipt record

#### Scenario: Nothing is written

- **WHEN** `fit` runs
- **THEN** no file below the film's root changes other than the decode work files below `build/runtime/work/audio-assembly/<edition>/`

### Requirement: Every step takes an edition's runtime and its credits from its timeline

Each step that stages, draws, derives, compares, scans, packages, verifies or delivers an edition's picture, films, captions, chapters or player page, or prepares its review prompt, SHALL take that edition's runtime from its assembled timeline, and the start of its credits as that runtime less the timeline's `credits_duration`. It SHALL refuse in one line that names `filmkit build assemble:<code>` an edition that has no timeline or whose timeline states no whole number of seconds.

#### Scenario: The films last the runtime

- **WHEN** an edition's timeline states a runtime of 1476 s
- **THEN** each of its four films holds 88,560 frames at 60 fps and 1476 s of sound, its last chapter ends at 1476 s, its player page shows 24:36, and the verifier accepts them

#### Scenario: The credits' start

- **WHEN** an edition's runtime is 1476 s and its timeline's credits last 3.56 s
- **THEN** the verifier accepts a caption that ends at 1472.44 s and refuses one that ends after it

#### Scenario: No assembled timeline

- **WHEN** an edition has no timeline
- **THEN** `stage-picture` refuses in one line that names `filmkit build assemble:<code>`, and no stage is written

### Requirement: The dry run refuses where the pause design would

`python -m filmkit.soundtrack.fit` SHALL exit with a refusal when the script's own pause policy cannot be designed, with the message the design gives, after it has reported every policy. A fraction that the gaps' ranges cannot take SHALL be no refusal.

#### Scenario: A policy that cannot be designed

- **WHEN** the script's thought boundaries need a larger statement pause than it declares
- **THEN** `fit` reports the script's policy with that refusal and no measures, and refuses with "Thought boundaries need a larger declared statement pause", as `assemble` refuses

#### Scenario: A fraction the gaps cannot take

- **WHEN** every gap with a weight already stands at the top of its range and the rounding leaves 0.40 s
- **THEN** `fit` reports the runtime in whole seconds, no seconds taken by the gaps and 0.40 s by the credits, and exits 0

### Requirement: A film compares variants of its pause policy by their runtimes

With `--variants <file>`, a file below the film's root or an absolute one that maps each variant's name to the voice-performance fields it replaces, `python -m filmkit.soundtrack.fit` SHALL validate every variant as the assembly validates a pause policy, refusing a field the policy does not read, before it decodes anything. It SHALL report each variant after the script's policy, with the runtime that variant would give. A variant SHALL NOT decide the command's exit.

#### Scenario: Each variant gives its own runtime

- **WHEN** a variant shortens the designed thought pause
- **THEN** `fit` reports the script's policy and the variant, each with the runtime its own count gives, and exits by the script's policy alone

#### Scenario: A variant that can be designed where the script's policy cannot

- **WHEN** the script's thought boundaries need a larger statement pause than it declares and a variant declares one
- **THEN** `fit` reports both policies, the variant with its runtime and gaps, and refuses by the script's policy alone

#### Scenario: A field the policy does not read

- **WHEN** a variant names `thought_pause`, which the pause policy does not read
- **THEN** `fit` refuses before decoding, naming the variant and the field

#### Scenario: A malformed variant

- **WHEN** a variant's `designed_pauses` omits the closing pause
- **THEN** `fit` refuses before decoding, naming the variant and the field
