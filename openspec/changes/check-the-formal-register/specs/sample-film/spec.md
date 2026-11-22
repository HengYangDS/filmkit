## MODIFIED Requirements

### Requirement: The sample film meets the owner's text and review bars

The sample film's text SHALL line up as the frame audit measures it, and its review configuration SHALL hold the overall score and every dimension at 95 or more, its words SHALL pass the register check, and its review declaration SHALL ask for formal standard written language under 雅.

#### Scenario: The sample's picture passes the text-layout measures

- **WHEN** `check-picture` audits either edition of the sample film
- **THEN** the frame audit reports no text-layout finding, and the closing checklist's items share one left edge beside their checks

#### Scenario: The sample's review floors

- **WHEN** the sample film's review configuration is read
- **THEN** its overall and dimension minimums are 95

#### Scenario: The sample's register

- **WHEN** the register check reads the sample film
- **THEN** it refuses nothing, and the sample's `language_quality` dimension and `雅` level ask for formal standard
  written language

### Requirement: The sample film's review holds three levels

The sample film SHALL declare `[review.levels]` holding each of its review dimensions in one of 信, 达 and 雅, and its prompt SHALL cite `{levels}` and `{sentences}`.

#### Scenario: The sample's review configuration

- **WHEN** the sample film's declaration and prompt are read
- **THEN** its six dimensions stand in the three levels and its prompts state the levels and name the sentences file
