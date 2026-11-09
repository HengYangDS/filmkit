# Changelog

All notable changes to filmkit are recorded here. The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/), and releases follow [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html). Until 1.0.0 the declaration format may change in a minor release.

## [Unreleased]

## [0.17.0] - 2026-11-09

### Changed

- `check-picture` refuses a jump at a stage cut (`motion_jumps`): the marks at ink level 60 or more that a cut keeps, matched at one size, which move whole by one shift of 8 px or more beyond the shift each moved by in the frame before, to within 2 px, while they hold half or more of their scene's firm ink, by box area times ink level, in the frame before the cut. The follower stops at a cut, so the 0.16.0 gate never judged the DDWG film's 04.2 field and name, which moved 354 px within one frame at a declared cut, or the English 05.2 case, which moved 224 px; its round-34 production review found both. A stage gliding through a cut keeps its motion and does not jump, while one that sets off at a cut faster than it then glides jumps by its first step: counted on the shift alone, at 30 fps every glide of 240 px/s or more through a cut would jump, as ten glides through the declared cuts of the DDWG and ETHOS films did. A finding names the jump's heaviest mark, its shift beyond the marks' motion, its distance and how many marks moved.
- A stage cut the composition declares that changes less than 35% of its scene's firm marks, counted and by ink, excuses the marks it takes away and no longer the marks it brings: a mark it brings at ink level 60 or more pops, and its finding says it came at a declared cut that keeps its stage. The DDWG film declared a cut where 06.2's statement appeared at full ink and where 02.2's divider replaced a tie, and 0.16.0 excused both.
- The headless canvas records each stroke's dash pattern as a canvas holds it, an odd pattern repeated and an invalid one ignored, and `check-picture` refuses a dash snap (`motion_dash_snaps`): a stroke followed at ink level 25 or more whose share of gap, the sum of its gaps over its period, changes by 0.25 or more within one frame outside a stage cut, as the DDWG film's 13.1 join did when it turned into dashes of 8 px on and 8 px off. A dashed way drawn on keeps its share, and gaps that open over a third of a second change it by a few hundredths a frame. Of two outlines crossfading on one box, each continues the outline of its own pattern.
- A film keeps a jump or a dash snap by declaring it in `[[picture.motion.exceptions]]` with kind `jump` or `dash`, and `filmkit.review.measurement` counts jumps and dash snaps and refuses a motion report that judges neither. On the DDWG film's round-34 composition the audit finds each of the eight cases its review named; on the films' current compositions it finds a pop and a dash snap in each DDWG edition, a jump and five pops in the ETHOS film's English edition and two jumps and two pops in its Chinese one, and two pops in each edition of the essentials film. This breaks a composition that moves the marks a cut keeps, brings a mark onto a stage that stands at a declared cut, or switches a stroke's dashes within one frame.

## [0.16.0] - 2026-11-08

### Changed

- `check-picture` refuses a still state off centre that its stage leaves: a run of 2 s or more in which the picture's full-size lit box stands more than 50 px off x 960 while its edges keep still, and which a stage cut the composition declares, or the next scene, then replaces. The frame audit reports such runs as `off_centre_finished` and the other still runs, which may wait for a part that docks to them, as `off_centre_settled`, still recorded without refusing. A frame after a stage cut no longer counts as growth from the state before it: the essentials film's 07.3 stood about 63 px left of centre for 11 s and passed because the next stage cut in with a wider box, where its sixth production review found it off balance. This breaks a composition with such a stage.

## [0.15.0] - 2026-11-08

### Fixed

- A declared caption term stays on one English caption line wherever it fits. The phrasing compares layouts first by how many of their breaks fall inside a declared term and then by their cost; a split had cost 90, as much as a line that ends on a word such as "for", so the ETHOS film's expanded name split after "Trust", its one whole layout ending a line on "for" and leaving a short line. A term longer than a line takes the fewest splits. On the films' current English scripts this moves the lines of one segment of the ETHOS film and one of the DDWG film.
- A short English quotation of several sentences stays on one caption line: a sentence that ends inside an open quotation continues into the next while both fit the caption limit, so the ETHOS film's "Done. All tests pass." no longer spans two captions. A longer quotation divides at its sentences as before. The quotation marks, which the review's sentences read the same way, move to `filmkit.narration.spoken_units`.

## [0.14.0] - 2026-11-08

### Added

- `check-picture` checks each clockwise `arc()` that sweeps a whole turn or more (less 1e-5 rad) from a start that is not a whole number of turns. The frame audit lists them as `whole_turns`, by scene and line, with each distinct start and end in its `TURNS` file, and the new `filmkit.tools whole-turns` draws each start once on a scratch canvas in the renderer's browser. The gate refuses a line whose arc paints no ink from one of its starts (`vanishing_arcs`), naming the frames, the start, how many of its starts fail and the line of `picture/film.js`, and records every other line; both name the remedy `ellipse(x, y, r, r, start, 0, 2 * Math.PI)`. Chrome Headless Shell 152.0.7977.30 computes such an arc in single precision and painted no ink for 64 of 4,000 starts through one turn and 13 of 1,000 through a longer sweep, with Metal and SwiftShader alike; anticlockwise arcs, starts at whole turns and ellipses always drew, and the headless stand-in drew every arc. This breaks only a composition whose whole turn paints no ink. The rings of the ETHOS and DDWG films, from π, 3π/2 and −π/2, paint and are recorded.
- The player check watches every switch it makes with a screencast of the page, from before its click until it settles, and fails a page whose switch paints the cover or a frame of one flat colour where the film should be, naming the switch and each frame's time after the click; a switch whose frames were not read fails too.

### Changed

