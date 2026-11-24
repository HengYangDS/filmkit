# film-package Specification

## Purpose

Package each edition's films so that their tracks, chapters and tags describe that edition.

## Requirements

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

Each edition SHALL deliver four films: `uhd` and `1080p-captioned`, which show its captioned picture, and `uhd-uncaptioned` and `1080p-uncaptioned`, which show its uncaptioned one, with one soundtrack, chapters, release metadata and cover. The film package SHALL bind both pictures and their equivalence record, and each film SHALL name the picture it shows and the picture file its encode read: its own picture, but the captioned one, painted, for the `1080p-uncaptioned` film of a derived pair.

#### Scenario: An edition packaged

- **WHEN** an edition with both pictures compared is packaged
- **THEN** its folder holds the four films, and its package names each film's picture

#### Scenario: A derived pair packaged

- **WHEN** an edition whose uncaptioned picture is derived is packaged
- **THEN** its `1080p-uncaptioned` film is recorded as showing the uncaptioned picture and as read from the captioned picture's file, and every other film as read from the file of the picture it shows

#### Scenario: A record that names another file

- **WHEN** a film's record names another picture file than the one its encode reads as the pictures stand
- **THEN** the verifier refuses the film package

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

### Requirement: The 1080p films are encoded in software on a forced keyframe grid

Packaging SHALL encode each 1080p film with the x264 encoder at a constant rate factor, without B-frames, with the keyframe interval and its minimum both set to 120 frames and scene-cut keyframes off, and with no hardware decoder or encoder, so that where its keyframes stand depends on its options alone.

#### Scenario: A 1080p film's encode command

- **WHEN** packaging builds the encode command of a 1080p film
- **THEN** the command names the encoder `libx264`, a constant rate factor, `-bf` of 0, `-g` and `-keyint_min` of 120 and `-sc_threshold` of 0, and names no VideoToolbox decoder or encoder

#### Scenario: A short film encoded with those options

- **WHEN** a film of four seconds at 60 frames per second is encoded with the 1080p options
- **THEN** its keyframes stand at frames 0 and 120 and at no other frame

### Requirement: No picture or film holds B-frames

Every rendered picture, derived picture and delivered film SHALL hold its frames in the order they are shown, without B-frames, as every film delivered before does. The validation of a picture, packaging's check of a finished film and the verifier's check of a delivered film SHALL each refuse a picture stream for which FFprobe reports B-frames.

#### Scenario: The four films of a derived pair

- **WHEN** a captioned picture, the picture derived from it and the four films packaged from the pair are made by the engine's commands
- **THEN** FFprobe reports no B-frames in the derived picture or in any of the four films, and packaging's check and the verifier's pass each film

#### Scenario: A film encoded with B-frames

- **WHEN** a 1080p film is encoded with x264's default B-frames
- **THEN** packaging refuses the finished film and links none into place, and the verifier refuses the same file, naming B-frames

#### Scenario: A derived picture with B-frames

- **WHEN** a derived picture's stream holds B-frames
- **THEN** its validation refuses it, naming B-frames

### Requirement: A delivery's destination is the caller's, the host's or the platform's videos folder

The delivery SHALL fill, in this order: the folder `--destination` names; the film's declared delivery folder below the root `FILMKIT_DELIVERY_ROOT` names; that folder below the user's videos folder, `~/Movies` on macOS and elsewhere the XDG videos directory. The engine SHALL name no other folder of a host. The delivery's readback and the command's summary SHALL state the destination and the rule that gave it.

#### Scenario: A folder the caller names

- **WHEN** the delivery runs with `--destination` naming a folder while `FILMKIT_DELIVERY_ROOT` is set
- **THEN** it fills that folder, and its readback states that folder and the rule `--destination`

#### Scenario: A host's delivery root

- **WHEN** the delivery runs without `--destination` on a host whose `FILMKIT_DELIVERY_ROOT` names a folder
- **THEN** it fills the film's declared delivery folder below that root, and its readback states the rule `FILMKIT_DELIVERY_ROOT`

