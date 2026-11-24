## Why

A take passes its units line only when no unit of its transcript differs from its text by reading. The engine
compares a Han character by its reading in context, so a transcript that writes 再 where the text has 在 holds what
a listener heard; it compares an English word by its letters, forgiving only an apostrophe and a join
(`narration/recognition.py:1-37`) [S3]. In the fused DDWG film's trial of 24 November 2026, the units line refused
three copies of the English edition eight times; in three of them only the spelling differs from the sound:
"labelled" written "labeled" (13.2), and "half tiers" written "half tears" (28.3 in one copy, 29.3 in another) [S7].
The derivation records this as its finding 1 and asks the release that settles it to say which homophones it lets
through, as the Chinese rule does [S2, §8].

On the same day the owner heard five other refused takes (Chinese 02.10, where 本片 was written 本篇; 14.4 and 21.3,
where 记入 was written 记录; English 09.1 and 28.4, where "an" was written "and") and said, at 12:37 [S1]:

- 「识别器不准。我听起来没问题」

No comparison can settle these: the readings differ, and "an" and "and" are different words. The engine takes a
person's hearing as the reference occurrence of a declared term (`narration/terms.py:1-20`), but offers no way for
the owner's hearing to settle a take the recognizer misheard.

At 13:03 he chose that a single thought under 18 dB of clarity is no longer refused automatically but sent to his
ear, while the soundtrack and every segment keep 18 dB [S1]:

- 「1 交给你的耳朵」

Today a take under its thought's clarity line is refused, and the convergence generates candidates for it
(`narration/judgment.py:423-433`, `narration/converge.py:245-248`); in the trial, three candidates of English 13.5
read 17.4 to 17.7 dB [S7].

## What Changes

- **English words are heard by their pronunciation.** Each language declares how a transcript's Latin-script word in
  other letters than the text's is heard, `latin_heard`: English declares `cmudict-pronunciations`, Chinese `letters`.
  In an English edition, a text unit that says no declared term is also alike a transcript unit when the transcript
  unit's first pronunciation in the engine's pinned CMUdict is one of the text unit's own readings: those the
  edition's pronunciation declares for that word, else CMUdict's first; a word it declares by letter names, such as
  "AI", is compared by its letters, so "I" or "eye" for "AI" stays refused. Primary stress counts and secondary stress
  reads as none. Words the dictionary lacks, declared terms, joins, numbers and the Chinese edition are compared as
  today. The owner chose this rule (option 1, D-49) over one that takes any of the transcript word's
  pronunciations (option 2); the design compares the two and counts the pairs each lets through in the films' words.
- **The supply step places the dictionary.** `filmkit.supply` downloads `cmudict.dict` from the CMUdict repository at
  commit `74790861f652b15e4ac49015a90074ad62a27690`, 3,618,488 bytes with the SHA-256 that the three films'
  pronunciations already cite, into the tool cache. A judgment of an English edition reads only that file, refuses it
  missing or altered in one line that names the supply step before any model loads, and names it in its record, which
  also binds the edition's pronunciation by its SHA-256.
- **The owner's hearing settles the lines it names for one take.** A film may record in its declaration, as
  `[[narration.heard]]`, that its owner heard one take of a thought: the edition, the thought, the SHA-256 of the
  take's audio, the lines the hearing settles (`units`, `clarity`), the listener, the date and a note. The listener
  must be the author the film declares. The judgment passes those lines of that take alone and keeps the measures in
  its record with his name; the selection refuses a record whose take is not its thought's selected take.
- **A thought under its clarity line goes to the ear.** A take under its thought's line, whose clarity no record
  settles, is named for the ear instead of refused: `judge`, `converge` and `audition` name it with its take's path,
  audio SHA-256, clarity and line; the convergence generates no candidate for it and exits 1 while it waits; audition
  proposes a take above its line before one for the ear. `produce preflight` passes a thought whose selected take the
  owner heard clear and names the others for the ear. `check-sound` still refuses a soundtrack or a segment under the
  floor, whatever was heard.
- **No take's request changes.** Neither the dictionary nor a record enters a request; the sample's golden requests
  stay byte for byte, and a new test plans them with both present.
- **Documents:** the README's supply, judgment and preflight sections, `NOTICE` (CMUdict's licence) and the
  Changelog.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `narration-convergence`: English words are also compared by their pronunciation; the owner's hearing settles the
  lines it names for one take, and a malformed or stale record is refused; a take is held to its words unless his
  hearing settles them; a thought under its clarity line goes to the ear; the judge and the audition name it; what
  judges a take binds no request.
- `film-engine`: a language's declaration states how a transcript's Latin-script words are heard.
- `render-preflight`: preflight takes the owner's hearing of the selected take, and names the thoughts it refuses for
  their clarity for the ear.
- `sound-gates`: a record of hearing settles no soundtrack and no segment.

## Impact

- **Base:** release 0.31.0 (`v0.31.0`).
- **Engine:** `languages/__init__.py`, `languages/en.toml`, `languages/zh.toml`; `narration/recognition.py`,
  `narration/judgment.py`, `narration/judge.py`, `narration/converge.py`, `narration/audition.py`,
  `narration/selection.py`; a new `narration/cmudict.py`; `preflight.py`; `supply.py`; `film.py`; their tests, with
  new `tests/narration/test_cmudict.py`, `tests/narration/test_units_line.py` and `tests/test_film_hearings.py`, and a
  host marker in `tests/conftest.py`; the README, `NOTICE` and the Changelog. No package is added, so `uv.lock`,
  `package-lock.json` and `released.json` keep their bytes.
- **Supply:** one more download at the supply step, 3,618,488 bytes from `raw.githubusercontent.com`, under CMUdict's
  two-clause BSD notice, which the engine does not redistribute. Hosted CI is unchanged: no portable gate reads the
  dictionary, and the one test that does is skipped and reported where it is not supplied.
- **What the films' narration is held to:** an English take passes its units line where the recognizer wrote a
  spelling whose usual pronunciation is a reading of the text word (724 pairs over the films' words; option 2 would
  add 43 that sound different); a take the owner heard passes the lines he settled; a thought under its clarity line
  waits for his ear instead of being retaken. No take that passes today is refused, apart from the new refusals that
  name a missing dictionary, a malformed record or a stale one. The clarity route and the listener are the owner's
  decisions (D-46; the films session under his delegation); the English rule is his choice of option 1 (D-49).
- **A film that adopts:** runs the supply step once more; changes no source; may add `[[narration.heard]]` records.
  Its takes, their requests and their fingerprints are unchanged, so nothing is narrated again for this Change.
- **Release:** a minor release of its own, the next after 0.31.0, before the fused film narrates its next round; not
  the derivation's R4, which waits for R2a and R2b (design decision 8).
- **Drafts:** none of the open drafts is edited.

Owner: the engine's maintainer.

## Sources

Numbered as in the design.

- **[S1]** `build/evidence/owner-words.md` in the engine's repository, items D-44, D-46 and D-49.
- **[S2]** `build/evidence/engine-derivation/derivation-2026-11-23.md` in the engine's repository: §8 finding 1.
- **[S3]** The engine at `v0.31.0`, the files and lines that the design cites.
- **[S7]** The fused film's trial: the judgments of the three trial copies, the retake plan and the owner's ear check.
