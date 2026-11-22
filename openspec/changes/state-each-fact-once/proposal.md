## Why

On 20 November 2026 the owner made it a hard requirement that each fact has one source: what repeats a fact is derived from its source, never kept beside it, and a check that refuses a disagreement afterwards is not a source. The review of that day (section C of `review-ssot.md`) listed the places where the engine still stated a fact twice, and its dispositions named five that need no decision. At `1e4d459` four of the five still stand twice; the fifth, the engine's name in the record's writer, needs a decision and leaves this Change. The same kinds of fact stand twice in more places than the review listed, among them two of the places the dispositions call single. This Change states each of these facts once and derives every repetition from it.

## What Changes

- The stage's file names, its page and its record, stand once in the Python engine and once among its Node modules; every module that writes or reads a stage takes them from there. The renderer is given the staged page instead of naming it.
- The player page pairs the delivered films into versions in one place, from the films the engine delivers.
- Each Node tool states its usage once, in the text it prints; the renderer's printed usage takes the form under which the renderer is run.
- The release names of an edition's review record and report derive from the names of their build files.
- The engine's version is read under one name for the engine, and the adoption command locates a film's manifests by the names the engine's record states.
- An edition's documents and its delivered page are named once, and the folders and frames that each edition's places and pictures state are read from their owners.
- Tests that build these names as inputs read the owners; a test's expected value stays a literal beside its input.

[design.md](design.md) states the owners, the places that read them and the reasons. The Change records itself under `Unreleased` in the Changelog.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement states how the code holds these names, and no requirement on output changes. `.openspec.yaml` sets `skip_specs: true`.

## Impact

- Engine modules of the picture, the delivery, the review, the captions, the sound gate, the pre-render check, the adoption command and the tools, and the tests that build these names as inputs. No film's tracked file, record or delivered byte changes, and no command line changes.
- Two printed texts change: the usage the renderer's Node module prints when it is invoked wrongly gains the word `node`, which it is run with; and the cover check refuses, before it paints, a stage whose record and page disagree, as the geometry check already does.
- The media server loads the film's declaration when it starts, so a film whose declaration does not load can no longer serve its built media.
- Acceptance builds the sample film's sound, pictures and packages on the base head and on the Change's head from one narration and compares the two builds file by file; it runs the changed geometry and cover checks on the released films' stages. It is host-heavy and runs under host tickets.
- Out of scope: the decisions note (`decisions.md`); module paths and command strings that name the import package, which every import statement names alike; the roots of the build layout, among them the work folder, which modules other than the edition's places use; prose that names a fact (README, Changelog, design, docstrings, messages); every film's tracked files, which stay frozen until December.
