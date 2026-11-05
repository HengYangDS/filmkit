# picture-gates Specification

## Purpose

Audit an edition's picture through all its speech, and keep a render from starting while a gated finding remains.

## Requirements

### Requirement: The frame audit measures balance and cover through speech

The frame audit SHALL measure, in every voiced frame it exercises, the box around every lit mark and legible name in the content band. It SHALL report per scene each run of 2 seconds or more of speech in which that box stands more than 12% of the frame's width or height off the content centre, or covers less than a tenth of the content band, with the run's start, end and worst value.

#### Scenario: A picture that stands off centre through a thought

- **WHEN** a scene's lit picture stands 13% above the content centre through 2.5 seconds of speech
- **THEN** the audit reports one off-centre run for that scene with its start, its end and its largest offset

#### Scenario: A brief excursion is not a run

- **WHEN** the lit picture stands 13% off for 1.5 seconds of speech and then returns within 12%
- **THEN** the audit reports no off-centre run

#### Scenario: Quiet does not count

- **WHEN** the lit picture covers less than a tenth of the band only while no one speaks
- **THEN** the audit reports no thin run

### Requirement: An edition's picture is checked before it renders

`check-picture` SHALL run the frame audit over every frame of the edition's timeline at one thirtieth of a second, the sync audit on that audit's trace and marks, and the motion audit at 30 frames per second, on the current composition and timeline. It SHALL write a gate record naming the SHA-256 of the composition, the timeline, the stylesheet and each declared font, the engine version, each audit's report and every gated finding, and SHALL refuse when a gated finding exists.

#### Scenario: A clean picture passes

- **WHEN** no audit reports a gated finding
- **THEN** `check-picture` writes a passing record and exits 0

#### Scenario: A gated finding refuses

- **WHEN** the frame audit reports an overlap or an off-centre run
- **THEN** `check-picture` writes a refused record, names each gated finding and exits with a refusal

### Requirement: A render waits for a passing gate record

`render-picture` SHALL refuse an edition before it starts the renderer unless the edition's gate record passed and names the current composition's, timeline's, stylesheet's and declared fonts' SHA-256 and the running engine version.

#### Scenario: The composition changed after its check

- **WHEN** `picture/film.js` changed after `check-picture` passed
- **THEN** `render-picture` refuses and names `check-picture` as the step to run again

#### Scenario: A font changed after its check

- **WHEN** a declared font changed after `check-picture` passed
- **THEN** `render-picture` refuses and names `check-picture` as the step to run again

#### Scenario: An edition that was never checked

- **WHEN** the edition has no gate record
- **THEN** `render-picture` refuses before the renderer starts

### Requirement: The headless audits measure text with the film's fonts

The frame and motion audits SHALL measure each text the composition draws by the advance widths of the face its font names, when the film's stylesheet declares that face with one of the film's declared fonts as its source: the sum of its characters' advances at its size, plus the letter spacing for each character. A family the stylesheet does not declare, and a character the face does not map, SHALL keep the estimate.

#### Scenario: A declared face

- **WHEN** the stylesheet declares the family `FilmLatin` from a declared font and the composition measures `Data` in 30px FilmLatin
- **THEN** the audit's width of `Data` is the sum of the four characters' advances in that font times 30

#### Scenario: A family the stylesheet does not declare

- **WHEN** the composition measures a text in a family the stylesheet does not declare
- **THEN** the audit measures it by the estimate, as without a table

#### Scenario: A character the face does not map

- **WHEN** a text in a declared face holds a character that the face's character map lacks
- **THEN** that character is measured by the estimate and the others by the face

### Requirement: The frame audit measures balance as the reviewers do

The frame audit SHALL take, in every frame it exercises, the box of every paint whose colour mixed over the ground at its opacity is brighter than grey 60 within rows 120–919, and its horizontal offset from x 960, and SHALL report per scene each run of 1.5 seconds or more in which that box stands more than 90 px off, with its start, its end and its largest offset in px.

#### Scenario: A build-up that stands off centre

- **WHEN** a scene's lit picture stands 120 px left of centre for 1.6 seconds while its parts arrive, then is centred
- **THEN** the audit reports one off-centre build-up for that scene with its start, its end and its offset of 120 px

#### Scenario: A brief state is not a build-up run

- **WHEN** the lit picture stands 200 px off for 1.4 seconds and then within 90 px
- **THEN** the audit reports no off-centre build-up

#### Scenario: A lone centred mark

- **WHEN** a single mark stands centred on x 960 before the rest of its scene arrives
- **THEN** the audit reports no run for it

### Requirement: The frame audit measures still states off centre

