## MODIFIED Requirements

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

### Requirement: The anchors of both editions are reported

`python -m filmkit.narration.anchors` SHALL print, for each edition, each segment's anchors with their thought, words and units and, where the edition's timeline holds them, their times, and with `--json` the same as one JSON document; it SHALL name as stale, and not give, times of other marks than the script's; and it SHALL name each id that one edition marks in a segment and some other edition does not, refusing nothing for it.

#### Scenario: An anchor in one edition only

- **WHEN** the Chinese script marks `fails` in segment 26 and the English script does not
- **THEN** the report lists `fails` under the Chinese edition, names it among the ids of one edition, and the command exits 0
