## ADDED Requirements

### Requirement: The opening shows the declared title

`check-picture` SHALL refuse an edition whose frames before the first word show every word of the title its script declares, in texts at 3:1 or more against the ground, for less than 1 second, naming the title and the words no such frame shows. A text counts for the title words it repeats as one run, so the title may stand in parts and on several lines beside other texts.

#### Scenario: A title card before the first word

- **WHEN** the title's two parts stand on two lines at full ink through the 2 seconds before the first word
- **THEN** `check-picture` writes no title finding

#### Scenario: An opening without the title

- **WHEN** the frames before the first word show only the Illustrative chip
- **THEN** `check-picture` writes a refused record that names the title and every word it never shows, and exits with a refusal

#### Scenario: A title only after the first word

- **WHEN** the title stands only once the narration has begun
- **THEN** `check-picture` refuses the edition

### Requirement: Text at rest stays legible against the ground

`check-picture` SHALL refuse each run of 0.7 seconds or more in which a text holding a letter or a digit shows above 4% opacity at a WCAG contrast below 4.5:1 against the ground, its colour composited over the ground at its opacity, naming its scene or role, its text, its run and its lowest contrast. A shorter run is a text entering or leaving the picture and SHALL NOT refuse.

#### Scenario: A named item dimmed at rest

- **WHEN** a list item rests at 3.34:1 for 1 second
- **THEN** `check-picture` writes a refused record that names the item, its run and 3.34:1, and exits with a refusal

#### Scenario: A fade

- **WHEN** a text fades in through 4.5:1 within 0.6 seconds
- **THEN** `check-picture` writes no contrast finding for it

#### Scenario: A mark that holds no letter

- **WHEN** an arrow drawn as text stands at 2:1
- **THEN** no contrast finding is written for it
