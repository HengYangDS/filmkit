## REMOVED Requirements

### Requirement: The pre-render check writes a readiness receipt

**Reason**: the run records state what the receipt bound; `preflight` retires.

**Migration**: `filmkit plan` states readiness from the run records, and a render and a package wait for the gates `preflight` asked (`run-records`, "A heavy node waits for the gates on its inputs").

### Requirement: Readiness is checked again without repeating the work

**Reason**: `admitted` retires into the plan's readiness, which reads the records and repeats no work.

**Migration**: `filmkit plan --json`, each node's `ready`.
