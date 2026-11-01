# Design

## Context

See [proposal.md](proposal.md). `python -m filmkit.tools` copies every `.mjs` module below the package into the film's tool cache, keeping its folder, so modules in subfolders reach the tools unchanged. `geometry-check.mjs` serialises six frame rules into the rendered page with `toString`, and the frame audit runs the same rules headlessly. `frame-audit.mjs` and `motion-audit.mjs` are scripts whose measures share module-level state.

## Goals / Non-Goals

**Goals:**

- Every code file stays within 500 effective lines, with no repository deviation.
- Each new module states one concept, and a reader finds a rule or a measure below the concept that owns it.
- The tools keep their names, entry paths, refusals and output bytes.

**Non-Goals:**

- Changing any rule, threshold, measure, report field or film output.
- Moving the existing `picture/` modules or the tools' entry paths.
- The repository's other supply pins and any publication, tag or release; each keeps its own decision.

## Decisions

### The rules move to `picture/rules/`, and importers name their owners

The frame rules are the shared contract of the real-browser check and the frame audit, so they leave the check. `ink.mjs` holds how strongly a mark reads, `balance.mjs` the reviewers' balance and cover, `frame.mjs` the frame analysis and `names.mjs` the name and list rules. `geometry-check.mjs` re-exports nothing; each importer names the module that owns what it uses. A serialised rule's text moves unchanged, so what the page runs does not change.

### Each audit keeps its entry and gains a folder of its parts

`picture/frame-audit.mjs` and `picture/motion-audit.mjs` stay the tools' entries: their command, their frame loop and the measures they read directly. Parts that own a concept move below a folder of the tool's name. In the frame audit these are `marks.mjs`, what the measures read of a painted mark; `composition.mjs`, the seat, container, balance, sparse and extent measures; and `report.mjs`, the report and the files it writes. In the motion audit it is `report.mjs`, the analysis of the tracked frames and the report. A part that needs the audit's state receives it as arguments, with its function bodies otherwise unchanged.

### The test file splits by subject

A test file counts as its subject, so a failure names what broke. `tests/picture/sample-film.mjs` holds what several of them share: the sample film's folder, the staged timeline and the scratch folders. `package.json`'s test command names each test file, as it does today. ETHOS treats every module below `tests/` as a test the runner must enter, so `.gitattributes` gives the helper the `tooling` role, as ddwg-film does for its `tests/engine.mjs`.

### Behaviour is compared, not assumed

Before the split lands, each audit's old and new modules run on the same staged timelines and their standard output and report files must be byte-identical. The serialised rules' `toString` texts must also be equal between the old and the new modules, and the real-browser page program test exercises them. The comparison scripts are scratch work, not tracked tests.

### Bind inside the lane

0.2.0-alpha.25 refuses the unsplit tree, and 0.2.0-alpha.21 does not know the new ceiling, so the split and the bind land together: the lane binds the family before its final gates and proves the archived head under 0.2.0-alpha.25.

## Risks / Trade-offs

- [A moved rule starts to depend on its module's scope, which breaks once it is serialised] → The rules stay self-contained, the `toString` comparison shows their texts unchanged, and the page program test runs every rule from its source.
- [A part's state is wired wrongly] → The byte comparison on both editions' timelines and the audits' existing tests read every report field.
- [The local `dev` stands ahead of the forges until the user approves a push] → The films pin v0.1.1 by tag, so nothing reads the unpublished head.

## Migration Plan

Split, compare, fix the encoding calls, copy the declaration, lock it, install the locked supply, bind the runtime, regenerate the CI projection, run the gates, prove the archived head, land and close out. To roll back, restore the 0.2.0-alpha.21 declaration and lock and bind the retained runtime with its own console's `hook install --runtime <0.2.0-alpha.21 runtime path>`.
