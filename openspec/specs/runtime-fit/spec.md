# runtime-fit Specification

## Purpose

Tell, before an edition's soundtrack is assembled, how much of the film's runtime its narration leaves for the designed gaps, under its pause policy and under variants of that policy, by the assembly's own steps.

## Requirements

### Requirement: The dry run allocates the gaps as the assembly does

`produce fit` SHALL decode, shape and design the edition's selected recordings and allocate its designed gaps by the steps that `assemble` runs, and SHALL report for the script's pause policy the speech with its thought pauses, the designed gaps, the closing quiet, the runtime left free or missing and the allocation's verdict. It SHALL write nothing but the assembly's decode work files.

#### Scenario: The dry run agrees with the assembly

- **WHEN** `fit` and then `assemble` run on the same selected recordings and script
- **THEN** the gaps and closing quiet that `fit` reports for the script's policy equal, to the sample, those the assembly receipt records

#### Scenario: Nothing is written

- **WHEN** `fit` runs
- **THEN** no file below the film's root changes other than the decode work files below `build/runtime/work/audio-assembly/<edition>/`

### Requirement: The dry run refuses where the allocation would

`produce fit` SHALL exit with a refusal when the script's own pause policy does not fit the runtime or the declared gap limits, with the message the allocation gives, after it has reported every policy.

#### Scenario: Narration over the runtime

- **WHEN** the edition's speech with its designed gaps and closing quiet exceeds the runtime by 0.10 s
- **THEN** `fit` reports 0.10 s missing for the script's policy and refuses with "Narration exceeds the runtime by 0.10 s", as `assemble` refuses

#### Scenario: Narration that fits

- **WHEN** the edition's speech leaves 2 s that the gap limits can take
- **THEN** `fit` reports 2 s free for the script's policy and exits 0

### Requirement: A film tries variants of its pause policy

With `--variants <file>`, a file below the film's root or an absolute one that maps each variant's name to the voice-performance fields it replaces, `produce fit` SHALL validate every variant as the assembly validates a pause policy, refusing a field the policy does not read, before it decodes anything, and SHALL report each variant after the script's policy. A variant SHALL NOT decide the command's exit.

#### Scenario: A variant that fits where the script overruns

- **WHEN** the script's policy overruns by 0.10 s and a variant shortens the designed thought pause
- **THEN** `fit` reports the script's policy and the variant with each one's free or missing runtime, and refuses by the script's policy alone

#### Scenario: A field the policy does not read

- **WHEN** a variant names `thought_pause`, which the pause policy does not read
- **THEN** `fit` refuses before decoding, naming the variant and the field

#### Scenario: A malformed variant

- **WHEN** a variant's `designed_pauses` omits the closing pause
- **THEN** `fit` refuses before decoding, naming the variant and the field