- A version or captions switch in the player keeps the film on the screen. The page makes the chosen film ready in a second video, hidden in the same place, and shows it only once it holds its frame at the time it takes over: a paused film's time, or the time a playing film has reached, which plays on meanwhile. The 0.13.0 page loaded the chosen film into the video it showed, which painted the cover in each of the 32 switches measured on the essentials films in Chrome from disk and over the media server, for 2 to 24 frames from 36 ms after the click; this page painted none. The page's script moves into `delivery/player-page.js`, which the engine inlines. Each edition's player page changes; a film's films, pictures and records do not.
- The player check holds a paused switch to the time within 0.02 s, as the page sets it, and lets a playing one play on from no earlier than 0.05 s before the click to no later than the time that has passed since; it finds the page's film by its id, `film`.

### Fixed

- A caption term declared with capitals stays on one caption line: the English phrasing compares each declared term's words with a caption's words in lowercase, as it reads them. The declaration and the concept check keep each term as written.
- `produce compare-pictures` refuses a frame under 45 dB PSNR outside the caption band, not 50 dB: the 50 dB floor refused the ETHOS film's Chinese pictures at one keyframe whose encoder noise spread thinly over the frame (49.76 dB, largest tile 1.847 levels). The tile limit of 4 levels still refuses a missing label, and the floor a uniform shift of 2 levels (42.1 dB).
- The Chinese player's size after a closing full-width bracket follows it without a space, as in `讲稿（Markdown，供下载）· 9 KB`, since the bracket holds its own; the English message for a film the browser cannot play sets `system’s` with a typographic apostrophe.

## [0.13.0] - 2026-11-07

### Added

- Each edition renders a second picture without its captions. `stage-picture --uncaptioned` stages the same composition and timeline with `captions` set to `[]` in `final-delivery-<edition>-uhd-uncaptioned/`, and `render-picture --uncaptioned` renders it with the same HyperFrames settings to `<slug>-final-picture-uncaptioned.mp4` and `render/receipt-uncaptioned.json`; `validate-picture --uncaptioned` binds it. Each stage record and receipt names its `picture`, `captioned` or `uncaptioned`; one written before 0.13.0 names none and stays the captioned picture's, so no captioned picture is rendered again for it.
- `produce compare-pictures` proves that the uncaptioned picture differs from the captioned one only by its captions and records it in `build/evidence/editions/<edition>/caption-equivalence.json`, which packaging requires. At the composition, `filmkit.tools caption-equivalence` runs the composition headlessly with and without the captions at every caption's start, middle and end and every 0.5 s, and refuses any paint that changes, goes or comes besides the caption paints: texts outside every scene that carry the display text of the cue that started last or of the next one, and that the frame's layout names as captions. In the encoded pictures, both are decoded at every 0.5 s and every caption's start, middle and end frame and compared outside the caption band, widened by 24 rows of 1080 and out to 16-pixel blocks: no tile of 64 luma or 32 chroma pixels may differ by more than 4 levels on average, and the compared samples must keep 50 dB PSNR. On the sample film the encoder's noise between the two pictures reached 1.51 and 1.24 levels and 60.2 and 61.1 dB at worst in the Chinese and English editions; a picture missing one muted note outside the captions differed by 24.8 and 17.2 levels in 31 and 29 of the 152 and 154 sampled frames, and the Chinese picture one frame off by 11.0 levels and 47.8 dB, while the English one frame off, slow at every sampled frame, stayed within both limits at 3.7 levels and 52.2 dB.
- Each edition delivers four films: `uhd` and `1080p-captioned` as before, and `uhd-uncaptioned`, the uncaptioned picture's copied stream, and `1080p-uncaptioned`, its 1080p encode, with the same soundtrack, chapters, metadata and cover. The film package binds both pictures and the equivalence record, and each member names the picture it carries.
- The player has a captions control: a button with `aria-pressed`, pressed while the captions show, reading `字幕：开` or `字幕：关` and `Captions: on` or `Captions: off`, with `字幕` or `Captions` as its name. It switches to the other film of the same version, and the version buttons keep its state; both keep the time and whether the film plays. The files list says of each film whether its picture draws the captions (`画面内含字幕` or `无字幕`, `captions in the picture` or `no captions`).
- `player-check players` turns the captions off on the paused viewing film, switches to the UHD version with them off and turns them on again while the UHD film plays, and fails a page whose control or version button does not reach the other film from the same time, does not keep the film paused or playing, or leaves the control pressed against the captions; all four films are played at three seek points.

### Changed

- **Breaking:** the delivery holds 25 members, each edition's four films among them; the verifier, the review rounds, the set-aside and the release manifest take every film of an edition. A build packaged before 0.13.0 is set aside with its two films and its captioned picture. A release manifest names either every edition's four films with its `uncaptioned_stage_sha256` or, for a release published before 0.13.0, only the two films with captions; the comparison then lists the rebuilt films without captions as unpublished.
- The preflight reports the uncaptioned picture's stage beside the captioned one's.
- The sample film's tasks stage, render and validate both pictures and compare them, and its review prompt describes the four films.

## [0.12.0] - 2026-11-07

### Added

