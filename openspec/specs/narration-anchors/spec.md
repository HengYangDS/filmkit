# narration-anchors Specification

## Purpose

Key every picture change to words of the narration by naming them in the script, once: a segment marks
anchors in its own thoughts, the timeline gives each anchor the times of its words, and the picture reads an
anchor by its id instead of quoting the narration, so an approved change of the words moves the picture with
them and never strands it.

## Requirements

### Requirement: A segment may mark anchors in its thoughts

A segment of an edition's script MAY hold `anchored_groups`: its utterance groups with anchors marked in them, each anchor written as its id in braces before its words and the id after a slash in braces after them, as `{order}有先后{/order}`. Anchors MAY nest and MAY cross, and two anchors MAY mark the same words under different ids. A segment that holds no `anchored_groups` SHALL be read as before.

#### Scenario: Anchors that cross

- **WHEN** a thought holds `{a}依据{b}有{/a}先后{/b}`
- **THEN** the script is accepted, and `a` holds 依据有 and `b` holds 有先后

#### Scenario: Two ids on the same words

- **WHEN** a thought holds `{law}{first-rank}法律{/first-rank}{/law}`
- **THEN** the script is accepted, and `law` and `first-rank` both hold 法律

#### Scenario: A script without anchors

- **WHEN** no segment of a script holds `anchored_groups`
- **THEN** its scripts, timelines, records and pictures are those the engine wrote before anchors existed, and narration's check of what the picture reads is the one step it adds

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

### Requirement: Script edits work on the anchored thoughts

`filmkit.narration.script_edits` SHALL apply each edit to a segment's `anchored_groups` when it holds them and fill its `utterance_groups`, text, spoken text and the narration mirror from them. Retakes SHALL follow the plain thoughts, and an edit that changes only marks SHALL be written. Nothing SHALL be written unless every edit of every edition applies. The report SHALL name, each kind apart, every anchor removed, whose words changed, moved, moved by rank, or moved to another thought.

#### Scenario: A refused edit among several

- **WHEN** an edits file holds three replacements and the third is refused
- **THEN** no script, cast or mirror is written

#### Scenario: An edit of marks alone

- **WHEN** an edits file adds an anchor to a thought that holds a retake
- **THEN** the script is written with the new anchor, and the retake stays bound to its thought

### Requirement: A replacement or a split keeps an anchor on its words or refuses

A replacement SHALL find its phrase in the thought's text without marks. An anchor whose words it does not touch SHALL keep them; one whose words are the phrase or hold it SHALL keep the new words when they hold a unit. A replacement whose phrase holds an anchor's boundary and reaches beyond it SHALL be refused, naming the anchor and its words, unless its new text restates the anchor's marks. A split whose seam falls inside an anchor SHALL be refused.

#### Scenario: A rewording outside an anchor

- **WHEN** a replacement changes 最先是 in a thought that marks `{law}法律{/law}` after it
- **THEN** `law` still holds 法律, and the report names no anchor

#### Scenario: A rewording of an anchor's words

- **WHEN** a replacement changes 轻量档 to 低风险档 in `{tier}轻量档{/tier}`
- **THEN** `tier` holds 低风险档, and the report names `tier` with its words before and after

#### Scenario: A rewording inside an anchor

- **WHEN** a replacement changes 轻量 to 低风险 in `{tier}轻量档{/tier}`
- **THEN** `tier` holds 低风险档

#### Scenario: A rewording that reaches beyond an anchor

- **WHEN** a replacement's phrase holds 如果 and `{reversible}后果是否可逆{/reversible}` after it, and its new text holds no `{reversible}` mark
- **THEN** script_edits refuses, names `reversible` and its words, and writes no file

#### Scenario: A rewording that restates the anchor

- **WHEN** the same replacement's new text is `或者{reversible}后果{/reversible}`
- **THEN** the edit applies and `reversible` holds 后果

#### Scenario: A split inside an anchor

- **WHEN** a split's seam falls between 有 and 先 in `{order}有先后{/order}`
- **THEN** script_edits refuses and names `order`

### Requirement: A rewrite moves each anchor to the words it still says

A rewrite, which replaces a segment's thoughts whole, SHALL move each anchor whose words, by their units, occur in the new thoughts exactly once, or as often as in the old ones, to that occurrence or to the one of the same rank; where spaces delimit the language's words, an occurrence SHALL begin and end at word boundaries. It SHALL be refused for every other anchor, naming each with its words, unless the new thoughts restate its marks, and for new thoughts that do not each say a spoken unit.

#### Scenario: A segment rewritten whole

- **WHEN** a rewrite gives a segment new thoughts in which the words of `law` occur once and the words of `apart` do not occur, and no new thought restates `apart`
- **THEN** script_edits refuses, names `apart` and its words, and writes no file; with `apart` restated in the new thoughts, the rewrite applies and the report names `law` as moved

#### Scenario: Words said twice before and twice after a rewrite

- **WHEN** an anchor marks the second of two occurrences of 依据 and the rewritten segment still says 依据 twice
- **THEN** the anchor moves to the second occurrence in the new thoughts, and the report names it among the moves by rank and, when that occurrence is in another thought, among the moves to another thought

#### Scenario: New thoughts that say nothing

- **WHEN** a rewrite's thoughts are not a nonempty list of strings, or one of them is empty or says no spoken unit, such as `。`
- **THEN** script_edits refuses, naming the segment or the thought, and writes no file

#### Scenario: Words said once before and twice after a rewrite

