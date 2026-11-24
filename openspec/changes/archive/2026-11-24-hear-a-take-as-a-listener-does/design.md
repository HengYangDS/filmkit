## Context

See [proposal.md](proposal.md) for what changes and the deltas for every obligation; this design gives the reasons,
the alternatives and what the rule lets through. The probes, their outputs and a scratch clone of `v0.31.0` stand
beside this draft in `hear-a-take-as-a-listener-does.scratch/`, outside the repository [S6]; the first independent
reading is `reading-1.md` in the draft's own folder, also outside the repository, and the films session's
decisions on it are [S8].

What the Change rests on in the engine at `v0.31.0` [S3]:

- The units line (`narration/judgment.py:436-458`, `UNIT_LIMIT` at line 106) compares a take's transcript with its
  spoken text through `recognition.compared` (line 336). Han characters are alike by their reading in context, the
  film's declared word first (`narration/recognition.py:11-17`); Latin units by their letters, joins and declared
  terms (lines 21-33, 181-192). `judge`, `converge` and `audition` reach the line through the bench (lines 172-190,
  221); `audition` qualifies a take that no line refuses and orders by phrase, ending or length
  (`narration/audition.py:6-10`, `propose`).
- English declares the reading check `cmudict-stress`, which holds stress targets to the phones the pronunciation
  states (`narration/pronunciation.py:118-130`). An edition's pronunciation declares readings of its own: a target
  of kind `letter-name` for an initialism such as "AI" (its letter names, in prose), and `arpabet` phones under a
  target's `lexical_stress`, one reading or one per part of speech for a heteronym; which part of speech an
  occurrence has stands apart, in the analyst readings (`readings.json`, keyed by segment and offset), and only the
  listening plan reads it (`review/listening_plan.py:182-232`). The engine loads no dictionary; the three films
  cite CMUdict at commit `74790861` by URL, SHA-256 and size [S5].
- A take's request binds the pronunciation's SHA-256 (`narration/thought_groups.py:130`, `:182`), so editing it
  changes every request of the edition; the film's declaration binds none (`narration/terms.py:15`; the golden test
  `tests/narration/test_synthesis.py:466-514`).
- A respelling of kind `english-name` must be declared as a term with IPA and a heard reference
  (`terms.respelling_failures`) [S8]; the kind `homophone` replaces substrings with no word boundary
  (`narration/pronunciation.py:150-154`).
- The clarity line holds a take's own clarity to its thought's line (`narration/judgment.py:423-433`,
  `review/clarity.py:224-261`); a take under it is refused and gets candidates (`narration/converge.py:245-248`);
  preflight refuses on the sound gate's measure of the assembled soundtrack (`preflight.py:217-258`); `check-sound`
  refuses a soundtrack or a segment under the floor.
- Every film declares `author` as the owner: the three released films' scripts and the fused trial's (read on 24
  November); from 0.31.0 the declaration states it once (`content/film.toml`).