- The motion audit follows every mark a scene draws as a viewer sees it move (`followed` in the motion report), at 30 fps in 1080p pixels per second. A mark keeps its identity by its scene, kind, words and line width, through moving whole, through growing, shrinking or redrawing in place or while it moves, and through words that change in place. A group of like marks continues the previous frame's by the least total miss from where each mark's own motion puts it, and of marks that stand alike the one nearest the mark's ink continues it. A mark's drawn pieces show its motion too, each where it is drawn from or, closed, at its centre: a pair whose box flips as a piece turns a corner continues by the shift its pieces share.
- `check-picture` refuses, outside stage cuts, `motion_halts` (a mark falling from 60 px/s or more to rest, under 1.5 px/s, within one frame), `motion_starts` (the reverse), `motion_races` (900 px/s or more) and `motion_pops` (a mark at ink level 60 or more that appears or vanishes within one frame, bringing or taking pieces 12 px or more across: the drawn subpaths that no like mark of the other frame holds in place). The thresholds are the brief's; an eased end, a last step under half the one before it, is not a halt or a start, a mark that holds one end of a drawn piece exactly where it stood grows or turns from it and does not travel, and a mark rests only where its box and the shift its drawn pieces share both show it at rest. A stage cut is a frame in which 35% or more of a scene's firm marks, counted or weighed by their ink, vanish or appear, or one in which the composition declares a cut of the scene in its global `stageCuts` map. Each finding names its time, scene, paints and words, its speed or ink and the composition line that drew it: the scene's own line rather than a shared helper, with its module where the composition is bundled from modules.
- `[[picture.motion.exceptions]]` declares each motion finding a film keeps, by its `edition`, `scene`, `source` (`film.js:<line>` or the composition's module), `kind` and `reason`; the gate record lists each kept finding and refuses an exception that matches no finding of its edition.
- The motion report records, for each scene, the fastest glide (a text or a mark more than 16 px across) and flow (a smaller mark) with their times.
- `[review.levels]` declares the review's three levels, `"信"`, `"达"` and `"雅"`, each with what it `asks` of the whole film and the `dimensions` it holds; a declaration whose levels miss, repeat or invent a dimension is refused. For such a film, `review.round prompts` states each level with its dimensions under it in `{levels}`, and refuses a template that does not cite `{levels}` and `{sentences}`. `review.round record` and the verifier accept a review only level by level: each level has a verdict and passes only when every dimension it holds meets the floor and no material finding remains in it, and each finding names its level. The sample film declares the three levels.
- `review.round prompts` writes, for a film with levels, each edition's sentences to `sentences-<edition>.json` in the round's directory, named in `{sentences}`: every sentence of every thought, split at 。？！ in Chinese and . ? ! in English with quotations kept whole, with its id `<segment>.<thought>.<sentence>`, its text and its start and end in the timeline (`filmkit.review.sentences`). A review gives every sentence a verdict, `ok` or the ids of the findings that concern it, and `record` and the verifier refuse a review that misses a sentence, names an unknown one or names a finding it does not hold. The production record carries the `levels` and `sentences` verdicts; its schema version stays 2, so a film without levels keeps its records.

- `review.measurement` records each edition's motion as `picture_motion`, from the motion report its picture gate judged: the counts of halts, starts, races and pops outside stage cuts, the findings and the declared ones, the fastest glide and flow per scene and for the edition, and every finding with its time, scene and drawing line. It refuses a gate record bound to another composition or timeline, or a report other than the one the record binds.

### Changed

- **Breaking:** the motion gate applies to every film from 0.12.0, whatever it declares. On the films' committed compositions it refuses ETHOS with 172 Chinese and 190 English findings (14 and 12 halts, 12 and 12 starts, 129 and 142 races, 17 and 24 pops), the essentials film's composition before its motion repair (`679b8db`) with 38 and 40 (6 races and 32 and 34 pops) and DDWG with 365 and 397 (1 and 2 halts, 1 Chinese start, 148 and 175 races, 215 and 220 pops), and passes the sample film and the essentials film's repaired composition (`90d3199`), whose flows move at an even pace with dots entering and leaving by size, glides ease in voice time and paths draw on along their length. The ETHOS film's motion repair (`3468694`) holds 5 findings in each edition, the pops of its facts row, whose lit ticks switch on and off at full ink as the lit window wraps from one end of the row to the other (`p03/kernel.js`, film.js:2256). The brief's prototype probe, run on the same compositions, left 797 to 1,423 events per edition without an origin and reported growing marks as pop pairs, a flow's dot wrapping by size as a race, a dot jumping to a like dot that appears elsewhere, rules halting in step as swapped halts and stage handoffs that keep a large frame as pops; the gate follows the first four and counts the last as stage cuts. On the repaired essentials composition it also found 28 and 29 findings that were its own: marks that give way to others at a stage cut the composition declares on a word, a bracket whose second end enters by size, a slab that eases down and joins its stack, and a bracket's moving end sliding through its fixed end; reading the declared cuts, judging a pop by the pieces it brings or takes and holding a pair to its fixed end resolve them. On the ETHOS motion repair it found 48 and 44 more of its own: links drawn on from a start that glides, whose box stops shifting as they turn a corner, read as halts and starts, a row of checks that grows a cell at its end while it glides as a halt and a start at each cell, a link drawn on from a rising start that turns its corner as pops and the figure it rises with as a halt and a start, and a box whose dashed outline gives way to a solid one while it glides as a pop; resting only where a mark's box and its pieces both show it at rest, following a pair by the shift its pieces share where its box flips, and continuing a mark by the like mark nearest its ink resolve them. On the other films these changes add no event and remove only such events, but for one that a viewer does see: in ETHOS 05 at 406.5 s in English the link from the Agent to its claim jumps from an L route to a straight line within one frame, which the gate had read as a halt and the repair no longer draws. Every finding names its line. On the ETHOS round-9 composition the owner watched, the gate finds 27 halts and 29 starts of flow dots in the English edition, every halt within 0.25 s of a word's end; on the committed composition, whose voice clock eases to rest between thoughts, 6 and 5 remain.
- A paint's origin (`openComposition().origin()`) is the innermost line of a scene's own code on its call stack, a scene's body or a module below `scenes/`, and otherwise the innermost line of the composition that drew it, where it was null before; `module(origin)` names the module of a bundled composition, and `declaredCuts()` the stage cuts the composition has declared in its `stageCuts` map.

## [0.11.0] - 2026-11-06

### Added

- `check-picture` judges every wrapped label at rest, from the lines the film paints (`wrapped_labels`). Within the lines of one size it refuses a line other than the last that spans less than `line_share` of the widest of them (0.8), a last line under `last_share` (0.6), an English line other than the last that ends on an article, preposition, conjunction, determiner, possessive, wh-word or auxiliary or on one of the film's `lead_words`, a last line holding one word of a name of three or more, and a Chinese line after the first that opens on closing punctuation. A film declares its shares, lead words and reasoned `exceptions` in `[picture.wrapping]`; the gate record lists each kept break and refuses a stale exception. On the current builds of the three films the audit's lines equal a real-browser readback for all 328 labels of the six editions, and the gate flags 59 English and 11 Chinese labels of DDWG round 33, among them the English breaks of EN33-1 and the Chinese blocks of R33-zh-2, 26 English and no Chinese labels of ETHOS round 8, and 5 English and 2 Chinese labels of the essentials film's round 4.
- `filmkit.narration.flow` measures the heard pause at every word boundary of a take or a soundtrack, by the marks between its words and whether the script switches there. A boundary without a pause mark may hold 0.2 s where Chinese characters and Latin script meet and 0.4 s elsewhere, unless `[narration.flow]` declares other limits; selection and assembly refuse a boundary above its limit and a declared exception that no boundary matches, naming the thought, the two words and the pause, and the audition proposes the most fluent qualifying take. On the current soundtracks of the three films only ETHOS round 8's Chinese 01.4 is refused, for a 0.49 s pause between 的 and Agent; DDWG's soundtracks hold no unmarked pause above 0.11 s.
- `[[narration.terms]]` declares each Latin-script term the narration says, with its `spoken` form, its `ipa` and, for each edition, a `reference` occurrence a person heard correct. The declaration lives in `film.toml`, so adding it changes no recording's fingerprint. Before any narration the readings check refuses a language whose pronunciation contract gives the term another spoken form or none; selection and assembly refuse an occurrence whose first vowel, read from its voiced frames up to 32 % into the word and from up to one 80 ms aligner frame before it but not into the word before, measures F1 above 1.5 times or F2 below 0.85 times the reference's, naming it with both ratios, and the audition prefers a take whose occurrences pass. With ETHOS declared as Eethos, the ETHOS film's committed contract is refused, as its English normalization says `Ethos`, and on its round-8 soundtracks 0 of 20 Chinese and 5 of 22 English occurrences are refused (01.6, 03.1, 03.6, 06.3 and 07.4, at 2.38 to 3.15 times the reference's F1, against at most 1.33 times among the occurrences that pass).
- The concept check carries a Latin-script word's number into Chinese. Where the English counterpart of a Chinese thought uses such a word only in its plural, the Chinese clause that holds it must hold a number word: 们, 些, 多, 几, 各, 每, 众, 两, 俩, 双, 它们, 他们, 一个个, or a numeral other than a lone 一 before its classifier. A `[number]` table in the concept contract adds `words` and the generic uses a film keeps, each an exception of a `thought`, a `term` and a `reason`, and a stale exception is refused. The check refuses the ETHOS film's committed Chinese at 01.4, 03.2, 03.7 and 08.6 and passes DDWG and the essentials film.
- `review.round prompts --dispositions <file>` states under `{dispositions}` one disposition of every finding of the previous round's reviews: fixed with its evidence, declared with the design that keeps it, or deferred with its owner and reason. A round after the first is refused without the file, with a missing or unknown finding, with an entry that lacks its fields or holds others, and with a template that does not cite the field.
- For each assembled edition the listening plan names the unmarked pauses from 0.15 s up to their limits and those kept by an exception, the largest rate, pitch and level steps between adjacent thoughts, and every declared term occurrence with its first vowel.
- The engine renders each edition's player (`filmkit.delivery.player`) in its language: the title and byline, links to the other edition's player and the entry page, the film, a button for each version, which keeps the time, a button for each chapter, the summary, the transcript and the files list. A film declares only each edition's `summary` and the colours of `[player]`.
- Every version's picture draws its captions, as 64 of 64 sampled cues across seven editions of four films show, so the player attaches the edition's WebVTT cues as a hidden metadata track that no control of the page or the browser can show, and whose active cue marks the transcript's current paragraph.
- The player's files list names each delivered file by kind, version, format and size and says of each film that its captions are in the picture. No link opens raw text in a tab: the Markdown transcript, the chapter files and the SRT and WebVTT captions are downloads labelled by kind and purpose, as data URLs that a page opened from disk can save, and the transcript in the page stays the place to read.
- `player-check players` follows every link, reads the track against the SRT and on both versions, clicks every control of the page, reads the browser's own captions control, plays from a transcript time, refuses a link that opens raw text, saves each download and sees that the page stayed, and records a verdict per page in the receipt's `pages`. On the essentials film's players the old pages fail and the engine's pass.