The frame audit SHALL report per scene each run of 2 seconds or more in which that box stands more than 50 px off while its left and right edges stay within 4 px, unless the frame that ends the run holds a wider box of the same scene that contains it, with its start, its end and its largest offset in px.

#### Scenario: A settled composition off centre

- **WHEN** a scene's finished picture stands still 60 px right of centre for 2.5 seconds
- **THEN** the audit reports one off-centre settled run for that scene with its offset of 60 px

#### Scenario: A still state the next part grows from

- **WHEN** the lit picture stands still 70 px off for 2.5 seconds and then widens to the right while it keeps every part it showed
- **THEN** the audit reports no settled run

#### Scenario: A build-up within its limit

- **WHEN** the lit picture stands 70 px off for 3 seconds while its right edge grows by 40 px
- **THEN** the audit reports no settled run and no build-up

### Requirement: The picture gate refuses a picture off the reviewers' balance

`check-picture` SHALL refuse `off_centre_builds` and SHALL record `off_centre_settled` in the gate record without refusing it.

#### Scenario: An off-centre build-up refuses

- **WHEN** the frame audit reports an off-centre build-up
- **THEN** `check-picture` writes a refused record that names it and exits with a refusal

#### Scenario: A still state off centre is recorded

- **WHEN** the frame audit reports an off-centre settled run and no gated finding
- **THEN** `check-picture` writes a passing record that lists the settled run

### Requirement: The frame audit measures how settled text lines up

The frame audit SHALL measure the settled names and marks of the content band in every voiced frame it exercises, and SHALL report per scene each text-layout defect that lasts 1 second or more, with its start, its end, its texts and its measured offsets.

#### Scenario: A row of names on two baselines

- **WHEN** two names of one size stand side by side through 2 seconds of speech with baselines 6 px apart
- **THEN** the audit reports one ragged row for that scene with its start, its end, both texts and both baselines

#### Scenario: A passing misalignment is not reported

- **WHEN** the two names stand on different baselines for half a second and then share one
- **THEN** the audit reports no ragged row

#### Scenario: Lines and columns that do not line up

- **WHEN** the lines of one left-aligned block start 5 px apart, or a line's ink stands 4 px below the ink of the line above it
- **THEN** the audit reports a ragged column or crammed lines for that scene with the texts and the offsets

#### Scenario: Marks at uneven pitch and names that touch marks

- **WHEN** like marks stand at uneven pitch under names at equal gaps, or a name comes within 3 px of a mark's stroke
- **THEN** the audit reports an uneven pitch or a touching mark, measured on the stroke's points rather than its bounding box

#### Scenario: A heading at the top of a tall card

- **WHEN** a name stands at the top of a card more than three of its lines tall
- **THEN** the audit reports no card-centre finding for it

### Requirement: The picture gate refuses every text-layout finding

`check-picture` SHALL refuse the text-layout findings `ragged_rows`, `ragged_columns`, `crammed_lines`, `off_card_centre`, `uneven_pitch`, `touching_marks` and `mixed_case`.

#### Scenario: A ragged row refuses

- **WHEN** the frame audit reports a ragged row
- **THEN** `check-picture` writes a refused record that names it and exits with a refusal

#### Scenario: An uneven pitch refuses

- **WHEN** the frame audit reports an uneven pitch
- **THEN** `check-picture` writes a refused record that names it and exits with a refusal

#### Scenario: Mixed case refuses

- **WHEN** the frame audit reports names of one set in mixed case
- **THEN** `check-picture` writes a refused record that names them and exits with a refusal

### Requirement: The picture gate refuses continuity findings

`check-picture` SHALL refuse each seat and each run of unnamed speech that the sync audit lists, naming each with its thought and its time, and SHALL list each thought that holds the previous picture over in the gate record without refusing it.

#### Scenario: A seat refuses

- **WHEN** the sync audit lists a mark that stands 1.2 seconds in speech before a name is legible at it
- **THEN** `check-picture` writes a refused record that names the seat's thought, its start and its wait, and exits with a refusal

#### Scenario: Unnamed speech refuses

- **WHEN** the sync audit lists a run of 1.6 seconds of a thought's speech with no legible name
- **THEN** `check-picture` writes a refused record that names the thought and the run

#### Scenario: A held picture is recorded

- **WHEN** the sync audit lists only a thought that keeps the previous picture for 2.5 seconds
- **THEN** `check-picture` writes a passing record that lists the held picture

### Requirement: The seat check judges stand-ins and pictograms

The seat check SHALL judge on its own a dashed closed outline that a link or other paint joins to a larger mark, naming it only by a legible name within its reach or by a mark or text inside it, and SHALL count a frame as named by its contents only when they hold a name, a written value or a named mark.

#### Scenario: A dashed place at a link's end

