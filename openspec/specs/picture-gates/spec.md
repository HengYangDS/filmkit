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

On the edition's current composition and timeline, `check-picture` SHALL run the frame audit over every frame at 1/30 s, the sync audit on its trace and marks, the motion audit at 30 fps and the detail audit at 60, and the mass audit on the uncaptioned stage. Its record SHALL name the SHA-256 of the composition, timeline, stylesheet, each declared font and the uncaptioned stage's record, the engine version, each report and every gated finding, and it SHALL refuse when a gated finding exists.

#### Scenario: A clean picture passes

- **WHEN** no audit reports a gated finding
- **THEN** `check-picture` writes a passing record and exits 0

#### Scenario: A gated finding refuses

- **WHEN** the frame audit reports an overlap or an off-centre run
- **THEN** `check-picture` writes a refused record, names each gated finding and exits with a refusal

#### Scenario: The record binds the detail audit's report

- **WHEN** `check-picture` passes
- **THEN** its record names the detail audit's report with its SHA-256 beside the frame, sync, text and motion reports

#### Scenario: An uncaptioned stage not yet staged

- **WHEN** the edition's uncaptioned stage has no record and `check-picture` runs
- **THEN** `check-picture` refuses before any audit starts, naming the stage and `stage-picture-uncaptioned`, and writes no record

#### Scenario: A stale uncaptioned stage

- **WHEN** the composition changed after the uncaptioned stage was staged, and only the captioned picture was staged again
- **THEN** `check-picture` refuses before any audit starts, naming what differs, and writes no record

#### Scenario: The record binds the mass audit's report and its stage

- **WHEN** `check-picture` passes
- **THEN** its record names the mass audit's report beside the other reports, and the SHA-256 of the uncaptioned stage's record

### Requirement: A render waits for a passing gate record

`render-picture` SHALL refuse an edition before it starts the renderer unless the edition's gate record passed and names the current composition's, timeline's, stylesheet's, declared fonts' and uncaptioned stage record's SHA-256 and the running engine version.

#### Scenario: The composition changed after its check

- **WHEN** `picture/film.js` changed after `check-picture` passed
- **THEN** `render-picture` refuses and names `check-picture` as the step to run again

#### Scenario: A font changed after its check

- **WHEN** a declared font changed after `check-picture` passed
- **THEN** `render-picture` refuses and names `check-picture` as the step to run again

#### Scenario: An edition that was never checked

- **WHEN** the edition has no gate record
- **THEN** `render-picture` refuses before the renderer starts

#### Scenario: The uncaptioned stage was staged again after its check

- **WHEN** the uncaptioned stage was staged again with other bytes after `check-picture` passed
- **THEN** `render-picture` refuses, names the stage's binding and `check-picture` as the step to run again

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

The frame audit SHALL take, in every frame it exercises, the box of every paint whose colour mixed over the ground at its opacity is brighter than grey 60 within rows 120–919, leaving out each declared frame stroke, and its horizontal offset from x 960, and SHALL report per scene each run of 1.5 seconds or more in which that box stands more than 90 px off, with its start, its end and its largest offset in px.

#### Scenario: A build-up that stands off centre

- **WHEN** a scene's lit picture stands 120 px left of centre for 1.6 seconds while its parts arrive, then is centred
- **THEN** the audit reports one off-centre build-up for that scene with its start, its end and its offset of 120 px

#### Scenario: A brief state is not a build-up run

- **WHEN** the lit picture stands 200 px off for 1.4 seconds and then within 90 px
- **THEN** the audit reports no off-centre build-up

#### Scenario: A lone centred mark

- **WHEN** a single mark stands centred on x 960 before the rest of its scene arrives
- **THEN** the audit reports no run for it

#### Scenario: A declared frame around content that leans left

- **WHEN** a scene declares its two full-height rails at x 200 and 1720 as frames, its names' box stands still 150 px left of x 960 for 3 s, and the next scene's picture then replaces it
- **THEN** the audit reports an off-centre build-up and an off-centre finished run for that scene, each with an offset of −150 px

#### Scenario: The same rails undeclared

- **WHEN** the same rails are not declared
- **THEN** the audit reports no off-centre build-up and no off-centre still run for the scene

