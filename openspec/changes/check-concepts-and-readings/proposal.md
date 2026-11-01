# Proposal

## Why

The films' narration has rendered a source concept by a nearby everyday word, and nothing stopped it. The `ethos-film` `v1.0.x` Chinese editions said 有权决定的人, a person with power to decide, for ETHOS's authority, which is the set of inputs a judgment may rest on; the DDWG films said 谁说了算 and 有决定权的人 for the guidelines' two kinds of authority. Each film's glossary lived only in design prose, the reviewers never read the source definitions, and one review endorsed the wrong rendering. Pronunciation has the same gap: a film's pronunciation contract lists some Chinese readings, but nothing requires a reading for every ambiguous character, so a polyphone such as 重 in 去重 or 行 in 行情 can reach narration unread, and nothing requires a declared spoken form for every name.

## What Changes

- A film may declare a concept contract, `content/concepts.toml`, named by `concepts` in `content/film.toml`. Each entry binds one concept sense to its exact passage in a document the source manifest pins, its essence, and one approved rendering per edition with its allowed forms and the counterexamples found.
- A concept check verifies each quotation at the pinned commit of a local source clone, requires each segment's declared concepts to be the same in both editions and to appear by their approved renderings, and refuses any counterexample in the narration, titles, caption terms or picture sources, naming each failure.
- A pronunciation contract of schema version 2 declares the reading of every watched Chinese character: by the declared words that contain it, or by a declared single character for a character whose other readings live only in known words. A readings check resolves every occurrence, refuses an undeclared one with its segment, thought and position, refuses a declared reading that is not a dictionary reading, requires a recorded reason where the dictionary's contextual reading disagrees, and refuses declarations the narration no longer needs. It also requires a declared spoken form for every name in either edition, and writes the resolved occurrence plan for review.
- Narration runs both checks before any speech model loads and refuses on either. The reviewer prompt names the concept contract and the occurrence plan.

## Capabilities

### New Capabilities

- `concept-contract`: a film's concept contract and the check that keeps its narration, titles and picture faithful to it.
- `spoken-readings`: the declared reading of every ambiguous Chinese character and the spoken form of every name, and the check that resolves each occurrence before narration.

### Modified Capabilities

None.

## Impact

- New `src/filmkit/concepts.py`, `src/filmkit/narration/readings.py` and the package's watch list; changes to `src/filmkit/film.py`, `src/filmkit/narration/narrate.py` and `src/filmkit/review/round.py`; the sample film's contract, scripts and pronunciation contract; tests; `README.md` and `CHANGELOG.md`.
- A new runtime dependency, `pypinyin`, at its latest stable release, for the dictionary readings of Chinese characters.
- A film that declares neither contract builds and narrates exactly as before. `ddwg-film` and `ethos-film` adopt both in their own Changes.
- Out of scope: checking that a recorded occurrence was spoken as declared, which compares each occurrence with an approved reference and is a separate Change; review scoring, which each film declares.
