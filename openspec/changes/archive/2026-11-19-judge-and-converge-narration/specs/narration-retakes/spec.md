## MODIFIED Requirements

### Requirement: An audition's proposal binds the speech it narrated

Binding an audition's proposals, or the choices of a narration's convergence, SHALL record each proposed seed with the display text and the spoken text that the take was narrated from. It SHALL refuse a proposal that records no spoken text, or whose spoken text is no longer the thought's current spoken text.

#### Scenario: Proposals from a stale audition

- **WHEN** a proposal's spoken text differs from the thought's current spoken text
- **THEN** binding refuses, names the thought and leaves the cast unwritten

#### Scenario: A current proposal

- **WHEN** a proposal's display and spoken texts are the thought's current ones
- **THEN** binding records the seed with both texts' SHA-256

#### Scenario: A convergence's choice

- **WHEN** a convergence chooses a candidate of a refused thought
- **THEN** the cast's retakes hold that candidate's seed with both texts' SHA-256, and its run-on when the candidate was read on, in the form an audition's binding writes
