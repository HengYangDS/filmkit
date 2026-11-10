## ADDED Requirements

### Requirement: A delivered film names its version

Packaging SHALL read the film repository's `VERSION`, a Semantic Versioning 2.0.0 version without build metadata, SHALL write it into each film's QuickTime key Information with the label of the edition's language, 版本号 or Version, and SHALL bind it among the film's production inputs. Packaging SHALL refuse a repository without a valid `VERSION`, and the verifier a delivered film whose version differs from it.

#### Scenario: A Chinese film's version in Spotlight

- **WHEN** a Chinese edition is packaged at `VERSION` 1.3.0
- **THEN** each of its films carries the QuickTime key Information 版本号 1.3.0, which Spotlight lists as its information

#### Scenario: A version changed after packaging

- **WHEN** `VERSION` changes after an edition was packaged
- **THEN** packaging reports the version as a stale binding and the verifier refuses the edition's films

#### Scenario: No version

- **WHEN** the film repository has no `VERSION`, or it holds `1.3`
- **THEN** packaging refuses and names `VERSION`

### Requirement: The pages name the film's version

Each edition's player page SHALL name the film's version, with its label, in the line under its title after the language, and the entry page SHALL name it under the film's title. The verifier SHALL refuse a delivered page whose version differs from `VERSION`.

#### Scenario: The page names the version

- **WHEN** an English edition's page is built at `VERSION` 2.0.0
- **THEN** the line under its title names Version 2.0.0 after the language

#### Scenario: A page from an earlier version

- **WHEN** a delivered page names Version 1.2.0 while `VERSION` holds 1.3.0
- **THEN** the verifier refuses the page