- **WHEN** an anchor's words occur once in the old thoughts and twice in the new ones, which do not restate it
- **THEN** script_edits refuses, names the anchor and both new occurrences, and writes no file

#### Scenario: English words inside a longer word

- **WHEN** an English anchor marks `last night` and the new thoughts say `last night's` and no other `last night`
- **THEN** the anchor is not moved there, and script_edits refuses and names it

### Requirement: Script edits mark and unmark words

An `anchor` edit SHALL name a thought, a span of units of the thought's text, the id, and the words it expects there. It SHALL place the open mark immediately before the span's first unit and the close mark immediately after its last, and SHALL be refused when the span's units differ from those of the expected words or the id is already marked in the segment. An `unanchor` edit SHALL remove an id's marks from a segment and SHALL be refused when the segment marks no such id.

#### Scenario: Words that are not where the edit says

- **WHEN** an `anchor` edit names a span whose units are not those of its expected words
- **THEN** script_edits refuses and names the thought, the span and both sets of words

#### Scenario: A span with marks inside it

- **WHEN** an `anchor` edit marks the units of 工作计划临时约定 in a thought that says 工作计划、临时约定，再往下
- **THEN** the thought holds `{plans}工作计划、临时约定{/plans}，再往下`

#### Scenario: The first anchor of a segment

- **WHEN** an `anchor` edit marks 有先后 in a segment that holds no `anchored_groups`
- **THEN** the segment gains `anchored_groups` equal to its utterance groups with that one anchor marked, and its `utterance_groups`, text and spoken text keep their bytes

### Requirement: The anchors of both editions are reported

`python -m filmkit.narration.anchors` SHALL print, for each edition, each segment's anchors with their thought, words and units and, where the edition's timeline holds them, their times, and with `--json` the same as one JSON document; it SHALL name as stale, and not give, times of other marks than the script's; and it SHALL name each id that one edition marks in a segment and some other edition does not, refusing nothing for it.

#### Scenario: An anchor in one edition only

- **WHEN** the Chinese script marks `fails` in segment 26 and the English script does not
- **THEN** the report lists `fails` under the Chinese edition, names it among the ids of one edition, and the command exits 0

### Requirement: The engine derives a timeline from a script for its checks

The engine SHALL derive, from an edition's script alone, a timeline for the checks that draw the picture before narration: the script's fields; for each segment one word per Han character and per run of Latin letters and digits of its text, each 0.2 s long, with 0.5 s between thoughts and 1.0 s before each segment; its anchors as `assemble` resolves them; and no captions. `filmkit.api.derived_timeline(code)` SHALL give it, so that a film's own tests draw the same timeline.

#### Scenario: The same script twice

- **WHEN** the derived timeline of one script is asked twice
- **THEN** both answers are equal, and each anchor's times are those of its words in it

### Requirement: Narration refuses a script that does not mark what its picture reads

Before any speech model loads, after the readings check and in a dry run too, narration SHALL draw the film's composition for each edition over that edition's derived timeline, and SHALL refuse each id that the composition reads from a segment's anchors and that the edition's script does not mark in that segment, naming every such id with its segment and edition. An id SHALL be required only of an edition whose picture reads it. A film without a composition SHALL not be asked.

#### Scenario: An anchor the English picture reads and the English script lacks

- **WHEN** the composition reads `order` in segment 03 of both editions and only the Chinese script marks it
- **THEN** narration refuses before any model loads and names `order`, segment 03 and the English edition

#### Scenario: An anchor that one edition's picture reads

- **WHEN** the composition reads `fails` in segment 26 only when it draws the Chinese edition, and only the Chinese script marks it
- **THEN** the check passes for both editions

### Requirement: The check before narration names what it could not judge

A scene that throws while the check before narration draws it SHALL be named as not judged with its error and the ids it read before it threw, and a composition that does not load SHALL be named as not judged for its whole edition with its error's one line, whether or not the film marks anchors; neither SHALL stop the narration, and the check's answer SHALL then say not judged, not pass. A check whose tool or packages are missing SHALL refuse, naming the reason.

#### Scenario: A scene that throws for another reason

- **WHEN** a scene throws `Missing spoken cue` while the check draws it
- **THEN** the check names the scene, the error and the ids it read before, refuses nothing for its error, and the narration goes on; an unmarked id that the scene read before it threw is refused

#### Scenario: A composition that does not load

- **WHEN** `picture/film.js` throws as it loads, in a film whose scripts mark anchors
- **THEN** the check names the edition as not judged with the error's one line, its answer says not judged, and the narration goes on

#### Scenario: Packages that are missing

- **WHEN** the film's Node packages are missing
- **THEN** narration refuses before any model loads and names the reason

### Requirement: The picture gate refuses an anchor that the edition does not mark

`check-picture` SHALL record every id that the composition reads from a segment's anchors while its audits draw the edition's timeline and that the edition does not mark there, with its segment and edition, giving the composition a stand-in so that the scene goes on. It SHALL refuse by those ids while one remains, also when an audit fails for another reason, and `render-picture` SHALL then refuse the edition.

#### Scenario: Two unmarked ids in one scene

- **WHEN** a scene reads `order` and `law` and the edition marks neither
- **THEN** the gate names both with their segment and edition and refuses

#### Scenario: An audit that fails for another reason

- **WHEN** the frame audit exits with an error and the composition read an unmarked id
- **THEN** the refusal names the unmarked id with its segment and edition beside the audit's error
