## ADDED Requirements

### Requirement: A film's editions are the languages it declares, in its order

The film's declaration SHALL name its editions as `[editions.<code>]` tables, one or more, and the engine SHALL take the set of a film's languages and their order from those tables alone, in the order the file gives them, wherever it covers several editions. The engine SHALL refuse at load, before any work, a declaration that names no edition, or a code for which the engine holds no language declaration, naming the languages it declares.

#### Scenario: A film of one edition

- **WHEN** a declaration names `[editions.en]` alone
- **THEN** the engine loads the film and builds its one edition

#### Scenario: An edition the engine does not declare

- **WHEN** a declaration names `[editions.xq]` and the engine holds no declaration for `xq`
- **THEN** the engine refuses at load in one line that names `xq` and the languages it declares

#### Scenario: The declared order

- **WHEN** the declaration names `[editions.en]` before `[editions.zh]`
- **THEN** every command that covers both editions takes English first, and every page and record that lists them lists English first

### Requirement: The engine declares each language once and branches on none

The engine SHALL hold one declaration for each language it builds, holding every value and choice specific to it: its tags and names, its unit of speech, whether spaces delimit its words, how it marks number, the language it reads each other script in, its captions, reading checks, stemmer, lead words, register rules and player words. Every step SHALL take a language's behaviour from that declaration, and no step SHALL choose a behaviour by a language's code, name, tag or script.

#### Scenario: Languages declared with others' values

- **WHEN** the engine's tests declare `xa` with Chinese's values and `xb` with English's, and a film whose one edition is each
- **THEN** the `xa` edition is captioned, measured, matched, checked and worded as Chinese's is and the `xb` edition as English's, under their own codes and tags

#### Scenario: A declaration that names an unknown kind

- **WHEN** a language declaration names a caption phrasing that the engine does not hold
- **THEN** the engine refuses it when it loads, naming the language and the kind

### Requirement: Script and punctuation classes are defined once

The engine SHALL define each class of script characters and each set of punctuation once, and every Python and Node step SHALL take its class or set from that definition.

#### Scenario: One class of Han characters

- **WHEN** a character of CJK Extension A stands in a Chinese thought
- **THEN** the flow, the recognition, the measurement, the spoken units, the pronunciation check, the register check and the frame audit each count it as a Han character

#### Scenario: One set of closing marks

- **WHEN** a wrapped label's line opens on 】 or on …
- **THEN** both of the frame audit's typography checks read it as opening on closing punctuation

### Requirement: Each edition's files stand in the folder of its code

Each edition's script, cast and pronunciation, and its readings where the film records any, SHALL stand in `content/<code>/`; its reference recording SHALL stand at `assets/audio/<code>/narration-reference.wav` and its cover at `assets/cover/<slug>-cover-<code>.png`. The engine SHALL derive each place from the edition's code and SHALL read no folder or cover that a film declares.

#### Scenario: An edition's places

- **WHEN** the engine builds the Chinese edition of a film whose file prefix is `sample-reel`
- **THEN** it reads `content/zh/film-script.json`, `content/zh/voice-reference.json`, `content/zh/pronunciation.json` and the reference recording `assets/audio/zh/narration-reference.wav`, and packages the cover `assets/cover/sample-reel-cover-zh.png`

#### Scenario: Shared files stay shared

- **WHEN** the film's concept contract, entry page, source manifest and review prompt stand in `content/`
- **THEN** every edition reads them from there

### Requirement: A declaration names no place that the engine derives

A declaration that names `editions.<code>.sources`, `editions.<code>.cover` or `review.readings` SHALL be refused at load, each in one line that says what to do instead, beside the declaration's other problems.

#### Scenario: A declared sources folder

- **WHEN** the declaration states `sources = "content"` for its Chinese edition
- **THEN** the engine refuses at load in one line that names `editions.zh.sources` and says that the edition's files stand in `content/zh/`

#### Scenario: A withdrawn key beside another problem

- **WHEN** the declaration names `review.readings` and gives a malformed file prefix
- **THEN** one refusal names both, `review.readings` with the folder where each edition's readings stand

### Requirement: A cast states only what the engine does not derive

