## ADDED Requirements

### Requirement: A round's prompts require a disposition of every previous finding

`review.round prompts` with a previous round SHALL require `--dispositions <file>`. The file gives each finding of the previous round's reviews one disposition: fixed, with the evidence that its reverification holds; declared, with the design section that keeps it; or deferred, with its owner and reason. The command SHALL refuse a finding without a disposition, a disposition for a finding the previous round does not hold, and a disposition without its evidence or reason.

#### Scenario: A note left without a disposition

- **WHEN** the previous round holds 28 findings and the dispositions file names 27
- **THEN** the command refuses and names the finding without a disposition

### Requirement: The prompts state each disposition

The prompts SHALL state the dispositions in three groups, fixed, declared and deferred, so that the reviewers re-verify each fixed finding by its reverification line and judge the others.

#### Scenario: Every finding disposed

- **WHEN** each finding has a disposition with its evidence or reason
- **THEN** the prompts state the dispositions in their three groups

### Requirement: A bound build is set aside before it is rebuilt

Assembling a soundtrack, and refreshing an edition's captions, SHALL refuse while a review round's prompts bind the edition's current films and that round has not been set aside. The refusal SHALL name the round and the set-aside command.

#### Scenario: Assembling over a reviewed build

- **WHEN** round 7's prompts bind the edition's current films and round 7 has not been set aside
- **THEN** assembly refuses before it writes anything and names round 7 and `review.round set-aside --round 7`

#### Scenario: A set-aside round

- **WHEN** the round that bound the edition's films has been set aside
- **THEN** assembly proceeds
