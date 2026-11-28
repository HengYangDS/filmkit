---
subject: filmkit:film-tests
role: reference
state: active
relations:
  projects:
    - ../openspec/specs/film-engine/spec.md
    - ../openspec/specs/sample-film/spec.md
---

# A film's tests and the sample film

A film's tests import only `filmkit.api` and one Node module, `filmkit.api.TEST_ENTRY` (`filmkit/picture/testing.mjs`), which opens the composition and the film's own modules headlessly.

## The sample film

`examples/sample-film` is a film of two editions whose text is written for the engine's tests. Its tasks run the verbs in its folder: `mise run sample:supply`, `sample:check`, `sample:narrate`, `sample:build` and `sample:verify`.