### Requirement: The frame audit measures still states off centre

The frame audit SHALL report per scene each run of 2 s or more in which that box stands more than 50 px off while its left and right edges stay within 4 px, timed from where a glide of 15 px/s or more settling into it passed 50 px, with its start, end and largest offset in px. It SHALL report as held a run whose next frame, after no stage cut, holds a wider box of the same scene that contains it, and as finished a run whose next frame shows another scene or follows a stage cut of its scene.

#### Scenario: A settled composition off centre

- **WHEN** a scene's finished picture stands still 60 px right of centre for 2.5 seconds
- **THEN** the audit reports one off-centre settled run for that scene with its offset of 60 px

#### Scenario: A still state the next part grows from

- **WHEN** the lit picture stands still 70 px off for 2.5 seconds and then widens to the right while it keeps every part it showed
- **THEN** the audit reports one held run for that scene with its offset of 70 px and no settled run

#### Scenario: A build-up within its limit

- **WHEN** the lit picture stands 70 px off for 3 seconds while its right edge grows by 40 px
- **THEN** the audit reports no settled run, no held run and no build-up

#### Scenario: A still state that a stage cut replaces

- **WHEN** the lit picture stands still 70 px off for 2.5 seconds and the next frame, after a stage cut the composition declares for its scene, holds a wider box that contains it
- **THEN** the audit reports one finished run for that scene with its offset of 70 px and no settled run

#### Scenario: A still state that another scene replaces

- **WHEN** the lit picture stands still 70 px off for 2.5 seconds and the next frame shows the next scene's picture
- **THEN** the audit reports one finished run and no settled run

#### Scenario: A still state that a glide settles into

- **WHEN** the lit picture glides out past 50 px off 0.25 seconds before it settles, then stands still 87 px off for 1.9 seconds until a stage cut the composition declares for its scene
- **THEN** the audit reports one finished run for that scene, 2.15 seconds long from the frame the glide passed 50 px, with its offset of 87 px

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

#### Scenario: A quotation followed by its list's comma

- **WHEN** the cue `“Agreed in principle”, ` shows while the label `Agreed in principle` is legible
- **THEN** the audit lists it as a quoted echo of 100%, and `check-picture` records it as a quotation without refusing

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

### Requirement: Wrapped labels are judged at rest from their painted lines

`check-picture` SHALL read the lines of every label a film paints on more than one line from the film's own layout records, and judge them at the frames where every line stands at 0.9 opacity or more. A refusal SHALL name the scene, the label's lines, the first time they stand at rest and each rule they break.

#### Scenario: A label that is still entering

- **WHEN** a wrapped label stands below 0.9 opacity
- **THEN** its lines are not judged until it stands at rest

#### Scenario: A name standing in two places

- **WHEN** the same wrapped name stands at two places of one frame
- **THEN** each place is judged as its own label

### Requirement: A wrapped English label breaks at a phrase

`check-picture` SHALL refuse a label whose words are English, as the language registry reads them in its edition, whose line other than the last ends on one of English's lead words (an article, preposition, conjunction, determiner, possessive, wh-word or auxiliary) or on a lead word the film declares for English. It SHALL also refuse a name of three or more words whose last line holds one word.

#### Scenario: An English line ends on a preposition

- **WHEN** a rail label stands at rest as "A trade in" over "the market"
- **THEN** `check-picture` writes a refused record that names the label's lines and the line ending on "in", and exits with a refusal

#### Scenario: One word left for the last line

- **WHEN** "Bias may hide" stands over "elsewhere"
- **THEN** `check-picture` refuses the label

#### Scenario: An English label in a Chinese edition

- **WHEN** a Latin-script label of the Chinese edition, which reads Latin script as English, stands at rest as "A trade in" over "the market"
- **THEN** `check-picture` refuses it for the line ending on "in"

#### Scenario: A Latin-script label of a language without lead words

- **WHEN** the engine's tests declare a language written in Latin script that declares no lead words, and a label of its edition stands at rest as "A trade in" over "the market"
- **THEN** `check-picture` does not refuse it for a lead word

### Requirement: The lines of a wrapped block stay even

