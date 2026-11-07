## ADDED Requirements

### Requirement: A set-aside moves the films its build made

A set-aside, reviewed or not, SHALL move each edition's films with captions, its films without captions and its uncaptioned picture when they are in place, its package record and, unless kept, its pictures, so a build packaged before the films without captions existed is set aside by its two films and its captioned picture, bound by the review or the consumer copies of those films.

#### Scenario: A round reviewed before 0.13.0

- **WHEN** a round whose reviews bind each edition's two films with captions is set aside
- **THEN** each edition's two films, package record and captioned picture move, and the set-aside names no missing film

## MODIFIED Requirements

### Requirement: An unreviewed build is set aside by its consumer's copies

`set-aside --unreviewed --consumer <dir>` SHALL move each edition's films, package record and rendered pictures into `build/artifacts/film/superseded/<label>/<code>/` with the manifest, move and readback of a reviewed round, labelled `round-<n>` or by `--label`. Before anything moves it SHALL refuse unless `<dir>/<code>/` holds each of the edition's films byte-identical, and it SHALL record that folder as their consumer.

#### Scenario: A preview the owner watched

- **WHEN** an unreviewed build whose films the preview folder holds byte-identical is set aside with that folder as its consumer
- **THEN** each edition's members move below the label's folder and are read back by their hashes, and each manifest names the edition's preview folder as the consumer

#### Scenario: A copy that differs

- **WHEN** one edition's copy in the consumer folder differs from its film
- **THEN** the set-aside refuses, naming the copy and the film, and moves nothing
