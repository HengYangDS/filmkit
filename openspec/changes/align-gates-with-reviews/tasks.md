# Tasks

## 1. Wrapped labels

- [x] 1.1 Group each frame's layout records into wrapped labels and judge them at rest by the declared rules in `picture/frame-audit/typography/`. Done when typography tests refuse an English line ending on a lead word, a one-word last line in a three-word name, a short block line and a short last line among lines of one size, and a Chinese line opening on closing punctuation, and spare a name over its smaller gloss, a label below 0.9 opacity and a repeated name standing in two places.
- [x] 1.2 Declare `[picture.wrapping]` (`line_share`, `last_share`, `lead_words`, `exceptions`) in `film.py` and gate wrapping findings in `check-picture`. Done when declaration tests refuse a share outside (0, 1], an exception without a reason and a stale exception, and gate tests record a declared exception and refuse an undeclared break by name.
- [x] 1.3 Compare the audit's lines with a real-browser readback of every wrapped label on the current builds of the three films. Done when both readings give the same lines for every label, recorded under `build/evidence/acceptance/`.

## 2. Narration flow

- [x] 2.1 Measure the heard pause at every word boundary, with its marks and script switch, in a new `narration/flow.py`, and record it in `review.measurement`. Done when tests on synthetic speech measure a 490 ms pause at a switch, a comma pause and no pause inside a word, and map hyphenated and apostrophised words to their marks.
- [x] 2.2 Refuse an unmarked pause above its limit at selection and assembly, with `[narration.flow]` limits and exceptions in `film.py`, and rank candidates by it in the audition. Done when tests refuse a 0.49 s switch pause, pass a 0.36 s unmarked clause pause under the default limits, record a declared exception, refuse a stale one, and propose the fluent take of two.
- [x] 2.3 Record rate, pitch and level steps between adjacent thoughts of a part in the measurement, and list the largest steps and the unmarked pauses from 0.15 s to their limits in the listening plan. Done when tests on synthetic thoughts measure a doubled rate, a 3-semitone step and a 2 dB step, and the plan lists them.

## 3. Term pronunciation

- [x] 3.1 Declare `[[narration.terms]]` (term, spoken form, IPA, reference occurrence per edition) in `film.py`, outside the pronunciation contract, and measure each occurrence's first-vowel formants in a module that `narration/readings.py` calls. Done when tests on synthetic vowels separate /iː/ from /ɛ/, refuse a stale reference, and show that adding a declaration leaves every recording's fingerprint unchanged.
- [x] 3.2 Refuse an occurrence whose F1 exceeds 1.5 times the reference's or whose F2 falls below 0.85 times, at selection and on the soundtrack, and in the audition prefer a take whose occurrences pass. Done when tests refuse an /ɛ/ occurrence against an /iː/ reference by name with both ratios, pass an occurrence at 1.35 times the reference's F1, and propose the passing take.
- [x] 3.3 Refuse, in the readings check before narration, a language whose contract normalization gives a declared term another spoken form or none. Done when tests refuse English `Ethos` against a declared Eethos, naming the language, the term and both forms, and the ETHOS film's committed contract is refused the same way.

## 4. Review rounds

- [x] 4.1 Require `--dispositions` for prompts with a previous round, and state the dispositions under `{dispositions}`. Done when prompt tests refuse a missing finding, an unknown finding and a disposition without evidence or reason, and write the three groups.
- [x] 4.2 Refuse `assemble` and `refresh-captions` over films a review round's prompts bind until that round is set aside. Done when tests refuse assembly over a bound round by name and command, and proceed after its set-aside.

## 5. Number in Chinese

- [x] 5.1 Refuse, in the concept check, a Chinese clause holding a Latin-script word whose English counterpart uses only its plural when the clause holds no number word, with `[number]` words and reasoned exceptions in `concepts.toml`. Done when tests refuse 可以互相替换的 Agent against "interchangeable Agents", pass 越来越多的 Agent and 那些可以互相替换的 Agent, record a declared generic use and refuse a stale one.

## 6. The viewer's player

- [x] 6.1 Render each edition's player in `delivery/packaging.py` from the film's summary and palette, with the engine's structure and interface text, and refuse a film that still supplies `player.html`. Done when packaging tests build the sample film's players from its declarations and refuse a copied page by naming the declarations that replace it.
- [x] 6.2 Attach the WebVTT captions to every version as a hidden track, with no toggle and no other control that shows it because every version draws its captions, let its cues mark the transcript's current paragraph, and keep the time across version switches. Done when the player readback switches versions and reads the track's state, the current paragraph and the time, and finds no control of the page or the browser that shows the track.
- [x] 6.3 Set the transcript as a paragraph per thought with m:ss chapter and section times, as controls that play the film in the player and as text in the Markdown transcript. Done when transcript tests read one paragraph per thought and the times, and a player test plays from a section's time.
- [x] 6.4 Name each delivered file by kind, version, format and size, link the other edition's player and the entry page, and tag the chapter stream with the edition's language. Done when tests read the files list and the links, and the packaged films' chapter streams carry the edition's language.
- [x] 6.5 Extend `player-check` to read every delivered player back in a browser and record a verdict per page: links, captions cues against the SRT, the track's state per version, transcript times and edition links. Done when the readback passes the sample film's delivery, fails a broken link by page and link, and passes a scratch build of the essentials film's players.

## 7. Acceptance, documentation and release notes

- [x] 7.1 Run the wrapping, flow, term, number and player checks on the current builds of DDWG round 33, ETHOS round 8 and essentials round 4. Done when they flag EN33-1's English breaks, R33-zh-2's Chinese blocks, the 0.49 s ETHOS pause, ETHOS's English spelling and its five English vowels, the Chinese 可以互相替换的 Agent, and the copied players, with the counts recorded under `build/evidence/acceptance/` and in the Changelog entry.
- [x] 7.2 Document the declarations, measures and refusals in `README.md`. Done when the README names `[picture.wrapping]`, `[narration.flow]`, `[[narration.terms]]`, `[number]`, the player's declarations and readback, `--dispositions` and the set-aside guard.
- [x] 7.3 Set `VERSION` and the README pin to 0.11.0 and add a `[0.11.0] - UNRELEASED` Changelog entry. Done when no tracked file outside the Changelog history names 0.10.0 as the current version and every `mise run check` command passes.

## Workflow follow-up

- Before the release: `mise run sample:build` and its verification on the narrated sample.
- Archive the Change, prove the archived head once, land it and close out.
- Release follow-up: date the Changelog entry when the release is cut; `ethos land --release --tag v0.11.0`, the tag's publication and the source-only Release pages.
