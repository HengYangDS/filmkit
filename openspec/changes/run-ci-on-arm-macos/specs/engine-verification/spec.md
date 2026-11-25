## Purpose

Check every head of the engine the same way wherever it is checked: on Apple-silicon macOS alone, by one check projected to each forge from one declaration, and with the same check and proof whatever remotes a checkout has.

## ADDED Requirements

### Requirement: The engine is checked on Apple-silicon macOS alone

The repository SHALL declare hosted verification on Apple-silicon macOS alone: on GitHub one job on the hosted runner `macos-latest`, and on GitLab one review job that selects runners by the tags `macos-latest` and `review` and one protected job that selects them by `macos-latest` and `protected`. It SHALL declare no CI job for another operating system, and neither its tool pins nor the locks its declarations shape SHALL name a Windows archive or a package that only Windows needs.

#### Scenario: GitHub's job

- **WHEN** the CI projection of the repository's declaration is checked
- **THEN** GitHub's one verification job runs on `macos-latest` and on no other runner

#### Scenario: GitLab's jobs by trust

- **WHEN** a proposal push or a merge request starts a GitLab pipeline
- **THEN** only the job tagged `macos-latest` and `review` runs
- **AND WHEN** `dev`, `main` or a version tag starts one
- **THEN** only the job tagged `macos-latest` and `protected` runs

#### Scenario: The Mise lock is regenerated

- **WHEN** the Mise lock is regenerated with Mise's own `mise lock`
- **THEN** it holds no table for a Windows platform, and every other platform table it held before stays

#### Scenario: uv's lock is regenerated

- **WHEN** uv's lock is regenerated with the pinned uv's `uv lock`
- **THEN** it holds no Windows wheel and no package that only a Windows marker brings in

### Requirement: Both forges run one check from one declaration

Both forges' CI files SHALL be generated from the repository's CI declaration by ETHOS's projection, and SHALL NOT be edited by hand. Every job of both SHALL install the same locked supply, run `mise run bootstrap`, run the full proof `ethos prove --host --execute --full` under the declaration's one deadline and keep its report for the declaration's days; every other part of a job SHALL be its forge's projection of that declaration.

#### Scenario: A hand edit of a CI file

- **WHEN** either CI file differs from what the projection generates from the declaration
- **THEN** the projection check refuses it, naming the file

#### Scenario: One deadline for both

- **WHEN** the declaration's deadline changes and both files are generated again
- **THEN** every job of both files carries the new deadline

### Requirement: The engine is checked and proved whatever remotes a checkout has

A checkout with no Git remote SHALL pass the whole check (`mise run check`) and the full proof at a head with the verdicts that the canonical checkout's runs give at that head. In a checkout that has only one of the declared peers' remotes, ETHOS's status and the proof's readiness SHALL report no required gap for the absent peer. No gate of the repository's proof sets SHALL contact a remote; the bootstrap MAY reach the package registries.

#### Scenario: A checkout with no remote

- **WHEN** `git remote` prints nothing in a clone of a head and its whole check and full proof run
- **THEN** both pass with the verdicts that the canonical checkout's runs at that head give

#### Scenario: A checkout with one remote

- **WHEN** a clone of a head has only the remote `gitlab`, or only `github`, fetched
- **THEN** ETHOS's status and the proof's readiness at that head report no required gap for the absent peer
