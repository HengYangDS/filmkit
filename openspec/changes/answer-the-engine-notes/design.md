## Context

filmkit 0.20.0 carries the production steps every film needs. The films' latest reviews, ETHOS round 16, DDWG round 36 and essentials round 13, left notes that name filmkit as their owner. This change answers the ones an engine change can close without a listening calibration and without new narration. The films adopt it at their next editions.

Evidence for each item is under `build/evidence/answer-the-engine-notes/`:

- the Spotlight importer test of 2026-11-12;
- the three films' English cue rates;
- essentials' whole-film balance probe of 2026-11-12;
- the reviewers' observations, quoted from each film's notes backlog.

## Goals / Non-Goals

**Goals:**

- Keywords that Spotlight imports without stray spaces and with Chinese phrases whole, checked where the host can check them.
- Players whose film and cover links never replace the player.
- English captions read at 25 characters per second or less wherever a join or a hold allows it.
- A sync audit that judges a label by its inflected words in its own thought, rather than leaving it unjudged.
- A balance gate that counts every still state off centre that the reviewers count.
- A motion audit that sees a piece a stroke gains or loses whole.

**Non-Goals:**

- Keeping English keyword phrases whole. No QuickTime encoding the importer reads does that (the 2026-11-12 test).
- Typesetting the timeline's text fields, which feed the narration's bindings.
- A syllable rate by sound.
- Level-step calibration.
- The HyperFrames and mlx-audio refresh.

## Decisions

### Keywords: "," without a space, read back with `mdimport`

The importer chooses how to split the string from its dominant script:

- A mostly-CJK string is split only at commas, and the importer keeps the space after each comma.
- A mostly-Latin string is split at commas and at every space.

Joining with "," and no space is the only encoding tested that keeps Chinese phrases whole and leaves no stray space. Alternatives tried on 2026-11-12, none of which kept an English phrase whole:

- ";" as the separator;
- a no-break space inside the phrase;
- hyphens;
- a single-keyword value;
- ExifTool `+=` lists;
- the XMP and item-list keyword tags, which produced no `kMDItemKeywords` at all.

The verifier reads the result back because the importer, not the file, decides what a viewer finds. Where `mdimport` is absent (Linux CI), the readback is recorded as unavailable rather than failing. A new module, `delivery/spotlight.py`, owns the import and the parse. `mdimport -t -d2` prints an old-style property list, and the module parses its `kMDItemKeywords` and `kMDItemAuthors` arrays, unescaping `\Uxxxx`.

The same readback checks the authors. A film that carried the author in both its author and artist keys imported the author twice, and Finder showed "Yang HENG (2)" until a user saw it (2026-11-09). The verifier now refuses any authors other than the declared author, once. An importer that reads no keywords at all is refused like a split phrase, since the readback could not then show the keywords whole.

### Player links: a new tab, proved by clicking

`target="_blank" rel="noopener"` keeps the page and its playback. The alternative, `download`, would save gigabytes on a click; the player promises no film download. The readback already opens each page in Chromium through puppeteer-core. It now clicks each film and cover link, waits for the new page, checks that page's address names the linked file, closes it, and checks the player's address is unchanged.

### Caption pace: the brief-cue rule, extended

`steady_short_cues` already joins a cue shown under 1 s to a neighbour under the same conditions, or holds it into the quiet after it. A cue read faster than 25 characters per second is treated the same way, with a rate in place of the duration:

- it may join when the joined text fits the limit;
- otherwise it holds until it reads at 25 characters per second;
- it never holds past the next cue's start.

The rate counts the shown text's characters, spaces included, over its interval: the measure the reviewers used, which gave "The inference is that the vendor" 28.6 characters per second. The rule applies to English only. The reviewers' notes concern English, and a Chinese limit would need its own reading-rate basis.

On the three films' current English timelines no fast cue can join or hold: each join would pass 66 characters or a sentence end, and contiguous English cues leave no quiet to hold into. Such a cue reads fast because the voice says its words fast, so a caption rule cannot slow it without parting the caption from its words. The caption record lists it with its rate, and the film answers it in the narration, with a calmer take of its thought.

Joining changes the cue list, so an English edition that adopts the release refreshes its captions and renders its captioned picture again. Every joined or held cue keeps its words and its start, so the caption equivalence and the cue-word checks hold.

### Inflected labels: Snowball stems within the label's thought

The audit already indexes each scene's spoken words with their times and clause starts. When a label's exact words are not said within 8 s, the audit now stems both the label's words and the thought's words with the English Snowball stemmer, then looks for the label's stems in order. The window is the thought spoken at the label's first legible frame, or the next thought if that frame falls between thoughts.

