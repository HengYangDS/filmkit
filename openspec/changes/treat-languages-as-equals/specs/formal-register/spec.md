## ADDED Requirements

### Requirement: Each place is checked by the rules of the languages its words are in

The register check SHALL check each place by the rules of every language whose words it holds, as the language registry reads them in its edition: the edition's language, and the language its edition reads each other script in. A place every edition shares, as the entry page, SHALL be checked by the rules of every declared language. No rule SHALL apply to a place because of its script alone.

#### Scenario: A rule one language does not take

- **WHEN** the engine's tests declare `xb` with English's rules but without the rule for contractions, and an `xb` thought says "don't"
- **THEN** the check refuses nothing for the contraction, while an English thought that says "don't" is refused

#### Scenario: English words in a Chinese thought

- **WHEN** a Chinese thought holds the English word "don't"
- **THEN** the check refuses the contraction, since the Chinese declaration reads Latin script as English

#### Scenario: A place every edition shares

- **WHEN** the entry page holds 你们 and "you"
- **THEN** the check refuses both, naming the entry page

## MODIFIED Requirements

### Requirement: A film's words hold no form its register refuses

Before a film narrates and before it renders, the engine SHALL check the words a viewer meets (titles, thoughts,
caption terms, release prose, the player summary and the entry page) by the rules their language takes, and SHALL
refuse while an error-level form stands unexcused, naming each place and form at once. Every occurrence of a
listed form SHALL be refused where its rule's language applies, unless the film excuses it at its place or it
stands inside a fixed idiom that the style states.

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
