## Context

`src/filmkit/delivery/packaging.py` writes each film's iTunes item-list tags (`release_tags`) and its QuickTime keys (`quicktime_keys`) from the edition's script, and records the film's production inputs by SHA-256 (`film_inputs`); `verification.py` refuses a delivered film whose tags differ from the release's or that carries any other QuickTime key (`only_release_keys`). `player.py` renders each edition's page and the entry page; the line under an edition's title reads `Yang HENG · 中文 · 25:00 · 60 fps`.

Each film repository already keeps a `VERSION` file under Semantic Versioning (the DDWG film 1.2.0, the ETHOS film 1.0.1, the essentials film 0.0.0), and `CHANGELOG.md` follows Keep a Changelog.

A probe film packaged by hand with ExifTool 13.55 on macOS 26 showed what Spotlight imports (`mdimport -t -d2`): the QuickTime key Information becomes `kMDItemInformation` and Comment becomes `kMDItemComment`; Title becomes no attribute. ExifTool writes no QuickTime key named Version.

## Goals / Non-Goals

**Goals:** a viewer can tell from a delivered file and from its page which edition it is; the version has one source; a film packaged under another version cannot pass verification.

**Non-Goals:** showing the version in the picture, which would need a render; changing the films' file names, which the pages, players and release manifests use; versioning previews differently from deliveries.

## Decisions

### The repository's `VERSION` is the only source

The films' repositories already maintain `VERSION` for their releases, so the engine reads it at the film's root rather than adding a field to the declaration. It must be a Semantic Versioning 2.0.0 version without build metadata (`1.3.0`, `2.0.0-rc.1`); packaging refuses anything else, naming the file. The record binds it as `version_sha256` among the production inputs, so `stale_bindings` reports a changed version like any other changed input.

### The version goes into the QuickTime key Information

Information is free text, ExifTool writes it, and Spotlight imports it. Title stays the film's name: a version in it would show in every list and in the player's title. The value carries a label in the edition's language, 版本号 for Chinese and Version for English, so that it reads on its own wherever an index shows it. 版本号 is used because the Chinese page already says 视频版本 for its choice of 1080p and 4K films. `only_release_keys` admits the new key because it is one of the release's keys.

### The pages name the version beside the author

An edition's page adds the label and version to the line under its title, after the language: `Yang HENG · 中文 · 版本号 1.3.0 · 25:00 · 60 fps`. The entry page names it under the film's title with both labels, `版本号 / Version 1.3.0`, in a line of its own just before the `<nav>` that holds its language links, so that the title and its subtitle stay together; packaging refuses an entry page whose language links stand in no `<nav>`. The viewing package records the version both pages name, and the verifier refuses one that differs from `VERSION`. The browser readback reads the page as before.

### A film repository sets its version before it packages

Packaging reads `VERSION` from the working tree, so a repository sets the version of the edition it builds, commits it, and then packages and reviews that build. An edition delivered to replace a delivered one takes the next version, so that two delivered editions never share one.

## Risks / Trade-offs

- [A version on a build that is never released] → Only reviewed builds are delivered, and a later repair takes the next version; previews carry the version they were packaged with.
- [Every film is packaged again on adoption] → Packaging copies the pictures and soundtracks; no render is needed, and a focused review proves the streams unchanged.

## Migration Plan

Release with the one-frame comparison as 0.19.0. Each film sets `VERSION`, adopts the release and packages again before its next delivery. Rollback pins 0.18.0.

## Open Questions

None.