- **WHEN** a dashed empty box at the end of a link from a named card stands through 5 seconds of speech before a name stands at it or its content arrives
- **THEN** the seat check lists a seat at the box with a wait of 5 seconds

#### Scenario: A solid card joined by a link

- **WHEN** a solid empty card joined by a link to a named mark stands through the same speech
- **THEN** it is judged with the mark it joins and no seat is listed for it

#### Scenario: A frame that holds only a pictogram

- **WHEN** a frame that holds only a tool's pictogram stands 4 seconds in speech before a name is legible at it
- **THEN** the seat check lists a seat for it

#### Scenario: A frame that holds a named mark

- **WHEN** a frame holds a card whose name is legible
- **THEN** the frame counts as named and no seat is listed for it

### Requirement: The sync audit lists caption cues that echo labels

The sync audit SHALL list each caption cue of three or more words whose words all stand, in their order, in one label legible during the cue, and each such cue of which at least 80% of the words stand in labels legible during it, with the cue's start, its text and the labels. `check-picture` SHALL refuse the first kind and record the second; a cue that is itself one quotation counts as the second kind.

#### Scenario: A cue drawn whole in one label

- **WHEN** the cue `The people watching the pipeline report this back,` shows while the label `The people watching the pipeline report this back` is legible
- **THEN** the audit lists it as a whole echo, and `check-picture` refuses and names the cue's start and text

#### Scenario: A cue drawn in two labels

- **WHEN** the cue `things can change without the view showing it:` shows while the labels `Things can change` and `Without the view showing it` are legible
- **THEN** the audit lists it as a partial echo of 100%, and `check-picture` records it without refusing

#### Scenario: A cue that quotes what the picture shows

- **WHEN** the cue `“Deduplicate by stock code and date.”` shows while the label `Deduplicate by stock code and date` is legible
- **THEN** the audit lists it as a quoted echo of 100%, and `check-picture` records it as a quotation without refusing

#### Scenario: A short cue

- **WHEN** a cue of two words shows while a label holds both
- **THEN** the audit lists no echo for it

### Requirement: The frame audit measures the case of a set of names

The frame audit SHALL report per scene each run of 1 second or more of speech in which names of one set, or of one row of one size and baseline, that begin with a letter of a cased script do not all begin in one case, with the names. A name whose first word holds a capital after its first letter, such as an acronym, SHALL be left out.

#### Scenario: Three equal cards in mixed case

- **WHEN** three cards in one row are named `The observation`, `The inference` and `the proposed remedy` through 2 seconds of speech
- **THEN** the audit reports mixed case for that scene with the three names

#### Scenario: A smaller qualifier under a name

- **WHEN** a lowercase qualifier of a smaller size stands under each capitalised name of a row
- **THEN** the audit reports no mixed case

#### Scenario: An acronym and a script without case

- **WHEN** a row holds `ETHOS` beside `each repository`, or Chinese names beside each other
- **THEN** the audit reports no mixed case

### Requirement: The opening shows the declared title

`check-picture` SHALL refuse an edition whose frames before the first word show every word of the title its script declares, in texts at 3:1 or more against the ground, for less than 1 second, naming the title and the words no such frame shows. A text counts for the title words it repeats as one run, so the title may stand in parts and on several lines beside other texts.

#### Scenario: A title card before the first word

- **WHEN** the title's two parts stand on two lines at full ink through the 2 seconds before the first word
- **THEN** `check-picture` writes no title finding

#### Scenario: An opening without the title

- **WHEN** the frames before the first word show only the Illustrative chip
- **THEN** `check-picture` writes a refused record that names the title and every word it never shows, and exits with a refusal

#### Scenario: A title only after the first word

- **WHEN** the title stands only once the narration has begun
- **THEN** `check-picture` refuses the edition

### Requirement: Text at rest stays legible against the ground

`check-picture` SHALL refuse each run of 0.7 seconds or more in which a text holding a letter or a digit shows above 4% opacity at a WCAG contrast below 4.5:1 against the ground, its colour composited over the ground at its opacity, naming its scene or role, its text, its run and its lowest contrast. A shorter run is a text entering or leaving the picture and SHALL NOT refuse.

#### Scenario: A named item dimmed at rest

- **WHEN** a list item rests at 3.34:1 for 1 second
- **THEN** `check-picture` writes a refused record that names the item, its run and 3.34:1, and exits with a refusal

#### Scenario: A fade

- **WHEN** a text fades in through 4.5:1 within 0.6 seconds
- **THEN** `check-picture` writes no contrast finding for it

#### Scenario: A mark that holds no letter

- **WHEN** an arrow drawn as text stands at 2:1
- **THEN** no contrast finding is written for it
