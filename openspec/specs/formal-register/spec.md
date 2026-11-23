# formal-register Specification

## Purpose

Hold every film's words to the formal register its owner approved: the engine carries the standard once, refuses
before narration and before a render the forms a word can show, and gives the reviewers the rest.

## Requirements

### Requirement: The engine carries the formal register as approved

The engine SHALL carry the films' formal register, its scope, its order of 信, 达 and 雅 and its rules R1 to R6, as
the films' owner approved it on 20 November 2026, in one tracked document; the register check's forms and the
reviewers' prompt SHALL take the rules from that document alone.

#### Scenario: The standard reaches the reviewers

- **WHEN** a review round is prepared
- **THEN** each prompt carries the rules R1 to R6 from the engine's document and the round's register report

#### Scenario: The checked part and the judged part

- **WHEN** the register check runs
- **THEN** it checks as errors the forms the document lists for R1 and R3, their inflections, English contractions
  and R5's marks, and as warnings R2, R4 and the forms the engine adds to R1's and R3's Chinese classes, and leaves
  the rest to the reviewers

#### Scenario: A form the engine would refuse beyond the document

- **WHEN** the style's rule for R1's pronouns or for R3's Chinese words refuses a form that the document does not
  list and that is no inflection of a listed form
- **THEN** the engine's own tests fail and name the form

#### Scenario: A class the document names

- **WHEN** the style refuses an English contraction or one of R5's marks
- **THEN** its rule file quotes the sentence of the document that names the class, and the engine's own tests fail
  for a rule file whose quotation the document does not hold

#### Scenario: A form the engine adds

- **WHEN** a thought holds 到底, 得由, 管用 or 各位, which the document does not list
- **THEN** the register check records a warning with its place and refuses nothing

#### Scenario: A listed form dropped from the style

- **WHEN** the style no longer refuses a form that the document lists for R1 or R3
- **THEN** the engine's own tests fail and name the form

### Requirement: A film's words hold no form its register refuses

Before a film narrates and before it renders, the engine SHALL check the edition's words a viewer meets (titles,
thoughts, caption terms, release prose, the player summary and the entry page) against its register style, and SHALL
refuse while an error-level form stands that the film does not excuse, naming each place and form at once. Every
occurrence of a form the document lists SHALL be refused unless the film excuses it at its place or it stands inside
a fixed idiom that the style states.

#### Scenario: An address of the audience

- **WHEN** a Chinese thought holds 你们 or an English thought holds "you"
- **THEN** the register check refuses and names the thought and the form, and narration does not start

#### Scenario: A listed form inside a standard word

- **WHEN** a thought holds 迷你, 跑道, 统一下发 or 酒吧, and the film declares nothing
- **THEN** the register check refuses the form, names its place, and says that a film keeps a standard word by
  declaring the place and the word

#### Scenario: A listed form in plain speech

- **WHEN** a thought says 通过大家的努力, 不过其实没那么复杂, 先规划一下, 测试跑通了, 喝点水吧, 一起跑测试 or 其实效果一般
- **THEN** the register check refuses the form

#### Scenario: An English form joined to another word

- **WHEN** an English thought says "a thank-you note", "you-all" or "your-team"
- **THEN** the register check refuses the form, and "young" and "you2" hold no occurrence of it

#### Scenario: A character the viewer does not see

- **WHEN** a soft hyphen, a zero-width character, a variation selector or a combining grapheme joiner stands inside
  其实 or 大家
- **THEN** the register check refuses the form as if the character were not there

#### Scenario: R5's marks

- **WHEN** a thought holds ！, !, ——, an em dash with or without spaces, a spaced en dash, …, ... or ……
- **THEN** the register check refuses it, and an unspaced en dash in a compound or a range passes

#### Scenario: A form the standard allows in some uses

- **WHEN** a thought holds 我们 or more than one question
- **THEN** the register check records a warning with its place and refuses nothing

### Requirement: A film excuses a form at one place

A film MAY declare in `[[register.exceptions]]` a place, an error-level form, the text within which the form stands
there (`within`, which holds a letter or a digit beyond the form) and a reason; the engine SHALL not refuse the form's
occurrences that lie inside that text at that place, SHALL refuse every other occurrence, SHALL refuse an exception
whose text its place does not hold or that excuses no refusal, and SHALL keep every warning in its report whatever the
film declares.

#### Scenario: A standard word

- **WHEN** a title reads 示例跑道 and the film declares that title, 跑, the text 跑道 and its reason
- **THEN** the register check reports nothing for it and lists the exception with its text and its reason

