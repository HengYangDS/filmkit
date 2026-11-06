## ADDED Requirements

### Requirement: The engine builds each edition's player from the film's words

The engine SHALL render each edition's player page itself. A film SHALL declare only its words and colours: each edition's summary and the player's palette. The engine supplies the structure and its Chinese and English interface text. Packaging SHALL refuse a film that still supplies a player page of its own, naming the declarations that replace it.

#### Scenario: A film with a copied player

- **WHEN** a film's sources still hold a player page
- **THEN** packaging refuses and names the summary and palette declarations

### Requirement: Every version draws its captions, and the track beside them stays hidden

Every version's picture draws its captions. The player SHALL attach the edition's WebVTT captions to every version as a hidden metadata track, whose active cue marks the transcript's current paragraph, and SHALL offer no control that shows the track, since showing it would double the drawn captions. Switching versions SHALL keep the playing time.

#### Scenario: Captions on the UHD version

- **WHEN** a viewer switches from the viewing edition to the UHD version
- **THEN** the film continues from the same time with the captions its picture draws, and the track stays hidden

#### Scenario: No control shows the track

- **WHEN** a viewer uses any control of the page or looks in the browser's own video controls
- **THEN** none of them shows the track or offers to

#### Scenario: The film plays on through a thought

- **WHEN** a cue of a thought is active
- **THEN** the transcript marks that thought's paragraph as the current one

### Requirement: The transcript reads by thought and leads into the film

The transcript SHALL set each thought as its own paragraph. Each chapter heading SHALL carry its chapter's start and each section heading its voice start, written m:ss, and in the player each time SHALL be a control that plays the film from that time. The Markdown transcript SHALL use the same paragraphs and times.

#### Scenario: A section's time

- **WHEN** a viewer selects a section heading's time in the player
- **THEN** the film plays from that section's voice start

### Requirement: The player names its files and links its editions

The player SHALL list each delivered file by its kind, version, format and size and SHALL say that both films hold their captions in the picture. It SHALL offer each text file, the Markdown transcript, the chapter files and the SRT and WebVTT captions, as a download labelled by its kind and purpose, so no link opens raw text in a tab, and SHALL promise no download of a film or cover. It SHALL link the other edition's player and the entry page.

#### Scenario: The files and the other edition

- **WHEN** the Chinese player is opened from its delivery folder
- **THEN** it names the UHD film and the viewing edition with their captions in the picture and the cover with their sizes, offers the transcript, the chapter files and both caption files as downloads with their sizes, and links the English player and the entry page

#### Scenario: A text file

- **WHEN** a viewer selects the Markdown transcript, a chapter file or a caption file in a player opened from its delivery folder
- **THEN** the browser saves the delivered file's bytes under its name, and the page stays where it is

### Requirement: The delivered players are read back in a browser

The player check SHALL open every delivered player from its folder in a real browser and record a verdict per page: every link resolves to a delivery member or a sibling page, the track's cues equal the SRT file's, the track stays hidden on every version and no control shows it, no link opens raw text, each download saves the delivered bytes without leaving the page, a transcript time plays from its time and the edition links exist. Delivery SHALL refuse a failing readback.

#### Scenario: A broken link

- **WHEN** a player links a file the delivery does not hold
- **THEN** the readback fails, names the page and the link, and delivery refuses