Carried onto 0.32.0 (`v0.32.0`, the derivation's R2a, `record-every-run`) [S3]: of the files cited above, 0.32.0
changed only `preflight.py`, whose `clarity` now stands at lines 215-256, and `film.py`; the other lines cited hold
the same code. 0.32.0 records each run of a node of an edition's build chain and states, in a node table
(`graph/chain.py`), what each node's run reads and writes, held to the reads by a check of what each run opens
(`graph/opens.py`). Of this Change's new reads by a node, one needed a declaration: preflight's of the selection
(decision 5). `select` and preflight read the records of hearing in the declaration, which every node binds whole,
and preflight reads the assembly record, which its node already declared. The dictionary is read only by `judge`,
`converge` and `audition`, which are no nodes, from below `build/runtime/`, which the check lets through as work.
0.32.0's picture and sound gate records also bind the declaration whole, so a record of hearing costs runs of the
gates (decision 5).

The trial [S7]: over three copies of the fused film's English edition eight takes failed the units line, three on a
spelling of the same sound (13.2 "labeled"; 28.3 and 29.3 "tears"); the owner heard five refused takes correct (D-44)
and chose the ear for a single thought under 18 dB (D-46) [S1].

## Goals / Non-Goals

**Goals:** a take whose transcript writes the text's English word in a spelling the dictionary says the same way
passes its units line, with everything that lets through listed; a take the owner heard passes the lines he settled,
for that take alone; a thought under its clarity line goes to his ear instead of to candidates, while the soundtrack
and every segment keep their floor; no request changes; no take that passes today is refused, apart from the new
refusals of a missing dictionary and of a malformed or stale record.

**Non-Goals:**

- Comparing the Chinese edition otherwise than today.
- Holding the `cmudict-stress` targets to the supplied dictionary; a follow-on Change could withdraw the phones a
  pronunciation restates from CMUdict.
- A command that writes a record of hearing; the film's lane writes it, as it writes a declared term.
- Pronunciations for words CMUdict lacks, and joins by pronunciation.
- Moving the record into R4's lock or R3's one list of exceptions, or retiring `review.clarity_exceptions`, which R3's
  one exception model absorbs with the record.
- Sending a thought refused by its units line alone to the ear before candidates: D-46 decides that for clarity only.

## English words: the two options

Decision 1 weighs these; the counts are `probe-6.json` and `probe-7.json` [S6].

|                                         | Option 1: first pronunciation (chosen)                            | Option 2: any pronunciation                                         |
| --------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| Pairs over the films' words that pass   | 724, for 350 text words                                           | 768, for 360 text words                                             |
| Pairs that sound different but pass     | 0 of the 43                                                       | 43 ("our" for "are", "effect" for "affect", "tears" for "tiers", …) |
| Fused trial, 194 thoughts, 4 mismatches | settles 13.2; 09.1, 28.3 and 28.4 go to the ear                   | settles 13.2 and 28.3; 09.1 and 28.4 go to the ear                  |
| Fused copy `ch9-10`, 65 thoughts, 4     | settles none; 24.9, 28.2, 28.8 and 29.3 go to the ear             | settles 29.3; 24.9, 28.2 and 28.8 go to the ear                     |
| December full film, 161 thoughts, 8     | settles none; 19.3 differs by 1 unit, not 2 ("right" for "write") | the same                                                            |
| December essentials, 46 thoughts        | no mismatch                                                       | no mismatch                                                         |
| ETHOS film                              | no judgment at hand                                               | no judgment at hand                                                 |
| Needs IY before closed R read as IH     | no: it would add only "teer" for "tier", a name                   | yes, for "tears" against "tiers"                                    |

## Decisions

1. **A transcript's English word passes for the text's only when its usual pronunciation is a reading of the text
   word (option 1), not when any of its pronunciations is (option 2).**
   - **Rests on:** the Chinese rule, which reads each side by its declared word or the dictionary's one reading in
     context (`recognition.py:11-17`); the text word's own readings: those its edition's pronunciation declares
     (letter names, such as "AI" in `ddwg-film`, `ddwg-essentials-film` and the fused trial's `ch1-5` copy, compared
     by letters; `arpabet` phones, every reading of a heteronym), else CMUdict's first; the films session's analysis
     that a mismatch is rare and the owner's hearing settles one in seconds [S8]; and the counts below, over the
     pinned file and the English words of the fused film, the three released films and the sample, read with each
     film's declarations, and over the trials' judgments (`probe-6.json`, `probe-7.json`) [S6].
   - **Considered:** option 1, the transcript word's first pronunciation is one of the text word's readings; option 2,
     any of its pronunciations is; and, ruled out earlier, (a) any pronunciation on both sides, which also passes weak
     forms ("are" for "or", "capped" for "kept"), (a'') the first on both sides, (b) a table of British and American
     spellings, which copies CMUdict by hand, and (c) a film's respelling, which costs a declared term, a heard
     reference and a narration of the whole edition, since the pronunciation's SHA-256 binds every request. The two
     options are compared in the section "English words: the two options".
   - **Chosen by:** the owner, at 14:44 on 24 November 2026, 「1 只认常用读音」 (D-49) [S1].
   - **Chosen because:** option 1 passes no pair whose usual sound differs from every reading of the text word, and
     refuses all 43 that option 2 lets through; what it gives up, in the trials, is "tears" for "tiers" (28.3, and
     29.3 in another copy), which the owner's ear settles in seconds under decision 5. Of the 724 pairs it passes, 17
     have a text word with several declared readings ("red" for "read", "ewes" for "use", "reckard" for "record",
     "fax" for "facts"): the sound is one of the word's own readings, perhaps not the one this occurrence needs, as
     today when the recognizer writes the same spelling and passes whichever reading was said. Every other passed
     pair shares the text word's reading as the other spelling's own first pronunciation: same-sounding spellings and
     names, in the appendix's list. Over the trials' 16 English mismatches, option 2 settles two more than option 1,
     both "tears"; neither settles a December one.
   - **Applies to:** `narration/recognition.py`, `narration/cmudict.py` (new), `narration/judgment.py` (`bench`); the
     judgment's record binds the pronunciation by its SHA-256.
   - **Reopened when:** the owner asks for option 2, which restores the any-pronunciation sentence, the "tears" scenario
     as passing and decision 2's reading of IY before a closed R as IH; or a pair that sounds the same is refused often
     enough that hearing it costs more than the rule.
2. **Pronunciations are compared with primary stress kept and secondary stress read as none.**
   - **Rests on:** reading stress 2 as 0 adds four pairs over the films' words, all the same sound (catalog/catalogue,
     company/compagnie, forward/foreword, welcome/wellcome), while primary stress keeps "uh" (`AH1`) apart from "a"
     (`AH0`) [S6]; CMUdict writes the NEAR vowel before an R that no vowel follows as IH 665 times and IY 134 times,
     and the lexical sets give NEAR as one set in RP and in GA [S9].
   - **Considered:** stress kept in full, which refuses catalogue/catalog; all stress dropped; reading IY as IH before
     a closed R, which option 2 needs; the same for SQUARE, CURE and FORCE; merging the reduced vowels AH0 and IH0,
     which would make "an" and "in" alike.
   - **Chosen because:** secondary against no stress on the same vowel tells no English word from another that the
     films say, and primary stress keeps the weak and strong forms of function words apart. Under option 1 the NEAR
     reading settles no trial case and adds one name, so it is left out; SQUARE has no case either, and CURE and FORCE
     differ between speakers.
   - **Applies to:** `narration/cmudict.py`.
   - **Reopened when:** option 2 is chosen, or a take whose sound is right is refused for a vowel CMUdict writes two
     ways.