### Changed

- `produce assemble` and `produce refresh-captions` refuse to write over an edition's films while a review round's prompts name them by their hashes and that round has not set them aside, naming the round and the `set-aside` command.
- `review.measurement` records, beside each edition's clarity, its word boundaries by their marks, the rate, pitch and level steps between adjacent thoughts, which it never refuses, and its terms' first vowels.
- The transcript, in the player and in the Markdown file, gives each thought a paragraph and heads each chapter with its start and each section with the start of its voice, as `m:ss`, or `h:mm:ss` past an hour; in the player each time is a button that plays the film from there. Adopting 0.11.0 rebuilds each edition's player and transcript, so a rebuild differs from a release published before it in those files.
- `filmkit.delivery.documents_folder` reads the pages back before rsync changes anything and refuses a page that fails, naming the page and its problems; a dry run reads no player.
- The viewing package records the declared summary and colours and the size of each listed file in place of the player template's hash, and packaging derives it again once the films are in place, since the player names their sizes.
- The concept check reads each edition's `summary` in place of the player page's text.
- The verifier refuses a film any of whose tracks, the chapter track included, carries another language than its edition's.

### Removed

- `<sources>/player.html`: a film that still holds one is refused when its declaration loads and at packaging, naming `editions.<code>.summary` and `[player]`.

