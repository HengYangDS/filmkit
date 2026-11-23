## MODIFIED Requirements

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