Among the lines of one size in a wrapped label, `check-picture` SHALL refuse a line other than the last that is narrower than the declared share of the widest (0.8 by default), and a last line narrower than the declared last share (0.6 by default).

#### Scenario: A short last line

- **WHEN** a Chinese label stands at rest as 先确认任务、要处理的对象、 over 现状和负责人, its last line 0.48 of its first
- **THEN** `check-picture` refuses the label and names its last line's share

#### Scenario: A name over its smaller gloss

- **WHEN** a name at the label size stands over a two-line gloss at the note size
- **THEN** the name and the gloss are each judged among their own lines, and the shorter gloss is not refused for its size

### Requirement: A Chinese line opens on no closing punctuation

`check-picture` SHALL refuse a wrapped Chinese label whose line after the first opens on closing punctuation.

#### Scenario: A comma at the start of a line

- **WHEN** a label's second line opens on 、
- **THEN** `check-picture` refuses the label

### Requirement: A film declares its wrapping rules and their exceptions

A film MAY declare `[picture.wrapping]` in `content/film.toml`: `line_share`, `last_share`, `lead_words` and `exceptions`, each exception the exact lines of one label with its reason. A label that matches an exception SHALL be recorded and SHALL NOT refuse. The declaration SHALL be refused for a share outside (0, 1], an exception without a reason, and an exception whose lines the film never paints.

#### Scenario: A declared exception

- **WHEN** the film declares "Stated" over "assumptions" as an exception with its reason
- **THEN** `check-picture` records that label with the reason and does not refuse it

#### Scenario: A stale exception

- **WHEN** an exception names lines that no frame of the edition paints
- **THEN** `check-picture` refuses and names the stale exception

### Requirement: The picture gate refuses a whole turn the browser paints without ink

`check-picture` SHALL draw each distinct start and end of every stroked clockwise arc that sweeps a whole turn or more, less 0.00001 rad, from a start off a whole number of turns, once on a scratch canvas in the browser that paints the cover. It SHALL refuse a scene's line whose arc that browser paints without ink from one of its starts and record every other, naming the scene, times, start, line of `picture/film.js` and remedy: an ellipse from 0 with the start as its rotation.

#### Scenario: A start the browser paints without ink

- **WHEN** a scene strokes `arc(x, y, r, a, a + 2 * Math.PI)` from a start `a` of 1.9335 rad, which Chrome Headless Shell 152 paints without ink
- **THEN** `check-picture` refuses, naming the scene, the times, the start, the line that drew the arc and `ellipse(x, y, r, r, a, 0, 2 * Math.PI)`

#### Scenario: A ring that turns

- **WHEN** a scene strokes a ring through a whole turn whose start moves with time and reaches a start the browser paints without ink
- **THEN** `check-picture` refuses that line, naming the frames of the starts that paint no ink and how many of its starts fail, and draws each start once

#### Scenario: Starts the browser paints

- **WHEN** a scene strokes a whole turn from π, 3π/2 or −π/2, which that browser paints in full
- **THEN** `check-picture` passes and records the line with its times, its start and the ellipse that draws it from any start

#### Scenario: Whole turns it never questions

- **WHEN** a scene strokes `ellipse(x, y, r, r, a, 0, 2 * Math.PI)`, `arc(x, y, r, 0, 2 * Math.PI)` or an anticlockwise arc
- **THEN** `check-picture` reports no such finding and starts no browser for it

### Requirement: The sync audit judges an English label by its inflected words in its own thought

When no exact occurrence of a label's words starts within 8 s of its first legible frame, and the language the registry reads those words in declares a stemmer, the sync audit SHALL look for the words in order by their stems in the thought spoken at that frame, or the next one between thoughts. It SHALL judge the label by the nearest such occurrence and record the match as inflected. Every other label SHALL be matched as before.

#### Scenario: A label over another form of its word

- **WHEN** the label "Availability" is first legible at 330.17 s, the thought spoken then says "available" at 330.36 s, and "availability" is next said at 338.60 s
- **THEN** the audit judges the label against "available" at 330.36 s, in sync within its tolerance, and records the match as inflected

#### Scenario: An exact occurrence near the label

- **WHEN** a label's exact words are said 1.2 s after it is first legible
- **THEN** the audit judges it by that occurrence, as before

