## Purpose

Draw a film's pictures on a native canvas from the composition the film already has, with no browser: state how a render draws, encodes and divides a film, what its receipt names, and what two draws of one stage must have in common.

## ADDED Requirements

### Requirement: A render draws the staged composition on a native canvas

`render-picture`, `render-picture --uncaptioned --native`, `render-draft` and `qualify-renderer` SHALL draw a stage with the engine's own Node module on a canvas of the `@napi-rs/canvas` package that the film's npm packages install, running the staged composition unchanged, with the canvas's text renderer set to `system` and each face the stage's record names registered from the staged fonts. No render SHALL start a browser.

#### Scenario: A picture is rendered

- **WHEN** `render-picture` runs on an edition's current stage
- **THEN** its command starts Node on the engine's module with the stage, and no browser process is started

#### Scenario: A face that does not register

- **WHEN** a staged font that the stage's record names cannot be registered
- **THEN** the render fails, naming the family, and its receipt records the exit

#### Scenario: A stage that names no faces, or holds a font none registers

- **WHEN** a stage's record names no faces, as a stage of an earlier engine, or the stage holds a font file that no face of its record registers
- **THEN** the render fails before it draws, asking for the picture to be staged again or naming the font

#### Scenario: Another canvas version

- **WHEN** the film's npm packages install another version of the canvas package than the engine draws with, or none
- **THEN** staging and rendering refuse before the renderer starts, naming both versions

### Requirement: The stylesheet's faces have one reader

The engine SHALL read a film's `@font-face` rules once, for the audits' text table and for the faces a stage's record names. A rule SHALL be read when it declares one family and one source, `url(<file>)` with or without `format(...)`, and beside them only `font-weight`, `font-style` or `font-display`. Any other rule, two rules of one family, a rule that names no declared font and a declared font that no rule names SHALL be refused by name, at staging and by the audits.

#### Scenario: The sample film's faces

- **WHEN** the sample film's picture is staged
- **THEN** the stage's record names its four families, each with its font's place in the stage, and the audits' table holds the same four

#### Scenario: A rule in another form

- **WHEN** a rule declares `src: local("B"), url(fonts/b.otf)` or a `unicode-range`
- **THEN** staging and the audits refuse, naming the rule, and no face is left out without a word

#### Scenario: A declared font that no rule names

- **WHEN** the film declares a font that no rule of its stylesheet names
- **THEN** staging refuses, naming the font

### Requirement: A rendered picture is encoded on the engine's keyframe grid

A render SHALL encode its frames with x264 by the one definition the derived picture is encoded by: at the same rate factor, with no B-frame, a keyframe at every 2 s from the first frame and nowhere else, 4:2:0 chroma in limited range, with BT.709 stated as its matrix, primaries and transfer, every frame on the frame rate's grid. A picture joined from spans SHALL hold the keyframes that one process writes, and validation SHALL refuse a rendered picture whose keyframes leave that grid.

#### Scenario: A rendered picture is validated

- **WHEN** a picture drawn in several spans is validated
- **THEN** it holds every frame of the film at the film's frame rate with no B-frame, and its keyframes stand at every 2 s and nowhere else

#### Scenario: A keyframe off the grid

- **WHEN** a rendered picture holds a keyframe between two of the grid, or lacks one of the grid
- **THEN** validation refuses the picture, naming the grid

#### Scenario: What the encoded picture states

- **WHEN** a rendered picture's stream is read
- **THEN** it states 4:2:0 chroma, limited range and BT.709 as its matrix, its primaries and its transfer, and a frame of pure red decodes to the BT.709 values of red in limited range

#### Scenario: One process and several spans

- **WHEN** one stage is drawn in one process and again in three spans
- **THEN** both films hold the same count of frames and the same keyframes

### Requirement: A picture is drawn in four spans unless a count is named for a measurement

A picture SHALL be drawn in 4 contiguous spans of whole groups of frames, one process and one encoder each, joined by stream copy, unless `FILMKIT_RENDER_SPANS` names a positive whole number, which it then uses; a draft SHALL be drawn in one process. A value that is no positive whole number SHALL be refused by the variable's name before the renderer starts. A span that fails, by its draw or by its encoder, SHALL end the others and fail the render at once.

#### Scenario: The count without the variable

- **WHEN** a picture is rendered with the variable unset
- **THEN** the renderer command names 4 spans and the receipt records 4

#### Scenario: A count named for a measurement

- **WHEN** `FILMKIT_RENDER_SPANS` is 6
- **THEN** the renderer command names 6 spans and the receipt records 6

#### Scenario: A value that is no count

- **WHEN** `FILMKIT_RENDER_SPANS` is `many`
- **THEN** the render is refused before the renderer starts, naming the variable

#### Scenario: A film shorter than its spans