## [0.10.0] - 2026-11-06

### Added

- `review.round prompts` writes a film's first production review: `--previous` is optional, and the template field `{previous_review}` cites the previous round's review files and findings, or states that no earlier production review exists. A template that cites `{previous}` and `{findings}` itself keeps working with `--previous` and is refused without it. `{clarity}` states the declared clarity floors. The sample film's prompt cites both.
- `review.round set-aside --unreviewed --consumer <dir>` sets aside a build nobody reviewed, such as a preview the owner watched, in the layout, manifest, move and readback of a reviewed round, bound by the consumer folder's byte-identical copies of each edition's two films and labelled `round-<n>` or by `--label`. Every set-aside takes `--language` for one edition, and `--without-picture` names the editions whose rendered picture stays; named alone it keeps both, as before.
- `review.measurement` records each edition's voice clarity, the median cepstral peak prominence over the loud frames of its soundtrack and of each segment's voice, computed as the reviewers' prompts state it, each value to 0.01 dB beside the floor a film declares for the edition in `[review] clarity_minimum_db`. On the six current soundtracks of the three films it keeps the reviewers' tool's frames and its medians, 17.35 to 19.64 dB, within 4e-15 dB. The sample film declares 18 and 17 dB.
- `check-picture` refuses an opening whose frames before the first word show the title the script declares for less than 1 s, in texts at 3:1 or more, and each run of 0.7 s or more in which a text holding a letter or a digit shows below 4.5:1 against the ground, its colour composited at its opacity. The frame audit writes a trace of every text of every frame, whatever its role, for both measures (`TEXTS`). On the current compositions of DDWG, ETHOS v2 and the essentials film both measures pass both editions, each opening on its title for 2.40–4.00 s; the ETHOS composition that lost its title signature (`28a177a`) shows none, and the DDWG composition before its legibility repair holds 143 Chinese and 145 English texts at rest below 4.5:1, among them every dimmed level its round-30 review measured.
- `produce preflight` reports at once every stale or missing input of an edition's render, by the owner that would refuse it later, and refuses while one remains: a stage that is not the current UHD picture, a tracked cover other than the one the stage paints, an earlier film package record, a draft still scan that is missing, failing or bound to another timeline or composition, a failing concept check, and a picture gate record that has not passed on the current inputs.

### Changed

- The still scan records the composition it judged beside the film and the timeline, and with `--language` judges the edition's draft against its timeline into `build/evidence/editions/<edition>/draft-stills.json`, which the pre-render check reads. A film's draft tooling moves to it; a record written by 0.9.0 binds no composition and is reported as stale.
- `filmkit.review.round` keeps its command and options; its prompts move to `filmkit.review.prompts`, its set-aside to `filmkit.review.set_aside` and the files every step reads to `filmkit.review.files`, so a script that imported them from `filmkit.review.round` imports them from their owners.
- The audition proposes a take that opens its recording when the assembly would begin its clip in quiet (`clip_opens_quiet`), in the take's own heard quiet or in its released onset, and records whether its onset is releasable (`onset_releasable`) beside the raw level of its first 10 ms (`first_dbfs`, `opens_quiet`). It formerly required those 10 ms to be heard as quiet, which refused takes the assembly accepts.

### Fixed

- The assembly releases a take's codec onset that would sound out of digital silence. At a thought join, sound of at most 0.1 s between digital silence after the thought's last word and the join's native quiet is released, and so is the sound a join's digital silence is left into where it ends the native quiet, when that sound meets heard quiet within 0.1 s and before the next word; the silence leaves into that quiet through a soft fade. A recording that offers its clip no heard quiet before its first word begins the clip in its onset released the same way, when that onset meets heard quiet within 0.1 s and by the first aligned word. Each designed thought pause and each clip's boundary fades record `released_onset_samples`. On the ETHOS film's round-6 Chinese inputs exactly three joins change: its two thumps at 03.6>03.7 and 08.8>08.9 (693 and 293 samples) and a burst at 05.1>05.2 that the review's 5 ms edge window does not reach (960 samples); the review's quiet edges leave no digital silence above −45 dBFS where they left two, the runtime stays 900 s, the timeline is unchanged and every other sample is identical.

## [0.9.0] - 2026-11-04

### Added

