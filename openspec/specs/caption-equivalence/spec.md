# caption-equivalence Specification

## Purpose

Give each edition a picture without its captions that is, apart from the captions, the picture with them, and prove that before its films are packaged.

## Requirements

### Requirement: Each edition renders a picture without its captions

`stage-picture --uncaptioned` SHALL stage the composition and timeline of the captioned picture with the timeline's captions replaced by none, in a stage of its own, and `render-picture --uncaptioned` SHALL render it with the captioned picture's renderer settings to its own picture file and receipt. Each stage record and receipt SHALL name its picture, and validation SHALL refuse a receipt read for the other picture.

#### Scenario: The uncaptioned stage

- **WHEN** an edition's uncaptioned picture is staged
- **THEN** its document inlines the captioned document's timeline with no captions, and its record names the uncaptioned picture

#### Scenario: A receipt of the other picture

- **WHEN** the uncaptioned picture is validated with a receipt that names the captioned picture or none
- **THEN** validation refuses and names both pictures

### Requirement: The compositions differ only by their caption paints

`compare-pictures` SHALL run the composition headlessly with and without the captions at every caption's start, middle and end and every half second, and SHALL refuse unless each frame without captions paints the frame with them, in order, less its caption paints: texts painted outside every scene whose letters and digits are a current cue's display text and that the frame's layout names as captions.

#### Scenario: A caption painter that alone reads the captions

- **WHEN** the sample film's composition runs with and without its captions
- **THEN** every instant matches, every cue is shown at its middle, and the report names the band the caption paints cover

#### Scenario: A mark drawn from the captions

- **WHEN** a composition also paints a mark outside every scene while a caption shows
- **THEN** compare-pictures refuses, naming the instant and the mark, and decodes no picture

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

### Requirement: Packaging waits for a current passing comparison

`package-film` SHALL refuse an edition until both pictures validate and its equivalence record passes and binds the current composition, timeline, engine and both pictures' stage documents, files and receipts.

#### Scenario: A picture rendered again after its comparison

- **WHEN** the uncaptioned picture changes after `compare-pictures` passed
- **THEN** packaging refuses and asks for `compare-pictures`
