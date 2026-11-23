## ADDED Requirements

### Requirement: The entry page leads to every edition

The film's entry page SHALL state `lang="mul"` at its root and hold one link to each declared edition's player, in the declared order, each link carrying its edition's language tag. The engine SHALL refuse a page that does not at load, naming each fault, so that no edition is packaged with it.

#### Scenario: An edition without a link

- **WHEN** a film declares Chinese, English and a third edition `xb`, and its entry page links the Chinese and the English players
- **THEN** the engine refuses at load, naming `xb`, and no viewing package is written

#### Scenario: A root language

- **WHEN** the entry page opens with `<html lang="zh-CN">`
- **THEN** the engine refuses at load, naming the root language and `mul`

#### Scenario: Links out of order or without their language

- **WHEN** the entry page links the English player before the Chinese one, or its Chinese link carries no `lang`
- **THEN** the engine refuses at load, naming each such link

#### Scenario: Every edition linked

- **WHEN** the entry page states `mul` and links every declared edition's player in the declared order, each in its own language
- **THEN** packaging writes it, each link showing its own edition's runtime

## MODIFIED Requirements

### Requirement: Every track of a delivered film carries the edition's language

The picture, narration and chapter tracks of every delivered film SHALL carry the ISO 639-2 language that the edition's language declaration states, and packaging SHALL refuse a finished film any of whose tracks carries another before it links the film into place.

#### Scenario: A Chinese film's chapter track

- **WHEN** the Chinese edition is packaged
- **THEN** its picture, narration and chapter tracks are each tagged `zho`

#### Scenario: A track in another language

- **WHEN** the chapter track of a finished Chinese film is tagged `eng`
- **THEN** packaging refuses the film and does not link it into place

### Requirement: The engine builds each edition's player from the film's words

The engine SHALL render each edition's player page itself. A film SHALL declare only its words and colours: each edition's summary and the player's palette. The engine supplies the structure, and the interface text of each language from that language's declaration. Packaging SHALL refuse a film that still supplies a player page of its own, naming the declarations that replace it.

#### Scenario: A film with a copied player

- **WHEN** an edition's folder still holds a player page
- **THEN** packaging refuses and names the summary and palette declarations

### Requirement: The player says whether each film draws its captions

The player SHALL list each delivered file by its kind, version, format and size and SHALL say of each film whether its picture draws the captions. It SHALL offer each text file, the Markdown transcript, the chapter files and the SRT and WebVTT captions, as a download labelled by its kind and purpose, so no link opens raw text in a tab, and SHALL promise no download of a film or cover. It SHALL link every other edition's player, in the film's declared order, and then the entry page.

#### Scenario: The files and the other edition

- **WHEN** the Chinese player is opened from its delivery folder
- **THEN** it names each version's film with its captions and without them, and the cover, with their sizes, offers the transcript, the chapter files and both caption files as downloads with their sizes, and links the English player and the entry page

#### Scenario: A text file

- **WHEN** a viewer selects the Markdown transcript, a chapter file or a caption file in a player opened from its delivery folder
- **THEN** the browser saves the delivered file's bytes under its name, and the page stays where it is

#### Scenario: A film of three editions

- **WHEN** the Chinese player of a film that declares Chinese, English and a third edition `xb`, in that order, is opened
- **THEN** it links the English player, then the `xb` player, then the entry page, and the readback finds those links

#### Scenario: A film of one edition

- **WHEN** the player of a film that declares one edition is opened
- **THEN** it links the entry page and no other player

### Requirement: A delivered film names its version

Packaging SHALL read the film repository's `VERSION`, a Semantic Versioning 2.0.0 version without build metadata, SHALL write it into each film's QuickTime key Information with the label that the edition's language declares, 版本号 for Chinese and Version for English, and SHALL bind it among the film's production inputs. Packaging SHALL refuse a repository without a valid `VERSION`, and the verifier a delivered film whose version differs from it.

#### Scenario: A Chinese film's version in Spotlight

- **WHEN** a Chinese edition is packaged at `VERSION` 1.3.0
- **THEN** each of its films carries the QuickTime key Information 版本号 1.3.0, which Spotlight lists as its information

#### Scenario: A version changed after packaging

- **WHEN** `VERSION` changes after an edition was packaged
- **THEN** packaging reports the version as a stale binding and the verifier refuses the edition's films

#### Scenario: No version

- **WHEN** the film repository has no `VERSION`, or it holds `1.3`
- **THEN** packaging refuses and names `VERSION`