- `check-picture` gates the sync audit's continuity. It refuses each seat, a mark that stands in speech for more than 0.6 s before a name is legible at it, and each run of a thought's speech longer than 1 s with no legible name, naming each with its thought and time. It lists each thought that keeps the previous picture for more than 1 s in the gate record without refusing it, since a deliberate index may stay while the first new name arrives.
- The seat check judges a dashed closed outline on its own where a link or a touch joins it to a larger mark: only a name within its reach, or a mark or text inside it, names it. The canvas stand-in records whether each stroke is dashed. The dashed box at the end of the link in ETHOS v2's 09.1, which stood 5–6 s before its seal and name, was judged with the card and the Agent the link joins, a mark that counted as named in every frame because its box held the Agent's inner dot.
- The sync audit lists the caption cues that labels repeat. `check-picture` refuses a cue of three or more words that one label legible during the cue holds exactly, in order, and records a cue at least 80% of whose words labels drawn during it repeat, and a cue that is itself one quotation, since the narration then reads out what the picture shows. The frame audit's `caption_echoes`, never gated, is retired.
- The frame audit reports `mixed_case`, the names of one set or of one row of one size, anywhere across the frame, that begin in both cases, and `check-picture` refuses it. A name counts once by its whole text; a CJK name, a quotation and a name whose first word holds a later capital are not judged. The frame audit reads a name's whole text, set and role from the record a composition publishes with each text.
- Packaging writes the edition's language into each film's chapter track in place, because FFmpeg tags that track English in every edition, and refuses a film any of whose tracks, the attached cover aside, carries another language.
- The concept check reads each edition's release synopsis, comment and description and the text its player page shows outside its scripts and styles, and refuses a counterexample there as in the narration.

### Changed

- A frame counts as named by what it holds only through a text, a named mark or, once it holds a mark, a name within its reach, so a pictogram drawn in a tool's frame no longer names the frame.
- The transcript's title and headings, `chapters.json`, the chapter metadata and the films' title, comment, description and synopsis tags set quotation marks as the captions do. On the current inputs of DDWG, ETHOS v2 and the essentials film, only ETHOS v2's English edition changes: the part title “Done” in the transcript and the player's transcript, the chapter title One requirement’s life in the transcript, the player's transcript and chapters, `chapters.json` and the chapter metadata, the part title of the same name in both transcripts, and the quotes of the synopsis tag. Each film's Chinese films change one more thing: their chapter track's language, English until now.
- The sample film tags each card with its kind of file or its step until the narration names it, so no card waits empty for its name.
- On the ETHOS v2 composition its round-4 review judged, the new gates refuse 11 seats in each edition, the English unnamed speech of 03.7 and 11 English runs of mixed case in 07–09, and record two held pictures in each edition and 41 Chinese and 23 English cues mostly drawn as labels, among them the three English cues that review named. Its seat repair leaves the dashed stand-in of 09.1 and the two tool frames of 03.6 in each edition, which the repair did not address. The concept check refuses the Chinese player of `411dd65^` for 模型提升 and passes every film's current inputs.
- The supply moves to ETHOS 0.2.0-alpha.29 and uv 0.13.7, and the CI projection to `jdx/mise-action` 5.2.6.

## [0.8.1] - 2026-11-04

### Fixed

- A Chinese caption line keeps the closing quotes and brackets that follow its last mark, as an English one already does, so no cue begins with one: in 。” the quote ends the line that 。 ends. A brief cue that ends in such a mark takes the same early start as one that ends at the mark, and a passage that ends in a closing quote no longer leaves the quote alone as a line its timing cannot place. A passage without such a mark is set as before.
- The display copy of cues, subtitles and transcripts sets each straight double quote as a typographic one: an opening quote at the start of the text or after a space, an opening bracket or a dash, and a closing quote elsewhere. A cue's text, its timing and the waveform do not change. A film refreshes its captions with `produce refresh-captions` to take both. On the current timelines this moves three closing quotes in the Chinese captions of ETHOS v2 and one in those of the essentials film, sets the quotes of twelve and four of their English cues, and changes no DDWG cue and no cue's timing.

## [0.8.0] - 2026-11-04

### Added

- The headless audits measure text with the film's own fonts. `filmkit.picture.metrics` reads each `@font-face` rule of `picture/film.css` whose source is one of the film's `picture.fonts` and records the advance width of every character each face maps, and the canvas stand-in measures a text as the sum of its characters' advances at its size plus its letter spacing. `check-picture` names the table to the frame and motion audits in `FILMKIT_TEXT_METRICS`, and `python -m filmkit.tools frame-audit` and `motion-audit` name it when the caller names none. A family the stylesheet does not declare and a character its face does not map keep the estimate, and every text's height keeps it.
- The frame audit measures balance as the reviews since DDWG round 29 do, in every frame it exercises: the box of every paint brighter than grey 60 at full size within rows 120–919, and its horizontal offset from x 960. `off_centre_builds` reports each run of 1.5 s or more in which the box stands more than 90 px off, and `off_centre_settled` each run of 2 s or more in which it stands more than 50 px off while its edges keep still, unless the picture then grows from it.

### Changed

- `check-picture` refuses `off_centre_builds`, and lists `off_centre_settled` in the gate record without refusing it, because whether a still state is a finished composition or a build-up held for its next part only the stage's intent tells.
- `check-picture` refuses `uneven_pitch` and `touching_marks` too. Measured with the film's widths, they report nothing on the repaired DDWG and ETHOS v2 compositions, and on the DDWG composition its third re-check judged they keep the touches the drafts showed real and drop the ones they showed clear.
- The gate record binds the SHA-256 of `picture/film.css` and of each declared font, and `render-picture` refuses a record measured with other fonts.
- The measures that already read text extents, such as the round-16 cover runs, read the film's widths too, so a film that passed 0.7.0 can be refused by this release before its next render.
- The engine renders with HyperFrames 0.9.9. The browser build stays Chrome Headless Shell 152.0.7977.30, and `package.json` keeps its `undici` override, because 0.9.9 still declares that build and pins `undici` 7.25.0. A new renderer can change the frames a film renders, so a film keeps its current filmkit pin until it produces, reviews and accepts an edition on a release that carries this one.
- The locks hold the newest releases their declared ranges admit; apart from HyperFrames, neither lock moves. OSV reports no advisory for any package either lock pins.

## [0.7.0] - 2026-11-04

