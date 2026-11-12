## ADDED Requirements

### Requirement: The sync audit judges an English label by its inflected words in its own thought

When no exact occurrence of an English label's words starts within 8 s of its first legible frame, the sync audit SHALL look for the label's words in order by their English Snowball stems in the thought spoken at that frame, or the next one between thoughts. It SHALL judge the label by the nearest such occurrence and record the match as inflected. Other labels, and every Chinese label, SHALL be matched as before.

#### Scenario: A label over another form of its word

- **WHEN** the label "Availability" is first legible at 330.17 s, the thought spoken then says "available" at 330.36 s, and "availability" is next said at 338.60 s
- **THEN** the audit judges the label against "available" at 330.36 s, in sync within its tolerance, and records the match as inflected

#### Scenario: An exact occurrence near the label

- **WHEN** a label's exact words are said 1.2 s after it is first legible
- **THEN** the audit judges it by that occurrence, as before

#### Scenario: Words that only look alike

- **WHEN** the label "Publish" is first legible while its thought says "public" and nothing else near it
- **THEN** the audit finds no match for the label in that thought

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

## MODIFIED Requirements

### Requirement: The frame audit measures still states off centre

The frame audit SHALL report per scene each run of 2 seconds or more in which that box stands more than 50 px off while its left and right edges stay within 4 px, with its start, its end and its largest offset in px. It SHALL report as held a run whose next frame, after no stage cut, holds a wider box of the same scene that contains it, and as finished a run whose next frame shows another scene or follows a stage cut of its scene.

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

## REMOVED Requirements

### Requirement: The picture gate refuses a picture off the reviewers' balance

**Reason**: it recorded a settled still state without refusing it, and left out a held one, while the reviewers count every still state 50 px off for 2 s. "The picture gate refuses every still state off the reviewers' balance" refuses held, settled and finished states alike.

**Migration**: a film whose picture holds a still state off centre repairs it before its next render: it glides the picture as one on the word that widens it, or stands it midway between its lasting states.