3. **A language declares how a transcript's Latin-script words are heard; the dictionary hears only units that say no
   declared term.**
   - **Rests on:** `film-engine`'s requirement that no step choose a behaviour by a language's code or script; Chinese
     reads Latin script as names, compared by terms and `stands_for`; the terms line measures a term's sound.
   - **Considered:** branching on the code; reusing `readings`, the reading checks; applying the dictionary to the
     Chinese edition's names, or to term units.
   - **Chosen because:** a field, `latin_heard` (`letters`, `cmudict-pronunciations`), names the behaviour where it is
     chosen, as `stemmer` does; the Chinese edition's verdicts do not move; a term stays held to its declared form.
   - **Applies to:** `languages/`, `narration/recognition.py`.
   - **Reopened when:** a Chinese take's Latin name is refused for a spelling CMUdict hears alike.
4. **The supply step downloads the pinned file; no package carries it.**
   - **Rests on:** CMUdict's latest commit, `74790861` of 24 October 2025, under Carnegie Mellon's two-clause BSD
     notice [S4]; the file's SHA-256 and size, equal to the films' citation [S5]; PyPI's `cmudict` 1.1.3, which
     bundles the same commit under GPL-3.0-or-later code; `pronouncing` (MIT) requires it; `nltk` downloads its corpus
     at run time; `g2p-en` was last released in 2019 [S4]. Hashing the file takes about 2 ms and parsing it about a
     second, holding about 76 MB, measured under Python's tracer [S6].
   - **Considered:** the PyPI package; the file vendored in the engine's tree; the supply step's download.
   - **Chosen because:** the download keeps the engine's licence and lock unchanged and the bytes pinned as the
     models are, and it reaches the network only where the engine already does; the judgment commands already need
     the supply for their models, and hosted CI judges no take.
   - **Applies to:** `supply.py`, `narration/cmudict.py` (the pin and `build/runtime/tool-cache/cmudict/cmudict.dict`),
     `NOTICE`, and a host marker for the one test that reads the pinned file (`tests/conftest.py`).
   - **Reopened when:** CMUdict publishes a later commit; a new pin is a release of its own.
