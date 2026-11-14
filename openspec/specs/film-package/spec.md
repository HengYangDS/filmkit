# film-package Specification

## Purpose

Package each edition's films so that their tracks, chapters and tags describe that edition.

## Requirements

### Requirement: Every track of a delivered film carries the edition's language

The picture, narration and chapter tracks of every delivered film SHALL carry the edition's ISO 639-2 language, and packaging SHALL refuse a finished film any of whose tracks carries another before it links the film into place.

#### Scenario: A Chinese film's chapter track

- **WHEN** the Chinese edition is packaged
- **THEN** its picture, narration and chapter tracks are each tagged `zho`

#### Scenario: A track in another language

- **WHEN** the chapter track of a finished Chinese film is tagged `eng`
- **THEN** packaging refuses the film and does not link it into place

### Requirement: The engine builds each edition's player from the film's words

The engine SHALL render each edition's player page itself. A film SHALL declare only its words and colours: each edition's summary and the player's palette. The engine supplies the structure and its Chinese and English interface text. Packaging SHALL refuse a film that still supplies a player page of its own, naming the declarations that replace it.

#### Scenario: A film with a copied player

- **WHEN** a film's sources still hold a player page
- **THEN** packaging refuses and names the summary and palette declarations

### Requirement: The transcript reads by thought and leads into the film

The transcript SHALL set each thought as its own paragraph. Each chapter heading SHALL carry its chapter's start and each section heading its voice start, written m:ss, and in the player each time SHALL be a control that plays the film from that time. The Markdown transcript SHALL use the same paragraphs and times.

#### Scenario: A section's time

- **WHEN** a viewer selects a section heading's time in the player
- **THEN** the film plays from that section's voice start

### Requirement: The delivered players are read back in a browser

The player check SHALL open every delivered player from its folder in a real browser and record a verdict per page: every link resolves to a delivery member or a sibling page, the track's cues equal the SRT file's, the track stays hidden on every film and no control shows it, no link opens raw text, each download saves the delivered bytes without leaving the page, a transcript time plays from its time and the edition links exist. Delivery SHALL refuse a failing readback.

#### Scenario: A broken link

- **WHEN** a player links a file the delivery does not hold
- **THEN** the readback fails, names the page and the link, and delivery refuses

### Requirement: Each edition delivers its films with and without captions

Each edition SHALL deliver four films: `uhd` and `1080p-captioned` from its captioned picture, as before, and `uhd-uncaptioned` and `1080p-uncaptioned` from its uncaptioned picture, made alike, with the same soundtrack, chapters, release metadata and cover. The film package SHALL bind both pictures and their equivalence record, and each of its films SHALL name the picture it carries.

#### Scenario: An edition packaged

- **WHEN** an edition with both pictures compared is packaged
- **THEN** its folder holds the four films, and its package names each film's picture

### Requirement: A viewer turns the captions on and off

The player SHALL open on the viewing film with its captions and SHALL offer one captions control, pressed while the captions show, whose words say whether they do in the edition's language. The control SHALL switch to the other film of the same version, and a version button to its version's film with the captions as they are; each switch SHALL keep the time and whether the film plays.

#### Scenario: Captions turned off while paused

- **WHEN** a viewer turns the captions off while the viewing film is paused
- **THEN** the viewing film without captions shows from the same time, still paused, and the control is no longer pressed

#### Scenario: A version chosen with the captions off

- **WHEN** a viewer chooses the UHD version with the captions off
- **THEN** the UHD film without captions shows from the same time, and the captions stay off

#### Scenario: Captions turned on while playing

- **WHEN** a viewer turns the captions on while a film without captions plays
- **THEN** the same version's film with captions plays on from the same time

### Requirement: The caption track stays hidden on every film

The player SHALL attach the edition's WebVTT captions to every film as a hidden metadata track, whose active cue marks the transcript's current paragraph, and SHALL offer no control that shows the track, since the pictures draw the captions and showing it would double them.

#### Scenario: No control shows the track

