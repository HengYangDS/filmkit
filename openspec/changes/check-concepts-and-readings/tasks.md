# Tasks

## 1. Concept contract

- [x] 1.1 Accept an optional `concepts` path in the film declaration and load the contract it names into a checked model that refuses malformed entries, repeated ids and source paths the manifest does not pin; verify with tests for each refusal and for a film without a contract.
- [x] 1.2 Verify each quotation in its document at the pinned commit of the clone named by `FILM_SOURCE_CHECKOUT`, compared as plain text without Markdown emphasis or code marks; verify with tests for a found quotation, a missing one, an unreadable document and no clone.
- [x] 1.3 Check each segment's declared concepts in both editions, their renderings in the narration, and every counterexample in narration, titles, caption terms and picture sources, reporting all failures together; verify with tests for each refusal and its named location.
- [x] 1.4 Report the check from `python -m filmkit.concepts`; verify with a test of its report and its refusal exit.

## 2. Spoken readings

- [x] 2.1 Add `pypinyin` at its latest stable release through `uv`; verify that `uv sync --frozen` installs it from the lock.
- [x] 2.2 Ship the watch list of word-class and single-character-class Mandarin characters as package data; verify with a test that every listed character has more than one dictionary reading and that the wheel carries the list.
- [x] 2.3 Resolve every watched occurrence of a schema version 2 contract through declared words and declared single characters, check declared readings against the dictionary, require a reason for each contextual disagreement and refuse stale declarations; verify with tests for each refusal, for a recorded disagreement and for a version 1 contract.
- [x] 2.4 Require a declared spoken form for every Latin word in the Chinese narration and every English word with two or more capitals; verify with tests for both refusals.
- [x] 2.5 Write each edition's occurrence plan and report the check from `python -m filmkit.narration.readings`; verify with a test of the plan's rows and the refusal exit.
- [x] 2.6 Propose a declaration for each unresolved Chinese occurrence from the dictionary's phrase segmentation, without changing the contract; verify with tests of the proposals, the widening of a word character and the unchanged contract.

## 3. Gates and review

- [x] 3.1 Run both checks in `filmkit.narration.narrate` before any speech model loads, including a dry run; verify with tests that a refusing check stops a dry run and a passing one proceeds.
- [x] 3.2 Name the concept contract and the occurrence plan in the reviewer prompt context; verify with a test of the context for a film with and without a contract.

## 4. Sample film and documents

- [x] 4.1 Declare a concept contract, segment concepts and a schema version 2 pronunciation contract in the sample film so both checks pass on it; verify that the sample film's narration plan runs.
- [x] 4.2 Describe what a film provides for both checks in `README.md`, and record the change in `CHANGELOG.md` under Unreleased; verify the Markdown formatting check.

## 5. Verification

- [x] 5.1 Run the engine's tests and gates; verify that `mise run check` and the gate-exact Ruff pass with the coverage the gates require.
- [x] 5.2 Run both checks on the `ddwg-film` and `ethos-film` scripts as they stand; verify that each check runs to a complete report on real scripts, and record the reports for the films' own Changes.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it after the alpha.26 rebind and close out.
- Publish with the next engine release after the user confirms that release.
