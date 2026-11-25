## MODIFIED Requirements

### Requirement: A cue's text is its typeset display copy

Each caption cue the engine writes into a timeline SHALL hold as its text its phrase as the segment's typeset text sets it, with no separate display copy, so a segment's cues join into its typeset narration. The segment's narration, thoughts and aligned words SHALL stay as the script and the aligner wrote them, and verification SHALL refuse a cue that holds a straight apostrophe or a straight double quotation mark.

#### Scenario: A contraction, a possessive and a quotation

- **WHEN** a segment reads They don't guess at the film's state. It says "Done. All tests pass."
- **THEN** its cues read They don’t guess at the film’s state. and It says “Done. All tests pass.”, at the times and with the subtitle lines they had before
- **AND** the segment's text and words are unchanged

#### Scenario: A timeline built before

- **WHEN** an English timeline's cue reads the film's data beside the display copy the film’s data
- **THEN** verification refuses it until `refresh-captions` rewrites the cue as the film’s data
