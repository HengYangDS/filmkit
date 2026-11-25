## MODIFIED Requirements

### Requirement: A refusal that a repair can answer names the repair

When the repair, `repair-pictures`, can repair every finding of a refused comparison, `compare-pictures` SHALL name the command that runs it, `python -m filmkit.picture.repair`, as the next step in its refusal.

#### Scenario: A fault of one picture

- **WHEN** `compare-pictures` refuses only a fragment that the uncaptioned picture holds for one frame
- **THEN** its refusal names `python -m filmkit.picture.repair --language zh` as the next step
