## MODIFIED Requirements

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

## ADDED Requirements

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
