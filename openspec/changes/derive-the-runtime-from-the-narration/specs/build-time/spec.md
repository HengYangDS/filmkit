## MODIFIED Requirements

### Requirement: A build counts the convergence that narrated it

Where an edition's latest whole narration started within the run of a convergence, the build SHALL start at that convergence's record `converge`. Where the convergence completed, the sum SHALL count it and list the narration as inside it without adding its seconds again. Where it did not complete, the sum SHALL leave the convergence out and count the narration.

#### Scenario: A converged edition

- **WHEN** a convergence of 343 s ran two narrations, the last of 41 s, and a render of 200 s followed
- **THEN** the build's sum holds 543 s, the narration's record is listed as inside the convergence, and the sum's line says that the build began at the convergence

#### Scenario: A convergence that did not complete

- **WHEN** a convergence of 343 s ran a narration of 41 s and ended with its edition refused by the assembly, and a render of 200 s followed
- **THEN** the convergence is listed as not completed and left out, and the build's sum holds 241 s: the narration and the render

#### Scenario: A narration after an earlier convergence

- **WHEN** an edition converged in an earlier build and is now narrated whole without a convergence
- **THEN** the build starts at that narration, and the earlier convergence's record is listed as earlier and left out
