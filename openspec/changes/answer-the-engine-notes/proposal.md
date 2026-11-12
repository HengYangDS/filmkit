## Why

The three films' latest reviews left notes whose owner is the engine; each film can close them only by adopting a release that fixes them.

- **Spotlight keywords.** Packaging writes the QuickTime keywords joined by ", ". Spotlight's importer splits that string at the commas and keeps each following space, so five of six keywords import with a leading space (ETHOS zh-R16-07, DDWG Z36-11). A test on 2026-11-12 found that "," with no space keeps every Chinese phrase whole with no leading space. No encoding kept an English phrase whole: the importer splits mostly-Latin strings at every space (essentials EN13-n6).
- **Player links.** Each player links its four films and its cover as plain `<a class="file">`, so a click replaces the player with the browser's view of the file (DDWG Z36-10).
- **English caption pace.** English cues are cut at phrase boundaries and timed to their words, and nothing bounds their reading rate. ETHOS has 5 cues above 25 characters per second (25.0 to 28.6), DDWG has 4 and essentials has 2 (ETHOS EN-R16-02, EN-R13-02).
- **Sync audit and inflected labels.** The sync audit judges a label by the nearest exact occurrence of its words. An English label whose words are said in another form in its own thought, such as "Availability" over "available", is matched to a later exact occurrence more than 8 s away and stays unjudged (essentials EN13-n5). It also judges each label only at its first legible frame in its scene, so a label shown again on its words later in the scene is never judged: the essentials 06.6 "Acceptance" first stood in 06.3 (EN13-n15, EN13-n14, ZH13-n2).
- **Held off-centre states.** The frame audit leaves out a still state off centre when the next frame grows from it. The reviewers count such a state at their 50 px for 2 s. On 2026-11-12 the essentials English 03.7 agenda stood −57 px for 2.4 s and 06.6's first pair +54 px for 2.4 s (EN13-n10, EN13-n15). A whole-film probe then found the Chinese 07.1 at −71 px and 08.2 at +61 px, each for 2.3–2.4 s. `check-picture` passed all four. It records still states that end within their stage without refusing them, and the reviewers count those too: DDWG's English 06 holds −72 px for 2.4 s and +61 px for 3.7 s on its current build.
- **A stroke that gains a piece whole.** The motion audit follows a stroke as one mark, so a piece the stroke gains whole within one frame while its other pieces stand never counts as a pop. DDWG's round-37 25.2 carries three lines in one stroke whose ink ramps on its first line only. The second, third and fourth lines each appear whole in one frame, and `check-picture` recorded no pop (DDWG Z37-1).

## What Changes

- Packaging writes the QuickTime keywords joined by "," with no space. Where the host has `mdimport`, film verification reads each film's imported keywords back. It refuses a film whose keywords include an entry with a leading or trailing space, or whose Chinese phrase does not import whole. In English, the importer's split into words is recorded as its behaviour, not refused.
- Each player link to a film or a cover opens in a new tab (`target="_blank" rel="noopener"`). The browser readback clicks every such link and requires the player to stay at its own address while a new tab opens the file.
- An English caption cue read faster than 25 characters per second is joined to a neighbour or held. The join takes a neighbour in the same segment with no sentence end between them, under 0.25 s of quiet and within the 66-character line, as a brief cue is joined. A cue that cannot join holds into the quiet after it, up to the time that brings it to 25 characters per second and never past the next cue's start. Chinese cues are unchanged.
- When no exact occurrence of an English label's words starts within 8 s of its first legible frame, the sync audit judges the label by the occurrence of its words with the same English Snowball stems in the thought spoken at that frame. It judges such a label `inflected`, with the same verdicts. Chinese labels are unchanged.
- The sync audit judges each appearance of a label, a run of legible frames after at least 1 s illegible in its scene, against the nearest occurrence of its words within 8 s that no earlier appearance was judged by. An appearance without one is recorded as a recall.
- The frame audit reports as held a still state off centre that the next frame grows from: more than 50 px off for 2 s or more, its edges steady within 4 px. `check-picture` refuses held, settled and finished still states alike, so the gate measures every still state as the reviewers do.
- The motion audit follows the drawn pieces of each mark it follows. Outside a stage cut, a piece that the mark gains or loses whole within one frame, at ink 60 or more and 12 px or more across, pops, and `check-picture` refuses it.

No film's soundtrack changes. The films' metadata changes (the keywords value), and so do the pages (the link attributes). An English edition whose cues join changes its captions, its timeline's captions and its captioned pictures; such a cue holds for longer and keeps its words. A film whose picture holds such a state off centre, or whose stroke gains a piece whole, now fails `check-picture` until its picture is repaired.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `film-package`: whole keywords read back where the host can, and file links that open beside the player.
- `caption-text`: English cues held to a reading rate.
- `picture-gates`: the sync audit judges inflected English labels and each appearance of a label, and the gate refuses every still state off centre that the reviewers count.
- `picture-motion`: a followed mark pops by a piece it gains or loses whole.

## Impact

- **Source:**
  - `src/filmkit/delivery/packaging.py` (the keywords value), `src/filmkit/delivery/verification.py` (the `mdimport` readback) and a new `src/filmkit/delivery/spotlight.py`.
  - `src/filmkit/delivery/player.py` (link attributes) and `src/filmkit/delivery/player-read.mjs` (the click readback).
  - `src/filmkit/captions/timing.py` (the reading-rate join and hold).
  - `src/filmkit/picture/sync_audit.py` (inflected matches and appearances) and `src/filmkit/picture/rules/balance.mjs` (held runs).
  - `src/filmkit/picture/frame-audit/report.mjs` and `src/filmkit/picture/gates.py` (the gated kinds).
  - `src/filmkit/picture/motion-audit/follow.mjs` (the pieces a followed mark gains or loses).
  - The tests of each.
- **Dependency:** `snowballstemmer` (BSD-3-Clause), a pure-Python implementation of the Snowball stemmers, pinned in `pyproject.toml` and `uv.lock`.
- **Release files:** `README.md`, `CHANGELOG.md` and `VERSION` 0.21.0.
- **Adoption:** each film adopts the release at its next edition. All three package again for the keywords and pages. ETHOS's and DDWG's English editions, and essentials' English edition, refresh their captions and render their captioned pictures again where cues join. A picture that the balance or motion gate refuses is repaired first: DDWG's English 06 on its current build, and its 25.2 on the round-37 build.
- **Out of scope:**
  - Typesetting the timeline's text fields (DDWG EN36-9).
  - Counting English syllables by sound (essentials EN13-n12).
  - Calibrating the level steps between thoughts against listening (ETHOS zh-R16-02, DDWG Z36-6).
  - The supply refresh of HyperFrames and mlx-audio, which re-narrates every take.

  Each of these needs a listening calibration or changes narration bindings, so a later release carries it.
