# Tasks

## 1. Implementation

- [ ] 1.1 Refuse an edition in the assembly when a bound thought take does not end naturally and its join declares no release, naming every such thought; verify with tests that an abrupt take refuses with its name, a declared release proceeds, and natural takes assemble unchanged.
- [ ] 1.2 Take each delivered thought's stop at the first digital silence after its last word begins, and judge a released thought on the 20 ms before its release; verify with tests on a soundtrack whose voice stops before its aligned end and one released at full voice.
- [ ] 1.3 Begin a run-on with a space when the thought ends in Latin text without one and the following text begins with a Latin letter or digit; verify with tests for an English thought that ends its segment and for Chinese thoughts.
- [ ] 1.4 Record the change in `CHANGELOG.md` under Unreleased; verify the Markdown formatting check.

## 2. Verification

- [ ] 2.1 Run the engine's Python and Node tests and the gate-exact Ruff; verify that they pass.
- [ ] 2.2 Judge real bound takes with the new refusal; verify that `ethos-film`'s `v1.0.0` takes name its eighteen abrupt thoughts, and that its repaired takes and `ddwg-film`'s takes name none.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Publish with the next engine release after the user confirms that release.
