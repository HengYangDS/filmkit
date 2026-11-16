## MODIFIED Requirements

### Requirement: The sample film renders its drafts before its pictures

The sample film SHALL declare its drafts. Its picture task SHALL stage both pictures of each edition, render the edition's draft with `render-draft` and pass `preflight` before it renders the edition's pictures, and SHALL end by asking `admitted` of both editions.

#### Scenario: The sample's picture task

- **WHEN** the sample film's picture task runs on a build without packaged films
- **THEN** `render-draft` writes each edition's draft record and `preflight` reports every input of each edition current before `render-picture` runs

#### Scenario: Both editions still admitted after their renders

- **WHEN** both editions' pictures are rendered, validated and compared
- **THEN** `admitted` reports each edition admitted on the receipts its `preflight` wrote
