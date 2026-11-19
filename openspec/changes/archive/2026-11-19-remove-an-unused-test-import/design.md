## Context

See [proposal.md](proposal.md). ETHOS's static gate lints the tracked `.js`, `.mjs` and `.cjs` files of a repository with its own ESLint and its own rules; it read 74 files of this one [S1]. The repository's check runs the Node suite, the Markdown check and the Python suite [S5], and none of them reads an import that nothing uses.

## Goals / Non-Goals

**Goals:**

- The static gate reports no message for the repository's JavaScript.

**Non-Goals:**

- A JavaScript linter of the repository's own. The gate's linter and its rules are ETHOS's, and a second linter here would be a second authority for the same rule and a new supply to hold. What is missing is a way to run the gate's lint before a proof without the proof's slot: asked for alone, the gate answers that behaviour is unproven and checks nothing [S4]. That is ETHOS's to offer and is put to its maintainer; this release is prepared with ETHOS's own lint run on the head before its proof is queued again [S3].

## Decisions

1. **The import is removed, and nothing else in the file changes.**
   - **Rests on:** the proof's record, one message in 74 files: `no-unused-vars` at line 8, column 10, for `fileURLToPath` [S1]; the commit that left it, which removed the constant `ENGINE`, the name's only use [S2]; ETHOS's lint run again on the lane's head, which reports the same message and no other, and on a copy of that head without the line, which reports none in 74 files [S3].
   - **Considered:** (a) removing the import; (b) a comment that exempts the line from the rule.
   - **Chosen because:** nothing in the file needs the name, so (b) would keep a dead line and state a reason that no reader could find.
   - **Applies to:** `tests/picture/headless-composition.test.mjs`.
   - **Reopened when:** not applicable.

## Risks / Trade-offs

- Another finding may stand that only the gate's run inside a proof would show. → The lint of [S3] is the gate's own adapter and linter, run over the same 74 files, and its only message on the lane's head is the one the proof reported.

## Sources

Read or measured on 19 November 2026, except [S4]. Paths under `build/evidence/` are the canonical checkout's local evidence.

- **[S1] The proof of 19 November 2026:** ETHOS 0.2.0-beta.10 on the lane's head `a620a57`, queued 09:12:42, admitted 10:06:30 and refused 10:07:11 CST; the JavaScript entry of its static gate (tool `eslint`, exit 1, 74 paths checked, one message) is kept as `build/evidence/remove-an-unused-test-import/proof-static-message.txt`.
- **[S2] The commit that left the import:** `3160404` of 18 November 2026, "feat(picture): draw pictures on a native canvas, with no browser"; its diff of `tests/picture/headless-composition.test.mjs` removes the constant `ENGINE`, built with `fileURLToPath` from the path of the animation library under `node_modules`.
- **[S3] The lint run again:** `build/evidence/remove-an-unused-test-import/js-static-a620a57.json` (one message, the proof's) and `js-static-repaired.json` (74 paths, no message), each the answer of ETHOS 0.2.0-beta.10's `static_observation` for the tracked JavaScript of the tree, read-only; `node-repaired.txt` beside them is the file's tests on the copy with the repair (14 tests, 14 pass, with the host's FFmpeg hidden).
- **[S4] The static gate asked for alone:** `build/evidence/remove-an-unused-test-import/static-gate-alone-6dc4105.json`, the answer of ETHOS 0.2.0-beta.10 on 18 November 2026 to `prove --host --execute --gate native-static` on the head `6dc4105` of an earlier lane: verdict `block`, state `gapped`, `quality_obligation_unproven:behavior`, no check run.
- **[S5] The repository's check:** `.config/mise/config.toml` at `a620a57`, the task `check` (`npm test`, `npm run format:markdown:check`, the Python suite) and `check:dependencies`, on which it depends.