### Added

- The frame audit measures how text lines up, from the exact anchors, sizes and baselines of each voiced frame's settled names and marks. `ragged_rows` reports names of one size side by side on baselines more than 3.5 px apart; `ragged_columns` reports the lines of a block or the items of a column off their shared edge or axis; `crammed_lines` reports stacked lines with less than 7 px between their inks; `off_card_centre` reports a name alone in a small card off its centre; `uneven_pitch` reports like marks at uneven pitch under names at equal gaps; and `touching_marks` reports a name within 3 px of a mark's stroke. Each lasts 1 s or more and is reported per scene with its span, texts and offsets.

### Changed

- `check-picture` refuses `ragged_rows`, `ragged_columns`, `crammed_lines` and `off_card_centre`, and records `uneven_pitch` and `touching_marks` in the gate record without refusing them, because they rest on the headless estimate of Latin text widths.
- The sample film's closing checklist stands left-aligned beside its checks, and its review floors are 95, as the owner set for every film on 2026-11-03.
- The engine renders with HyperFrames 0.9.8. The browser build stays Chrome Headless Shell 152.0.7977.30, and `package.json` keeps its `undici` override, because 0.9.8 still declares that build and pins `undici` 7.25.0. A new renderer can change the frames a film renders, so a film keeps its current filmkit pin until it produces, reviews and accepts an edition on a release that carries this one.
- The locks hold the newest releases their declared ranges admit; apart from HyperFrames, neither lock moves. OSV reports no advisory for any package either lock pins.

### Fixed

- An editable install is rebuilt when `VERSION` changes, so the gate records of a bumped engine name the version that ran: `pyproject.toml` declares `tool.uv.cache-keys` for itself and `VERSION`.

## [0.6.0] - 2026-11-03

### Added

- `python -m filmkit.produce check-picture --language zh|en` runs the frame, sync and motion audits of an edition's current composition and timeline. It writes `build/evidence/editions/<edition>/picture-gates.json`, which binds the composition, the timeline and the engine version and lists every gated finding, and refuses while one remains.
- The frame audit follows the lit picture through all speech. `off_centre_runs` and `thin_runs` report each run of 2 s or more of one scene's speech in which the picture stands more than 12% off the content centre or covers less than a tenth of the content band, with its start, end and worst value; both are gated.

### Changed

- `render-picture` refuses an edition without a passing gate record for its current composition, timeline and engine version. A film's picture task runs `check-picture` before each render, as the sample film's now does.
- The sample film's composition is reworked to pass the gate: each scene stands centred from its first word, names each thing on its words and changes within 3.5 s.
- A thought retake that `filmkit.narration.audition apply` binds records `spoken_sha256`, the SHA-256 of the spoken text its audition narrated. Binding refuses a proposal without spoken text or with speech its thought no longer says, and narration refuses a retake whose thought now speaks other text, naming the thought. A retake bound before 0.6.0 keeps its text-only binding.
- A review round refuses to write prompts for a film that declares a concept contract unless its reviewer prompt cites `{concepts}` and `{readings}` and its dimensions include `concept_fidelity`, and names each omission. The sample film scores concept fidelity.
- The engine renders with HyperFrames 0.9.6. The browser build stays Chrome Headless Shell 152.0.7977.30, and `package.json` keeps its `undici` override, because 0.9.6 still declares that build and pins `undici` 7.25.0. A new renderer can change the frames a film renders, so a film keeps its current filmkit pin until it produces, reviews and accepts an edition on a release that carries this one.
- The locks hold the newest releases their declared ranges admit; apart from HyperFrames, neither lock moves. OSV reports no advisory for any package either lock pins.

## [0.5.0] - 2026-11-03

### Added

- The README's "Whole endings" section explains why in-context takes from mlx-audio 0.6.4 can end inside their last syllable, how `filmkit.narration.audition` keeps their endings whole, and the upstream fix, Blaizzy/mlx-audio#1116. The command table lists `filmkit.narration.audition`.

### Changed

- The repository runs ETHOS 0.2.0-alpha.28.
- The engine renders with HyperFrames 0.9.5. The browser build stays Chrome Headless Shell 152.0.7977.30, and `package.json` keeps its `undici` override, because 0.9.5 still declares that build and pins `undici` 7.25.0. A new renderer can change the frames a film renders, so a film keeps its current filmkit pin until it produces, reviews and accepts an edition on a release that carries this one.
- The speech engine is mlx-audio 0.6.4. Its in-context path without streaming narrates the same takes as 0.6.3 from the same seeds, so a film that moves to it keeps its accepted takes.
- The locks hold the newest releases their declared ranges admit: `filelock` 4.2.7 in `uv.lock` and `semver` 7.8.6 in `package-lock.json`. OSV reports no advisory for any package either lock pins.

### Fixed

- The reviewer prompt names a coda, an inner pause cap or a thought boundary ratio that a script does not declare as "none declared", instead of raising `KeyError`.

## [0.4.0] - 2026-11-02

### Changed

- The repository runs ETHOS 0.2.0-alpha.27, and its CI workflow uses `jdx/mise-action` 5.2.5.
- The engine renders with HyperFrames 0.9.3. The browser build stays Chrome Headless Shell 152.0.7977.30, and `package.json` keeps its `undici` override, because 0.9.3 still pins 7.25.0. A new renderer can change the frames a film renders, so a film keeps its current filmkit pin until it produces, reviews and accepts an edition on a release that carries this one.
- The locks hold the newest releases their declared ranges admit: anyio 4.16.0 in `uv.lock`, and @hono/node-server 2.1.6, ansi-regex 6.5.0, hono 4.13.16, nanoid 3.3.20, postcss 8.5.32, tslib 2.9.1 and ws 8.22.1 in `package-lock.json`. OSV reports no advisory for any package either lock pins.

