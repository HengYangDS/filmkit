## REMOVED Requirements

### Requirement: A picture is derived only under software capture

**Reason**: it qualified a derivation by the browser build that drew the captioned picture. No browser draws a picture now. "A picture is derived only from a render by the pinned canvas" states the same rule for the canvas build that the engine pins.

**Migration**: none for a film that declares `software` capture and installs the engine's pinned canvas: its uncaptioned picture is derived as before, once its captioned picture is rendered by this engine.

## ADDED Requirements

### Requirement: A picture is derived only from a render by the pinned canvas

For a film that declares another capture than `software`, for a captioned picture whose receipt does not name the pinned canvas build with `system` text, and with `--native`, `render-picture --uncaptioned` SHALL draw the uncaptioned stage, and `compare-pictures` SHALL then compare the pair at every frame. The uncaptioned picture's receipt and the comparison record SHALL each say whether it was derived or rendered, and why.

#### Scenario: A film that declares no capture

- **WHEN** a film that declares no capture, and so declares `fast`, runs `render-picture --uncaptioned`
- **THEN** its uncaptioned stage is drawn, and the receipt says that the picture was rendered because the film declares `fast` capture

#### Scenario: A native render asked for under software capture

- **WHEN** a film that declares `software` capture runs `render-picture --uncaptioned --native`
- **THEN** its uncaptioned stage is drawn, and the receipt says that a render was asked for

#### Scenario: A derived picture under another capture

- **WHEN** a film changes its declared capture from `software` to `screenshot` after its uncaptioned picture was derived
- **THEN** validation refuses the derived picture and asks for `render-picture --uncaptioned`

#### Scenario: A captioned picture drawn by another canvas build

- **WHEN** a film that declares `software` capture rendered its captioned picture with a canvas package whose recorded integrity is not the pinned build's, or whose processes loaded another native library than the pinned one
- **THEN** the captioned receipt names that integrity and that library's SHA-256, `render-picture --uncaptioned` draws the uncaptioned stage, and its receipt says that the captioned picture is no render by the pinned build, naming what differs

#### Scenario: A captioned receipt that names no canvas

- **WHEN** the captioned picture's receipt names no canvas
- **THEN** `render-picture --uncaptioned` draws the uncaptioned stage and says so

#### Scenario: A repair's render of the uncaptioned picture

- **WHEN** `repair-pictures` renders the uncaptioned picture of a rendered pair again and the pair then passes
- **THEN** the new receipt and the passing comparison record say that the picture was rendered and why, as the receipt it replaces did

#### Scenario: The comparison record of a rendered pair

- **WHEN** `compare-pictures` passes a pair whose uncaptioned picture was rendered under `fast` capture
- **THEN** its record holds every level's measures and says that the picture was rendered because the film declares `fast` capture
