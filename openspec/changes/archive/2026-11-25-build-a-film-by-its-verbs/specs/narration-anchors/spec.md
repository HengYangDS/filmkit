## MODIFIED Requirements

### Requirement: The engine refuses a broken anchor before it writes anything

An id SHALL be kebab-case (lowercase ASCII letters and digits, single hyphens, a letter first), not `constructor`, and unique among its segment's anchors in its edition. An anchor SHALL open and close in one thought and hold a unit of the text. `utterance_groups` SHALL equal `anchored_groups` without its marks. Every command that reads a script's anchors SHALL refuse a script that breaks a rule before it writes anything, naming every failure at once by edition, segment, thought and id.

#### Scenario: An anchor that is never closed

- **WHEN** a Chinese thought holds `{order}有先后` and no `{/order}`
- **THEN** `assemble` refuses before it writes anything and names the Chinese edition, the segment, the thought and `order`

#### Scenario: Plain thoughts edited by hand

- **WHEN** a segment's `utterance_groups` differ from its `anchored_groups` with the marks removed
- **THEN** the refusal names the edition and the segment, says that the segment's plain thoughts are filled from its anchored ones, and names `filmkit.narration.script_edits` as the way to change its words

#### Scenario: An id that is not kebab-case

- **WHEN** a thought marks an anchor `{Order_2}` or `{order-}`
- **THEN** the refusal names the id

#### Scenario: An id that every JavaScript object inherits

- **WHEN** a thought marks an anchor `{constructor}`, a name a composition's read of which cannot be told from the object's own member
- **THEN** the refusal names the id

#### Scenario: One id twice in a segment

- **WHEN** two anchors of one segment in one edition carry the id `law`
- **THEN** the refusal names both thoughts and `law`

### Requirement: The timeline gives each anchor the times of its words

When an edition's script marks any anchor, `assemble` SHALL give every segment of its timeline `anchors`, empty where it marks none, each id in the order of its open mark: `start`, the start of the aligned word holding its first unit; `end`, the end of the word holding its last; `units`, its first unit's index among the units of the segment's text and the index after its last; `thought`, counted from 1. A timeline whose script marks none SHALL carry no `anchors`.

#### Scenario: An anchor on three characters

- **WHEN** the second thought of a segment marks `{order}有先后{/order}` and the segment's words 有, 先 and 后 start at 81.20 s, 81.36 s and 81.52 s and the last ends at 81.70 s
- **THEN** the timeline's segment gives `order` the start 81.20, the end 81.70, the units of those three characters and the thought 2

#### Scenario: A segment without marks in an edition with anchors

- **WHEN** an edition's script marks anchors in segment 03 and none in segment 04
- **THEN** the timeline's segment 04 holds an empty `anchors` object

#### Scenario: A film that marks no anchor

- **WHEN** an edition whose script marks no anchor is assembled
- **THEN** its timeline holds the same bytes as the engine before this capability wrote for the same inputs

### Requirement: A timeline of other words takes its anchors from the engine

`filmkit.api.place_anchors(timeline, code)` SHALL give a timeline that other code built of its own words the anchors its marks take from those words, as `assemble` gives them.

#### Scenario: A timeline of a test's own words

- **WHEN** a test builds a timeline of its own words for a segment that marks `{order}有先后{/order}` and runs `--place` on it
- **THEN** the timeline's segment gives `order` the start of the test's word 有 and the end of its word 后

### Requirement: A change of anchors alone keeps the soundtrack

`refresh-captions` SHALL adopt a script whose segments differ from the timeline's only in `anchored_groups` and in the caption fields it already adopts. It SHALL give each timeline segment the script's `anchored_groups`, or remove them where the script holds none, with the `anchors` they take from the timeline's words, and SHALL record a presentation revision that keeps the soundtrack, the words and the narration selection. A changed word of the text SHALL still be refused.

#### Scenario: An anchor added to a narrated edition

- **WHEN** an anchor is added to a segment of an edition whose soundtrack is assembled, `refresh-captions` runs and the edition is staged
- **THEN** the timeline's segment holds the script's `anchored_groups` and the anchor's times, the soundtrack's SHA-256 is unchanged, the receipt records the presentation revision, and `stage-picture` accepts the timeline as following its script

#### Scenario: Anchors removed from a segment

- **WHEN** a script drops a segment's `anchored_groups` and `refresh-captions` runs
- **THEN** the timeline's segment holds no `anchored_groups`, and `stage-picture` accepts the timeline

#### Scenario: A word changed with an anchor

- **WHEN** a script changes a word of a thought besides its marks
- **THEN** `refresh-captions` refuses as it refuses a changed word today

### Requirement: The engine derives a timeline from a script for its checks

The engine SHALL derive, from an edition's script alone, a timeline for the checks that draw the picture before narration: the script's fields; for each segment one word per Han character and per run of Latin letters and digits of its text, each 0.2 s long, with 0.5 s between thoughts and 1.0 s before each segment; its anchors as `assemble` resolves them; and no captions. `filmkit.api.derived_timeline(code)` SHALL give it, so that a film's own tests draw the same timeline.

#### Scenario: The same script twice

- **WHEN** the derived timeline of one script is asked twice
- **THEN** both answers are equal, and each anchor's times are those of its words in it

### Requirement: The picture gate refuses an anchor that the edition does not mark

`check-picture` SHALL record every id that the composition reads from a segment's anchors while its audits draw the edition's timeline and that the edition does not mark there, with its segment and edition, giving the composition a stand-in so that the scene goes on. It SHALL refuse by those ids while one remains, also when an audit fails for another reason, and `render-picture` SHALL then refuse the edition.

#### Scenario: Two unmarked ids in one scene

- **WHEN** a scene reads `order` and `law` and the edition marks neither
- **THEN** the gate names both with their segment and edition and refuses

#### Scenario: An audit that fails for another reason

- **WHEN** the frame audit exits with an error and the composition read an unmarked id
- **THEN** the refusal names the unmarked id with its segment and edition beside the audit's error
