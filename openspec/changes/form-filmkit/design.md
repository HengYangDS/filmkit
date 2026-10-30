# Design

## Context

`ddwg-film` formed the engine as the package `src/filmkit` inside the film's repository (see that repository's archived Change `form-ddwg-film`). The package already takes the film's identity, editions, review policy and timing from `content/film.toml` and the scripts, but it still finds the film by its own location, stages four named font files, reads the pronunciation contract from a fixed path, and runs its Node tools from its source tree, where Node resolves `puppeteer-core` from the film's `node_modules`. Installed as a dependency, the package would live in a virtual environment, away from any film. The ETHOS introduction film will be built with this engine, so it must work from an installed release and be tested without DDWG content.

## Goals / Non-Goals

**Goals:**

- One engine repository whose release a film installs and pins.
- The engine finds the film it builds, the film's npm packages and the film's declared fonts and contracts, wherever the engine is installed.
- A sample film that the engine's tests load and that builds end to end.
- No output byte of an existing film changes.

**Non-Goals:**

- Publishing, tagging or a package registry; the user confirms each push.
- Moving `ddwg-film` onto the release; its own Change does that and rebuilds both editions under its reproduction standard.
- New engine features, other languages than Chinese and English, or other frame rates.

## Decisions

### Snapshot import

The engine's Python modules and Node tools and the tests that exercise the engine come from `ddwg-film` at `37549a9`, each verified against its blob there. History stays in `ddwg-film`, whose commit the import names. Tests that check one film's content stay with that film: the DDWG composition's Node suite, the check of DDWG's retained receipts, the release manifest checks and the checks of the DDWG scripts and players. The speech-plan tests need golden receipts of real takes; they hold the sample film's own takes of its first segment, so that no DDWG recording remains in the engine's tests.

### Finding the film

The film is the folder that `FILMKIT_ROOT` names, or else the nearest folder at or above the working directory that holds `content/film.toml`. Mise tasks run at the film's root, so a film needs no variable; the engine's tests and any tool that serves several films set it. An explicit `--root` option on every command was rejected because the declaration is loaded when the engine's modules are imported, and the many entry points would each need the option. The film's npm packages are found as Node finds them, in the nearest `node_modules` at or above the film, so the renderer command, the browser installer and the animation library resolve the same way for a film at a repository root and for the sample film in a subfolder.

### What the film declares

The declaration gains `[picture] fonts`, the font files the picture stages in order, replacing the engine's list of four names. Each script already names its pronunciation contract, which replaces the fixed path in the listening plan; the plan still reads one contract for both editions, so it refuses scripts that name different ones, and merging per-edition contracts is deferred until a film needs it.

The listening plan's analyst readings are the film's review data, not the engine's: the context readings of Chinese words that the contract's targets do not cover, the English heteronyms with a reading for each part of speech, the variants the dictionary targets lack, and the part of speech of each heteronym occurrence, keyed by segment and offset in that film's script. The declaration names their file as `[review] readings`; without it the plan adds no analyst readings. The engine keeps only how the plan is derived and how a reading is written in the contract's lexical-stress shape.

Other paths stay conventions that the README states: `content/film.toml`, the composition `picture/index.html`, `film.js` and `film.css`, the release manifest `content/release.json`, and the `build/` layout. A film that declares its current fonts in their current order stages byte-identical documents and members, and one that declares its current readings derives the same listening plan.

### Node tools

The wheel carries the Node tools as package data. `python -m filmkit.tools <tool> [arguments]` copies them, keeping their folders, into `build/runtime/tool-cache/filmkit/<version>/` below the film, replacing any copy whose bytes differ, and runs the named tool there with Node at the film's root. Their static imports then resolve `puppeteer-core` from the film's `node_modules`, exactly as they do in the film's repository today; the composition and the supplied browser builds resolve from the film's root, the folder the tools run in, and a browser check receives the browser the renderer uses. Alternatives:

- an npm package from the same tag, rejected because the film's two locks would have to agree on one engine version through two install channels;
- resolving imports through `createRequire` from the film root, rejected because it loads the packages' CommonJS builds instead of the ES modules the tools use now;
- Node loader hooks, rejected as more machinery than one copy into the tool cache.

### Renderer version

The engine renders with HyperFrames 0.8.150 and checks the digest of the Chrome Headless Shell 152.0.7977.30 build that this renderer pins. The film owns its npm lock, because the renderer's dependency tree decides its stages and renders, so the engine reads the installed renderer's version and refuses any other before staging, rendering or running a Node tool, naming both versions.

### Sample film

`examples/sample-film/` holds a bilingual film of a few seconds per chapter, with its own declaration, scripts, casts, voice contracts, player and entry pages, covers and a small composition. Its text is new and MIT-licensed with the code. Its narrator reference recordings are the DDWG narrator's, by the same author under CC BY 4.0, and its fonts keep the SIL Open Font License; `NOTICE` names both. As in the DDWG films, text with a Chinese character is set in Noto Sans CJK SC, subset to the characters the sample draws, and Latin-only text in unmodified IBM Plex Sans, whose apostrophes and quotes are Latin glyphs rather than full-width CJK ones; a test checks that each font maps every character the film draws with it, and the picture task paints each cover from the staged document and compares it with the tracked one. The engine's tests set `FILMKIT_ROOT` to the sample; values that named DDWG, such as the file prefix or the duration, take the sample's. The sample builds end to end with the engine's Mise tasks after the supply step, locally, since hosted runners have neither the models nor the browser build.

### Distribution and version

hatchling reads `VERSION`, the only version source once releases are tagged. A film declares the engine as a uv Git source at a release tag, and its lock pins the tag's commit. The first release is 0.1.0: the declaration format may still change while the ETHOS film is made. A package registry was deferred: no account or package name is established, and Git tags serve the two known films.

### Governance and CI

As in `ddwg-film`, the proof sets hold the portable gates, static analysis, the Python and Node suites and source integrity, which ETHOS projects into GitHub Actions and GitLab CI on Apple-silicon runners. The sample film's build needs the models and the browser build and stays a local acceptance.

## Risks / Trade-offs

- [A moved test weakens] → It keeps every assertion; only values that named DDWG take the sample's.
- [An engine change alters a film's bytes] → The boundary changes are byte-preserving by construction, and `ddwg-film`'s migration rebuilds and compares both editions before it adopts the release.
- [A stale tool copy runs] → The copy is keyed by the engine version and replaced whenever its bytes differ from the package's.
- [The sample's content drifts from the engine's formats] → The suites load it on every run, so a format change that the sample does not follow fails at once.

## Migration Plan

1. Form and land `filmkit` 0.1.0 locally; publish after the user confirms.
2. In `ddwg-film`, a Change replaces `src/filmkit` with the release, declares the fonts and a readings file that carries the four tables its engine copy holds (the Mandarin readings, heteronyms, variants and grammar), runs the Node checks through the engine command, rebuilds both editions and compares them under the reproduction standard. Derived from those tables, its listening plan and staged members are byte-identical to the current ones.
3. The ETHOS film depends on a 0.1 release from its first commit.

## Open Questions

- The GitLab namespace is `dig/misc/tools`, beside the guidelines group; the user confirms it with the push.
