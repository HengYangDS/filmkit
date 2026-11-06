# Proposal

## Why

The owner keeps finding faults in delivered builds that every gate passed. Across the last 11 production review rounds of the three films (22 edition reviews), 25 of the 39 findings that cost points were picture faults the gates did not measure. The owner's first listening of the ETHOS round-8 build found two faults that no gate measures:

- a 0.49 s pause that splits 可以互相替换的 Agent inside its phrase;
- an English edition that says ETHOS as /ˈɛθɒs/ 5 times out of 20, where the word is /ˈiːθɒs/.

Each fault class has so far been caught by a person and fixed by a one-off script. The engine should measure what reviewers and listeners judge, so that a fault is found before the render instead of after the review.

## What Changes

- **Wrapped labels.** `check-picture` reads every wrapped label's lines, as the film paints them, at rest. It refuses:
  - an English line that ends on an article, preposition, conjunction, determiner or wh-word;
  - a one-word last line in a name of three or more words;
  - a block line under the declared share of the block's longest line (by default 0.8, and 0.6 for the last line);
  - a Chinese line that opens on closing punctuation.

  A film declares its ratios, extra lead words and reasoned exceptions in `[picture.wrapping]`.

- **Narration flow (new).** `review.measurement` records the heard pause at every word boundary by the punctuation between the words. Selection and assembly refuse a pause above the declared limit where the text has no mark: by default 0.25 s, and 0.15 s where Chinese and Latin script meet. The audition prefers fluent takes. The measurement also records rate, pitch and level steps between adjacent thoughts, and the listening plan lists the riskiest moments for human listening.
- **Term pronunciation.** A film declares each Latin-script term's pronunciation and a reference occurrence heard correct. Every occurrence's first vowel must match the reference by its formants, in the audition, at selection and on the soundtrack.
- **Review rounds.**
  - `review.round prompts --dispositions <file>` requires a disposition of every finding of the previous round: fixed, declared or deferred, each with its evidence or reason. The prompts state these dispositions.
  - Assembly refuses to write over a build that a review round has bound but not set aside.
- **Out of scope.** These are left to later releases: native production orchestration (a `review-build` command replacing film-side drivers), the narration engine as a separately pinned supply so a film holding its voice can take engine fixes, and gating continuity steps before they are calibrated against the owner's ear.

## Capabilities

### New Capabilities

- `narration-flow`: heard pauses at word boundaries and continuity between thoughts, measured on takes and soundtracks, gated where the text has no mark, used in auditions and listed for human listening.

### Modified Capabilities

- `picture-gates`: wrapped labels break by the declared rules, measured from the film's own painted lines.
- `spoken-readings`: a declared Latin-script term is said like its reference occurrence wherever it occurs.
- `review-rounds`: a round's prompts state a disposition of every previous finding, and a bound build is set aside before it is rebuilt.

## Impact

- **Code.**
  - `src/filmkit/picture/frame-audit/typography/` and `picture/gates.py`;
  - a new `src/filmkit/narration/flow.py`, with `review/measurement.py`, `review/listening_plan.py`, `narration/audition.py` and the selection and assembly gates;
  - `narration/readings.py` for terms;
  - `review/prompts.py`, `review/round.py` and `review/set_aside.py`;
  - `film.py` for the declarations.
- **Film declarations.** `content/film.toml` gains `[picture.wrapping]` and `[narration.flow]`, and the pronunciation contract gains `latin_terms`.
- **Adoption.**
  - Output bytes do not change.
  - A film's verdicts can change when it adopts 0.11.0: a film whose labels or narration break these rules is refused until it repairs them or declares an exception with its reason.
  - DDWG holds filmkit 0.5.0 for its narration engine and adopts after the engine's voice is supplied separately.
