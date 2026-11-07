## ADDED Requirements

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

The player check SHALL turn the captions off on the paused viewing film, choose the UHD version with them off and turn them on while the UHD film plays, and SHALL fail the page unless each switch reaches the other film from the same time, keeps the film paused or playing and leaves the control pressed as the captions show, and every film plays at its size and duration.

#### Scenario: A control that does not switch

- **WHEN** a player's captions control changes its state but leaves the film it showed
- **THEN** the readback fails, names the page, the film shown and the film expected, and delivery refuses

### Requirement: A release names the films with and without captions

A release manifest SHALL name every edition's four films and its uncaptioned picture's stage, or, for a release published before the films without captions existed, only every edition's films with captions; the comparison SHALL refuse any other set, compare the films the release publishes and list the rebuilt films it does not publish.

#### Scenario: A release published before 0.13.0

- **WHEN** a rebuild with four films per edition is compared with a release that publishes two
- **THEN** the two published films of each edition are compared, and the other two are listed as unpublished

## MODIFIED Requirements

### Requirement: The delivered players are read back in a browser

The player check SHALL open every delivered player from its folder in a real browser and record a verdict per page: every link resolves to a delivery member or a sibling page, the track's cues equal the SRT file's, the track stays hidden on every film and no control shows it, no link opens raw text, each download saves the delivered bytes without leaving the page, a transcript time plays from its time and the edition links exist. Delivery SHALL refuse a failing readback.

#### Scenario: A broken link

- **WHEN** a player links a file the delivery does not hold
- **THEN** the readback fails, names the page and the link, and delivery refuses

## REMOVED Requirements

### Requirement: Every version draws its captions, and the track beside them stays hidden

**Reason**: the films without captions draw none. The hidden track moves to "The caption track stays hidden on every film" and the version switch to "A viewer turns the captions on and off".

**Migration**: none for a film; the engine renders the player.

### Requirement: The player names its files and links its editions

**Reason**: the films no longer all hold their captions in the picture; "The player says whether each film draws its captions" replaces it with its scenarios.

**Migration**: none for a film; the engine renders the player.
