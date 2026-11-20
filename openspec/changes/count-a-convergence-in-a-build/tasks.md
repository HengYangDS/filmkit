## 1. The record

- [ ] 1.1 Open the convergence's run in `narration/converge.py` and name its phases `narration`, `judgment`, `candidates` and `count`, the run told that it failed where the edition ends unsettled or refused; verify `tests/narration/test_converge.py` and `tests/narration/test_converge_fit.py`: a convergence of two narrations writes `converge` with the three phases and both narrations in the first, an unsettled edition's and a missed runtime's record say that the command did not complete, a settled edition's says that it did, and a convergence refused before its first effect (`test_a_convergence_refused_before_its_first_effect_writes_no_duration_record`: a negative reserve, a refused pause policy, a receipt declared elsewhere, a former record that cannot be read, a leftover request) writes no `converge` record and leaves a standing one byte for byte; `tests/narration/test_converge_fit_refusals.py` passes unchanged.

## 2. The sum

- [ ] 2.1 Start a build at the `converge` record whose run holds the latest `narrate` record's start, count that convergence, and list the narration as inside it without adding its seconds; verify `tests/test_build_durations.py`: a convergence of 343 s with a last narration of 41 s and a render of 200 s sums to 543 s with the narration listed as inside, a narration after an earlier convergence starts the build and leaves the convergence out as earlier, a convergence that needed no narration is counted after the narration that stands, a convergence that did not complete is left out with its narration counted, and an edition without a convergence prints what it printed.
- [ ] 2.2 State the convergence's record and the build's start in the README's paragraph on duration records and in the Changelog's unreleased section; verify the repository's Markdown check on both files.

## 3. Acceptance

- [ ] 3.1 Run every command of `mise run check` and the proof's static lint on the lane's head; verify that each passes.
- [ ] 3.2 Run the convergence on the sample film's English edition after a sample build, as the child of a host ticket since it loads the judgment's models, and print the durations; verify that `build/evidence/count-a-convergence-in-a-build/sample.txt` holds a `converge` record that is counted in the edition's sum after the narration that stands.
