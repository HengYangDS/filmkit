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