- **WHEN** a film of two groups of frames is drawn in 8 spans
- **THEN** it is drawn in two spans of one group each

#### Scenario: A render asked to end

- **WHEN** a command that draws a picture in spans is sent SIGTERM while they draw
- **THEN** no span process and no encoder is left when the command exits, and no picture or report that a later run could take for a whole render

#### Scenario: A draw that fails midway

- **WHEN** the composition fails at a frame after the encoders have started, in one process or in one span of several
- **THEN** the renderer exits with a failure at once, no encoder is left waiting for frames, the other spans end, and the receipt records the exit

#### Scenario: An encoder that takes fewer frames than its span

- **WHEN** an encoder ends with status 0 before it was given every frame of its span
- **THEN** the render fails, naming the frames it took and the frames of the span

#### Scenario: A spans' folder that holds anything else

- **WHEN** the folder named for a render's spans holds a file that no render wrote
- **THEN** the render refuses and removes nothing

### Requirement: A render receipt names the canvas that drew the picture

Each render receipt SHALL name the canvas package with its installed version and the integrity npm recorded for it, the native library the render loaded, the text renderer its processes ran, the operating system, the spans, the frames given to the encoders and the digest of the drawn frames. Validation SHALL refuse a picture whose receipt names another package, version or text renderer, or no canvas.

#### Scenario: The receipt of a render

- **WHEN** a picture is rendered
- **THEN** its receipt names `@napi-rs/canvas`, the installed version and its integrity, the loaded library's path, SHA-256 and package, `system` text, the operating system's system, release and version, the spans and the frames

#### Scenario: A render that failed

- **WHEN** a render that did not complete left a receipt, which names no text renderer
- **THEN** validation refuses it as a render that did not complete, not as another renderer's

#### Scenario: A picture a browser drew

- **WHEN** a picture's receipt names no canvas, as the receipt of a render by a browser does
- **THEN** validation refuses the picture and asks for it to be rendered again

#### Scenario: A render that reports nothing

- **WHEN** a renderer exits 0 without reporting the frames it drew
- **THEN** the render is refused after its receipt is written

### Requirement: A receipt names the native library a render loaded

Each drawing process of a render SHALL report the native library it loaded for the canvas: its path, its SHA-256 and the package whose manifest stands beside it. The receipt SHALL name that library as reported, on any platform, with the integrity npm recorded for its package. The engine SHALL pin the library's SHA-256 for the platform a release qualifies, and SHALL NOT pass `NAPI_RS_NATIVE_LIBRARY_PATH`, by which the canvas's loader takes another library, on to a render.

#### Scenario: The pinned library

- **WHEN** a film that installs the pinned canvas build renders a picture on Apple silicon
- **THEN** the receipt names the library's path in the binary package, the pinned SHA-256 and that package, and the picture is a render by the pinned build

#### Scenario: Another library than the package's

- **WHEN** a render's processes load another native library than the pinned package holds, as another platform's package or a file that differs
- **THEN** the receipt names that library by its SHA-256 and its package as they are, and the picture is no render by the pinned build

#### Scenario: The variable in the caller's environment

- **WHEN** a render command runs in an environment that names another library to the canvas's loader
- **THEN** the renderer's environment does not hold that variable, and holds the caller's others

### Requirement: Two draws of one stage state one digest of their drawn frames

A render SHALL state a digest over the pixels of every frame it drew, in the film's order, that does not depend on the spans the film was drawn in. Two renders of one stage SHALL state the same digest, and `qualify-renderer` SHALL refuse two renders that state different ones. The encoded bytes of two renders SHALL NOT be required to be equal.

#### Scenario: One process and several spans

- **WHEN** one stage is drawn in one process and again in three spans
- **THEN** both receipts state the same digest, whether or not the two files hold the same bytes

#### Scenario: Another picture

- **WHEN** an edition's captioned and uncaptioned stages are drawn
- **THEN** their receipts state different digests

#### Scenario: Two renders that drew different frames

- **WHEN** `qualify-renderer` renders a stage again and the second render states another digest than the first
- **THEN** it refuses, its record says that the renders were not drawn alike, and the second render is kept

### Requirement: A stage holds the picture's data beside its document

`stage-picture` SHALL write the picture's data, the timeline with its render offset and edition and, for the uncaptioned picture, no captions, as `film.json` in the stage, and the document SHALL inline the same data. A stage SHALL copy the composition, the stylesheet and the declared fonts, and no timeline engine. A stage whose data differs from what the current sources derive SHALL be refused.

#### Scenario: The data and the document

- **WHEN** an edition's picture is staged
- **THEN** the stage's `film.json` holds exactly the data its document inlines

#### Scenario: Data changed after staging

- **WHEN** a stage's `film.json` is edited or removed after staging
- **THEN** the stage is refused as not the current picture
