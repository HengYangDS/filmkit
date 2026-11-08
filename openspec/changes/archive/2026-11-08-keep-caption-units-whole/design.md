# Design

## Context

See proposal.md for why. The English phrasing (`captions/english.py`) first divides a segment into caption sentences: `english_caption_sentences` cuts after each run of sentence marks and the closing marks after it, and divides a sentence longer than the caption limit of 66 characters at its semicolons. No caption crosses the end of one of these units. Within each unit, `_cheapest_lines` chooses the lines whose summed cost is least: a line costs 16, the cost of its break, 90 more when it is short and the square of its distance from 48 characters over 80. `_break_cost` adds 90 to a break inside a declared caption term, the same as a line that ends on a word that binds to what follows, such as "for" or "the", where no punctuation closes the phrase.

On the ETHOS film's sentence "Its name stands for Evidence-grounded Trust for Human-Agent Operational Stewardship.", the term is 64 characters. The only break that keeps it whole ends the first line on "for" and leaves a short line of 19 characters, so its layout costs 171.7, against 135.1 for the split after "Trust". On "An Agent hands back one sentence: "Done. All tests pass."", the splitter ends a unit after "Done." although the quotation is still open, so the quotation spans two cues. The review's sentences (`review/sentences.py`) already keep a quotation whole: no mark inside one ends a sentence.

## Goals / Non-Goals

**Goals:**

- A declared caption term that fits a line is never split, as the caption-text requirement says.
- A quotation of several short sentences reads as one caption when it fits one.

**Non-Goals:**

- Chinese captions: a Chinese caption ends a sentence inside a quotation by design, and the Chinese phrasing has no declared terms.
- Changing the line costs, which set every caption the three films show today.

## Decisions

### A term split counts before the line costs

`_cheapest_lines` compares layouts first by how many of their breaks fall inside a declared term and then by their summed cost, and `_break_cost` no longer adds 90 for such a break. A layout that keeps every term whole therefore wins whenever one exists, however short a line or awkward a line end it needs; among layouts that keep the terms whole the costs are the ones the phrasing had, so a sentence whose term was never split is set as before. A term longer than a line takes the fewest splits and, among those, the cheapest breaks.

Alternatives considered: waiving the 90 for a line that ends on a function word where a term begins, as the reviewer proposed, keeps this sentence whole too, but it lets every such line end on "and" or "for" before any declared term, which moved breaks that split no term in four segments of the ETHOS film, three of the DDWG film and two of the essentials film. A large constant for a split works only while no layout costs more than it.

### A quotation keeps its sentences together while they fit

`english_caption_sentences` joins a unit that ends inside an open quotation to the next unit while the two, without the spaces after them, fit the caption limit, and repeats while the quotation stays open and the joined unit fits. A quotation opens and closes as the review's sentences read it: at “ ‘ 「 or 『 and its closing mark, or at a straight double quote and the next one. The marks move from `review/sentences.py` to `narration/spoken_units.py`, which holds the other marks both read, so the captions and the review share one definition. A unit longer than the limit after joining stays apart, so a long quotation divides at its sentences, and at its semicolons when a sentence is longer than the limit, as before.

### The films' current captions

Measured with this phrasing on each film's English script at the start of the change: the ETHOS film's segment 03 keeps its name whole ("Its name stands for" | "Evidence-grounded Trust for Human-Agent Operational Stewardship."), and segments 01 and 09 keep "Done. All tests pass." with the sentence that holds it on one line; the DDWG film's segment 28 keeps its declared list whole ("Agent output standing in for" | "fact, authorization or responsibility."); the essentials film's captions are unchanged.

## Risks / Trade-offs

- [A whole term can leave a line ending on a function word] → It happens only where the film declares the term, so the film chooses it, and the reviewer of the ETHOS film proposed exactly that line.
- [A joined quotation can make a caption longer than the units it replaces] → It stays within the limit of 66 characters, the limit of every other caption.

## Migration Plan

Release 0.15.0. Each film refreshes its captions; where they change, its captioned picture is staged, checked, rendered and compared again, and its package and delivery follow. Rollback pins 0.14.0 again.

## Open Questions

None.
