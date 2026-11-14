## ADDED Requirements

### Requirement: Edge slivers stay within the declared bound

`compare-pictures` SHALL measure at every frame the samples more than 40 levels apart in the densest 32-pixel block of the two rendered pictures outside the caption band, SHALL record the one-frame transients and each sliver of 33 samples or more with its frames, time, block, samples and level, and SHALL refuse a frame whose block holds more than 96, naming the picture that holds a one-frame difference.

#### Scenario: A sliver within the bound

- **WHEN** one picture shows two rows across a block 45 levels lighter than its twin for five frames
- **THEN** the comparison passes and its record lists the sliver with its frames, its block, 64 samples and level 45

#### Scenario: A dim mark missing for one frame

- **WHEN** the uncaptioned picture lacks for one frame a mark 60 levels lighter than the ground that covers 192 samples of one block
- **THEN** `compare-pictures` refuses, naming the frame, the samples, the bound and the uncaptioned picture, and names `repair-pictures` as the next step

#### Scenario: A dim difference that lasts

- **WHEN** the uncaptioned picture lacks that mark for five frames
- **THEN** `compare-pictures` refuses, naming the frames, the samples and the bound, and no picture
