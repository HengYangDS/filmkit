## ADDED Requirements

### Requirement: The sample film renders its drafts before its pictures

The sample film's picture task SHALL stage both pictures of each edition, render the edition's draft with `render-draft` and pass `preflight` before it renders the edition's pictures.

#### Scenario: The sample's picture task

- **WHEN** the sample film's picture task runs on a build without packaged films
- **THEN** `render-draft` writes each edition's draft record and `preflight` reports every input of each edition current before `render-picture` runs
