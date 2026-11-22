## Why

The films' owner made a standard of formal register final on 20 November 2026: a film's language as a whole follows
formal standard written language under strict 信, 达 and 雅 (`build/evidence/formal-register/standard.md`, rules R1
to R6). Each film's review declaration asks the opposite today ("plain spoken language a person would say"), and no
check holds the forms the standard refuses: the released films address their audience in 11 places, use an
inclusive 我们 in 5 and colloquial words in 24 (`build/evidence/formal-register/inventory.md`). The lexical part of
the standard (R1 to R3, and R5's marks) is mechanical and belongs in a check that runs before narration; the rest
(R4 to R6, and the organization of sentences) stays with the reviewers.

A research trial of the same evening (`build/evidence/tooling-assessment-2026-11-20/prose-tools.md`) found that
Vale, the prose linter ETHOS already supplies and pins for its own `prose` gate, carries those rules declaratively,
with rule tests and 0.03 s a film, and matched the inventory's R1 and R2 counts on all three films.

## What Changes

- **The standard's text in the engine's specification** (`formal-register`): R1 to R6 under 信, 达 and 雅, once.
- **A register check** (`python -m filmkit.register`, run by `narrate` and `preflight` beside the concept check): the
  engine renders the edition's words a viewer meets (titles, thoughts, caption terms, release prose, the player summary,
  the entry page), one place a paragraph, runs the pinned Vale once with the engine's register style, maps each alert
  back to its place by a table and applies the film's exceptions. `error` refuses, naming each place at once;
  `warning` is recorded and goes into the review round's inputs.
- **The engine's base style**: R1, R3 and R5 as errors; R2 and R4 as warnings; each rule with its `vale test` cases.
  A listed form is refused wherever it stands; the engine holds no table of words that excuse one.
- **A film excuses a form at one place** in `[[register.exceptions]]` (`place`, `form`, `within`, `reason`: the text the form stands within there, a standard word or a quotation); a stale
  exception is refused, as for the film's other exceptions.
- **Vale pinned in the engine's Mise configuration and lock** at 3.27.0, ETHOS's version; the release record states it,
  the adoption reader reports a film that pins another or none, and the check refuses another Vale on the path.
- **The review round** writes the register report into its inputs; the prompt cites it.
- **The sample film** passes the check, and its review declaration asks for formal standard written language.

## Capabilities

### New Capabilities

- `formal-register`: the standard, and the forms a film's words may not hold, checked before narration and before a
  render.

### Modified Capabilities

- `engine-distribution`: the release record states the pinned Vale, and the adoption reader compares a film's pin.
- `review-rounds`: a round carries the register report and the standard's rules.
- `concept-contract`: the film's entry page is a place where a viewer meets words.
- `sample-film`: the sample passes the register check and its review asks for the formal register.
- `edition-readiness`: the receipt binds the film's entry page.
- `render-preflight`: the pre-render check asks the register.

## Impact

- New: `src/filmkit/register/` (the check and the base style) and its tests; `concepts.places`; `narrate`, `preflight`,
  `review.round prepare`, `released`, `adoption` call it; Mise's configuration and lock; the README and the Changelog.
- **Breaking for a film:** after adopting, a film whose words hold an error-level form is refused before narration
  and before a render, naming each place. Every released film holds such forms (the inventory); each fixes them in
  its December edition, with its owner's approval of the words. A film that adopts also pins Vale as
  `github:vale-cli/vale` in the Mise file of its tasks and has that Vale on the path for narration, the pre-render
  check and a review round, cites `{register}` in its reviewer prompt template, and asks for formal standard written
  language where its review declaration scores language.
- Out of scope: R4 to R6 beyond the warnings, which stay with the reviewers; the picture's words, which join the check
  once the geometry check records the texts it paints; the films' texts; the concept check's counterexamples.
