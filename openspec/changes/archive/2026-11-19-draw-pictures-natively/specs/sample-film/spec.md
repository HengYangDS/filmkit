## REMOVED Requirements

### Requirement: The sample build qualifies the renderer

**Reason**: it qualified a browser build under `software` capture and compared the receipts' browsers and renderer versions. "The sample build qualifies the canvas the engine pins" keeps the second render and its comparison, and adds the digest of the drawn frames. Its scenario "The supply that ran" becomes "The build that ran is not the pinned one", for a canvas build in place of a browser, and "Renders that differ by the encoder alone" is kept under its name.

**Migration**: none for a film: `qualify-renderer` keeps its name and its record's place. A record written by an earlier engine names a browser and a capture; one written now names the canvas and whether the two renders were drawn alike.

## ADDED Requirements

### Requirement: The sample build qualifies the canvas the engine pins

The sample film SHALL declare `software` capture. Its picture task SHALL render the Chinese captioned stage a second time with `qualify-renderer`, in another count of spans than the first, and refuse unless the two renders state one digest of their drawn frames and pass the comparison of a rendered pair with no row left out, and SHALL render the Chinese uncaptioned picture with `--native` and compare that pair at every frame. A release of the engine requires this qualification to pass.

#### Scenario: Two renders of one stage

- **WHEN** `qualify-renderer` runs after the Chinese captioned picture is rendered and validated
- **THEN** its record names the canvas that ran with the native library it loaded, says whether that is the pinned build, names both renders' SHA-256, spans, drawn digests and frames, the second drawn in one process where the first was drawn in four, says that they were drawn alike, holds the comparison's report without a finding, and states how many frames decode identically, the first that does not, and the lowest PSNR of any frame with that frame

#### Scenario: A picture another canvas build drew

- **WHEN** `qualify-renderer` runs and the captioned picture's receipt names another canvas build than the one the film's npm packages install now
- **THEN** it refuses before it renders, naming both, and writes no record

#### Scenario: A second render that loads another library

- **WHEN** the second render's processes load another native library than the first render's receipt names
- **THEN** `qualify-renderer` refuses, naming both builds by the package's integrity, the library's SHA-256 and the text renderer, and writes no record

#### Scenario: The build that ran is not the pinned one

- **WHEN** both renders are drawn by one canvas build that is not the build the engine pins
- **THEN** the two are compared as any pair, and the record names that build and says that it is not the pinned one

#### Scenario: Renders that differ by the encoder alone

- **WHEN** the two renders state one digest and their decoded frames differ within the encoders' noise
- **THEN** `qualify-renderer` passes, and its record states how many frames decode identically and the lowest PSNR of any frame, which one pass over both renders measured

#### Scenario: A picture another renderer made

- **WHEN** `qualify-renderer` runs and the captioned picture's receipt names another canvas version than the engine's, or no canvas
- **THEN** it refuses before it renders, and writes no record

#### Scenario: A pass over every frame that fails

- **WHEN** the pass that counts the frames that decode identically fails after the comparison has passed
- **THEN** the record holds the comparison's report and its verdict, and says why those facts were not measured

#### Scenario: Renders that drew different frames

- **WHEN** the second render states another digest of its drawn frames than the first
- **THEN** `qualify-renderer` refuses, naming both digests, and keeps the second render

#### Scenario: A one-frame fault in one render

- **WHEN** the second render holds a fragment for one frame that the first does not
- **THEN** `qualify-renderer` refuses, naming the frame, its time, its box and the render that holds it, and keeps the second render

#### Scenario: A difference that lasts, or another length

- **WHEN** the renders differ beyond the encoders' noise for two frames or more, or hold different counts of frames
- **THEN** `qualify-renderer` refuses, naming the frames or both counts
