## ADDED Requirements

### Requirement: Attributed one-frame faults are rendered again within a limit

`repair-pictures` SHALL start from the edition's current comparison record. When that record refused only one-frame faults that each name the picture that holds them, it SHALL render only the named pictures again and compare again, at most `--attempts` times, 2 unless given, and stop at the first comparison that passes. A current passing record SHALL leave both pictures as they are.

#### Scenario: An injected glyph fault

- **WHEN** the comparison refused a 4x4 fragment, 150 levels off its twin, that the uncaptioned picture holds for one frame
- **THEN** `repair-pictures` renders the uncaptioned picture again and not the captioned one, compares again and passes in one attempt

#### Scenario: A fault that remains

- **WHEN** the named picture holds a one-frame fault after each of two attempts
- **THEN** `repair-pictures` refuses after the second attempt, naming the remaining faults and the attempts it made

#### Scenario: A record that passed

- **WHEN** the edition's current comparison record passed
- **THEN** `repair-pictures` renders nothing and exits 0

### Requirement: A refusal that a repair can answer names the repair

When `repair-pictures` can repair every finding of a refused comparison, `compare-pictures` SHALL name `repair-pictures` as the next step in its refusal.

#### Scenario: A fault of one picture

- **WHEN** `compare-pictures` refuses only a fragment that the uncaptioned picture holds for one frame
- **THEN** its refusal names `python -m filmkit.produce repair-pictures --language zh` as the next step

### Requirement: A repair keeps the faulty pictures and records each attempt

Before it renders a picture again, `repair-pictures` SHALL move the faulty picture and its receipt, with a copy of the refused comparison record, into the next numbered attempt folder below the edition's evidence, and SHALL record there the faults, each kept file's SHA-256, the pictures rendered again with their receipts, and the verdict and findings of the comparison after them.

#### Scenario: The kept evidence of an attempt

- **WHEN** an attempt renders the uncaptioned picture again
- **THEN** its folder holds the faulty uncaptioned picture byte for byte, its receipt and the refused record, and its record names the fault's frame, box, peak and picture

#### Scenario: A later run

- **WHEN** `repair-pictures` runs again after an earlier run's attempts
- **THEN** its attempts take the next numbers and no earlier attempt's folder changes

### Requirement: A repair refuses what rendering one picture again cannot repair

`repair-pictures` SHALL refuse, before it moves or renders anything, a missing comparison record, one that binds other pictures or inputs, and one whose findings include a composition difference, a sampled frame beyond the encoders' noise other than an attributed fault's frame outside the caption band, a difference over two frames or more, or a one-frame difference that no one picture holds or that the record does not attribute; and a named picture whose stage or gate record is not current.

#### Scenario: A fault on a sampled frame

- **WHEN** the record refused a fragment that the uncaptioned picture holds for one frame at a sampled frame, which therefore also differs beyond the encoders' noise, and every other sampled frame passed
- **THEN** `repair-pictures` renders the uncaptioned picture again as for any other one-frame fault

#### Scenario: A difference that no one picture holds

- **WHEN** the record refused a one-frame difference of 150 levels that neither picture holds alone
- **THEN** `repair-pictures` refuses, naming the frame and, as the next step, rendering both pictures again with `render-picture`, and moves and renders nothing

#### Scenario: A difference that lasts

- **WHEN** the record refused a difference over frames 10 to 12
- **THEN** `repair-pictures` refuses, naming the frames

#### Scenario: A record of other pictures

- **WHEN** a picture was rendered again after the comparison that the record holds
- **THEN** `repair-pictures` refuses, naming `compare-pictures`