An edition's cast SHALL NOT declare `narration_language`, `language`, `reference_language`, `provider`, `reference_audio`, `reference_text_sha256` or `performance_recording`, which the engine derives from the edition, its layout, its transcript or its one provider. The engine SHALL refuse a cast that declares any of them at load, in one line that names the cast and the key and says what to do instead.

#### Scenario: A cast that states its language

- **WHEN** the English cast declares `"language": "English"`
- **THEN** the engine refuses in one line that names `content/en/voice-reference.json` and `language` and says to remove it

#### Scenario: Derived evidence

- **WHEN** the Chinese edition's recordings are selected
- **THEN** its narration receipt and alignment are read from `build/evidence/editions/zh/ear-first/`

### Requirement: A cast states none of the engine's pins and keeps its reference's history in its derivation

An edition's cast SHALL NOT declare `model`, `revision` or `reference_mode`, which restate the engine's pins, nor `scope`, whose history of the reference recording belongs in the cast's `derivation`, which the engine keeps unread. The engine SHALL refuse each at load in one line that names the cast and the key and says what to do instead.

#### Scenario: A cast that states the engine's pins

- **WHEN** the Chinese cast declares `model`, `revision` or `reference_mode`
- **THEN** the engine refuses at load, naming the cast and each key, and every request takes the engine's pinned model, revision and mode

#### Scenario: A cast that records its reference's history in scope

- **WHEN** the English cast declares `scope` with the history of its reference recording
- **THEN** the engine refuses at load in one line that names the cast and `scope` and says to move its text into the cast's `derivation` as `derivation.scope`

### Requirement: No copy of a script's narration is kept beside it

The engine SHALL neither write nor read a narration text kept beside an edition's script; every step that needs the narration SHALL read it from the script. A film that still keeps `content/<code>/narration.md` SHALL be refused at load and told to remove it.

#### Scenario: A script edited

- **WHEN** `script_edits` applies an edit to the Chinese script
- **THEN** it writes the script and the cast and no other file of the edition

#### Scenario: A narration verified

- **WHEN** the verifier binds an edition's narration
- **THEN** it reads the script's texts and compares no file of narration text with them

### Requirement: A take is bound to its reference recording by its content

Every step that binds a take to its edition's reference recording, or opens that recording for a take, SHALL take the recording at the edition's place and compare its SHA-256, its transcript and its treatment with those the take recorded, and SHALL NOT open or compare the path the take recorded.

#### Scenario: A reference moved with its bytes

- **WHEN** the Chinese reference recording moves from `assets/audio/narration-reference-clear.wav` to `assets/audio/zh/narration-reference.wav` with the same bytes
- **THEN** every kept Chinese take is still selected, and an audition of a kept take generates its candidates from the moved recording

#### Scenario: A reference with other bytes

- **WHEN** the recording at the edition's place holds other bytes than a take recorded
- **THEN** the selection refuses the take, naming it and the reference

### Requirement: An edition's text holds only the scripts its language reads

Narration SHALL refuse, before any speech model loads, an edition whose text holds a character of a script that its language neither writes nor reads as another language's, or whose reference transcript holds none of its language's own script.

#### Scenario: A text in a script its language does not write

- **WHEN** the English script's text holds a Han character
- **THEN** narration refuses before any speech model loads, naming the segment and the character's script

#### Scenario: English words in a Chinese text

- **WHEN** the Chinese script's text holds the Latin-script word Agent
- **THEN** narration accepts it, since Chinese reads Latin script as English

#### Scenario: A reference transcript in another script

- **WHEN** the Chinese cast's reference transcript holds no Han character
- **THEN** narration refuses before any speech model loads, naming the cast

### Requirement: The loader refuses every withdrawn key wherever a source stands

The engine SHALL read, as it loads the declaration, each edition's script, cast and pronunciation where the declaration still names them and at their derived places where it names none, and SHALL refuse each key that the engine's one table of withdrawn keys names in any of them, all in one refusal beside the declaration's other problems and each in one line that says what to write instead. No later step SHALL refuse a fact that the loader refuses.

#### Scenario: A withdrawn key in a script not yet moved

- **WHEN** the declaration still names `content` as the Chinese edition's folder and `content/film-script.json` declares `duration`
- **THEN** the refusal names `content/film-script.json` and `duration` with what to do instead, beside `editions.zh.sources`

### Requirement: The loader names each misplaced, missing or retired file

