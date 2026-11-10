## Why

The owner asked on 2026-11-10 that each delivered film carry its version (「按你推荐的补上版本标识」). Today nothing in a delivered film says which edition it is. Its QuickTime keys name the author, title, album, genre, description, comment, copyright, keywords and year, and its player page names the author, language, runtime and frame rate. In two weeks each film was delivered again many times (the DDWG film from review rounds 29 to 36), and files from different editions look the same.

## What Changes

- Packaging reads the film repository's `VERSION`, a Semantic Versioning 2.0.0 version, and writes it into each film's QuickTime key Information, as 版本号 1.3.0 in a Chinese edition and Version 1.3.0 in an English one. Spotlight imports the key as `kMDItemInformation`. Packaging refuses a film whose repository has no valid `VERSION`.
- The film package record binds `VERSION` with the other production inputs, so a film packaged before the version changed is stale and is packaged again.
- Each edition's player page names the version in the line under its title, and the entry page names it under the film's title.
- The verifier refuses a delivered film or page whose version differs from `VERSION`.
- **BREAKING**: a film packaged by 0.18.0 is stale under this release and is packaged again. A film repository sets `VERSION` to the edition it builds before it packages it, and an edition delivered to replace a delivered one takes the next version.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `film-package`: a delivered film and its pages name the film's version.

## Impact

`src/filmkit/delivery/packaging.py`, `player.py` and `verification.py` and their tests, the sample film's new `examples/sample-film/VERSION`, the README's paragraph on packaging and the release notes. Films adopt the release before their next package; no picture or sound byte changes.
