## ADDED Requirements

### Requirement: A followed mark pops by a piece it gains or loses whole

Outside a stage cut, a mark the motion audit follows SHALL also pop by each drawn piece it gains or loses within one frame, at ink 60 or more and 12 px or more across, that no piece of the other frame continues and no like mark there holds. A piece SHALL continue one drawn from or ending at its point, or a closed piece one at its centre, under the shift that pairs most pieces, or one that moves as a mark of its own. `check-picture` SHALL refuse it as `motion_pops`, naming the drawing line.

#### Scenario: Lines that join a stroke whole

- **WHEN** one stroke draws three links whose first inks in over 0.3 s, and its second link joins the stroke whole at full ink in one frame while the first stands
- **THEN** `check-picture` refuses a pop for the second link that names the stroke's drawing line

#### Scenario: A piece drawn on

- **WHEN** a stroke's second link draws on from its first point, under 12 px long in its first frame
- **THEN** the audit reports no pop for it

#### Scenario: A piece that turns a corner

- **WHEN** a link drawn on from a rising start turns from a vertical stub into a horizontal line within one frame
- **THEN** the audit continues its piece from its first point and reports no pop for it

#### Scenario: A path split at a gap

- **WHEN** a path stroke splits into two pieces where a station's gap opens, the second piece ending where the path ended
- **THEN** the audit continues the second piece from that end and reports no pop for it

#### Scenario: A tick that moves on its own inside one stroke

- **WHEN** one stroke draws a ruler and a tick that slides along it, the tick moving by more than the ruler's shift
- **THEN** the audit continues the tick as a piece that moves with a mark of its own and reports no pop for it
