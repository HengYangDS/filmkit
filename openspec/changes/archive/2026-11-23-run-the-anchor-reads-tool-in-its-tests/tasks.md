## 1. The tool in its tests

- [x] 1.1 Add `tests/picture/anchor-reads.test.mjs`, which runs `src/filmkit/picture/anchor-reads.mjs` as `filmkit.picture.anchor_reads` runs it and holds its report and its exit status. Done when the file's tests pass and each of four broken copies of the tool fails one of them.
- [x] 1.2 Every line of `src/filmkit/picture/anchor-reads.mjs` runs under the Node suite's coverage. Done when the c8 that ETHOS ships reports the file at 100 % of its lines over the new test; at `0b941b1` the gate's report has no row for it.
