## ADDED Requirements

### Requirement: The cover check paints at the frame of the stage's record

The cover check SHALL paint a stage's cover at the width and height that the stage's record, `stage.json`, states. Before it opens a browser it SHALL refuse, with status 1, one line that names the file, what is wrong with it and `stage-picture`, and no painting, a stage whose record is absent, holds no JSON or lacks a whole positive width, height, seconds or frames a second, whose page is absent or holds no film element, or whose page states another width, height or seconds than its record.

#### Scenario: A stage the engine writes

- **WHEN** the check is handed the UHD stage that `stage-picture` wrote
- **THEN** it paints the cover at 3840 by 2160 and compares it with the tracked cover

#### Scenario: A folder without a stage's record

- **WHEN** the folder holds a page and no `stage.json`, or a record that states no frames a second
- **THEN** the check exits 1 with one line that names the record and `stage-picture`, opens no browser and writes no painting

#### Scenario: A page with no film element

- **WHEN** the stage's record is whole and its page holds no film element
- **THEN** the check exits 1 with one line that names the page and `stage-picture`, and writes no painting

#### Scenario: A page and a record that disagree

- **WHEN** the stage's page states a width of 1920 and its record a width of 3840
- **THEN** the check exits 1, naming both figures and `stage-picture`, and writes no painting
