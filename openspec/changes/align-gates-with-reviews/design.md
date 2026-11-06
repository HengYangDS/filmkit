# Design

## Context

The proposal's evidence comes from the owner's reviews and listening. The engine's gates already measure balance, pitch, contrast, sync, endings and loudness, but none of them measures four faults that reviewers and the owner found:

- where a label's lines break;
- how long the voice pauses between two words the text joins;
- how a Latin-script term is said;
- whether every finding of the last round was dealt with.

Each check here measures one of those classes. It is calibrated on the current builds of the three films: it must flag the cases reviewers or the owner found and spare the ones they accepted. Unit tests prove each method on synthetic input.

## Goals / Non-Goals

**Goals**

- Refuse, before a render or a soundtrack is accepted, the label breaks, unmarked pauses and term pronunciations that reviewers and the owner judged wrong.
- Keep every exception visible: a film either repairs a fault or declares it with its reason, and the record shows the declaration to reviewers.
- Make each round answer every finding of the previous one, and protect a reviewed build from being overwritten.

**Non-Goals**

- Native production orchestration (`review-build`), and supplying the narration engine separately, are the next releases.
- Gating continuity steps between thoughts. They are recorded and listed for listening until the owner's ear calibrates them.
- Checking a term's pronunciation beyond its first vowel, or the grammar of mixed-language sentences.

## Decisions

### Wrapped labels are judged from the film's own layout records

The frame audit already reads `window.__filmLayout.texts`. Each record holds the painted line, its bounds, size and opacity, and the whole name it belongs to (`whole`, `placed`).

- **Grouping.** The lines of one label share a `whole` and a scene. Pieces on one baseline form one line, and successive lines whose joined text equals the whole form one instance, so the same name may stand in several places.
- **Judgement.** A label is judged once every line stands at 0.9 opacity or more.
- **Rules.**
  - Lead words are articles, prepositions, conjunctions, determiners, possessives, wh-words and auxiliaries, plus the film's declared `lead_words`.
  - The share rule judges the lines of one size together, so a name over its smaller gloss is two blocks.
  - A one-word last line counts only in a name of three or more words. A two-word name stacked on two lines is resolved by its layout or declared.

The defaults are the rule DDWG's design §8 already declares, whose breaks cost its English edition 93 in round 33.

The headless audit measures text by the declared faces' advance widths, the same widths the film's wrapping uses. Task 1.3 confirms that the audit's lines equal a real-browser readback on the three films. The alternative, a real-browser pass inside `check-picture`, would duplicate the geometry check's browser launch and its cost.

### The heard pause is measured between word middles

The heard pause is the longest run of 10 ms frames at least 24 dB below the speech median, between the middles of two adjacent aligned words. The aligner may assign a pause to either word, and the middles bound the quiet whichever word holds it. Words are matched to the text with hyphens and apostrophes allowed inside a written word; the characters between two matches are the boundary's marks.

On the six current soundtracks, the unmarked boundaries have a median of 0–20 ms and a 99th percentile of 40–90 ms. The few at 0.15 s or more are:

- ETHOS Chinese: 0.49 s between 的 and Agent, and 0.19 s between ETHOS and 就;
- ETHOS English: 0.36 s between "commit" and "and";
- essentials English: 0.36 s between "work" and "until";
- essentials Chinese: 0.22 s between 投产 and 或者.

Only the first is inside a phrase; the rest stand at clause boundaries the text leaves unmarked. The limit is therefore 0.2 s at a script switch, where Chinese speech synthesis hesitates, and 0.4 s elsewhere. The boundaries from 0.15 s up to the limit go to the listening plan.

The audition measures candidates the same way and ranks fluent takes first, selection refuses, and the assembly measures the soundtrack again.

### Continuity steps are recorded, not gated

Three steps are recorded between adjacent thoughts of a part:

- the speaking-rate ratio, in Chinese characters or English syllables per voiced second;
- the pitch step, as the median F0 by autocorrelation, in semitones;
- the level step.

On the current builds the within-part steps reach rate ratios of 1.49 and 0.70, a pitch step of 3.1 st on a question, and a level step of 2.2 dB. Questions raise the pitch on purpose and short thoughts give noisy rates, so a gate would refuse sound speech. The listening plan lists the largest steps instead.

### A term's first vowel is compared with a reference a person heard

LPC formants (order 12 at about 11 kHz), taken over the voiced frames of the first 32 % of each aligned occurrence, give the term's first vowel.

On ETHOS:

- The Chinese edition's 20 occurrences cluster at F1 238–332 Hz and F2 2643–2879 Hz (/iː/).
- In the English edition, 15 cluster there, and 5 measure F1 587–775 Hz and F2 1985–2111 Hz (/ɛ/).

A declared reference occurrence, with bounds of 25 % on F1 and 15 % on F2, separates the two clusters by a wide margin. An absolute vowel target would need a calibration for every narrator.

### Dispositions are structured, and assembly guards a bound build

The dispositions file is JSON, with one entry per finding id:

```json
{"round": N, "findings": {"<id>": {"disposition": "fixed" | "declared" | "deferred", ...}}}
```

A fixed entry holds `evidence`, a declared entry holds `design`, and a deferred entry holds `owner` and `reason`. The prompts render the entries in three groups under `{dispositions}`. This replaces a prose changes note that could omit a finding: DDWG round 33 left 19 of round 32's 28 findings without any disposition.

The set-aside guard reads the media hashes that every round's prompts name under `build/evidence/reviews/`. While an edition's current films match a round that has no set-aside record under `build/artifacts/film/superseded/round-<n>/`, `assemble` and `refresh-captions` refuse. A retake driver assembled over a reviewed build twice in two days.

## Risks / Trade-offs

- **[A clause boundary inside an unmarked sentence holds a long natural pause]** → The 0.4 s limit spares the measured clause pauses (0.22–0.36 s). A film declares an exception, with its reason, for a longer one.
- **[Headless widths differ from the browser's]** → Task 1.3 compares every wrapped label on the three films before the gate is trusted.
- **[An existing film is refused when it adopts 0.11.0]** → Output bytes do not change. The refusals name each label, boundary or occurrence, and a film repairs it or declares it.
- **[DDWG holds filmkit 0.5.0 for its narration engine]** → Its labels are checked by the same rules from its staged composition until the engine's voice is supplied separately.
- **[The first-vowel check misses a fault later in a term]** → A person still confirms the reference occurrence, and the listening plan lists each term's occurrences.
