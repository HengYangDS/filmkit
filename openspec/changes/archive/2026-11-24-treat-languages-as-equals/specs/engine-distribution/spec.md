## ADDED Requirements

### Requirement: The command reports the loader's refusals once

The question `declaration` SHALL report every refusal of the loader, each withdrawn key and each misplaced, missing or retired source among them, each once and with what to write instead; no other question SHALL name a fact that the loader refuses.

#### Scenario: Restated keys

- **WHEN** both scripts declare `language` at their tops and in a segment, and the English cast declares `language`, `provider` and `reference_text_sha256`
- **THEN** the question `declaration` names each key with its file, and its segment where it stands in one, and what to do instead, and no other question names them

#### Scenario: A declaration key

- **WHEN** the declaration still names `editions.zh.sources`
- **THEN** the question `declaration` names it, and no other question does

### Requirement: The command names every text the loader does not read that names an old place

Until the release that retires the command, the question `editions` SHALL name each line of a tracked text file whose facts no refusal of the loader owns, a film's Mise tasks, NOTICE and test loaders among them, that names a file this release moves or removes by its old path, with its file, its number and the new path. It SHALL name each file it cannot read, SHALL fail while a finding stands, and SHALL need no declaration that loads.

#### Scenario: Old paths in other files

- **WHEN** the film's NOTICE names `content/film-script.json`, a task's tool line names `assets/cover/ddwg-cover.png` and `tests/picture/page.mjs` names `content/film-script.json`
- **THEN** the question names each line with its file, its number and the new path, and the command exits with a failure

#### Scenario: The old paths it knows

- **WHEN** the declaration's `sources` and a cast's `reference_audio` are still stated, the Chinese cast's derivation cites `assets/audio/narration-reference.wav`, a line names `content/narration.md` and the NOTICE names the cited recording
- **THEN** the question takes as old paths those the withdrawn keys still state, the fixed names this release retires and each recording a cast's derivation cites, whose new path is `assets/audio/narrator-identity.wav`, and names both lines

#### Scenario: A copy that Git does not hold

- **WHEN** a copy of the film's tracked files stands in a folder that another repository ignores, or below which it tracks nothing
- **THEN** the question reads every file of the copy but its built output, packages and Git's records, and names each line it would name were the files tracked

#### Scenario: An old path that another finding owns

- **WHEN** the declaration still names `cover = "assets/cover/ddwg-cover.png"` and the Chinese cast names its reference by its old path
- **THEN** the declaration's line and the cast's key are each named once, by `declaration`, and the question `editions` names neither line

#### Scenario: A film that holds what the release asks

- **WHEN** no tracked text that the loader does not read names an old path
- **THEN** the question reports no finding

### Requirement: The command asks no edit of a film's history

A film's history and the record the engine writes of its release, its changelog, its archived OpenSpec changes and `content/release.json`, listed once in the command's module, SHALL hold no finding of the question `editions`: the command SHALL list each of their lines that names an old path under `history`, with its file, its number and the new path, and SHALL NOT fail for them, since a film keeps them as they stand.

#### Scenario: History and the release record

- **WHEN** `CHANGELOG.md`, a file below `openspec/changes/archive/` and `content/release.json` each name `content/film-script.json`, and no other text names an old path
- **THEN** the command lists each of their lines under `history` with its file, its number and the new path, the question `editions` reports no finding, and the command does not fail for them

## MODIFIED Requirements

### Requirement: The command reads a film's picture template

The command SHALL report each text of the picture template that staging would refuse, all in one run, a language anchor other than `<html lang="und">` among them, and every script or stylesheet the template names beside the two that staging inlines.

#### Scenario: Two template faults

- **WHEN** the template holds one of staging's texts twice and lacks another
- **THEN** one run reports both

#### Scenario: A second naming of the inlined stylesheet

- **WHEN** the template names the stylesheet staging inlines once more, in a tag that is not the one staging replaces
- **THEN** the command reports it as a source staging does not inline

#### Scenario: A template whose anchor is a language's tag

- **WHEN** the template opens with `<html lang="zh-CN">`
- **THEN** the command names it with the anchor `<html lang="und">` that staging replaces

### Requirement: The command reads what a film states of its runtime and credits

The command SHALL report each line of the review prompt that cites the runtime's field without saying "This edition", with what to do instead, by the question `runtime`. Each script that declares `duration` or `credits_duration`, each cast that declares `runtime_fit` and a declaration without `credits_duration` SHALL be reported once, by the declaration's question, as the loader refuses them, each in one line that says what to do instead.

#### Scenario: A film that has not adopted the release

- **WHEN** both scripts declare `duration` and `credits_duration`, a cast declares `runtime_fit` and the review prompt says "Each edition: exactly {duration} s"
- **THEN** one run names each key with its file and what to do instead, by `declaration`, and the prompt's line with its number and the wording to use, by `runtime`, and the command exits with a failure

#### Scenario: A declaration without the credits

- **WHEN** the declaration states no `credits_duration`
- **THEN** the command names it once, in one line that says to declare the credits' length there

#### Scenario: A prompt line that cites the runtime in other words

- **WHEN** a line of the review prompt cites the runtime's field, with a format or without one, and does not say "This edition"
- **THEN** the command names the line, whatever else it says, and a line that only escapes the field's braces is not named

#### Scenario: A film that holds what the release asks

- **WHEN** no script or cast declares a withdrawn key, the declaration states its credits and every line of the review prompt that cites the runtime says "This edition"
- **THEN** the question reports no finding

#### Scenario: A script that has not moved

- **WHEN** the declaration still states `sources = "content"` for its Chinese edition and `content/film-script.json` declares `duration`
- **THEN** the question `declaration` names `content/film-script.json` and `duration` beside `editions.zh.sources`, and the question `runtime` names neither