#### Scenario: The videos folder on macOS

- **WHEN** the delivery runs on macOS with neither
- **THEN** it fills the film's declared delivery folder below `~/Movies`, and nothing below `~/Documents`

#### Scenario: The XDG videos directory

- **WHEN** the delivery runs elsewhere with neither
- **THEN** the videos folder is `XDG_VIDEOS_DIR` of the environment, else the `XDG_VIDEOS_DIR` line of `user-dirs.dirs` below `XDG_CONFIG_HOME` or `~/.config`, else `~/Videos`

#### Scenario: The videos line as xdg-user-dirs writes it

- **WHEN** the `XDG_VIDEOS_DIR` line of `user-dirs.dirs` holds its value in double or in single quotes, as `$HOME/...` or as an absolute path, with or without a comment after it
- **THEN** that folder is the videos folder, and of several such lines the last counts

#### Scenario: A videos line that cannot be used

- **WHEN** that line holds a relative value, a value without quotes or anything else after the value than a comment
- **THEN** the videos folder is `~/Videos`, and the rule the readback records says that the file's line was not usable and gives the line

#### Scenario: A dry run

- **WHEN** the delivery runs with `--dry-run`
- **THEN** its report states the destination and the rule, and the destination is not created

### Requirement: A delivery refuses a destination that is not its own to empty

Before it reads a player or changes anything, and in a dry run too, the delivery SHALL refuse: an empty `--destination`; a `FILMKIT_DELIVERY_ROOT` that is no absolute path; a destination that is the film's root, holds it or lies inside it, however its path is spelled and whichever rule gave it; and one that is no folder, or holds entries other than `.DS_Store` and `.claude` and no entry page of an earlier delivery. The refusal SHALL name the folder, the rule that gave it and what was found.

#### Scenario: An empty destination

- **WHEN** the delivery runs at the film's root with `--destination ""`, as an unset variable in a script leaves it
- **THEN** it refuses, naming the empty value, and no file below the root is moved

#### Scenario: The film's root, by each rule

- **WHEN** the destination resolves to the film's root or to a folder that holds it: named by the caller, as `.` or through a symbolic link; given by `FILMKIT_DELIVERY_ROOT` where the film's checkout has the name of its delivery folder; or given by the videos folder where the film is checked out inside its delivery folder
- **THEN** the delivery refuses, naming that rule and the film's root, and nothing is read back, run or written

#### Scenario: A folder that holds the root or lies inside it

- **WHEN** the destination is a folder above the film's root, or a folder below it
- **THEN** the delivery refuses, naming the film's root

#### Scenario: The film's own tree under another spelling

- **WHEN** the destination names the film's root, a folder above it or a folder below it, one that does not exist yet among them, in another letter case on a volume that folds case, through a symbolic link above it, or by a second path to the same volume
- **THEN** the delivery refuses as it does for the spelling the root has, and no file of the film is moved

#### Scenario: A host's root that is no absolute path

- **WHEN** `FILMKIT_DELIVERY_ROOT` is a relative path or holds only blanks
- **THEN** the delivery refuses, naming the variable and its value, and fills no folder below the working directory

#### Scenario: A populated folder that no delivery filled

- **WHEN** the destination holds a user's files and folders and no `index.html`
- **THEN** the delivery refuses, naming how many entries it holds and the first of them, and the folder is unchanged

#### Scenario: A folder an earlier delivery filled

- **WHEN** the destination holds the `index.html` of an earlier delivery and an entry beside the members
- **THEN** the delivery fills it, and that entry is moved into the predecessors

#### Scenario: A dry run refuses the same

- **WHEN** any of these destinations is given with `--dry-run`
- **THEN** the dry run refuses as the delivery does

### Requirement: A release record is written from the reviewed, delivered build