5. **The owner's hearing settles the lines it names for one take, recorded in the film's declaration.**
   - **Rests on:** D-44 and D-46, which make the owner's ear the judge and ask for his hearing bound to the take's
     audio [S1]; the films session's decision that the listener is the owner alone [S8]; the declared term's
     reference, a take a person heard, declared in the film because the pronunciation binds every recording
     (`narration/terms.py:1-20`).
   - **Considered:** the record in the pronunciation, the cast or R4's lock; any named listener; a record bound to the
     thought alone; one record for every line, or one that names its lines.
   - **Chosen because:** the declaration binds no request; the take's audio SHA-256 names exactly what was heard and
     falls away with any other take; `lines` says whether the owner settled the words, the clarity or both, since a
     check of the words is no judgment of the voice; no hearing settles a phrase end, an ending, a pause or a term.
     The listener must be the film's declared `author`, the owner, and the loader refuses any other name; a later
     Change may widen it if he asks. The selection refuses a record whose take is not its thought's selected take,
     which also refuses a record of a thought the script does not hold. A record that a line no longer needs is said
     so and refused by nothing.
   - **Applies to:** `film.py`, `narration/judgment.py`, `narration/selection.py`, `preflight.py`; and the node
     table, `graph/chain.py`, where preflight's node declares the selection, beside the gate records it judges, since
     its run now reads it to find each thought's selected take; the readiness receipt keeps its ten digests.
   - **Cost on 0.32.0:** the picture and sound gate records bind the declaration whole (`bound_inputs` in
     `picture/gates.py` and `soundtrack/gates.py`), so each batch of records makes `check-picture` (heavy),
     `check-sound` and `preflight` run again before a render, where on 0.31.0 only `preflight` ran again;
     `filmkit plan` also reports every node stale, as after any edit of the declaration, though no command of 0.32.0
     refuses on that. The Change's owner accepts that cost for this release. R2b-1 (`build-a-film-by-its-verbs`,
     drafted and reviewed) removes it by binding only the tables of the declaration that a node reads.
   - **Reopened when:** the owner names another listener, or R3 or R4 lands; or, before R2b-1 lands, the gates' runs
     for a batch of records cost more than the owner accepts.
6. **A thought under its clarity line goes to the owner's ear; the soundtrack and segments stay hard lines.**
   - **Rests on:** D-46 [S1]; the trial, where the three candidates of English 13.5 stayed at 17.4 to 17.7 dB under
     its 18.0 dB line [S7].
   - **Considered:** refusing and retaking first; a film declaration choosing the route; a hearing that settles a
     segment.
   - **Chosen because:** it is the route the owner chose; a take under its line is neither passed nor refused, so the
     convergence spends no candidate on it and still prefers a take above the line; `judge`, `converge` and preflight
     name it with the take's path and SHA-256, so the clip and the record's key are at hand; `audition` proposes a
     take above its line before one for the ear and names the latter, so a thought the owner rejects is not answered
     with a muddier take; `check-sound` reads no record. One route for every film, since D-46 covers every edition
     from the fused film on.
   - **Applies to:** `narration/judgment.py`, `narration/judge.py`, `narration/converge.py`,
     `narration/audition.py`, `preflight.py`.
   - **Reopened when:** the owner asks for candidates before his ear.
7. **What judges a take binds no request, and a test holds it.**
   - **Rests on:** the golden requests of the sample (`tests/narration/golden/sample-requests.json`), written before
     this Change; a candidate's request (`narration/candidates.py:62-66`).
   - **Considered:** a new golden file; a comparison with and without the new inputs only.
   - **Chosen because:** the golden file unchanged, and the same requests planned with a record and the dictionary in
     place, prove both that nothing changed and that the new inputs reach no request.
   - **Applies to:** `tests/narration/test_synthesis.py`.
   - **Reopened when:** a request comes to bind the film's or a language's declaration.
8. **A release of its own before the fused film narrates again; one Change for its three parts.**
   - **Rests on:** the derivation, which puts the finding in R4 or in a Change of its own before the fused film
     narrates [S2, §8]; R4 waits for R2b, R2a having been released as 0.32.0 [S2, §5.7]; the trial waits on these
     takes.
   - **Considered:** R4; a Change for each part.
   - **Chosen because:** nothing here depends on the lock; the three parts meet in the take's judgment and in one
     record, and separate Changes would give the record one line now and another later. Groups 2 and 3 of the tasks
     do not depend on each other, so either part can be cut before it is built.
   - **Applies to:** the release after 0.32.0.
   - **Reopened when:** the owner withholds a part.

## Risks / Trade-offs

- **Option 2's 43 pairs** would let a word through that a listener could hear apart. → Option 1 refuses them, and
  the owner hears the few takes they would have settled.
- **Option 1 sends a same-sound spelling to the ear** where CMUdict gives it first another sound ("tears"). → A clip
  of a few seconds; the record of hearing settles it.
- **The owner's ear is one person's.** → The record keeps the measure beside his name and binds one take; the review
  rounds still hear the whole film.
- **A film that has not run the supply again cannot judge an English take.** → One line names the supply step, before
  any model loads.
- **A thought for the ear waits on the owner,** and the render waits with it. → Each is named with its clip.
- **A record goes stale when another take is bound.** → It does nothing for that take, and the selection refuses it.

## Migration Plan

1. Release the engine (tasks).
2. The fused film adopts it in its lane, runs the supply step and judges again: 13.2 passes by reading; 28.3 (and
   29.3 in the `ch9-10` copy) is named for the ear; the seven thoughts under their clarity line are named for the ear.