- **WHEN** a viewer uses any control of the page or looks in the browser's own video controls
- **THEN** none of them shows the track or offers to

#### Scenario: The film plays on through a thought

- **WHEN** a cue of a thought is active
- **THEN** the transcript marks that thought's paragraph as the current one

### Requirement: The player says whether each film draws its captions

The player SHALL list each delivered file by its kind, version, format and size and SHALL say of each film whether its picture draws the captions. It SHALL offer each text file, the Markdown transcript, the chapter files and the SRT and WebVTT captions, as a download labelled by its kind and purpose, so no link opens raw text in a tab, and SHALL promise no download of a film or cover. It SHALL link the other edition's player and the entry page.

#### Scenario: The files and the other edition

- **WHEN** the Chinese player is opened from its delivery folder
- **THEN** it names each version's film with its captions and without them, and the cover, with their sizes, offers the transcript, the chapter files and both caption files as downloads with their sizes, and links the English player and the entry page

#### Scenario: A text file

- **WHEN** a viewer selects the Markdown transcript, a chapter file or a caption file in a player opened from its delivery folder
- **THEN** the browser saves the delivered file's bytes under its name, and the page stays where it is

### Requirement: The readback turns the captions off and on

The player check SHALL turn the captions off on the paused viewing film, choose the UHD version with them off and turn them on while the UHD film plays, and SHALL fail the page unless each switch reaches the other film, keeps a paused film's time within 0.02 s, lets a playing film play on from no earlier than the click and no later than the time that passed, keeps the film paused or playing and leaves the control pressed as the captions show, and every film plays at its size and duration.

#### Scenario: A control that does not switch

- **WHEN** a player's captions control changes its state but leaves the film it showed
- **THEN** the readback fails, names the page, the film shown and the film expected, and delivery refuses

#### Scenario: A playing film that starts over

- **WHEN** a player's version button shows the chosen film from a time earlier than the time at the click while the film plays
- **THEN** the readback fails and names the times before and after the switch

### Requirement: A release names the films with and without captions

A release manifest SHALL name every edition's four films and its uncaptioned picture's stage, or, for a release published before the films without captions existed, only every edition's films with captions; the comparison SHALL refuse any other set, compare the films the release publishes and list the rebuilt films it does not publish.

#### Scenario: A release published before 0.13.0

- **WHEN** a rebuild with four films per edition is compared with a release that publishes two
- **THEN** the two published films of each edition are compared, and the other two are listed as unpublished

### Requirement: A switch keeps the film on the screen

The player SHALL keep a frame of the film on the screen across every switch by the captions control or a version button, and SHALL paint neither the cover nor a frame of one flat colour while it switches. The shown film SHALL stay until the chosen one holds its frame at the time it takes over: a paused film's time, or the time a playing film has reached, from which the chosen film plays on.

#### Scenario: Captions turned off on a paused film

- **WHEN** a viewer turns the captions off while the viewing film is paused
- **THEN** every frame the page paints until the switch ends is the viewing film's frame at its time or the uncaptioned film's frame at the same time, and the time does not move

#### Scenario: A version chosen while the film plays

- **WHEN** a viewer chooses the UHD version while the viewing film plays
- **THEN** the viewing film plays on until the UHD film takes over at the time the viewing film has reached, and no frame in between is the cover or a flat frame

### Requirement: The readback watches what each switch paints

For each switch it makes, to a version or by the captions control, the player check SHALL record every frame the page paints from the click until the chosen film shows, and SHALL fail the page for a frame nearer the cover than the film's frames before and after the switch, or of one flat colour where neither of those is, naming the switch and each such frame's time after the click.

#### Scenario: A page that reloads its film

- **WHEN** a player switches by loading the chosen film into the video it shows, so that the browser paints the cover until the film's frame decodes
- **THEN** the readback fails the page, names the switch and the frames that showed the cover with their times, and delivery refuses

#### Scenario: A page that keeps the film on the screen