#### Scenario: Words that only look alike

- **WHEN** the label "Publish" is first legible while its thought says "public" and nothing else near it
- **THEN** the audit finds no match for the label in that thought

#### Scenario: An English label in a Chinese edition

- **WHEN** the Chinese edition shows the label "Agents" while its thought says "Agent"
- **THEN** the audit finds the inflected match by English's stems, as it does today

#### Scenario: A Latin-script label of a language without a stemmer

- **WHEN** the engine's tests declare a language written in Latin script that declares no stemmer, and its edition shows the label "Availability" while its thought says "available"
- **THEN** the audit finds no inflected match and judges the label by its exact words alone

### Requirement: The sync audit judges each appearance of a label

An appearance of a label SHALL be a run of frames in which it is legible in its scene, begun after at least 1 s illegible there. The sync audit SHALL judge each appearance by the nearest occurrence of the label's words that starts within 8 s of its first legible frame and that no earlier appearance was judged by. An appearance with no such occurrence SHALL be recorded as a recall and not judged.

#### Scenario: A label shown again on its words

- **WHEN** "Acceptance" is legible from 214.2 s on its words in 06.3, stands illegible from 240.0 s, and is legible again at 330.17 s while "acceptance" is said at 330.40 s
- **THEN** the audit judges two appearances, the second against 330.40 s

#### Scenario: A label that comes back without its words

- **WHEN** a label legible on its words stands illegible for 3 s and is legible again while its words are not said within 8 s
- **THEN** the audit judges its first appearance and records the second as a recall

#### Scenario: A label across a stage cut

- **WHEN** a label fades out for 0.4 s at a stage cut and is legible again at the same place
- **THEN** the audit judges one appearance

### Requirement: The picture gate refuses every still state off the reviewers' balance

`check-picture` SHALL refuse `off_centre_builds`, `off_centre_held`, `off_centre_settled` and `off_centre_finished`, so that every state the reviewers count off centre refuses the picture.

#### Scenario: An off-centre build-up refuses

- **WHEN** the frame audit reports an off-centre build-up
- **THEN** `check-picture` writes a refused record that names it and exits with a refusal

#### Scenario: A still state off centre refuses

- **WHEN** the frame audit reports an off-centre settled run and no other finding
- **THEN** `check-picture` writes a refused record that names the settled run and exits with a refusal

#### Scenario: A still state held for its next part refuses

- **WHEN** the frame audit reports an off-centre held run
- **THEN** `check-picture` writes a refused record that names it and exits with a refusal

#### Scenario: A finished composition off centre refuses

- **WHEN** the frame audit reports an off-centre finished run
- **THEN** `check-picture` writes a refused record that names it and exits with a refusal

### Requirement: The geometry check records names that stand too close on a row

The geometry check SHALL record every pair of neighbouring names of one scene that stand at rest on one row for a second or more with a clear gap under 1.5 em of the smaller face, each with its scene, both names, its tightest gap in px and in em, when it first stood and the frames that show it. It SHALL count such a pair as a finding and fail only when it is run with `--gate-row-gaps`.

#### Scenario: Two names 1.2 em apart

- **WHEN** two names of one face stand level 36 px apart in a 30 px face for a second
- **THEN** the receipt records a row gap with the gap 36 and 1.2 em, and without `--gate-row-gaps` the check passes

#### Scenario: A film that gates its rows

- **WHEN** the same picture is checked with `--gate-row-gaps`
- **THEN** the pair is a finding and the check fails

#### Scenario: Texts that are not neighbours

- **WHEN** two texts share one registered whole, stand under half an em apart, are set in different sizes, have a lit mark between them, or the first ends in a joining mark such as 、 or a comma after its words
- **THEN** no row gap is recorded

### Requirement: The frame audit measures runs far off centre

The frame audit SHALL report, in every frame, spoken or not, each run of 0.5 s or more within one scene through which the reviewers' box, declared frame strokes left out, stands more than 400 px off x 960 on one side, with its span and its largest offset. The picture gate SHALL refuse each such run that the film does not declare.

#### Scenario: A first mark alone at the far left