3. It records the owner's hearings (D-44) with `lines = ["units"]` for 02.10, 14.4, 21.3 and 09.1 at once, and for
   28.3 once he has heard it; 28.4 also fails its phrase line and goes to candidates, so its record is written only
   if no candidate is bound, for the take then bound, after he hears it.
4. The owner hears the seven; each take he hears clear gets `lines = ["clarity"]`, each he rejects goes to `audition`.
5. The hearings of a round are recorded together, then `check-picture`, `check-sound` and `preflight` run once
   before the next render, since on 0.32.0 each edit of the declaration makes the gate records stale (decision 5).
6. `ethos-film` adopts the release with its December edition; it needs no record.

Rollback: a film that wrote no record is judged by the previous release as before; one that did removes its records,
which the previous release refuses as an unknown key.

## Open Questions

None. Decision 1's question, which rule the films' English narration is held to, was the owner's: he chose option 1
at 14:44 on 24 November 2026, 「1 只认常用读音」 (D-49) [S1].

## Sources

Read or measured on 24 November 2026, read only.

- **[S1]** `build/evidence/owner-words.md` in the engine's repository: D-44 (12:37 CST), D-46 (13:03 CST) and D-49
  (14:44 CST).
- **[S2]** `build/evidence/engine-derivation/derivation-2026-11-23.md` in the engine's repository: §8 finding 1, §5.7.
- **[S3]** The engine at `v0.31.0`: the files and lines cited, and `openspec/specs/`; read again at `v0.32.0`, whose
  `openspec/specs/` leaves the four capabilities this Change modifies as they were.
- **[S4]** CMUdict, <https://github.com/cmusphinx/cmudict>, its commits and `LICENSE` at
  `74790861f652b15e4ac49015a90074ad62a27690`; PyPI's JSON for `cmudict`, `pronouncing`, `g2p-en`, `nltk` and
  `breame`; `python-cmudict`'s submodule and `LICENSE` at its tag `v1.1.3`.
- **[S5]** `content/voice-performance.json` of `ddwg-film`, `ddwg-essentials-film` and `ethos-film`.
- **[S6]** The probes in the scratch folder, run on the pinned file streamed from its URL with its SHA-256 checked:
  `probe/cmudict_probe.py` to `cmudict_probe_5.py`, their plans and outputs (`probe-1.json`, `probe-2.json`,
  `probe-3-kept.json`, `probe-3-secondary.json`, `probe-4.json`, `probe-5.txt`, and `cmudict_probe_6.py` with
  `plan-6.json` and `probe-6.json`, which reads each film's declared readings; `cmudict_probe_7.py` with `plan-7.json`
  and `probe-7.json`, which compares the two options over the films' words and the judgments of the fused copies and
  the December trials; and `near_check.py`).
- **[S7]** The fused trial's judgments and receipts below `build/runtime/work/trial-fused/<copy>/build/evidence/` for
  `ch1-5`, `ch6-11` and `ch9-10`; `build/evidence/ddwg-fused-film/whole/retake-plan.md`.
- **[S8]** The films session's messages of 24 November 2026: the `english-name` term requirement; the cases of the
  heard takes and of clarity; its decisions on `reading-1.md` (the narrower rule; the owner as the only listener;
  the audition path and the released films' acceptance).
- **[S9]** The Wikipedia article "Lexical set", its table of Wells' sets (NEAR, SQUARE, CURE, FORCE), read on 24
  November 2026.

## Appendix: what decision 1 lets through in the films' words

Each entry is a text word of the English narrations of the fused film, `ddwg-film`, `ddwg-essentials-film`,
`ethos-film` or the sample, read with its film's declared readings, then each other spelling a transcript can hold
that the rule takes for it, from `probe-6.json` and `probe-7.json` [S6]. A declared term is compared as a term whatever
its entry says.

The list stands as evidence, not in this folder: 724 pairs that both options pass, where the other spelling's first
pronunciation is a reading of the text word, and 43 pairs that option 2 alone passes, where the other spelling has
the reading only as a later pronunciation, in `build/evidence/hear-a-take-as-a-listener-does/let-through.txt` below
the engine's repository (ignored by Git; the release promotes the lane's evidence), 8,107 bytes, SHA-256
`df0e8a09b889ff7af1bab7e7a1cfcde65059a3afbf4382f88bab8627044baf2d`. A Change folder holds only OpenSpec's artifacts,
and the list holds 58 spellings the proof's codespell takes for misspellings.