The loader SHALL refuse each edition's file at an old place, with its destination and not as missing; each reference recording missing at its place; each file this release removes; an edition without its own pronunciation and a declaration without `[pronunciation]`; and each source it cannot read.

#### Scenario: A film that has not moved

- **WHEN** the declaration states `sources = "content"` for its Chinese edition, the Chinese script and cast stand in `content/`, the Chinese reference recording in `assets/audio/` and the Chinese cover without a code
- **THEN** one refusal at load names `editions.zh.sources` and each of those files with its destination

#### Scenario: A script at its old place

- **WHEN** the Chinese script stands at `content/film-script.json` and not at `content/zh/film-script.json`
- **THEN** the refusal names it with its destination, and not as missing

#### Scenario: A contract key removed without the split

- **WHEN** both scripts no longer declare `pronunciation_contract`, `content/voice-performance.json` still holds both languages and no edition holds `pronunciation.json`
- **THEN** the refusal names the common contract to split, each edition without its pronunciation and the declaration without `[pronunciation]`

#### Scenario: A reference the cast no longer names

- **WHEN** the Chinese cast no longer declares `reference_audio` and `assets/audio/zh/narration-reference.wav` does not exist
- **THEN** the refusal names the missing recording and its place

### Requirement: The loader names a cast's derivation that cites the identity recording elsewhere

The loader SHALL refuse each recording that a cast's derivation cites outside `assets/audio/narrator-identity.wav`, with that destination, and each cast without a derivation that names it where the film holds one.

#### Scenario: The identity recording at its old place

- **WHEN** the Chinese cast's derivation cites `assets/audio/narration-reference.wav` as the recording every reference derives from, and the English cast's derivation names none
- **THEN** the refusal names it with its destination `assets/audio/narrator-identity.wav`
- **AND** the same refusal names the English cast as without a derivation that names it

### Requirement: The loader refuses a prompt's former fields and an entry page that breaks its rule

The loader SHALL refuse each line of the review prompt that names an edition's file by path, `{other}` or `{other_language}`, or groups the declared codes in braces, and an entry page that the entry page's rule refuses.

#### Scenario: A prompt of the former fields

- **WHEN** the review prompt names `ROOT/content/en/film-script.json` and `{{zh,en}}` in one line and cites `{other_language}` in another
- **THEN** the refusal names each line with its number and the field to use instead

#### Scenario: An entry page with a root language

- **WHEN** the entry page opens with `<html lang="zh-CN">`
- **THEN** the refusal names the page's root language with `mul`

### Requirement: A segment names its chapter by its id alone

A segment SHALL name its chapter by `chapter` and SHALL NOT declare `chapter_index` or `chapter_title`. The engine SHALL derive both from the script's chapters, write them into each timeline segment, and refuse at load a segment that declares either, saying what to do instead.

#### Scenario: A segment's chapter derived

- **WHEN** a segment names `"chapter": "build"`, the second of the script's chapters, and declares no `chapter_index` or `chapter_title`
- **THEN** its timeline segment holds `chapter_index` 1 and the chapter's title, and the picture and the documents read them there

#### Scenario: A segment that states its chapter's title

- **WHEN** a segment declares `chapter_title`
- **THEN** the engine refuses at load in one line that names the script, the segment and the key and says to remove it, since its `chapter` names the chapter

### Requirement: A script's pause policy holds no prose that no step reads

A script's `voice_performance` SHALL NOT declare `performance_intent`, `energy_curve`, `pacing_profile` or `provider_notes`. The engine SHALL refuse each at load, saying to remove it and to move any words that record how the voice, its reference or its takes were made or approved into the edition's cast `derivation`.

#### Scenario: Prose of the pause policy

- **WHEN** a script's `voice_performance` declares `pacing_profile`
- **THEN** the engine refuses when it loads with one line that names the script and the key and says to remove it and to move any words that record an approval into the cast's `derivation`

## MODIFIED Requirements

### Requirement: A film declares its parameters

A film SHALL declare, in one declaration, its file prefix, author, delivery folder, entry page, source manifest, its editions with each one's summary and caption terms, its picture's fonts, the pronunciation provenance its editions share, and its review prompt, floors and scored dimensions. The engine SHALL refuse an invalid or incomplete declaration before any work, naming each failing field with any key an earlier release renamed or withdrew; a cover may be absent until the engine paints it.

