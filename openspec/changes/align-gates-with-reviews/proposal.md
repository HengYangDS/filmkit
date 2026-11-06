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

- **Narration flow (new).** `review.measurement` records the heard pause at every word boundary by the punctuation between the words. Selection and assembly refuse a pause above the declared limit where the text has no mark: by default 0.4 s, and 0.2 s where Chinese and Latin script meet. The audition prefers fluent takes. The measurement also records rate, pitch and level steps between adjacent thoughts, and the listening plan lists the riskiest moments for human listening.
- **Term pronunciation.** A film declares each Latin-script term's spoken form, its pronunciation and a reference occurrence heard correct, in its declaration rather than in the pronunciation contract, whose hash binds every recording. Before narration, every language's contract must give the term that spoken form: ETHOS reached the voice as Eethos in Chinese and `Ethos` in English, and the English edition said /ɛ/ in about half of all takes. Every occurrence's first vowel must match the reference by its formants, in the audition, at selection and on the soundtrack.
- **Number in Chinese.** A Latin-script word keeps its base form in Chinese, so where the English uses its plural the Chinese clause must carry the number in words; the concept check refuses 可以互相替换的 Agent against "interchangeable Agents".
- **The viewer's player.** The engine renders each edition's player from the film's summary and palette instead of a copied page. Every version's picture draws its captions, which a hidden track follows for the transcript, the transcript reads by thought with times that play the film, files are named by kind and size, the editions link each other, and the player check reads every page back in a browser.
- **Review rounds.**
  - `review.round prompts --dispositions <file>` requires a disposition of every finding of the previous round: fixed, declared or deferred, each with its evidence or reason. The prompts state these dispositions.
  - Assembly refuses to write over a build that a review round has bound but not set aside.
- **Out of scope.** These are left to later releases: native production orchestration (a `review-build` command replacing film-side drivers), the narration engine as a separately pinned supply so a film holding its voice can take engine fixes, and gating continuity steps before they are calibrated against the owner's ear.

## Capabilities

### New Capabilities

- `narration-flow`: heard pauses at word boundaries and continuity between thoughts, measured on takes and soundtracks, gated where the text has no mark, used in auditions and listed for human listening.

### Modified Capabilities

- `picture-gates`: wrapped labels break by the declared rules, measured from the film's own painted lines.
- `spoken-readings`: a declared Latin-script term is given one spoken form in every language and is said like its reference occurrence wherever it occurs.
- `review-rounds`: a round's prompts state a disposition of every previous finding, and a bound build is set aside before it is rebuilt.
- `concept-contract`: a Latin-script word's number is carried by Chinese words where the English uses its plural.
- `film-package`: the engine builds each edition's player, with the captions every version draws, a transcript that leads into the film, named files and linked editions, and reads every player back in a browser.
- `film-engine`: the player's structure and interface text are the engine's own; a film supplies its player prose and colours.

## Impact

- **Code.**
  - `src/filmkit/picture/frame-audit/typography/` and `picture/gates.py`;
  - a new `src/filmkit/narration/flow.py`, with `review/measurement.py`, `review/listening_plan.py`, `narration/audition.py` and the selection and assembly gates;
  - `narration/readings.py` for terms;
  - `review/prompts.py`, `review/round.py` and `review/set_aside.py`;
  - `concepts.py` for number in Chinese;
  - a new `delivery/player.py`, `delivery/player-read.mjs` and `delivery/player-verdict.mjs`, with `delivery/packaging.py`, `captions/documents.py` and `delivery/player-check.mjs`, for the player;
  - `film.py` for the declarations.
- **Film declarations.** `content/film.toml` gains `[picture.wrapping]`, `[narration.flow]`, `[[narration.terms]]` and the player's summary and palette; `concepts.toml` may gain `[number]`; each edition's `player.html` is retired.
- **Adoption.**
  - The films' picture and sound bytes do not change; each edition's player page and transcript are rebuilt, and its Markdown transcript and chapter metadata may change.
  - A film's verdicts can change when it adopts 0.11.0: a film whose labels or narration break these rules is refused until it repairs them or declares an exception with its reason.
  - A film whose pronunciation contract gives a declared term different spoken forms is re-narrated once with the declared form.
  - DDWG holds filmkit 0.5.0 for its narration engine and adopts after the engine's voice is supplied separately.