- **WHEN** the lit box of a scene stands 624 px left of centre for 1 s while a build's first mark stands alone
- **THEN** the frame audit reports the run with its span and -624 px, and the gate refuses it

#### Scenario: A shorter run, or one at 400 px

- **WHEN** the box stands 624 px off for 0.4 s, or exactly 400 px off for longer
- **THEN** the frame audit reports no far run

#### Scenario: A box that crosses to the other side

- **WHEN** the box stands 500 px left for 1 s and then 500 px right for 0.3 s
- **THEN** the frame audit reports the run on the left and none on the right

#### Scenario: A run that two scenes share

- **WHEN** the box stands 500 px left through the last 0.4 s of one scene and the first 0.4 s of the next
- **THEN** the frame audit reports no far run

#### Scenario: A declared run

- **WHEN** a film declares the far runs on the left of one scene of an edition with a reason
- **THEN** the gate records that scene's runs on the left with the reason and still refuses a run on its right

#### Scenario: A first mark inside a declared frame

- **WHEN** a build's first mark stands alone 624 px left of centre for 1 s inside two rails declared as frames
- **THEN** the frame audit reports the run with -624 px, as without the rails

### Requirement: The geometry check takes its frame from the stage's record

The geometry check SHALL take a picture's width, height, seconds and frames a second from the record of the stage it is handed, `stage.json`, each a whole positive number, and SHALL read no rate from the stage's page. Before it opens a browser it SHALL refuse, in one line that names the file, what is wrong with it and `stage-picture`, a stage whose record is absent, holds no JSON or lacks one of the four, and a stage whose page states another width, height or seconds than its record.

#### Scenario: A stage the engine writes

- **WHEN** the check is handed a stage that `stage-picture` wrote for a film whose template states no rate
- **THEN** it inspects the frames of the record's seconds at the record's rate

#### Scenario: A workspace without a stage's record

- **WHEN** the folder holds a page and no `stage.json`, or a record that states no `fps`
- **THEN** the check exits 1 with one line that names the record and `stage-picture`, opens no browser and writes no receipt

#### Scenario: A page and a record that disagree

- **WHEN** the stage's page states a width of 3840 and its record a width of 1920
- **THEN** the check refuses, naming both figures and `stage-picture`

### Requirement: The geometry check refuses a record that does not cover the staged film

The node `geometry-check` SHALL refuse, after it writes its record, a record that did not pass, that holds a finding or an error, or that does not cover the whole current staged film at a step of 1 or 2 frames, naming the record and what it lacks.

#### Scenario: A record of fewer frames

- **WHEN** the geometry check sampled fewer frames than the staged film's runtime gives at its step
- **THEN** the node refuses, naming the record and the frames it checked against the frames it must

#### Scenario: A covering record

- **WHEN** the record passed on the whole current staged film at a step of 2
- **THEN** the node passes, and the plan holds the edition's render behind no geometry refusal

### Requirement: A composition declares the strokes that only frame a stage

A composition MAY declare a stroke drawn only to frame a stage, a declared frame stroke, by setting `window.__paintRole` to `"frame"` while it strokes it and back to `null` after. The headless audits SHALL record the role on each paint as they record its scene. The frame audit SHALL report as an error a role of another value, and a role in effect while `fill`, `fillText` or `fillRect` is called. The renderer SHALL draw a declared frame stroke as any other stroke.

#### Scenario: A declared rail

- **WHEN** a composition strokes two rails with `window.__paintRole` set to `"frame"` and its names with it `null`
- **THEN** the rails' paints carry the role `frame` and the names' paints carry none

#### Scenario: A misspelt role

- **WHEN** a composition sets `window.__paintRole` to `"frmae"` while it paints
- **THEN** the frame audit reports an error naming the value, and `check-picture` refuses

#### Scenario: A rail drawn as a fill

- **WHEN** a composition calls `fillRect`, or `fill` on a rectangular path, with `window.__paintRole` set to `"frame"`
- **THEN** the frame audit reports an error that only a stroke can be a declared frame stroke, and `check-picture` refuses

#### Scenario: The picture does not change

- **WHEN** the same stage is rendered with and without its frame strokes declared
- **THEN** both renders state the same drawn-frame digest

### Requirement: The frame audit records the declared frame strokes

