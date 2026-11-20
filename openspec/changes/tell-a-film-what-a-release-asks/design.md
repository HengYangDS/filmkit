## Context

Read in the engine at `v0.24.1` on 19 November 2026 (its `src/` equals `v0.24.0`'s). A mark such as [S2] names an entry under Sources.

- `engine-distribution` requires that each release state, in the README, what a film must provide. The README names three npm packages and their versions in a sentence; `picture/renderer.py` holds the canvas version again as a constant; no code names the browser driver's version; nothing names the indirect Python packages. [S3]
- `filmkit.film` loads the declaration when it is imported, and every command imports it. A declaration that does not load ends any command at its first problem, and the loader stops at the first of four stages. [S3]
- A film's tasks are the film's. Nothing in the engine reads a task list; only the `admitted` command reads a readiness receipt, so a film whose picture task never asks `preflight` builds without it and is refused nowhere. [S3]
- The trial met seven gaps at seven places [S1]. A read-only prototype over the three films at their tags prints one list for all three: packages the engine no longer runs, the canvas missing, the browser driver one version behind, 15 to 16 shared Python packages older than the engine's lock and none newer, a delivery task that names a module the engine renamed, a renamed declaration key, a picture task without `preflight`, a template with a script source the engine does not inline. [S2]

## Goals / Non-Goals

**Goals:**

- A film reads everything a release asks of its tracked files in one run of one light command, before any install.
- What the command asks is read from the engine itself, so it cannot drift from the release.
- A film that adopted completely gets an empty list; the sample film does in every run of the repository's tests.

**Non-Goals:**

- A second readiness tool. Questions about a build's state stay `preflight`'s (the draft `decide-before-heavy-work`, decision 3).
- Editing a film. The command lists; the film's author changes.
- A history of releases. The command says what this release asks, not how the last one differed.

## Decisions

1. **What a release asks is read from the engine's own manifests and code, and one command compares a film's tracked files with it.**
   - **Rests on:** [S1] findings 6 and 7; [S2].
   - **Considered:** (a) fuller adopting sentences in the Changelog, the form that failed; (b) a table of renames and removals kept by hand for each release, which states what was and must be kept beside the code; (c) a comparison with what the engine is: the packages it runs, the versions it was released on, the commands it has, the anchors its staging replaces.
   - **Chosen because:** (c) cannot drift, since it is read from the release that asks. The one rename the loader already refuses by name stays where it is.
   - **Applies to:** `filmkit.adoption`, a command with no option but the film's root as every command finds it.
   - **Reopened when:** a release asks something of a film that no manifest, command list or anchor of the engine expresses.
   - **Sources:** [S1] [S2] [S3].
2. **The command needs no declaration that loads and nothing installed in the film.**
   - **Rests on:** an adopting film's declaration does not load (its renamed key), and its first heavy steps are a lock, an install and a supply of 7.6 GB. [S1] [S3]
   - **Considered:** (a) loading the declaration lazily in every module, a change across the engine; (b) a command that does not import the module-level declaration and asks the loader's own function for the problems of a root.
   - **Chosen because:** (b) is one module's care. Questions that need a loaded declaration are named as not asked when it does not load, so a second run after the declaration's repair completes the list.
   - **Applies to:** the command's imports; it runs in the film, or from an engine checkout with `FILMKIT_ROOT` naming the film.
   - **Reopened when:** the declaration's lazy loading is wanted for another reason.
   - **Sources:** [S3].
3. **The declaration reports every problem it holds.**
   - **Rests on:** the loader's four stages, each ending the load. [S3]
   - **Considered:** leaving the loader and collecting in the new command only, which gives two readers of one declaration.
   - **Chosen because:** one loader; every command's refusal improves with it.
   - **Applies to:** `filmkit.film`: a function returns the problems of a root, and the load refuses with all of them.
   - **Reopened when:** a later stage cannot be judged on a declaration an earlier stage refused (then that stage is named as not judged).
   - **Sources:** [S3].
4. **The engine's `package.json` says which packages a film declares.**
   - **Rests on:** the engine holds its three runtime packages and its formatter in one group, so "what a film must hold" exists only as the README's sentence. [S3]
   - **Considered:** (a) a list in Python; (b) reading the README; (c) the manifest's own two groups: `dependencies` for what the engine runs in a film, `devDependencies` for the repository's tools.
   - **Chosen because:** (c) is the manifest's native meaning and adds no carrier. The record is written from it by the repository's fix task, the renderer reads the canvas's version and integrity from the record, and the README names the manifest as the versions' one source and restates no number: each fact has one source (the owner's rule of 20 November 2026), and a test that compares two hand-kept copies is none.
   - **Applies to:** the engine's `package.json`; the film's `package.json` (each of those packages at that version) and its lock (each of them at the engine's version and integrity). The tree below them is npm's to resolve: the trial's film stood three entries older in the browser driver's tree and built the same pictures, and the canvas's native library is checked by its bytes when a picture is drawn. The binary package's integrity is the lock's alone: the engine pins that package's native library by its bytes. An engine that holds no record it can read, or a record that does not state both the canvas's version and its integrity, ends in an error whose one line names the record's file and the command that writes it, `python -m filmkit.released`, which the fix task runs. A caller sees that line as the last of a traceback: when the renderer is imported, which reads its pin then, and from `python -m filmkit.adoption`, which reads the record when it compares; the engine's other refusals at import read the same way. A record that is JSON of another shape than the command writes is a fault in the engine's own record and keeps its own traceback. That command reads no record, so it writes one where none stands. The repository's tests build each version of a declared package from the record, so a version changes in the manifest alone and in no test. A package the film alone holds is the film's and is not a finding.
   - **Reopened when:** a film has reason to run another version of one of them.
   - **Sources:** [S3].
5. **A film pins this release, its Python lock holds the engine's released versions of every package they share, and the command prints the lines that close the gap.**
   - **Rests on:** the engine pins its six direct dependencies; a film locked on another day resolves other indirect versions (twelve older in the trial, the tokenizer library among them), and nothing compares them. uv 0.13.9's `lock` takes no constraints file; `constraint-dependencies` under `[tool.uv]` is its place for them, and the trial's hand-written twelve lines brought the film's lock to the engine's. [S1] [S4]
   - **Considered:** (a) the engine pinning its whole tree as direct dependencies: native, but every supply refresh is then edited twice and a film's own packages lose their room; (b) comparing and leaving the repair to the film's author; (c) comparing the engine's runtime closure with the film's lock and printing the constraint lines.
   - **Chosen because:** (c) uses uv's own place for it and removes the hand work. The repository's own development group is left out, so a film's own pin of a tool it tests with is no finding.
   - **Applies to:** the command, and one data file in the package that holds the engine's released npm tree and Python closure. The repository's fix task writes it from the locks and its check refuses a difference: the wheel holds `src/filmkit` only, so an installed engine cannot read the locks themselves.
   - **Reopened when:** uv offers a film a way to take a dependency's lock.
   - **Sources:** [S1] [S3] [S4].
6. **A film's tasks are read for what the engine can know exactly: commands that exist, and readiness asked at all.**
   - **Rests on:** all three films' delivery tasks name a module the engine renamed; none asks `preflight`, and nothing else asks the receipt. [S2] [S3] A first form of this question also judged whether readiness is asked before the render and for which edition, from the tasks' shell text. Three independent review passes each found new faults there (a variable's value, a loop, a nested shell, a here-document), the third in the second's repair: what a shell makes of a text has no boundary an engine can read.
   - **Considered:** (a) not reading tasks, which are the film's; (b) comparing a film's task with the sample's command by command, which forbids a film its own order; (c) reading the shell: order, editions, variables; (d) two things read from the text as text: every engine module a task names after `-m` exists and every `filmkit.produce` command names an action the engine has; and where the tasks render a picture, some task asks `preflight`.
   - **Chosen because:** (d). Both are statements about the text that are true or false as read. The trial's gap was the second, an absence, and an absence needs no order. Which task runs first, and for which edition, is the film's and Mise's.
   - **Applies to:** the film's Mise tasks. A task runner other than Mise is named as not read; a `filmkit.produce` command that holds a variable and names no action of this engine by a word is named as not compared, whatever else it names, and the tasks' readiness is then not judged.
   - **Reopened when:** a film has reason to render without readiness.
   - **Sources:** [S2] [S3].
7. **The template is asked for every anchor at once, and for no source the engine does not inline.**
   - **Rests on:** staging replaces ten anchors and refuses at the first that does not stand once; it inlines one stylesheet and one script. The films' templates still name the timeline library's script. [S2] [S3]
   - **Considered:** the engine owning the template outright, which removes the question and belongs to the draft `faster-films-less-by-hand`.
   - **Chosen because:** the anchors are the engine's own list, read from where staging holds it; a staged document is self-contained, so another script or stylesheet source is a finding.
   - **Applies to:** `picture/index.html` of a film.
   - **Reopened when:** the engine owns the template.
   - **Sources:** [S3].
8. **The findings are printed together and the command exits 1 while one stands; it writes no receipt.**
   - **Rests on:** `preflight`'s form: each question returns a finding or none, one JSON line reports them, one refusal joins them. Nothing would read a receipt of this command.
   - **Chosen because:** the form the engine has; no file without a consumer.
   - **Applies to:** the command's output. The repository's tests run it on the sample film, so every check proves the empty list, hosted ones included.
   - **Sources:** [S3].

## Risks / Trade-offs

- The data file is a copy of the locks. → It is generated, and the repository's check refuses a difference, as it does for the version.
- Three films meet the Python finding at once. → The command prints the lines; the trial's lock equalled the engine's after them.
- A film may render without readiness on purpose. → It is one finding with its reason; decision 6 says when it is reopened.

## Open Questions

- Whether a film's Mise tasks are the only task list worth reading. The three films and the sample use Mise; another runner is named as not read.

## Sources

- **[S1] The whole-edition trial:** `build/evidence/faster-films-less-by-hand/whole-edition-trial/report.md` in the canonical checkout (19 November 2026), its preparation log, findings 6, 7 and 11, and the ranked order.
- **[S2] The three films at their tags:** `gaps.py` and its output of 19 November 2026 beside this draft's first form: `ddwg-film` `v1.3.1`, `ethos-film` `v2.0.1`, `ddwg-essentials-film` `v1.0.2`, tracked files only, against the engine at `v0.24.1`.
- **[S3] The engine at `v0.24.1`:** `src/filmkit/film.py` (the loader), `preflight.py` (the questions and the receipt), `produce.py` (the actions), `picture/rendering.py` (the anchors), `picture/renderer.py` (the version constant), `package.json`, `pyproject.toml` (the wheel's packages), the README's section on installing the engine in a film, `openspec/specs/engine-distribution/spec.md`.
- **[S4] uv 0.13.9, as installed:** `uv lock --help` and `uv export --help`, read 19 November 2026.
