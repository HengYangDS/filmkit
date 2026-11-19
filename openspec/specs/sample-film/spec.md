# sample-film Specification

## Purpose

Prove the engine end to end with a short bilingual film that the repository carries, builds and verifies, and that the engine's tests load instead of any production film.

## Requirements

### Requirement: The repository builds a sample film

The repository SHALL carry a short bilingual sample film whose tracked sources and declared supply let the engine build it end to end on Apple-silicon macOS, offline after the supply step, writing only below the sample's `build/` folder. Its build SHALL pass the sound gate on each edition's soundtrack before any picture is staged.

#### Scenario: The sample film builds and verifies

- **WHEN** the supply step and then the sample's build run on Apple silicon
- **THEN** both editions' recordings, soundtracks, captions, pictures and packaged films are produced below the sample's `build/`
- **AND** the technical verification of both editions passes

#### Scenario: The sample's soundtracks pass the sound gate

- **WHEN** the sample's sound stage has assembled an edition's soundtrack and written its captions
- **THEN** `check-sound` records a pass for that edition before its picture stage runs

### Requirement: The engine's tests load only the sample film

The engine's tests SHALL load the sample film as the film the engine builds, and no test SHALL read another film's sources.

#### Scenario: The suites run without another film

- **WHEN** the engine's Python and Node suites run in a checkout of this repository alone
- **THEN** every test that loads a film loads the sample film, and the suites pass

### Requirement: The sample film meets the owner's text and review bars

The sample film's text SHALL line up as the frame audit measures it, and its review configuration SHALL hold the overall score and every dimension at 95 or more.

#### Scenario: The sample's picture passes the text-layout measures

- **WHEN** `check-picture` audits either edition of the sample film
- **THEN** the frame audit reports no text-layout finding, and the closing checklist's items share one left edge beside their checks

#### Scenario: The sample's review floors

- **WHEN** the sample film's review configuration is read
- **THEN** its overall and dimension minimums are 95

### Requirement: The sample film's review holds three levels

The sample film SHALL declare `[review.levels]` holding each of its review dimensions in one of 信, 达 and 雅, and its prompt SHALL cite `{levels}` and `{sentences}`.

#### Scenario: The sample's review configuration

- **WHEN** the sample film's declaration and prompt are read
- **THEN** its five dimensions stand in the three levels and its prompts state the levels and name the sentences file

### Requirement: The sample film offers its captions on and off

The sample film's build SHALL make and validate each edition's picture with and without captions, the Chinese uncaptioned picture rendered and the English one derived, compare each pair, package the four films and read the players back with the captions turned off and on.

#### Scenario: The sample film's four films

- **WHEN** the sample film is built and its players are read back
- **THEN** each edition's comparison passes, its four films verify, and each player's captions control switches between its films

### Requirement: The sample film renders its drafts before its pictures

The sample film SHALL declare its drafts. Its picture task SHALL stage both pictures of each edition, render the edition's draft with `render-draft` and pass `preflight` before it renders the edition's pictures, and SHALL end by asking `admitted` of both editions.

#### Scenario: The sample's picture task

- **WHEN** the sample film's picture task runs on a build without packaged films
- **THEN** `render-draft` writes each edition's draft record and `preflight` reports every input of each edition current before `render-picture` runs

#### Scenario: Both editions still admitted after their renders

- **WHEN** both editions' pictures are rendered, validated and compared
- **THEN** `admitted` reports each edition admitted on the receipts its `preflight` wrote

### Requirement: The sample film prints its build's durations

The repository SHALL carry a task that prints the duration records of the sample film's build with each edition's sum and the time of the build.

#### Scenario: After a sample build

- **WHEN** the durations task runs after the sample film was built
- **THEN** it lists each edition's commands from narration to verification with their seconds, the geometry check and the cover check among them, and prints the time of the build

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
