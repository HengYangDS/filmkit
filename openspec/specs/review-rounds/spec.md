# review-rounds Specification

## Purpose

Prepare each independent review round of a film's two editions: set the packages of the previous build aside before the next render, and write each edition's reviewer prompt.

## Requirements

### Requirement: A first production review gets its prompts

`filmkit.review.round prompts` SHALL write each edition's prompt without a previous round, its `{previous_review}` stating that no earlier production review exists and citing no previous review. With a previous round, `{previous_review}` SHALL cite that round's review files and findings. A template that cites `{previous}` or `{findings}` SHALL be filled only from a previous round and refused without one, before any prompt is written.

#### Scenario: A film's first production review

- **WHEN** a round's prompts are written without `--previous` from a template that cites `{previous_review}`
- **THEN** each prompt states that no earlier production review exists and names no previous review file

#### Scenario: A later round

- **WHEN** the prompts are written with `--previous` naming the round before
- **THEN** `{previous_review}` cites that round's review files with their findings and asks the reviewer to verify each repair

#### Scenario: A template that cites the previous review itself

- **WHEN** a template cites `{previous}` and `{findings}` and no previous round is named
- **THEN** the command refuses, naming both fields and `{previous_review}`, and writes no prompt
- **AND** with `--previous` the same template is filled as before

### Requirement: An unreviewed build is set aside by its consumer's copies

`set-aside --unreviewed --consumer <dir>` SHALL move each edition's films, package record and rendered picture into `build/artifacts/film/superseded/<label>/<code>/` with the manifest, move and readback of a reviewed round, labelled `round-<n>` or by `--label`. Before anything moves it SHALL refuse unless `<dir>/<code>/` holds both films byte-identical, and it SHALL record that folder as their consumer.

#### Scenario: A preview the owner watched

- **WHEN** an unreviewed build whose films the preview folder holds byte-identical is set aside with that folder as its consumer
- **THEN** each edition's members move below the label's folder and are read back by their hashes, and each manifest names the edition's preview folder as the consumer

#### Scenario: A copy that differs

- **WHEN** one edition's copy in the consumer folder differs from its film
- **THEN** the set-aside refuses, naming the copy and the film, and moves nothing

### Requirement: A set-aside moves the editions and pictures it names

A set-aside, reviewed or not, SHALL move only the edition that `--language` names when it names one, and SHALL leave the rendered picture in place for each edition that `--without-picture` names, or for every edition when it names none.

#### Scenario: One edition rebuilt

- **WHEN** an unreviewed build is set aside with `--language en --without-picture en`
- **THEN** only the English films and package record move, and the English picture and the whole Chinese edition stay in place

#### Scenario: Every picture kept

- **WHEN** a reviewed round is set aside with `--without-picture` and no edition
- **THEN** each edition's films and package record move and both pictures stay

### Requirement: A round's prompts require a disposition of every previous finding

`review.round prompts` with a previous round SHALL require `--dispositions <file>`. The file gives each finding of the previous round's reviews one disposition: fixed, with the evidence that its reverification holds; declared, with the design section that keeps it; or deferred, with its owner and reason. The command SHALL refuse a finding without a disposition, a disposition for a finding the previous round does not hold, and a disposition without its evidence or reason.

#### Scenario: A note left without a disposition

- **WHEN** the previous round holds 28 findings and the dispositions file names 27
- **THEN** the command refuses and names the finding without a disposition

### Requirement: The prompts state each disposition

The prompts SHALL state the dispositions in three groups, fixed, declared and deferred, so that the reviewers re-verify each fixed finding by its reverification line and judge the others.

#### Scenario: Every finding disposed

- **WHEN** each finding has a disposition with its evidence or reason
- **THEN** the prompts state the dispositions in their three groups

### Requirement: A bound build is set aside before it is rebuilt

Assembling a soundtrack, and refreshing an edition's captions, SHALL refuse while a review round's prompts bind the edition's current films and that round has not been set aside. The refusal SHALL name the round and the set-aside command.

#### Scenario: Assembling over a reviewed build

- **WHEN** round 7's prompts bind the edition's current films and round 7 has not been set aside
- **THEN** assembly refuses before it writes anything and names round 7 and `review.round set-aside --round 7`

#### Scenario: A set-aside round

- **WHEN** the round that bound the edition's films has been set aside
- **THEN** assembly proceeds

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
