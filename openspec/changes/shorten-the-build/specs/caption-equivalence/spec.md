## ADDED Requirements

### Requirement: The uncaptioned picture is derived from the captioned one

For a film that declares `software` capture, `render-picture --uncaptioned` SHALL, unless `--native` is given, derive the uncaptioned picture from the edition's valid captioned picture: every frame encoded again with the rows of the caption band painted in the ground that the captioned picture holds there. Its receipt SHALL say that the picture is derived and name the captioned picture's SHA-256, the painted rows, the ground and the command.

#### Scenario: A derived picture

- **WHEN** an edition whose band holds only captions on a flat ground derives its uncaptioned picture
- **THEN** the picture has the captioned picture's frame count, frame rate, frame size and duration, its band holds the ground in every frame, and its receipt names the captioned picture it was derived from

#### Scenario: A captioned picture that is not current

- **WHEN** the captioned picture's receipt binds another stage than the current one
- **THEN** the derivation refuses before it encodes anything

### Requirement: A picture is derived only under software capture

For a film that declares any other capture than `software`, and with `--native` for every film, `render-picture --uncaptioned` SHALL render the uncaptioned stage, and `compare-pictures` SHALL then compare the pair at every frame. The receipt of an uncaptioned picture and the edition's comparison record SHALL each say whether the picture was derived or rendered, and why: the film's declared capture, or a render asked for.

#### Scenario: A film that declares no capture

- **WHEN** a film that declares no capture, and so captures `fast`, runs `render-picture --uncaptioned`
- **THEN** its uncaptioned stage is rendered, and the receipt says that the picture was rendered because the film declares `fast` capture

#### Scenario: A native render asked for under software capture

- **WHEN** a film that declares `software` capture runs `render-picture --uncaptioned --native`
- **THEN** its uncaptioned stage is rendered, and the receipt says that a render was asked for

#### Scenario: A derived picture under another capture

- **WHEN** a film changes its declared capture from `software` to `screenshot` after its uncaptioned picture was derived
- **THEN** validation refuses the derived picture and asks for `render-picture --uncaptioned`

#### Scenario: The comparison record of a rendered pair

- **WHEN** `compare-pictures` passes a pair whose uncaptioned picture was rendered under `fast` capture
- **THEN** its record holds every level's measures and says that the picture was rendered because the film declares `fast` capture

### Requirement: A derivation proves that the band holds only captions on the ground

Before it encodes, a derivation SHALL run the composition headlessly at every thirtieth of a second and refuse unless every caption paint lies within the painted rows and no other paint reaches them. After it encodes, it SHALL refuse, and leave no uncaptioned picture in place, unless the captioned picture's band stood within 3 levels of the ground in every frame at which the composition painted no caption.

#### Scenario: A mark that reaches the band

- **WHEN** a scene of the composition draws a stroke into the rows the derivation would paint
- **THEN** the derivation refuses before it encodes, naming the instant and the mark, and names `--native`

#### Scenario: A caption that leaves the band

- **WHEN** a caption is painted partly above the rows the derivation would paint
- **THEN** the derivation refuses before it encodes, naming the instant and the caption

#### Scenario: A band that is not the ground

- **WHEN** the captioned picture's band holds, at a frame without a caption, samples 10 levels from the ground
- **THEN** the derivation refuses, naming the frame, and no uncaptioned picture stays in place

### Requirement: A derived pair is compared by its derivation's record

For a pair whose uncaptioned picture is derived, `compare-pictures` SHALL decode no picture. It SHALL pass only when the composition report finds no difference beyond the captions and the derivation's receipt binds the current captioned picture, composition, timeline and engine, names the report's band and records both proofs as passed; its record SHALL say that the pair is derived. The requirements on two rendered pictures hold for a `--native` pair.

#### Scenario: A current derived pair

- **WHEN** `compare-pictures` runs on a pair whose uncaptioned picture was derived from the current captioned picture
- **THEN** it passes without decoding a picture, and its record says that the pair is derived and names the painted rows

#### Scenario: A captioned picture rendered again after the derivation

- **WHEN** the captioned picture is rendered again after its uncaptioned picture was derived
- **THEN** `compare-pictures` refuses and asks for `render-picture --uncaptioned`

## MODIFIED Requirements

### Requirement: A refusal names the picture to render again

When `compare-pictures` refuses a one-frame difference, or passes as residue one within 120 levels that no one picture holds alone, its record SHALL list each such frame with its time, box, peak and the picture whose frame departs from its own neighbouring frames, and a refusal SHALL name the command that renders that picture again.

#### Scenario: A fault in the uncaptioned picture

- **WHEN** the uncaptioned picture holds a one-frame fragment that the captioned picture does not
- **THEN** the record names the uncaptioned picture and the refusal names `render-picture --uncaptioned --native` for its edition, the command that renders that picture and never derives it

### Requirement: Each edition renders a picture without its captions

`stage-picture --uncaptioned` SHALL stage the composition and timeline of the captioned picture with the timeline's captions replaced by none, in a stage of its own, and `render-picture --uncaptioned --native` SHALL render it with the captioned picture's renderer settings to its own picture file and receipt. Each stage record and receipt SHALL name its picture, and validation SHALL refuse a receipt read for the other picture.

#### Scenario: The uncaptioned stage

- **WHEN** an edition's uncaptioned picture is staged
- **THEN** its document inlines the captioned document's timeline with no captions, and its record names the uncaptioned picture

#### Scenario: A receipt of the other picture

- **WHEN** the uncaptioned picture is validated with a receipt that names the captioned picture or none
- **THEN** validation refuses and names both pictures

### Requirement: Packaging waits for a current passing comparison

`package-film` SHALL refuse an edition until both pictures validate and its equivalence record passes and binds the current composition, timeline, engine and both pictures' files and receipts, with the stage document of each picture that was rendered.

#### Scenario: A picture rendered again after its comparison

- **WHEN** the uncaptioned picture changes after `compare-pictures` passed
- **THEN** packaging refuses and asks for `compare-pictures`
