# runtime-fit Specification

## Purpose

Tell, before an edition's soundtrack is assembled, how much of the film's runtime its narration leaves for the designed gaps, under its pause policy and under variants of that policy, by the assembly's own steps.

## Requirements

### Requirement: The dry run allocates the gaps as the assembly does

`produce fit` SHALL decode, shape and design the edition's selected recordings and allocate its designed gaps by the steps that `assemble` runs, and SHALL report for the script's pause policy the speech with its thought pauses, the designed gaps, the closing quiet, the runtime the assembly would give, the seconds of the rounding's fraction that the gaps and the credits take, and the allocation's verdict. It SHALL write nothing but the assembly's decode work files.

#### Scenario: The dry run agrees with the assembly

- **WHEN** `fit` and then `assemble` run on the same selected recordings and script
- **THEN** the runtime, the gaps, the closing quiet and the credits that `fit` reports for the script's policy equal, to the sample, those the timeline and the assembly receipt record

#### Scenario: Nothing is written

- **WHEN** `fit` runs
- **THEN** no file below the film's root changes other than the decode work files below `build/runtime/work/audio-assembly/<edition>/`

### Requirement: An edition lasts as long as its narration at its designed pauses

The assembly SHALL make each edition's runtime the credits the film declares plus the speech with its designed thought pauses, the designed gaps and the closing quiet, counted in samples and rounded up to the next whole second. It SHALL state the runtime as a whole number of seconds, as the timeline's `duration` and in the assembly receipt, and the soundtrack SHALL last the runtime to the sample.

#### Scenario: A count rounded up

- **WHEN** an edition's speech with its designed thought pauses, its designed gaps and its closing quiet comes to 1472.14 s and the credits last 3 s
- **THEN** the timeline and the receipt state a runtime of 1476 s, a whole number, and the soundtrack holds 1476 s of samples

#### Scenario: A count of whole seconds

- **WHEN** that count comes to exactly 597 s and the credits last 3 s
- **THEN** the runtime is 600 s

#### Scenario: The editions differ in length

- **WHEN** the Chinese edition's count gives a runtime of 1636 s and the English edition's 1476 s
- **THEN** each edition's timeline states its own runtime, and neither edition is refused for the difference

### Requirement: The rounding's fraction goes to the gaps within their ranges, then to the credits

The assembly SHALL share the rounding's fraction among the gaps by their declared weights, each capped at its range's top: a paragraph gap at the top of `paragraph_pause_range`, an opening or chapter gap at its declared limit. What the gaps cannot take SHALL go to the credits, which hold no pause, stated as laid out as the timeline's `credits_duration`. No thought pause or closing quiet SHALL change, nor any gap leave its range.

#### Scenario: The gaps take all of the fraction

- **WHEN** the rounding leaves 0.86 s and the gaps' ranges have room for 2.40 s
- **THEN** the gaps hold 0.86 s beyond their designed pauses, each within its range, the timeline's credits last the declared 3 s, and the speech with its thought pauses that the receipt lays out is the count's own, to the sample

#### Scenario: The gaps take part, the credits the rest

- **WHEN** the rounding leaves 0.86 s and the gaps' ranges have room for 0.30 s
- **THEN** the gaps take 0.30 s, none past its range's top, the timeline's credits last 3.56 s, and the runtime is 1476 s

#### Scenario: The gaps take none

- **WHEN** the rounding leaves 0.86 s and every gap with a weight already stands at the top of its range
- **THEN** every gap keeps its designed pause, the timeline's credits last 3.86 s, and the runtime is 1476 s

#### Scenario: No fraction

- **WHEN** the count comes to whole seconds
- **THEN** every gap keeps its designed pause, and the credits keep their declared length

### Requirement: Every step takes an edition's runtime and its credits from its timeline

Each step that stages, draws, derives, compares, scans, packages, verifies or delivers an edition's picture, films, captions, chapters or player page, or prepares its review prompt, SHALL take that edition's runtime from its assembled timeline, and the start of its credits as that runtime less the timeline's `credits_duration`. It SHALL refuse in one line that names `produce assemble` an edition that has no timeline or whose timeline states no whole number of seconds.

#### Scenario: The films last the runtime

- **WHEN** an edition's timeline states a runtime of 1476 s
- **THEN** each of its four films holds 88,560 frames at 60 fps and 1476 s of sound, its last chapter ends at 1476 s, its player page shows 24:36, and the verifier accepts them

#### Scenario: The credits' start

- **WHEN** an edition's runtime is 1476 s and its timeline's credits last 3.56 s
- **THEN** the verifier accepts a caption that ends at 1472.44 s and refuses one that ends after it

#### Scenario: No assembled timeline

- **WHEN** an edition has no timeline
- **THEN** `stage-picture` refuses in one line that names `produce assemble`, and no stage is written

### Requirement: A page or a check that covers both editions gives each its own runtime

The entry page, the player check's binding and the delivery's readback receipt SHALL state each edition's runtime by its code, the player check SHALL play and seek each edition's films against their own, and each edition's review prompt SHALL state its own. A binding that names one duration for the film SHALL be refused.

#### Scenario: The entry page

- **WHEN** the Chinese edition's runtime is 1636 s and the English edition's 1476 s
- **THEN** the entry page's Chinese link shows 27:16 and its English link 24:36

#### Scenario: The player check

- **WHEN** the delivery is bound for the player check with those two runtimes
- **THEN** the binding names 1636 s for the Chinese edition and 1476 s for the English edition, and each edition's films are played and sought against their own

#### Scenario: A binding of the former shape

- **WHEN** the player check is given a binding that names one `duration` for the film
- **THEN** it refuses the binding and reads no page

#### Scenario: The review prompts

- **WHEN** a round's prompts are prepared from a template that says "This edition: exactly {duration} s"
- **THEN** the Chinese prompt states 1636 s and the English prompt 1476 s

### Requirement: The dry run refuses where the pause design would

`produce fit` SHALL exit with a refusal when the script's own pause policy cannot be designed, with the message the design gives, after it has reported every policy. A fraction that the gaps' ranges cannot take SHALL be no refusal.

#### Scenario: A policy that cannot be designed

- **WHEN** the script's thought boundaries need a larger statement pause than it declares
- **THEN** `fit` reports the script's policy with that refusal and no measures, and refuses with "Thought boundaries need a larger declared statement pause", as `assemble` refuses

#### Scenario: A fraction the gaps cannot take

- **WHEN** every gap with a weight already stands at the top of its range and the rounding leaves 0.40 s
- **THEN** `fit` reports the runtime in whole seconds, no seconds taken by the gaps and 0.40 s by the credits, and exits 0

### Requirement: A film compares variants of its pause policy by their runtimes

With `--variants <file>`, a file below the film's root or an absolute one that maps each variant's name to the voice-performance fields it replaces, `produce fit` SHALL validate every variant as the assembly validates a pause policy, refusing a field the policy does not read, before it decodes anything. It SHALL report each variant after the script's policy, with the runtime that variant would give. A variant SHALL NOT decide the command's exit.

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
