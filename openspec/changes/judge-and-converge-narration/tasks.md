## 1. Units by reading

- [ ] 1.1 Compare recognition units by reading in `narration/recognition.py`: a Han character's reading in its context from `narration/readings.py`, a declared word's reading where the contract declares one, the particles 的, 地 and 得 as one, a Latin unit only as itself; verify `tests/narration/test_recognition.py` (homophones, particles, another tone, a dropped unit, an English take, a declared word).

## 2. One judgment of a take

- [ ] 2.1 Add `narration/judgment.py`: the measures of a take moved out of the audition, the film's held lines (releases, clarity floor, thought line, kept thoughts), a take's verdict on every line with every failing line named, a take's clarity on the 16 grids of a thought, and the choice among judged takes; verify `tests/narration/test_judgment.py`.
- [ ] 2.2 Have `narration/audition.py` measure its takes through `judgment` and rank by units differing by reading, with no other change of what it proposes, and bind proposals through one function the convergence shares; verify `tests/narration/test_audition.py` unchanged but for the count by reading in a take's record, and that the module stands under 300 non-blank lines.

## 3. Commands

- [ ] 3.1 Add `python -m filmkit.narration.judge`: every thought of the edition's receipt judged, one record beside the receipt, exit 1 with every refused thought and every failing line; verify `tests/narration/test_judgment.py` (two refused thoughts, the same record on a second run, a stale receipt refused before any model).
- [ ] 3.2 Add `python -m filmkit.narration.converge`: narrate what is missing, judge, rounds of candidates at the audition's seeds for refused thoughts, the choice bound into the cast's retakes, a run-on round, the record, exit 1 for what is not narratable as written, nothing repeated on a second run, and a request to end under `child_processes.ending`; verify `tests/narration/test_converge.py`.

## 4. Acceptance

- [ ] 4.1 Run `judge` and `converge --rounds 2 --takes 3` on both editions of a whole film whose casts' retakes are emptied, as host tickets, and record per edition the thoughts refused after the first take, settled after each round and unsettled at the end by line, the takes generated and the wall seconds with the host's load and memory; verify that `build/evidence/judge-and-converge-narration/report.md` holds the table with its records and commands.
- [ ] 4.2 Run every command of `mise run check` with the suite's warnings as errors and the proof's static lint; verify that each passes on the Change's head.
- [ ] 4.3 State the two commands, the comparison by reading and what a film's declarations decide in the README and the Changelog; verify the repository's Markdown check on both files.

## 5. Repair after the independent review

- [ ] 5.1 Hold a take to its words: Latin units by their letters and digits and joined, no Latin unit alike to a Han character, the particle rule only where the text says a particle, and a units line with a limit of none differing by reading; verify `tests/narration/test_recognition.py`, `test_judgment.py` (a spelling passes, another word is refused) and `test_converge.py` (a candidate that is not heard to say its text is never bound), after the measurement on the stored first takes (`build/evidence/judge-and-converge-narration/units-line/measure.txt`: no run refuses more than three thoughts of 46).
- [ ] 5.2 Give each rule the judgment shares with a gate one owner (`take_edges.kept_ending` and `opens_recording`, `review.clarity.thought_lines` and `under_its_line`, `group_generation.too_short`, `selection.narrated`) and have the audition qualify by the judgment's lines; verify `test_judgment.py` (the assembly and the judgment keep the same endings; `preflight` and the judgment refuse the same thoughts) and `test_audition.py`.
- [ ] 5.3 Close the convergence's gaps: a narration due where a check's output is not of the receipt, the record `running` from the first effect, a candidate found again only under the same request, a run-on take whose alignment misses and a take of one second or less as refused candidates, a thought first refused by the last narration named as untried, the selection's gates asked after each narration, a started request named by its file, and a cast that declares another receipt refused; verify `test_converge.py`, with two tests through the engine's own synthesis.
- [ ] 5.4 Collect the narration tests on a host without the speech runtime: the judgment imported inside the fixtures that need it, and the two new test modules listed with the modules that load the runtime; verify `tests/narration/test_recognition.py` and `test_flow.py` with `mlx` made unloadable.
- [ ] 5.5 Run the acceptance of 4.1 again on the repaired tree, since the units line changes what is accepted; verify that the record states, per edition, the thoughts refused for units and whether a candidate settled each.
