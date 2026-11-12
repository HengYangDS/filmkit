## ADDED Requirements

### Requirement: A followed mark pops by a piece it gains or loses whole

Outside a stage cut, a mark the motion audit follows SHALL also pop by each drawn piece it gains or loses within one frame, when no piece of the mark in the other frame continues it, it is at ink 60 or more and it is 12 px or more across. An open piece SHALL continue a piece drawn from the same first point, and a closed piece one at the same centre, each where the mark's shared shift puts it. `check-picture` SHALL refuse such a pop as `motion_pops`, naming the mark's drawing line.

#### Scenario: Lines that join a stroke whole

- **WHEN** one stroke draws three links whose first inks in over 0.3 s, and its second link joins the stroke whole at full ink in one frame while the first stands
- **THEN** `check-picture` refuses a pop for the second link that names the stroke's drawing line

#### Scenario: A piece drawn on

- **WHEN** a stroke's second link draws on from its first point, under 12 px long in its first frame
- **THEN** the audit reports no pop for it

#### Scenario: A piece that turns a corner

- **WHEN** a link drawn on from a rising start turns from a vertical stub into a horizontal line within one frame
- **THEN** the audit continues its piece from its first point and reports no pop for it
