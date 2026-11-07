## MODIFIED Requirements

### Requirement: The encoded pictures agree outside the caption band

`compare-pictures` SHALL decode both rendered pictures at every half second and every caption's start, middle and end frame, and SHALL refuse a frame whose difference outside the caption band, widened to the encoder's blocks, exceeds the encoders' measured noise: 4 levels on average over any tile of 64 luma or 32 chroma pixels, or a PSNR under 45 dB.

#### Scenario: Pictures that differ only by their captions

- **WHEN** the two pictures differ only in the caption band
- **THEN** every sampled frame passes and the record holds the largest tile difference and the lowest PSNR

#### Scenario: A label missing outside the captions

- **WHEN** the uncaptioned picture lacks a label that the captioned picture shows above the caption band
- **THEN** compare-pictures refuses, naming the frames that differ

#### Scenario: Noise at a keyframe

- **WHEN** a keyframe of both encodes differs by noise spread thinly over the frame, at about 49.8 dB with no tile above 2 levels
- **THEN** that frame passes

#### Scenario: A difference spread across the frame

- **WHEN** the uncaptioned picture is 2 levels lighter than the captioned one across the frame outside the caption band
- **THEN** compare-pictures refuses on the frame's PSNR of about 42.1 dB, though no tile reaches 4 levels