#### Scenario: An invalid declaration refuses before work

- **WHEN** the declaration names no edition, names a font or another file that is missing other than a cover, gives a malformed file prefix or a review floor outside 0 to 100
- **THEN** the engine refuses when it loads, before any synthesis, and names each failing field

#### Scenario: Two problems of different kinds

- **WHEN** the declaration still names its delivery folder by the key an earlier release used and gives a malformed file prefix
- **THEN** one refusal names the renamed key and the file prefix, and the folder the renamed key carries is not reported as missing

#### Scenario: Missing files and a player page together

- **WHEN** a declaration whose fields load leaves an edition's script missing from its folder, and an edition's folder still holds a player page
- **THEN** one refusal names both

#### Scenario: The declared fonts are staged in their declared order

- **WHEN** the engine stages a film's picture
- **THEN** the stage holds each declared font, and no other font, below `fonts/` in the declared order

#### Scenario: The listening plan takes the film's own readings

- **WHEN** the listening plan is derived for an edition whose folder holds its readings
- **THEN** each English heteronym occurrence takes the part of speech the edition's readings record for it
- **AND** an occurrence the readings record no part of speech for, or a recorded one that names no current occurrence, refuses the plan

### Requirement: Each script declares its edition

Each edition's script SHALL declare the edition's title and chapters, and SHALL NOT declare `language`, at its top or in a segment, `pronunciation_contract`, `duration`, `credits_duration`, `author` or `fps`, which the code, the folder, the narration, the declaration and the engine state. The engine SHALL take the author from the declaration, render 60 fps, and refuse before any work scripts that disagree on the chapter count or declare any of those keys. The editions MAY differ in length.

#### Scenario: Scripts that disagree refuse before work

- **WHEN** the editions' scripts declare different chapter counts, or a script declares `author` or `fps`
- **THEN** the engine refuses when it loads and names the value or the key, the key with what to do instead

#### Scenario: A script that declares a duration

- **WHEN** a script declares `duration`
- **THEN** the engine refuses when it loads with one line that names the script and the key and says to remove it, since an edition lasts as long as its narration

#### Scenario: A script that declares the credits

- **WHEN** a script declares `credits_duration`
- **THEN** the engine refuses when it loads with one line that names the script and the key and says to state the credits in the film's declaration instead

#### Scenario: Editions of different lengths

- **WHEN** the Chinese edition's narration gives a runtime of 1636 s and the English edition's 1476 s
- **THEN** the engine refuses neither edition for the difference

#### Scenario: A script that states its language or its contract

- **WHEN** a script declares `language`, at its top or in a segment, or `pronunciation_contract`
- **THEN** the engine refuses when it loads with one line that names the script and the key and says to remove it, since the edition's code and folder state them

### Requirement: A film paints its covers from its picture

The engine SHALL paint each edition's cover from the edition's staged picture and compare it with the tracked cover at `assets/cover/<slug>-cover-<code>.png`. A film MAY be without its covers before it paints them; packaging SHALL refuse an edition whose cover is missing, naming the cover's path. A painted cover with no tracked cover to compare SHALL be written and reported as uncompared, and SHALL NOT pass the cover check.

#### Scenario: A new film narrates before it paints its covers

- **WHEN** a film's covers do not exist yet
- **THEN** the engine loads the declaration, narrates and stages the picture
- **AND** packaging refuses each edition whose cover is missing and names the cover's path

#### Scenario: A first cover is painted with nothing to compare

- **WHEN** the cover check paints an edition's cover and the tracked cover does not exist
- **THEN** it writes the painted cover and reports that no tracked cover was compared
- **AND** it fails until the painted cover is tracked and identical to a new painting

### Requirement: The film's declaration states the credits' length once

The film's declaration SHALL state `credits_duration`, the length of the credits in whole seconds, once for every edition, and the engine SHALL take the credits' length from it alone. A declaration that omits it, or states no whole number of seconds, SHALL be refused with the field named.

#### Scenario: A declaration without the credits

- **WHEN** `content/film.toml` states no `credits_duration`
- **THEN** the engine refuses the declaration, naming `credits_duration`

#### Scenario: Both editions take the declared credits

- **WHEN** the declaration states `credits_duration = 3`
- **THEN** each edition's assembly lays out its credits from 3 s
