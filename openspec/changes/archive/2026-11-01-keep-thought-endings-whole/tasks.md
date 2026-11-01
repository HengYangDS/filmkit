# Tasks

## 1. Implementation

- [x] 1.1 Refuse an edition in the assembly when a bound thought take does not end naturally and its join declares no release, naming every such thought; verify with tests that an abrupt take refuses with its name, a declared release proceeds, and natural takes assemble unchanged. The refusal names 01.1 and 02.2 before any recording is decoded, a release declared for 01.1 proceeds to decoding, and natural takes give the same soundtrack bytes (`tests/soundtrack/test_assembly.py`).
- [x] 1.2 Take each delivered thought's stop at the first digital silence after its last word begins, and judge a released thought on the 20 ms before its release; verify with tests on a soundtrack whose voice stops before its aligned end and one released at full voice. Both are listed as cut while voiced, and each test failed before the change (`tests/review/test_measurement.py`).
- [x] 1.3 Begin a run-on with a space when the thought ends in Latin text without one and the following text begins with a Latin letter or digit; verify with tests for an English thought that ends its segment and for Chinese thoughts. The segment-final thought reads on into " Then decide."; a thought ending in a space and the Chinese thoughts keep the following text unchanged (`tests/narration/test_run_on.py`).
- [x] 1.4 Record the change in `CHANGELOG.md` under Unreleased; verify the Markdown formatting check. The entries are under Changed (breaking) and Fixed, and the Prettier check passes.

## 2. Verification

- [x] 2.1 Run the engine's Python and Node tests and the gate-exact Ruff; verify that they pass. `mise run check` passed at 20:03 (646 Python and 63 Node tests, Prettier), and the native-static Ruff selection and format check pass on the changed files.
- [x] 2.2 Judge real bound takes with the new refusal; verify that `ethos-film`'s `v1.0.0` takes name its eighteen abrupt thoughts, and that its repaired takes and `ddwg-film`'s takes name none. `v1.0.0` names zh 01.4, 03.2, 04.4, 05.2, 05.5, 06.3, 06.5, 07.2, 07.4, 10.1, 11.2, 12.4, 13.6, 14.5, 16.2 and 16.4 and en 11.5 and 18.1; the repaired takes and DDWG's 347 bound takes name none, every take's bytes matching its record (`build/evidence/endings/2026-11-01-real-take-refusal.jsonl`).

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Publish with the next engine release after the user confirms that release.
