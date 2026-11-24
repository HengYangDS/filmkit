## Why

The release proof of 0.31.0 on the lane's head `e377a2d` failed on 24 November 2026 in its gate `native-behavior` with `quality_behavior_javascript_native_test_scope_incomplete:tests/delivery/film.mjs,tests/picture/lead-words.mjs` [S1]. `treat-languages-as-equals` added the two files as modules that the Node tests import (the sample film as a delivery binding names it, and English's lead words with the wrapping rules) [S2]. They are not tests, and the repository declares each such module by its role in `.gitattributes`, as it does `tests/picture/sample-film.mjs` and `tests/picture/rules/fixtures.mjs` [S3]; the two new ones were not declared.

The Change that added them is archived on this lane, and an archive with a commit after it cannot be returned, so the repair is a Change of its own.

## What Changes

- `.gitattributes` declares `tests/delivery/film.mjs` and `tests/picture/lead-words.mjs` as `ethos-role=tooling`, beside the two test modules it declares already.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement speaks of how a test module's role is declared, and no behaviour changes, so `.openspec.yaml` sets `skip_specs: true`.

## Impact

`.gitattributes` only. No engine behaviour, test, record or byte of a film changes, and the Changelog gains no entry: nothing a film or its maintainer meets changes. Out of scope: the gate's rule, which is ETHOS's. `tasks.md` is the sole progress ledger.
