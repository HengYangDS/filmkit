## ADDED Requirements

### Requirement: A switch keeps the film on the screen

The player SHALL keep a frame of the film on the screen across every switch by the captions control or a version button, and SHALL paint neither the cover nor a frame of one flat colour while it switches. The shown film SHALL stay until the chosen one holds its frame at the time it takes over: a paused film's time, or the time a playing film has reached, from which the chosen film plays on.

#### Scenario: Captions turned off on a paused film

- **WHEN** a viewer turns the captions off while the viewing film is paused
- **THEN** every frame the page paints until the switch ends is the viewing film's frame at its time or the uncaptioned film's frame at the same time, and the time does not move

#### Scenario: A version chosen while the film plays

- **WHEN** a viewer chooses the UHD version while the viewing film plays
- **THEN** the viewing film plays on until the UHD film takes over at the time the viewing film has reached, and no frame in between is the cover or a flat frame

### Requirement: The readback watches what each switch paints

For each switch it makes, to a version or by the captions control, the player check SHALL record every frame the page paints from the click until the chosen film shows, and SHALL fail the page for a frame nearer the cover than the film's frames before and after the switch, or of one flat colour where neither of those is, naming the switch and each such frame's time after the click.

#### Scenario: A page that reloads its film

- **WHEN** a player switches by loading the chosen film into the video it shows, so that the browser paints the cover until the film's frame decodes
- **THEN** the readback fails the page, names the switch and the frames that showed the cover with their times, and delivery refuses

#### Scenario: A page that keeps the film on the screen

- **WHEN** every frame painted during a switch is the shown film's or the chosen film's
- **THEN** the readback records the frames it watched and finds no problem in them

### Requirement: The player's words follow its edition's typography

Each player SHALL set its interface words as its edition's typography does: in Chinese a size that follows a closing full-width bracket SHALL follow it without a space, and in English an apostrophe SHALL be a right single quotation mark.

#### Scenario: A Chinese download

- **WHEN** the Chinese player lists the Markdown transcript of 9 KB
- **THEN** its label reads 讲稿（Markdown，供下载）· 9 KB

#### Scenario: A film the browser cannot play

- **WHEN** the English player's film reports a media error
- **THEN** the message it shows names the system’s player with a right single quotation mark

## MODIFIED Requirements

### Requirement: The readback turns the captions off and on

The player check SHALL turn the captions off on the paused viewing film, choose the UHD version with them off and turn them on while the UHD film plays, and SHALL fail the page unless each switch reaches the other film, keeps a paused film's time within 0.02 s, lets a playing film play on from no earlier than the click and no later than the time that passed, keeps the film paused or playing and leaves the control pressed as the captions show, and every film plays at its size and duration.

#### Scenario: A control that does not switch

- **WHEN** a player's captions control changes its state but leaves the film it showed
- **THEN** the readback fails, names the page, the film shown and the film expected, and delivery refuses

#### Scenario: A playing film that starts over

- **WHEN** a player's version button shows the chosen film from a time earlier than the time at the click while the film plays
- **THEN** the readback fails and names the times before and after the switch
