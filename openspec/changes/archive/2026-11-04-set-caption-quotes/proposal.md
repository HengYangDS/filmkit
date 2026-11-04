# Proposal

## Why

On 2026-11-04 the fifth typography re-check of the ETHOS v2 drafts found three Chinese caption cues that begin with a closing quotation mark: ”这句话，到底说明了多少？, ”照这句话去做，最该留下的那些更正，恰好会被删掉。 and ”按 ETHOS 的做法，这句话后面要跟着存证：. The narration writes 。” together. The caption phrasing splits a Chinese passage into clauses that each end at a clause mark, so a closing quotation mark after a sentence end starts the next clause, and with it the next cue.

The same check found that the English edition's captions set its straight double quotes as typed ("Done. All tests pass."), while the picture sets them as typographic quotes. The display copy turns only an apostrophe into a typographic quote. Both reach every film's captioned edition, its SRT and VTT subtitles and its transcript.

## What Changes

- A Chinese caption line keeps the closing quotation marks and brackets that follow its last punctuation mark, as an English caption line already does, so no cue begins with one.
- The display copy sets a straight double quote as a typographic one: an opening quote where it begins a word, a closing quote elsewhere, as it already sets an apostrophe as a right single quote. A cue's text, its timing and the waveform do not change.
- The sample film's captions do not change, because its scripts hold no such quotes.
- Record the fix under `Unreleased`, date it as `[0.8.1]`, and set `VERSION` and the README pin to 0.8.1.

## Capabilities

### New Capabilities

- `caption-text`: how a caption line keeps its punctuation and how the display copy sets quotation marks.

### Modified Capabilities

None.

## Impact

The Change touches `src/filmkit/captions/chinese.py`, `src/filmkit/captions/timing.py` and their tests in `tests/captions/`, and `README.md`, `CHANGELOG.md` and `VERSION`. A film that adopts 0.8.1 refreshes its captions with `produce refresh-captions`, which changes only the cues that hold such quotes; its picture does not change. ETHOS v2 adopts it before its render. In the 0.x series this is a patch release.
