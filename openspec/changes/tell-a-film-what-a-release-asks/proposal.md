## Why

A film that adopts an engine release learns what the release asks of it one refusal at a time. In the whole-edition trial of 19 November 2026 (the essentials film from engine 0.22.3 to 0.24.0) seven gaps were met at seven places: at the lock, at a test, at the picture task's shape, and at `preflight` after 200 s of stages and checks. What a release asks is stated in prose only: the README names the npm packages and their versions, the Changelog names renames in its adopting sentences, and nothing names the indirect Python packages, that a picture task asks readiness, or the template's shape. Read on the same day from the three films' tracked files at their tags, the same eight classes of gap stand in each of them, and each film adopts in December.

The capability `engine-distribution` already requires that a release state what a film must provide. This Change makes that statement one the engine can check.

## What Changes

- **One light command tells a film everything the release asks of it.** `python -m filmkit.adoption` reads a film's tracked files only (its declaration, its `package.json` and lock, its Python lock, its tasks, its picture template) and lists every finding at once, before the film has installed, supplied, narrated or staged anything. It runs in the film, or from an engine checkout on a film named by `FILMKIT_ROOT`.
- **The declaration reports all its problems together.** Today the loader stops at the first of four stages: a renamed key, the model's fields, the named files, a copied player page.
- **What a film must hold is read from the engine's own manifests.** The engine's `package.json` separates the packages a film declares from the repository's own tools; the versions the engine was released on, npm and Python, travel inside the installed engine as one data file that the repository's checks hold equal to its locks. The README's sentence and the renderer's version constant are held to the same source.
- **The Changelog's adopting sentence names the command.** A rename or a removal is still stated there; the list of what one film must change is the command's.

Not breaking: no film's build changes, and no existing command refuses anything it passed before.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `engine-distribution`: a release states what a film must provide in a form one command checks against a film's tracked files.
- `film-engine`: a declaration is refused with every problem it holds, not the first.

## Impact

- `src/filmkit/adoption.py` (new), `src/filmkit/film.py` (the loader collects), the packaged data file of the engine's released versions with its generator in the repository's fix task and its equality in the repository's check, `package.json` (the three packages a film declares move to `dependencies`), `picture/renderer.py` (its version constant is checked against the manifest), the README and the Changelog, tests (which run the command on the sample film).
- Each film: nothing until it adopts; then the command's list.
- Out of scope, each with its owner: questions that need a timeline, such as a caption above the reading rate, stay `preflight`'s, and their cheapest point is the sound gate (the draft `decide-before-heavy-work`, decision 1); a film's own tests; a film's NOTICE and README versions and the writer of `content/release.json` (the trial's rank 3); a template the engine owns outright (the draft `faster-films-less-by-hand`, decision 5).
