# caption-equivalence Specification

## Purpose

Give each edition a picture without its captions that is, apart from the captions, the picture with them, and prove that before its films are packaged.

## Requirements

### Requirement: Each edition renders a picture without its captions

`stage-picture --uncaptioned` SHALL stage the composition and timeline of the captioned picture with the timeline's captions replaced by none, in a stage of its own, and `render-picture --uncaptioned --native` SHALL render it with the captioned picture's renderer settings to its own picture file and receipt. Each stage record and receipt SHALL name its picture, and validation SHALL refuse a receipt read for the other picture.

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

`compare-pictures` SHALL refuse any frame of the two rendered pictures where, outside the caption band widened to the encoder's blocks, a luma sample differs by more than 90 levels, except that a one-frame difference no one picture holds alone is refused only above 120. At every half second and every caption's start, middle and end frame it SHALL also refuse a difference beyond the encoders' measured noise: 4 levels on average over any tile of 64 luma or 32 chroma pixels, or a PSNR under 45 dB.

#### Scenario: Pictures that differ only by their captions

- **WHEN** the two pictures differ only in the caption band
- **THEN** every frame passes and the record holds the largest tile difference and the lowest PSNR

#### Scenario: A label missing outside the captions

- **WHEN** the uncaptioned picture lacks a label that the captioned picture shows above the caption band
- **THEN** compare-pictures refuses, naming the frames that differ

#### Scenario: Noise at a keyframe

- **WHEN** a keyframe of both encodes differs by noise spread thinly over the frame, at about 49.8 dB with no tile above 2 levels
- **THEN** that frame passes

#### Scenario: A difference spread across the frame

- **WHEN** the uncaptioned picture is 2 levels lighter than the captioned one across the frame outside the caption band
- **THEN** compare-pictures refuses on the frame's PSNR of about 42.1 dB, though no tile reaches 4 levels

#### Scenario: A glyph fragment for one frame between the sampled frames

- **WHEN** one picture shows a 4x4 fragment 150 levels brighter than its twin at one frame that is not a sampled frame
- **THEN** compare-pictures refuses, naming that frame, the fragment's box and the picture that holds it

#### Scenario: A moving mark's residue

- **WHEN** the two pictures differ for one frame by 93 levels at one sample of a moving mark, where neither picture departs from its own neighbouring frames
- **THEN** that frame is recorded and passes

### Requirement: Packaging waits for a current passing comparison

`package-film` SHALL refuse an edition until both pictures validate and its equivalence record passes and binds the current composition, timeline, engine and both pictures' files and receipts, with the stage document of each picture that was rendered.

#### Scenario: A picture rendered again after its comparison

- **WHEN** the uncaptioned picture changes after `compare-pictures` passed
- **THEN** packaging refuses and asks for `compare-pictures`

### Requirement: Neither picture changes for one frame in its caption band

`compare-pictures` SHALL scan the caption band of both rendered pictures at every frame and SHALL refuse a frame where a luma sample differs by more than 90 levels from both neighbouring frames while those two agree within 30 levels.

#### Scenario: A caption glyph broken for one frame

- **WHEN** the captioned picture shows a fragment of a caption's glyph 150 levels darker for one frame while the caption stands
- **THEN** compare-pictures refuses, naming that frame, the fragment's box and the captioned picture

#### Scenario: A caption that appears and leaves

- **WHEN** a caption appears at one frame and leaves at a later one
- **THEN** the caption band passes

### Requirement: A refusal names the picture to render again

When `compare-pictures` refuses a one-frame difference, or passes as residue one within 120 levels that no one picture holds alone, its record SHALL list each such frame with its time, box, peak and the picture whose frame departs from its own neighbouring frames, and a refusal SHALL name the command that renders that picture again.

#### Scenario: A fault in the uncaptioned picture

- **WHEN** the uncaptioned picture holds a one-frame fragment that the captioned picture does not
- **THEN** the record names the uncaptioned picture and the refusal names `render-picture --uncaptioned --native` for its edition, the command that renders that picture and never derives it

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