The frame audit SHALL record per scene the declared frame strokes it leaves out of the reviewers' box, with their number and the box they span, and the picture gate SHALL refuse nothing for them.

#### Scenario: Two declared rails

- **WHEN** a scene strokes two rails declared as frames
- **THEN** the frame report records two declared frame strokes for that scene with the box they span, and `check-picture` refuses nothing for them

### Requirement: The other frame measures count what they counted

Every measure of the frame audit other than the reviewers' box runs, the vertical runs and the mass SHALL count declared frame strokes and paints outside every scene as any other paint.

#### Scenario: A declared rail and the cover

- **WHEN** the same stage is audited with its rails declared as frames and with them undeclared
- **THEN** both reports state the same `thin_lit` and `sparse_runs`

### Requirement: The mass audit reads a lit cell as the reviewers do

The mass audit SHALL reduce each frame it draws to a 480 × 270 grey, each cell the full-range BT.709 luma (0 to 255) of the mean colour of the 4 × 4 pixels of the 1920 × 1080 frame it covers, and SHALL take as lit each cell of rows 30 to 229 whose grey is above 60.

#### Scenario: The grey of a lit cell

- **WHEN** a frame holds a uniform cell of luma 61 and another of luma 59
- **THEN** the first is lit and the second is not

### Requirement: The mass audit weighs each frame's lit scene paints

The mass audit SHALL draw the edition's uncaptioned stage on the renderer's native canvas at 1920 × 1080 every 0.25 s with the renderer's text renderer, drawing the ground the composition lays with `fillRect` and every paint of the scene being drawn, and leaving out every other paint of no scene and every declared frame stroke. A frame of 40 lit cells or more SHALL have a mass centre, the mean of its lit cells' centres; one of fewer has none.

#### Scenario: A thin line over the ground

- **WHEN** a scene's 2 px line in the line colour, of luma 115, covers half of a cell over the composition's ground of luma 20
- **THEN** the cell reads as the line over the ground, luma 67, and is lit, as in the rendered picture, not as over the canvas's starting black, which would read 57

#### Scenario: A filled square

- **WHEN** a frame shows only a filled square of the ink from x 200 to 600
- **THEN** its mass centre stands at x 400 within 4 px

#### Scenario: Bands outside the content

- **WHEN** a running head above row 120 is added to a frame
- **THEN** its lit cells and its mass centre do not change

#### Scenario: Credits are not weighed

- **WHEN** the credits are drawn with no scene for 3 s
- **THEN** those frames have no mass centre and the mass audit reports no run for them

#### Scenario: A frame of declared frame strokes alone

- **WHEN** a scene paints only strokes declared as frames
- **THEN** the frame is that scene's, has no mass centre and counts its declared frame strokes

#### Scenario: A picture too faint to weigh

- **WHEN** a frame has 39 lit cells
- **THEN** it has no mass centre

#### Scenario: A declared frame stroke is not weighed

- **WHEN** a frame shows a filled square from x 200 to 600 and a rail at x 1720 declared as a frame
- **THEN** its mass centre stands at x 400 within 4 px

#### Scenario: A film that declares no frame

- **WHEN** the same rail at x 1720 is not declared
- **THEN** the rail's lit cells count, and the mass centre moves toward it

### Requirement: The mass audit refuses a frame without its ground

The mass audit SHALL refuse, naming the frame, a frame that paints a scene before it lays its ground, a `fillRect` over the whole canvas at full opacity, so that no frame is weighed on the frame before it.

#### Scenario: A frame without its ground

- **WHEN** a frame lays its ground with a path fill, or with a `fillRect` that does not cover the canvas, or not at all, before it paints a scene
- **THEN** the mass audit refuses it, naming the frame, and weighs nothing on the frame before it

### Requirement: The mass audit reports where the weight leans

The mass audit SHALL report per scene drawn each run of 1.5 s or more through which that scene is drawn and the mass centre stands more than 90 px off x 960, moving or not, with its start, its end and its largest signed offset in px; a frame in which another scene is drawn, a frame without a mass centre and a gap in the samples SHALL each end a run.

#### Scenario: An undeclared frame around content that leans left