#### Scenario: A quoted phrase

- **WHEN** a thought quotes 「先搞清楚」 as an example and the film declares that thought, 搞, the text 先搞清楚 and its
  reason
- **THEN** the register check reports nothing for it and lists the exception with its reason

#### Scenario: The same form used once more

- **WHEN** that thought also uses 搞 outside the quotation
- **THEN** the register check refuses that occurrence and no other

#### Scenario: An exception that excuses nothing

- **WHEN** a declared exception's place does not hold its text
- **THEN** the register check refuses and names the stale exception

#### Scenario: An exception for a fixed idiom the style states

- **WHEN** a title reads 这个示例名副其实 and the film declares that title, 其实, the text 名副其实 and its reason
- **THEN** the register check refuses the exception as one that excuses no refusal, naming its place and its text

#### Scenario: A text that is the form itself

- **WHEN** a film declares an exception whose text does not hold its form, or adds only marks or spaces to it (吧。
  for 吧), or declares two exceptions at one place of which one text holds the other
- **THEN** the film's declaration is refused before any word is read

#### Scenario: A warning a film would keep out of the report

- **WHEN** a film declares an exception for 我们 at a thought that holds it
- **THEN** the register check refuses the exception as one that excuses no refusal, and the warning stays in the report

### Requirement: The register checker is the pinned one

The register check SHALL run the Vale version the engine's release record states and SHALL refuse, before it reads
any word, an executable that reports another version.

#### Scenario: Another Vale first on the path

- **WHEN** the Vale the check would run reports a version other than the record's
- **THEN** the check refuses and names both versions

#### Scenario: A checker whose run cannot be read

- **WHEN** the checker prints no JSON object, names a line that no place holds or a span where its place does not
  hold the form, outlives its deadline, cannot be run, or the engine's own Vale configuration or rule files are not
  where it installed them
- **THEN** the check refuses in one line that names what happened, and neither passes nor ends in a traceback

### Requirement: Each place is read as the viewer meets it

The register check SHALL read each text run of the film's entry page as a paragraph of its own under the one place
`entry page`, with the words of its `alt`, `title` and `aria-label` attributes, and SHALL name a caption term's place
with its term, so that a refusal names one place and two elements never join into a form or hide one.

#### Scenario: A particle at the end of a heading

- **WHEN** an entry page's heading ends in 吧 and the next element begins with a Chinese character
- **THEN** the register check refuses the particle and names the entry page

#### Scenario: Two list items

- **WHEN** one list item ends in 一 and the next begins with 下
- **THEN** the register check reports no 一下

#### Scenario: Two caption terms with a form

- **WHEN** two caption terms of an edition each hold "you"
- **THEN** the refusal names each term's own place

### Requirement: A run of the entry page ends only at a block

A run of the entry page SHALL end only where a block element begins or ends; every other element SHALL be read as
inline, and a line break SHALL be read as a space inside its run. A page that cannot be read as text SHALL be refused
in one line.

#### Scenario: A form parted by an element the engine does not know

- **WHEN** an entry page writes 其 and 实 either side of a `wbr`, an `s`, a `ruby` or a custom element
- **THEN** the register check refuses 其实 and names the entry page

#### Scenario: A line break in either spelling

- **WHEN** one line of an element ends in 一 and the next begins with 下, parted by `<br>` or by `<br/>`
- **THEN** the register check reports no 一下 in either spelling, and two questions either side of the break count
  as one run's

#### Scenario: A page that is no text

- **WHEN** the entry page's bytes are not UTF-8
- **THEN** the check refuses in one line that names the page, and the pre-render check writes a refused receipt

### Requirement: A fixed idiom keeps a listed form's characters

The register style SHALL state, beside a listed form, each fixed idiom whose characters hold the form but not the
listed word, and the register check SHALL not refuse the form inside such an idiom; it SHALL refuse every other
occurrence of the form, and the engine SHALL hold no other list of words that excuses one.

#### Scenario: A fixed idiom the style states

- **WHEN** a title reads 这个示例名副其实 and the film declares nothing
- **THEN** the register check refuses nothing for it

#### Scenario: A listed form beside a fixed idiom

- **WHEN** a thought says 其实不难，名副其实 or 名副其实，其实不难
- **THEN** the register check refuses the 其实 outside the idiom, once

#### Scenario: An idiom parted by a character the viewer does not see

- **WHEN** a zero-width space stands inside 名副其实
- **THEN** the register check reads the idiom as if the character were not there and refuses nothing for it