## [0.3.0] - 2026-11-02

### Added

- A concept contract: `concepts` in the declaration names a TOML file that states what each concept a film names means in its pinned source, quoting the passage, and which words each edition uses for it. `python -m filmkit.concepts` checks that each segment says the concepts it declares, the same in both editions, by their approved words; that no counterexample appears in the narration, titles, caption terms or picture sources; and, with a source clone, that each quotation is in its document at the pinned commit.
- A readings check for pronunciation contracts of schema version 2: every Chinese character on the engine's watch list must have a declared reading wherever the narration says it, each declared reading must be a dictionary reading, or in the neutral tone after a word's first character, and a reading the dictionary contradicts in context needs a recorded reason. Every name in either edition needs a declared spoken form. `python -m filmkit.narration.readings` writes each edition's occurrence plan for review, and with `--propose` the dictionary's word and reading for each occurrence nothing declares yet. The dictionary is `pypinyin` 0.55.0, a new dependency.
- The reviewer prompt context names the concept contract as `concepts` and the occurrence plans as `readings`.

### Changed

- Narration runs the concept and readings checks before any speech model loads, including a dry run, and refuses on either. A film that declares no concept contract and keeps a version 1 pronunciation contract narrates as before.

## [0.2.0] - 2026-11-01

### Added

- `CONTRIBUTING.md`: how to prepare the tools, change the engine in an ETHOS Work Lane, verify a change, commit, and cut and publish a release.

### Changed

- **Breaking:** the assembly refuses an edition whose bound thought take ends abruptly, naming every such thought, unless the film declares a release for that thought's join in `released_tail_seconds`. It judges each take by the criterion that auditions and the review already use. Before, it faded such a take over 60 ms where the silence after it began, which hid the cut but swallowed the last syllable. A film whose takes all end naturally assembles the same soundtrack as before.
- The repository runs ETHOS 0.2.0-alpha.25, whose 500-line ceiling bounds JavaScript too. The frame rules and the reviewers' measures that the geometry check and the frame audit share now live in `src/filmkit/picture/rules/`, each audit keeps its entry and holds its parts in a folder of its name, and the picture tests are split by subject. The tools keep their names, invocations and output.
- The engine renders with HyperFrames 0.8.225 and narrates with mlx-audio 0.6.3 and MLX 0.32.4, drives the browser with puppeteer-core 25.16.0 and @puppeteer/browsers 3.2.6, and builds with Node 26.13.0, uv 0.13.6 and Pydantic 2.14.2. The browser build stays Chrome Headless Shell 152.0.7977.30. A new renderer and speech engine change the frames and narration a film renders, so a film keeps its current filmkit pin until it produces, narrates, reviews and accepts an edition on this engine; moving that pin is not a routine update.

### Fixed

- The review's measure of delivered endings takes each thought's stop at the first digital silence after its last word begins, not after the word's aligned end, which the aligner can place after the voice has stopped, and judges a released thought on the 20 ms before the samples the assembly released. It had counted thoughts whose voice was cut and then faded as natural endings.
- A thought that ends in Latin text without a space, such as an English thought that ends its segment, is auditioned as a run-on that reads into the next thought after a word space, so the two thoughts' words stay apart.

### Security

- `package.json` overrides `undici` to 7.30.1. HyperFrames 0.8.225 pins 7.25.0, which 29 advisories affect, among them TLS certificate validation bypasses (GHSA-vmh5-mc38-953g, GHSA-w293-vg96-wgc3). The new browser driver also moves `zod` from 3.25.76 to 4.6.7, outside GHSA-mrhx-c7xc-m3w5.

## [0.1.1] - 2026-10-31

### Fixed

- A new film can name its covers before it paints them: the declaration loads without them, packaging refuses an edition whose cover is missing and names its field, and the cover check writes a painting that has no tracked cover yet and reports it as uncompared.

## [0.1.0] - 2026-10-30

### Added

- The engine that rebuilt the DDWG introduction films, from [ddwg-film](https://github.com/HengYangDS/ddwg-film) at `37549a9`: narration with a local speech model, soundtrack assembly, captions, picture staging and rendering with HyperFrames 0.8.150, packaging, verification, delivery and independent review rounds.
- The engine finds the film it builds from `FILMKIT_ROOT` or the working directory, and its npm packages in the nearest `node_modules`. It takes every film-specific value from `content/film.toml` and the files it names, now including the fonts the picture stages and the listening plan's readings, and each script names its pronunciation contract.
- `python -m filmkit.tools` runs the Node tools from a copy below the film with the film's npm packages. Staging, rendering and every tool refuse a renderer other than HyperFrames 0.8.150.
- A one-minute bilingual sample film that the tests load and the `sample:` Mise tasks build end to end.
- ETHOS governance, with the portable proof projected into GitHub Actions and GitLab CI.
- The MIT License for the code, with the sample film's recordings and fonts and the third-party software in `NOTICE`.

[Unreleased]: https://github.com/HengYangDS/filmkit/compare/v0.10.0...HEAD
[0.10.0]: https://github.com/HengYangDS/filmkit/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/HengYangDS/filmkit/compare/v0.8.1...v0.9.0
[0.8.1]: https://github.com/HengYangDS/filmkit/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/HengYangDS/filmkit/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/HengYangDS/filmkit/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/HengYangDS/filmkit/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/HengYangDS/filmkit/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/HengYangDS/filmkit/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/HengYangDS/filmkit/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/HengYangDS/filmkit/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/HengYangDS/filmkit/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/HengYangDS/filmkit/releases/tag/v0.1.0