`filmkit.delivery.release` SHALL write the release manifest and stage every asset it names, under its release name, with the checksums file. It SHALL do so only from a build whose bound inputs the film verifier accepts, whose staged pictures are current, whose recorded reviews cover its current films, and whose members the film's own delivery folder holds. The first refusal SHALL stop it before any file is written.

#### Scenario: A reviewed and delivered build

- **WHEN** both editions are reviewed and delivered to the film's own folder, and the command runs
- **THEN** the release folder holds exactly every edition's films, captions, transcript, cover and review and the checksums file, each with the bytes the manifest records
- **AND** the manifest loads as a release manifest and states the film's version

#### Scenario: A bound input that moved

- **WHEN** an edition's soundtrack differs from the one its assembly record names
- **THEN** the command refuses in one line as the verifier words it, and no file changes

#### Scenario: A stale uncaptioned stage

- **WHEN** an edition's uncaptioned picture was derived and its staged document differs from the one its sources stage now
- **THEN** the command refuses in one line that names the edition and the uncaptioned picture, and no file changes

#### Scenario: An edition without a recorded review

- **WHEN** an edition has no production review record
- **THEN** the command refuses in one line that names the record, and no file changes

#### Scenario: A tracked manifest that is none

- **WHEN** `content/release.json` exists and cannot be read as a release manifest
- **THEN** the command refuses in one line that names the file, and no file changes

#### Scenario: A dry run

- **WHEN** the command runs with `--dry-run` on a build it would record
- **THEN** it prints the manifest it would write and no file changes

### Requirement: A release is recorded from what the film's own folder holds

The command SHALL compare every delivery member in the film's own delivery folder, as the host names that folder when the command runs, with the build's file, and SHALL refuse a member that is missing or holds other bytes, by its path.

#### Scenario: A build delivered only to a named folder

- **WHEN** the build was delivered to a folder named with `--destination` and the film's own folder holds an earlier build
- **THEN** the command refuses and names a member of the film's own folder that differs

#### Scenario: A delivery under the host's root

- **WHEN** the host names its delivery root, and the film's folder below it holds every member with the build's bytes
- **THEN** the command records the release

### Requirement: The release folder is not overwritten with other bytes unasked

The command SHALL refuse, naming the entries and `--replace`, a release folder that holds any entry other than an asset with the bytes the record would write; with `--replace` it SHALL replace the folder. It SHALL leave a folder that already holds exactly the record's assets, and otherwise stage the whole set beside the folder before it puts it in the folder's place. It SHALL write the manifest last. A release or staging path that is a link or no folder SHALL be refused by its path.

#### Scenario: A second run on the same build

- **WHEN** the command runs twice on one build
- **THEN** the second run's manifest and release folder hold the bytes the first run's held

#### Scenario: The films of the release before

- **WHEN** the release folder holds the last release's films and the command runs on a new build
- **THEN** the command refuses, names those films and `--replace`, and the folder and the manifest hold the bytes they held

#### Scenario: A record written again after its review was recorded again

- **WHEN** the folder holds this version's assets, an edition's review was recorded again, and the command runs with `--replace`
- **THEN** the folder holds exactly the new record's assets and the manifest names the new review's bytes

#### Scenario: A staging that fails

- **WHEN** the copy of an asset fails while the set is staged
- **THEN** the release folder and the manifest hold the bytes they held, and the next run stages again

#### Scenario: A path that is no folder

- **WHEN** the release folder's path, or the path of the folder the set is staged in, is a file or a link
- **THEN** the command refuses in one line that names the path, with `--replace` too, and nothing is staged or removed

### Requirement: A run that stops late is completed by the next run

A run that stops after it removed the release folder, or after it put the staged set in the folder's place and before it wrote the manifest, SHALL leave the tracked manifest as it was, and the next run SHALL complete the record without `--replace`.

#### Scenario: A run that stops before the staged set is in place

- **WHEN** a run stops after it removed the release folder and before it renamed the staged set to it
- **THEN** no release folder stands, the staged set is whole beside its place, and the manifest holds the bytes it held
- **AND** the next run, without `--replace`, stages the set again and writes the manifest

