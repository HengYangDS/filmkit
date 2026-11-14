## ADDED Requirements

### Requirement: The geometry check records names that stand too close on a row

The geometry check SHALL record every pair of neighbouring names of one scene that stand at rest on one row for a second or more with a clear gap under 1.5 em of the smaller face, each with its scene, both names, its tightest gap in px and in em, when it first stood and the frames that show it. It SHALL count such a pair as a finding and fail only when it is run with `--gate-row-gaps`.

#### Scenario: Two names 1.2 em apart

- **WHEN** two names of one face stand level 36 px apart in a 30 px face for a second
- **THEN** the receipt records a row gap with the gap 36 and 1.2 em, and without `--gate-row-gaps` the check passes

#### Scenario: A film that gates its rows

- **WHEN** the same picture is checked with `--gate-row-gaps`
- **THEN** the pair is a finding and the check fails

#### Scenario: Texts that are not neighbours

- **WHEN** two texts share one registered whole, stand under half an em apart, are set in different sizes, or have a lit mark between them
- **THEN** no row gap is recorded