When the repair, `repair-pictures`, can repair every finding of a refused comparison, `compare-pictures` SHALL name the command that runs it, `python -m filmkit.picture.repair`, as the next step in its refusal.

#### Scenario: A fault of one picture

- **WHEN** `compare-pictures` refuses only a fragment that the uncaptioned picture holds for one frame
- **THEN** its refusal names `python -m filmkit.picture.repair --language zh` as the next step

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

### Requirement: The uncaptioned picture is derived from the captioned one

For a film that declares `software` capture, `render-picture --uncaptioned` SHALL, unless `--native` is given, derive the uncaptioned picture from the edition's valid captioned picture: every frame encoded again, without B-frames, with the rows of the caption band painted in the ground the captioned picture holds there. Its receipt SHALL say that the picture is derived and name the captioned picture's SHA-256, the painted rows, the ground and the command.

#### Scenario: A derived picture

- **WHEN** an edition whose band holds only captions on a flat ground derives its uncaptioned picture
- **THEN** the picture has the captioned picture's frame count, frame rate, frame size and duration, its band holds the ground in every frame, and its receipt names the captioned picture it was derived from

#### Scenario: A captioned picture that is not current

- **WHEN** the captioned picture's receipt binds another stage than the current one
- **THEN** the derivation refuses before it encodes anything

#### Scenario: A stylesheet changed after the derivation

- **WHEN** the stylesheet, a font, the template, the script or the soundtrack changes after an uncaptioned picture was derived
- **THEN** `validate-picture --uncaptioned` refuses the derived picture as it refuses the captioned one

### Requirement: A derivation proves that the band holds only captions on the ground

Before it encodes, a derivation SHALL run the composition headlessly at every thirtieth of a second and refuse unless every caption paint lies within the painted rows and no other paint reaches them. It SHALL then refuse, leaving no uncaptioned picture in place and naming `--native`, unless the captioned picture stood within 3 levels of the ground in its band at every frame without a caption, and in the painted rows' edge rows, which no caption reaches, at every frame.

#### Scenario: A mark that reaches the band

- **WHEN** a scene of the composition draws a stroke into the rows the derivation would paint
- **THEN** the derivation refuses before it encodes, naming the instant and the mark, and names `--native`

#### Scenario: A caption that leaves the band

- **WHEN** a caption is painted partly above the rows the derivation would paint
- **THEN** the derivation refuses before it encodes, naming the instant and the caption

#### Scenario: A ground that changes while a caption shows

- **WHEN** the captioned picture's whole ground is another colour on exactly the frames that show a caption
- **THEN** the derivation refuses on the edge rows, naming the first such frame and `--native`, though every frame without a caption holds the ground

#### Scenario: A side of the painted rows without a row to measure

- **WHEN** the captions come so close to one edge of the painted rows that no edge row is left there, and the picture continues beyond that edge
- **THEN** the derivation refuses before it encodes, naming that side and `--native`, though the other side has edge rows

#### Scenario: Painted rows at the frame's own edge

- **WHEN** the painted rows end with the frame's last row and have edge rows at their top
- **THEN** the derivation measures the top edge rows alone and goes on, since no picture row lies beyond the bottom

#### Scenario: A ground that leaves by degrees

- **WHEN** the ground under a caption stands a little off for thirty frames and far off for thirty more
- **THEN** the refusal names the first frame beyond the tolerance with its departure, and beside it how many frames stand beyond the tolerance and the largest departure with its frame

#### Scenario: A band that is not the ground

- **WHEN** the captioned picture's band holds, at a frame without a caption, samples 10 levels from the ground
- **THEN** the derivation refuses, naming the frame, and no uncaptioned picture stays in place

### Requirement: A derivation scans the captioned picture's caption band for one-frame faults

While it encodes, a derivation SHALL judge the captioned picture's caption band at every frame by the rule a rendered pair's comparison applies there: a sample far from both neighbouring frames, which agree, is a one-frame fault. It SHALL refuse on one before any uncaptioned picture is in place, naming the first ten by frame, time and box, the count of the rest and the command that renders the picture again. The receipt SHALL record the scan, and validation SHALL require that it passed.