- **WHEN** every frame painted during a switch is the shown film's or the chosen film's
- **THEN** the readback records the frames it watched and finds no problem in them

### Requirement: The player's words follow its edition's typography

Each player SHALL set its interface words as its edition's typography does: in Chinese a size that follows a closing full-width bracket SHALL follow it without a space, and in English an apostrophe SHALL be a right single quotation mark.

#### Scenario: A Chinese download

- **WHEN** the Chinese player lists the Markdown transcript of 9 KB
- **THEN** its label reads 讲稿（Markdown，供下载）· 9 KB

#### Scenario: A film the browser cannot play

- **WHEN** the English player's film reports a media error
- **THEN** the message it shows names the system’s player with a right single quotation mark

### Requirement: A delivered film names its author once

Every delivered film SHALL carry its author in one QuickTime key, Author, beside its item-list artist and album-artist tags, so that an index which reads every author-bearing QuickTime key lists the author once. Packaging SHALL refuse a finished film, and the verifier a delivered film, that carries a QuickTime key outside its release's keys and its creation date.

#### Scenario: A film's authors in Spotlight

- **WHEN** Spotlight imports a delivered film
- **THEN** the film's authors list Yang HENG once

#### Scenario: A film with a second author key

- **WHEN** a finished film carries the QuickTime key Artist
- **THEN** packaging refuses it as differing from the delivery contract, and the verifier refuses it once delivered

### Requirement: The 1080p films keep the master's strokes

Each 1080p film SHALL show its UHD picture averaged over blocks of 2×2 pixels, so that a stroke carries no fringe or lifted white that the master lacks.

#### Scenario: A stroke on the dark ground

- **WHEN** a frame of a 1080p film is compared with the same frame of its UHD film averaged over 2×2 blocks
- **THEN** fewer than 2 % of the ground pixels within 3 px of ink are more than 8 levels darker than the ground, and the brightest 0.5 % of its ink stands within 4 levels of the master's

### Requirement: The 1080p films hold a keyframe every 2 seconds

Each 1080p film SHALL hold a keyframe at every 120th frame from its first frame and at no other frame, and packaging and the verifier SHALL refuse a 1080p film whose keyframes fall elsewhere.

#### Scenario: The encoder's default interval

- **WHEN** a 1080p film holds a keyframe every 12 frames
- **THEN** packaging refuses it as differing from the delivery contract, and the verifier refuses it once delivered

#### Scenario: A film keyed every 2 seconds

- **WHEN** a 1080p film's keyframes stand at frames 0, 120, 240 and every 120th frame after them
- **THEN** its keyframes meet the delivery contract

### Requirement: A delivered film names its version

Packaging SHALL read the film repository's `VERSION`, a Semantic Versioning 2.0.0 version without build metadata, SHALL write it into each film's QuickTime key Information with the label of the edition's language, 版本号 or Version, and SHALL bind it among the film's production inputs. Packaging SHALL refuse a repository without a valid `VERSION`, and the verifier a delivered film whose version differs from it.

#### Scenario: A Chinese film's version in Spotlight

- **WHEN** a Chinese edition is packaged at `VERSION` 1.3.0
- **THEN** each of its films carries the QuickTime key Information 版本号 1.3.0, which Spotlight lists as its information

#### Scenario: A version changed after packaging

- **WHEN** `VERSION` changes after an edition was packaged
- **THEN** packaging reports the version as a stale binding and the verifier refuses the edition's films

#### Scenario: No version

- **WHEN** the film repository has no `VERSION`, or it holds `1.3`
- **THEN** packaging refuses and names `VERSION`

### Requirement: The pages name the film's version

Each edition's player page SHALL name the film's version, with its label, in the line under its title after the language, and the entry page SHALL name it under the film's title. The verifier SHALL refuse a delivered page whose version differs from `VERSION`.

#### Scenario: The page names the version

- **WHEN** an English edition's page is built at `VERSION` 2.0.0
- **THEN** the line under its title names Version 2.0.0 after the language