Snowball is a published, maintained algorithm. It maps "availability" and "available" to "avail" while keeping "public" and "publish" apart; a shared-prefix rule would have joined those. Restricting the search to the label's own thought keeps a stem match from reaching a different mention of the word. The `snowballstemmer` package is pure Python, BSD-3-Clause and has no dependencies.

### Appearances: runs of legible frames, each judged once

`legible_labels` keeps one time per label and scene, the first frame it is legible, so a label the picture shows again on its words later in the scene is never judged. The audit now keeps each run of legible frames that begins after at least 1 s in which the label stood illegible in its scene. A stage cut fades a kept label for 0.18 s in the films that declare their cuts, so a label kept across a cut stays one appearance; a label taken away and brought back on its words is two.

Each appearance takes the nearest occurrence of its words within 8 s that an earlier appearance has not taken, so two appearances are never judged against one utterance. An appearance with no such occurrence shows a named thing again without its words, as a recap does; the audit records it as a recall and judges nothing, as it lists a label far from its words today.

### Balance: held runs reported and every still run gated

`reviewedRuns` drops a still run when the next frame grows from it, so a build held still while its next part waits leaves no trace. That is the state the reviewers counted in essentials 03.7 and 06.6. The change keeps such a run as `held` instead of dropping it. `check-picture` refuses `off_centre_held` and `off_centre_settled` alongside `off_centre_builds` and `off_centre_finished`.

The earlier design recorded settled runs without refusing them, because only a stage's intent tells a settled composition from a paused build. The reviewers do not draw that line: they count any still state 50 px off for 2 s. Every film's picture also has a native repair: glide the picture as one on the word that widens it, or stand midway between its lasting states. The essentials repair `f0e7924` uses both.

### Pieces: a followed mark pops by what it gains whole

The follower already records each mark's drawn pieces, one per subpath, and uses them to tell a mark that grows or turns from one that travels. A mark that appears or vanishes pops by the pieces no like mark holds. A mark it follows is never checked again, so one stroke that draws several lines can gain a line whole in one frame and report nothing: the DDWG 25.2 pattern.

The follower now pairs the pieces of each followed pair, in `motion-audit/pieces.mjs`:

- an open piece with the piece drawn from the same first point, or ending at the same last point;
- a closed piece with the one at the same centre;
- each under whichever shift pairs the most pieces: the pair's motion, the pieces' own shift in order, or none.

A piece left unpaired may still continue a leftover piece of the other frame that moves as a mark of its own, as a balance pan, a gate bar or a ruler's tick does inside one stroke; this second pass waives the follower's small-mark rule, so an arc grown from a 5 px seed continues. A piece left unpaired after both, at the mark's ink of 60 or more and 12 px or more across, pops, as an appearing mark's pieces do today.

The strict pairing by first point and centre alone misfired on every film. ETHOS 03's path split at a station's gap, DDWG 17's stamp arc grew from its seed, and span and ruler ticks slid inside their strokes; each refinement has a test. Measured at 30 fps on the six editions, the rule adds exactly the six DDWG 25.2 lines (three in each edition, `film.js:8198`) and changes no other finding. One case stays unseen: a piece removed and another drawn near it in the same frame reads as one piece that moved.

A dash pattern opening or shutting stays the dash-snap audit's, since dashes are not subpaths.

## Risks / Trade-offs

- **[Gating settled and held runs refuses current pictures.]** DDWG's English 06 holds two settled runs (−72 px for 2.4 s, +61 px for 3.7 s). Mitigation: the films adopt the release at their next editions, which repair those stages before rendering; the refusal names each run's span and offset.
- **[`mdimport` behaviour differs between macOS releases.]** Mitigation: the readback refuses only a stray space and a split Chinese phrase. It records everything else, and records "unavailable" where `mdimport` is absent.
- **[A stem match in a long thought could pick the wrong mention.]** Mitigation: the search is ordered and nearest-first within one thought; a match is recorded as inflected, so a reviewer can see it.
- **[A new dependency.]** Mitigation: a pure-Python package pinned by version and hash in `uv.lock`, under a permissive licence, loaded only by the sync audit.
- **[Piece pops refuse pictures that passed.]** A composition that draws several pieces in one stroke and lets one appear whole now fails, as DDWG's 25.2 does on its round-37 build. Mitigation: the pop names the drawing line, and the repair is native: give each piece its own ink ramp or draw it on its words.

## Migration Plan

Release 0.21.0. Each film's next edition:

1. Pins the tag.
2. Refreshes the English captions where cues join.
3. Repairs any still state or piece pop the gate refuses.
4. Renders the captioned pictures again where captions changed, and packages both editions.
5. Reads back the keywords and links.

Rollback: pin 0.20.0, whose outputs the films' current deliveries hold.

## Open Questions

None. The excluded notes stay open in each film's backlog with this change named as not their owner.