#### Scenario: A run that stops before the manifest is written

- **WHEN** the release folder was replaced and the manifest's write fails
- **THEN** the folder holds the new record's assets and the manifest the bytes it held
- **AND** the next run, without `--replace`, leaves the folder and writes the manifest

### Requirement: A record keeps each film's floor

The command SHALL record for each film the PSNR floor that the manifest it replaces states for a film of that name, and no floor for a film that manifest does not name, and SHALL print each film's floor or that it has none.

#### Scenario: A film's next release

- **WHEN** the replaced manifest states 45.0 dB for each of an edition's four films
- **THEN** the written manifest states 45.0 dB for each of them

#### Scenario: A film's first record

- **WHEN** no manifest exists and the command writes one
- **THEN** the manifest states no floor and the command names each film as without one

### Requirement: A record's film-bound sources are stated at every run

The command SHALL require `--sources` at every run and SHALL record, in sorted order and each once, the SHA-256 of each path it names. It SHALL take no source from the manifest it replaces. It SHALL refuse a stated path that the manifest's model does not list as a source's path, in words that name that model and print its pattern, and a stated source that is not a file.

#### Scenario: A run without its sources

- **WHEN** the command runs without `--sources`, with or without a manifest to replace
- **THEN** the command line refuses and names the option, and no file changes

#### Scenario: A script changed since the last release

- **WHEN** a script changed since the last release and the command runs with `--sources` naming it
- **THEN** the script's entry in the written manifest holds its current SHA-256

#### Scenario: A stated set replaces the listed one

- **WHEN** the manifest the command replaces lists a path that `--sources` does not name
- **THEN** the written manifest lists exactly the named paths and not that one

#### Scenario: A source that is gone

- **WHEN** `--sources` names a path that is not a file
- **THEN** the command refuses and names the path

#### Scenario: A path the manifest's model does not list

- **WHEN** `--sources` names a file as `.config/policy.toml` or `content/My Notes.md`, by an absolute path, or by a path that holds `./` or `..`
- **THEN** the command refuses in one line that names the manifest's model of a source's path, prints that model's pattern and names the path

### Requirement: A stated source is a file of the film that is neither its record nor generated

The command SHALL take as a stated source a file below the film's root that is neither the release manifest nor below the folder that holds what the engine generates, and that no link leads to either or outside the root. It SHALL refuse any other by name, before any file is written. It compares paths as they are spelled.

#### Scenario: The record itself

- **WHEN** `--sources` names `content/release.json`, with or without a manifest to replace
- **THEN** the command refuses in one line that says it is the release record itself, and no file changes

#### Scenario: A path below the generated folder

- **WHEN** `--sources` names a file below `build/`, or a link elsewhere below the film's root that leads to one
- **THEN** the command refuses in one line that names the path, and no file changes

#### Scenario: A link that leads outside the film

- **WHEN** `--sources` names a link below the film's root that leads to a file outside it
- **THEN** the command refuses in one line that names the path, and no file changes

### Requirement: The command says which record it replaces

The command SHALL print the version of the manifest it replaces beside the version it writes, and SHALL refuse a film version the manifest cannot state, by name. Beside the versions it SHALL print each path the replaced manifest listed as a source that the run does not state, and each path the run states that the replaced manifest did not list, in a dry run too, and SHALL refuse nothing for either.

#### Scenario: A stated set that differs from the replaced list

- **WHEN** the manifest the command replaces lists one source that the run does not state, and the run states one that manifest did not list
- **THEN** the command's output names each of the two paths with what it is, in a dry run as in a run, and the record is written with the stated set

#### Scenario: The same version written again

- **WHEN** the manifest states version 1.0.2 and the command runs on a film whose `VERSION` is still 1.0.2
- **THEN** the record is written and the command's output says that it replaces a record of 1.0.2

#### Scenario: A pre-release version

- **WHEN** the film's `VERSION` holds a pre-release
- **THEN** the command refuses and says that a release manifest states three numbers

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
