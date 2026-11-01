# Design

## Context

See `proposal.md` for the defect. Three engine parts meet at a thought's ending. `narration.take_edges.ending` judges a take: quiet final 30 ms, a final syllable that dies away to -55 dBFS, and no voiced fall faster than 6 ms. `soundtrack.pauses` and `soundtrack.assembly` place digital silence after each thought and fade a recording that is still heard there over 60 ms, or over the seconds a film declares in `released_tail_seconds` for that join. `review.endings` reports both the takes and the delivered soundtrack to the reviewers. Before this change, only the report read the take judgement, and nothing acted on it.

## Goals / Non-Goals

**Goals:**

- No edition assembles with a thought whose take stops inside its last syllable, unless the film has declared that release.
- The delivered-endings report agrees with what a listener hears.
- Every thought, including one that ends an English segment, can be retaken as a run-on.

**Non-Goals:**

- Changing the take criterion, the release length or how narration synthesizes takes.

## Decisions

**The assembly enforces the take judgement.** The assembly is where a still-sounding take is faded, so it refuses there, naming every abrupt thought at once after it binds the selected recordings and before it decodes them. Refusing at narration was rejected: auditions read the narration receipt, so narration has to finish before a thought can be retaken. Refusing at delivery verification was rejected because it comes after the picture is timed and rendered. A declared release stays the explicit exception, because the film's performance contract already owns that decision for a thought whose every take still sounds.

**The judgement is the existing take criterion.** The assembly calls `take_edges.ending` on each thought take that the selected record binds, the same function the audition uses to propose takes and the review uses to report them. One criterion keeps the audition, the gate and the report in agreement.

**The report finds the true stop.** The stop is searched from the start of the thought's last word rather than its aligned end, because the aligner can place that end after the sound has stopped. A released thought is judged on the 20 ms before its release, where the voice was cut, rather than 70–90 ms earlier.

**The run-on joins with a space only where words need one.** `following_spoken_text` adds a space when the thought ends in Latin text without whitespace and the following text begins with a Latin letter or digit. Chinese thoughts and English thoughts that already end with a space are unchanged, so every existing cast keeps its run-on texts.

## Risks / Trade-offs

- [A film with abrupt bound takes no longer assembles on this engine] → The refusal names each thought, and the audition retakes it; a film adopts the release only with a new edition. The DDWG films and the repaired `ethos-film` have no abrupt take.
- [The take criterion refuses a take a listener would accept] → The film declares a release for that join, and the refusal does not apply to it.
- [The report's numbers change for existing records] → Only the report changes; the soundtrack, captions and timeline do not.

## Migration Plan

Released with the next engine release. A film that adopts it narrates, assembles, reviews and accepts an edition on it, as the engine contract requires.