#### Scenario: A page from an earlier version

- **WHEN** a delivered page names Version 1.2.0 while `VERSION` holds 1.3.0
- **THEN** the verifier refuses the page

### Requirement: A film's keywords import whole where the importer allows

Packaging SHALL write each film's QuickTime keywords as the release's keywords joined by "," with no space. Where the host has `mdimport`, the verifier SHALL read each delivered film's imported keywords and SHALL refuse a film with an imported keyword that has a leading or trailing space, no keyword while some are declared, or a declared keyword holding a Chinese character that does not import whole. Where the host has no `mdimport`, the verifier SHALL record the readback as unavailable.

#### Scenario: Chinese keywords in Spotlight

- **WHEN** a Chinese edition declares the keywords DDWG, 数据质量 and 人与人工智能的协作
- **THEN** its films carry the QuickTime keywords `DDWG,数据质量,人与人工智能的协作`, and `mdimport` imports the three keywords, each without a space at either end

#### Scenario: An English phrase in Spotlight

- **WHEN** an English edition declares the keyword "authority to act"
- **THEN** the verifier records that the importer split it into words and does not refuse the film

#### Scenario: Keywords joined with spaces

- **WHEN** a delivered film carries the QuickTime keywords `DDWG, 数据质量` and the host has `mdimport`
- **THEN** the verifier refuses the film, naming the keyword imported with a leading space

#### Scenario: Keywords the importer does not read

- **WHEN** an English edition declares the keyword "authority to act" and `mdimport` imports no keyword from its film
- **THEN** the verifier refuses the film

### Requirement: A film's author imports as the declared author alone

Where the host has `mdimport`, the verifier SHALL read each delivered film's imported authors and SHALL refuse a film whose authors are not exactly the release's declared author, once. Where the host has no `mdimport`, the verifier SHALL record the readback as unavailable.

#### Scenario: The declared author alone

- **WHEN** a delivered film's importer reads its authors as `Yang HENG`, the release's declared author
- **THEN** the verifier records the author and does not refuse the film

#### Scenario: A second author entry

- **WHEN** a delivered film carries the declared author in both its author and artist keys, so the importer reads `Yang HENG` twice and Finder shows "Yang HENG (2)"
- **THEN** the verifier refuses the film, naming the two author entries it read

### Requirement: A film or cover link opens beside the player

Each player SHALL link each delivered film and cover with `target="_blank"` and `rel="noopener"`. The browser readback SHALL click every such link and SHALL refuse a page that leaves its own address or opens no new tab holding the linked file.

#### Scenario: A film link clicked

- **WHEN** the readback clicks a player's link to its UHD film
- **THEN** a new tab opens the film, and the player stays at its own address

#### Scenario: A link that replaces the player

- **WHEN** a player's cover link has no `target`
- **THEN** the readback fails, names the page and the link, and delivery refuses

### Requirement: A rebuilt film that holds the published bytes is not decoded

The comparison SHALL report a rebuilt film whose size and SHA-256 equal those the release manifest records for its published film as an identical file, without decoding either film: its frame count, decoded audio and container hold, and its PSNR is reported as not measured. Such a film SHALL NOT pass without a recorded floor, and the report SHALL state that it calibrates none. A rebuilt film that differs in any byte SHALL be decoded and compared in every layer.

#### Scenario: A rebuilt film that holds the published bytes

- **WHEN** a rebuilt film has its published film's size and SHA-256 and the manifest records its floor
- **THEN** no frame or audio of it is decoded, and its report names an identical file, a PSNR that is not measured and a pass

#### Scenario: An identical file without a floor

- **WHEN** a rebuilt film holds its published film's bytes and the manifest records no floor for it
- **THEN** its report measures no minimum, states that it calibrates no floor, and the comparison does not pass

#### Scenario: A rebuilt film that differs by one byte

- **WHEN** a rebuilt film has its published film's size and one byte that differs
- **THEN** both films are decoded and every layer is compared as before