#### Scenario: A fragment for one frame in the band

- **WHEN** the captioned picture shows a fragment inside its caption for exactly one frame
- **THEN** the derivation refuses, naming that frame, its time and box and `render-picture` of the captioned picture, and names no native uncaptioned render

#### Scenario: Captions that appear, change and leave

- **WHEN** a caption appears, another takes its place at once, and it leaves
- **THEN** the scan finds no one-frame change, and the receipt records every frame scanned and no change

#### Scenario: A receipt without the scan

- **WHEN** a derived picture's receipt holds no passed scan of the band
- **THEN** validation refuses the picture and asks for the derivation again

### Requirement: A derived pair is compared by its derivation's record

For a pair whose uncaptioned picture is derived, `compare-pictures` SHALL decode no picture. It SHALL pass only when the composition report finds no difference beyond the captions and the derivation's receipt binds the current captioned picture, composition, timeline and engine, names the report's band and records its proofs as passed; its record SHALL say that the pair is derived. The requirements on two rendered pictures hold for a `--native` pair.

#### Scenario: A current derived pair

- **WHEN** `compare-pictures` runs on a pair whose uncaptioned picture was derived from the current captioned picture
- **THEN** it passes without decoding a picture, and its record says that the pair is derived, names the painted rows and carries the derivation's proofs, the scan of the band among them

#### Scenario: A captioned picture rendered again after the derivation

- **WHEN** the captioned picture is rendered again after its uncaptioned picture was derived
- **THEN** `compare-pictures` refuses and asks for `render-picture --uncaptioned`

### Requirement: A picture is derived only from a render by the pinned canvas

For a film that declares another capture than `software`, for a captioned picture whose receipt does not name the pinned canvas build with `system` text, and with `--native`, `render-picture --uncaptioned` SHALL draw the uncaptioned stage, and `compare-pictures` SHALL then compare the pair at every frame. The uncaptioned picture's receipt and the comparison record SHALL each say whether it was derived or rendered, and why.

#### Scenario: A film that declares no capture

- **WHEN** a film that declares no capture, and so declares `fast`, runs `render-picture --uncaptioned`
- **THEN** its uncaptioned stage is drawn, and the receipt says that the picture was rendered because the film declares `fast` capture

#### Scenario: A native render asked for under software capture

- **WHEN** a film that declares `software` capture runs `render-picture --uncaptioned --native`
- **THEN** its uncaptioned stage is drawn, and the receipt says that a render was asked for

#### Scenario: A derived picture under another capture

- **WHEN** a film changes its declared capture from `software` to `screenshot` after its uncaptioned picture was derived
- **THEN** validation refuses the derived picture and asks for `render-picture --uncaptioned`

#### Scenario: A captioned picture drawn by another canvas build

- **WHEN** a film that declares `software` capture rendered its captioned picture with a canvas package whose recorded integrity is not the pinned build's, or whose processes loaded another native library than the pinned one
- **THEN** the captioned receipt names that integrity and that library's SHA-256, `render-picture --uncaptioned` draws the uncaptioned stage, and its receipt says that the captioned picture is no render by the pinned build, naming what differs

#### Scenario: A captioned receipt that names no canvas

- **WHEN** the captioned picture's receipt names no canvas
- **THEN** `render-picture --uncaptioned` draws the uncaptioned stage and says so

#### Scenario: A repair's render of the uncaptioned picture

- **WHEN** `repair-pictures` renders the uncaptioned picture of a rendered pair again and the pair then passes
- **THEN** the new receipt and the passing comparison record say that the picture was rendered and why, as the receipt it replaces did

#### Scenario: The comparison record of a rendered pair

- **WHEN** `compare-pictures` passes a pair whose uncaptioned picture was rendered under `fast` capture
- **THEN** its record holds every level's measures and says that the picture was rendered because the film declares `fast` capture
