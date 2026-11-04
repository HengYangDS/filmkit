## ADDED Requirements

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

The sync audit SHALL list each caption cue of three or more words whose words all stand, in their order, in one label legible during the cue, and each such cue of which at least 80% of the words stand in labels legible during it, with the cue's start, its text and the labels. `check-picture` SHALL refuse the first kind and record the second.

#### Scenario: A cue drawn whole in one label

- **WHEN** the cue `The people watching the pipeline report this back,` shows while the label `The people watching the pipeline report this back` is legible
- **THEN** the audit lists it as a whole echo, and `check-picture` refuses and names the cue's start and text

#### Scenario: A cue drawn in two labels

- **WHEN** the cue `things can change without the view showing it:` shows while the labels `Things can change` and `Without the view showing it` are legible
- **THEN** the audit lists it as a partial echo of 100%, and `check-picture` records it without refusing

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

## MODIFIED Requirements

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
