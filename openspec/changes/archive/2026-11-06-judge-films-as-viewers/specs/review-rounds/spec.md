## ADDED Requirements

### Requirement: A film declares its review levels

A film MAY declare `[review.levels]` in `content/film.toml`: the three levels `信`, `达` and `雅`, each with what it asks of the whole film and the review dimensions it holds. The declaration SHALL be refused unless every declared dimension stands in exactly one level and every dimension a level names is declared.

#### Scenario: A dimension in no level

- **WHEN** the levels hold four of the film's five declared dimensions
- **THEN** the declaration is refused and names the dimension without a level

#### Scenario: An unknown dimension

- **WHEN** a level names a dimension the film does not declare
- **THEN** the declaration is refused and names that dimension

### Requirement: The prompts state the levels

For a film that declares levels, `review.round prompts` SHALL fill `{levels}` with each level, what it asks and, under it, each of its dimensions with what that dimension asks, and SHALL refuse a template that does not cite `{levels}` and `{sentences}`. A film without levels SHALL keep its prompts.

#### Scenario: A film with levels

- **WHEN** the prompts are written for a film whose levels hold its five dimensions
- **THEN** each prompt states 信, 达 and 雅 with what each asks and each dimension under its level

#### Scenario: A template without the field

- **WHEN** a film declares levels and its template does not cite `{levels}`
- **THEN** the command refuses and writes no prompt

### Requirement: A review passes level by level

For a film that declares levels, each review SHALL give every level a verdict, pass or fail, with the findings in it, and each finding SHALL name its level. `review.round record` and the verifier SHALL refuse a review that misses a level, whose level fails, or whose level passes while a dimension it holds is below the floor or a material finding remains in it, besides today's floors.

#### Scenario: A level passed by averaging

- **WHEN** the overall score is 96 but a dimension of 雅 scores 93 and the review passes 雅
- **THEN** `review.round record` refuses and names 雅 and the dimension

#### Scenario: A level that fails

- **WHEN** a review fails 达
- **THEN** the record is refused and the verifier refuses a record that holds it

#### Scenario: A finding without its level

- **WHEN** a finding names no level
- **THEN** the record is refused and names the finding

### Requirement: The prompts name every sentence a viewer hears

`review.round prompts` SHALL write, for each edition, every sentence of every thought, split at 。？！ in Chinese and . ? ! in English with quotations kept whole, each with its id `segment.thought.sentence`, its text and its start and end in the timeline, and SHALL name the file in `{sentences}`.

#### Scenario: A thought of two sentences

- **WHEN** thought 02.3 holds two sentences
- **THEN** the file lists 02.3.1 and 02.3.2 with their texts and the times of their first and last words

#### Scenario: A quoted sentence

- **WHEN** a sentence quotes “Done. All tests pass.”
- **THEN** the quotation stays in one sentence

### Requirement: A review judges every sentence

For a film that declares levels, each review SHALL give every sentence id of its edition a verdict, `ok` or the ids of the findings that concern it. `review.round record` and the verifier SHALL refuse a review that misses a sentence, names an unknown one or names a finding the review does not hold.

#### Scenario: A sentence left out

- **WHEN** a review gives verdicts for all but sentence 05.2.1
- **THEN** `review.round record` refuses and names 05.2.1
