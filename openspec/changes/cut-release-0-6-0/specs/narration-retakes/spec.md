## Purpose

Keep each thought retake bound to the text and the speech it was auditioned on, so that a seed is never narrated against speech it was not chosen for.

## ADDED Requirements

### Requirement: A retake binds the speech it was auditioned on

A thought retake SHALL record the SHA-256 of the spoken text its audition narrated, beside the SHA-256 of its display text. Synthesis SHALL refuse a retake whose recorded spoken text differs from the thought's current spoken text, and name the segment and thought. A retake that records no spoken text SHALL bind by its display text alone.

#### Scenario: A reading changes after the audition

- **WHEN** a pronunciation change alters the spoken text of a retaken thought but not its display text
- **THEN** synthesis refuses that retake, names the thought and narrates nothing

#### Scenario: Unchanged speech narrates as before

- **WHEN** a thought's display text and spoken text both equal the ones its retake records
- **THEN** synthesis applies the retake's seed and run-on as before

#### Scenario: A retake bound before 0.6.0

- **WHEN** a retake records no spoken text and its display text matches the thought's
- **THEN** synthesis applies it as before

### Requirement: An audition's proposal binds the speech it narrated

Binding an audition's proposals SHALL record each proposed seed with the display text and the spoken text that the audition narrated. It SHALL refuse a proposal that records no spoken text, or whose spoken text is no longer the thought's current spoken text.

#### Scenario: Proposals from a stale audition

- **WHEN** a proposal's spoken text differs from the thought's current spoken text
- **THEN** binding refuses, names the thought and leaves the cast unwritten

#### Scenario: A current proposal

- **WHEN** a proposal's display and spoken texts are the thought's current ones
- **THEN** binding records the seed with both texts' SHA-256