- **WHEN** a scene draws two undeclared rails 4 px wide at x 200 and 1720 from row 120 to row 919, and names whose lit cells outnumber the rails' two to one and whose own mass stands 150 px left of x 960 stand still for 3 s
- **THEN** the frame audit reports no off-centre box run for the scene, and the mass audit reports one run for it with its span and an offset beyond −90 px

#### Scenario: A declared frame around content that leans left

- **WHEN** the same rails are declared as frames
- **THEN** the mass audit reports one run for the scene with an offset of −150 px within 4 px

#### Scenario: The same names centred

- **WHEN** the same scene's names stand with their mass on x 960 between the same rails for 3 s
- **THEN** the mass audit reports no run for the scene

#### Scenario: The outgoing scene drawn into the next segment

- **WHEN** the next segment's timeline starts while the composition still draws the outgoing scene for 1.25 s, until the incoming scene's cut, and the outgoing scene's mass stands 120 px left from 0.5 s before the segment starts to its cut
- **THEN** the mass audit reports one run for the outgoing scene, 1.75 s long, spanning the segment's start

#### Scenario: A brief lean is not a run

- **WHEN** the mass stands 120 px left for 1.2 s and then within 90 px
- **THEN** the mass audit reports no run

#### Scenario: A lean of exactly 90 px

- **WHEN** the mass stands exactly 90 px off for 3 s
- **THEN** the mass audit reports no run

#### Scenario: A frame without a mass inside a lean

- **WHEN** a frame without a mass centre falls 1.25 s into 2.5 s through which the mass stands 120 px left
- **THEN** the mass audit reports no run, since neither part lasts 1.5 s

### Requirement: The mass audit summarises each scene's weight

The mass audit SHALL report for every scene drawn the frames it measured, the mass centre's median offsets from (960, 510) and its share of frames within 90 px of x 960.

#### Scenario: The scene's summary

- **WHEN** the mass audit has measured a scene
- **THEN** its report states the scene's frames measured, its median horizontal and vertical offsets and its share of frames within 90 px

### Requirement: The frame audit measures still states off the vertical centre

The frame audit SHALL report per scene drawn each run of 2 s or more through which the box of that scene's lit paints, declared frame strokes left out, keeps its four edges within 4 px of where they began and its centre more than 50 px above or below y 510, with its span and largest signed offset in px. A declared stage cut, a frame drawing another scene, a frame without a lit scene box and a gap in the samples SHALL each end a run.

#### Scenario: A still stage that sits low

- **WHEN** a scene's lit box stands still with its centre at y 590 for 2.5 s
- **THEN** the frame audit reports one vertical run for that scene with its span and an offset of 80 px

#### Scenario: A row that grows sideways

- **WHEN** a row of names at y 600 grows sideways, one name after another, for 3 s
- **THEN** the frame audit reports no vertical run

#### Scenario: A stage that grows downward

- **WHEN** a scene's box stands more than 50 px below y 510 for 3 s while its bottom edge grows by 40 px
- **THEN** the frame audit reports no vertical run

#### Scenario: A stage cut ends the run

- **WHEN** a box centre stands at y 590 for 1.5 s, a stage cut the composition declares for the scene falls, and it stands there 1.5 s more
- **THEN** the frame audit reports no vertical run

#### Scenario: Credits sit low

- **WHEN** the credits, drawn with no scene, stand still with their box centre at y 584 for 3 s
- **THEN** the frame audit reports no vertical run

### Requirement: The picture gate refuses a picture whose content stands off centre

`check-picture` SHALL refuse each run of the mass audit and each vertical run of the frame audit, naming its scene, span and offset. The mass audit's summary of each scene SHALL refuse nothing.

#### Scenario: A mass run refuses

- **WHEN** the mass audit reports a run and no audit reports another gated finding
- **THEN** `check-picture` writes a refused record that names the run and exits with a refusal

#### Scenario: A vertical run refuses

- **WHEN** the frame audit reports a vertical run
- **THEN** `check-picture` writes a refused record that names it and exits with a refusal

#### Scenario: A summary alone

- **WHEN** a scene's mass stands 60 px left at its median, no run is reported and no other finding exists
- **THEN** `check-picture` passes and its record binds the mass report that states the median
