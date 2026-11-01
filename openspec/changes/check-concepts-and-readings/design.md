# Design

## Context

See `proposal.md` for the defect. A film's language rests on three of its own files: each edition's script (`film-script.json`), its pronunciation contract (the `pronunciation` object of the voice-performance file the scripts name), and its source manifest, which pins the canonical documents the film explains. `filmkit.sources` already verifies the manifest against a local clone named by `FILM_SOURCE_CHECKOUT`; `filmkit.narration.pronunciation` checks English stress targets and derives spoken text; `filmkit.narration.narrate` runs synthesis, alignment and transcription; `filmkit.review.round` writes the reviewer prompts. No part of the engine knew what a concept means, which word an edition must use for it, or how an ambiguous Chinese character is read.

## Goals / Non-Goals

**Goals:**

- A film states, once, what each concept it names means in its source, and which word each edition uses for it; the engine refuses narration that departs from that statement, wherever the departure is.
- Every Chinese character whose reading is ambiguous in narration has a declared reading at each occurrence before narration, and every name has one declared spoken form.
- A reviewer sees the contract and the resolved readings, not only the script.

**Non-Goals:**

- Judging whether a rendering is good; the film's author and reviewers decide that and the contract records it.
- Certifying natural-language understanding, or proving that a recording was spoken as declared; the occurrence check that compares recordings is a separate Change.
- Changing how a film without either contract builds.

## Decisions

**The film owns its contract; the engine owns the check.** `content/film.toml` may name a concept contract with `concepts`. The contract is TOML, which people write and comment, and is read by `tomllib` and checked by a pydantic model like the film declaration. Each `[[concept]]` has an `id`, the source `term`, an `essence`, a `source` with a `path` and a `quote`, and a `zh` and an `en` table holding `rendering`, `forms` and `avoid`. The `path` must be a document the source manifest pins, so a quotation is always bound to a digest. A concept sense that one source word carries in two senses is two entries.

**Quotations are checked where the manifest is checked.** With `FILM_SOURCE_CHECKOUT`, the check reads each document at the pinned commit through `git show`, as `filmkit.sources.verify` does. It compares the quotation with the document as plain text: Markdown emphasis and code marks are dropped and runs of whitespace become one space, so a quotation need not copy the document's line breaks or bold type. Without a clone the quotations are reported as not checked, as the manifest is, so CI, which has no clone, still runs the other checks.

**Segments declare concepts; both editions declare the same.** A segment of a script may list `concepts`, the ids it states. The same segment id declares the same set in both editions, so neither edition is translated from the other's concepts. A declared concept must appear in that segment by its rendering or one of its forms: as a substring in Chinese, and as a case-insensitive whole-word phrase in English.

**Counterexamples are refused everywhere a viewer meets words.** Each `avoid` string is searched in every segment's narration text, every segment and chapter title, the edition's caption terms, and every text file below `picture/` with the extension `.js`, `.mjs`, `.html` or `.json`, so a label in the picture cannot keep a rejected rendering. Each hit is named with its file, segment or title and its position, and all are reported at once. Requiring the approved rendering in picture labels was rejected: a picture does not declare which concepts a scene states, so presence there has no anchor; the review reads the picture against the contract instead.

**A reading is resolved per occurrence, from declarations, never guessed.** The engine ships a watch list of Mandarin characters whose readings a narrator can confuse, in two classes. A word character, such as 重, 行, 长 or 只, has more than one reading in ordinary words, so every occurrence must lie inside a declared word of two or more characters. A single character, such as 还, 了, 的 or 和, has one reading wherever it stands alone and others only inside known words, so the film may declare the character itself, and the words that read it otherwise are declared as words. The check resolves each watched occurrence by the longest declared word covering it and refuses any occurrence that none resolves, naming its segment, thought, position and the text around it. A word that contains no watched character may still be declared, and the check honours it. A declaration is a target of the existing kind `contextual-mandarin-word`; schema version 2 adds no new table.

**A dictionary checks the declarations.** `pypinyin` provides each character's dictionary readings and the contextual reading of each run of Han characters from its phrase dictionary. A declared word's reading must divide into one dictionary reading per character, whether written with spaces or without; after a word's first character, that reading may also be in the neutral tone, as in 还是 háishi, which the dictionary does not list. Where the contextual reading of an occurrence differs from the declared one, the declaring word must record its reason in `dictionary_disagreement`; otherwise the check refuses. A single character cannot record a reason, so it can never silently cover a word the dictionary reads otherwise, such as 还 in 还原, and a dictionary error, such as its reading of 去重, is overruled only by a declared word with a written reason. Writing a Mandarin reading engine was rejected: the phrase dictionary is the mature part, and a declaration that the author and reviewer read is the authority.

**Declarations stay current.** A word declared twice, a declared word the Chinese narration never says, and a reason that no occurrence needs are refused, so the contract describes the narration as it stands and an edited script cannot leave readings behind.

**Names have one spoken form.** A Latin word in the Chinese narration must be declared in the contract's embedded English targets, and an English word written with two or more capitals, such as ETHOS, OpenSpec or GitLab, must be an English target, so every name the narrator says has one declared form.

**Schema version 2 opts a film in.** The readings check applies to a pronunciation contract of `schema_version` 2, which adds `dictionary_disagreement` to the Chinese targets and makes every watched occurrence need a declaration. A version 1 contract keeps its meaning, so a film's existing editions narrate as before until the film declares version 2.

**The occurrence plan is a view, written for review.** The readings check writes `build/evidence/readings/<code>-plan.json`, listing each watched occurrence with its thought, position, character class, covering word, declared reading and dictionary reading. It is derived and rewritten on every check, never read back as authority; the contract stays the only place a reading is declared.

**Narration refuses first.** `filmkit.narration.narrate` runs the concept check and the readings check before any speech model loads, including with `--dry-run`, so a refused script never reaches synthesis. The reviewer prompt context gains the contract's path and the plan's path, and a film's prompt template names them.

## Risks / Trade-offs

- [The dictionary disagrees often, and authors write reasons by rote] → The reasons are in the contract, where the reviewer reads them beside the plan; a reason does not change the declared reading, so a rote reason cannot make a wrong reading pass review.
- [The watch list misses a character a narrator misreads] → The list is package data with a test that every listed character has more than one dictionary reading; a film can declare any word's reading, and a missed character found in listening is added to the list in a later release.
- [A counterexample is a substring of a correct phrase] → A counterexample is chosen as a whole phrase, and English matching is whole-word; the refusal names the exact text, so a wrong counterexample is corrected in the contract.

## Migration Plan

Released with the next engine release. `ddwg-film` and `ethos-film` adopt it in their own Changes by declaring both contracts, declaring each segment's concepts and raising their pronunciation contracts to version 2; a film that declares neither builds unchanged.
