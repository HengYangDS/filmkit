# narration-convergence Specification

## Purpose

Let an edition's narration settle by itself: judge every take by the lines the film already holds for a take, generate and choose candidates for what a line refuses, and name what cannot be settled as a question of the text.

## Requirements

### Requirement: Han characters are compared by reading

Where a transcript is compared with a take's text, two Han characters with the same reading in their own context, tone kept, SHALL count as the same unit. A character under a word whose reading the pronunciation contract declares SHALL take the declared reading. The particles 的, 地 and 得 SHALL count as the same unit only where the text says a particle. A take's record SHALL state its differing units by reading beside its differing units by unit.

#### Scenario: A homophone in the transcript

- **WHEN** a Chinese take's text holds 在 and its transcript holds 再 at that place
- **THEN** the take differs by one unit and by no unit by reading

#### Scenario: Another tone

- **WHEN** a take's text holds 买 and its transcript holds 卖
- **THEN** the take differs by one unit by reading

#### Scenario: A character that is no particle

- **WHEN** a take's text holds 土地 and its transcript holds 土的
- **THEN** the take differs by one unit by reading

### Requirement: Latin units are compared by their letters and digits

Two units of Latin letters or digits SHALL count as the same by reading when their letters and digits are the same, and adjacent Latin units SHALL be joined where the other side writes them as one. A Latin unit and a Han character SHALL never count as the same. A number said and its digits SHALL stay different.

#### Scenario: The recognizer's spelling

- **WHEN** an English take's text holds "checks" and "backtest" and its transcript holds "check's" and "back test"
- **THEN** the take differs by units and by no unit by reading

#### Scenario: Another word

- **WHEN** a take's text holds "and" and its transcript holds "in"
- **THEN** the take differs by one unit by reading

#### Scenario: A number

- **WHEN** a take's text holds "ten" and its transcript holds "10"
- **THEN** the take differs by one unit by reading

### Requirement: An audition qualifies a take by the judgment's lines

An audition SHALL propose only a take that no line of the judgment refuses, and SHALL record each take's lines and its counts by unit and by reading. The required phrase and the preference for an ending or a length SHALL order the qualified takes and qualify none.

#### Scenario: A take that a line refuses

- **WHEN** one take ends most quietly and differs from its text by one unit by reading, and another passes every line
- **THEN** the audition proposes the other take

#### Scenario: The required phrase

- **WHEN** two takes pass every line and only one transcript holds the required phrase
- **THEN** the audition proposes that take, and proposes the other when it is the only one

### Requirement: A take is judged by every line the film holds for a take

The engine SHALL judge a take of a thought by its length, its ending, its phrase ends, its opening, its unmarked pauses, the declared terms it says and its units, and SHALL name every failing line at once. Each limit but the units' SHALL be the film's declaration or the constant of the engine's gate for that line, read from the function that gate asks.

#### Scenario: A take that fails two lines

- **WHEN** a thought that opens its recording begins in sound and ends abruptly with no declared release
- **THEN** its verdict names the opening line and the ending line together

#### Scenario: A declared release

- **WHEN** a take ends abruptly and the film's pause contract declares a release for its join
- **THEN** the ending line passes, as the assembly keeps that ending

#### Scenario: A thought that does not open its recording

- **WHEN** the second thought of a segment begins in sound
- **THEN** the opening line is recorded as not judged for it

#### Scenario: A take of one second or less

- **WHEN** a take is 0.8 s long
- **THEN** the length line fails, as the engine refuses such a recording

### Requirement: A take is held to its words

A take SHALL be refused when a unit of its transcript differs from its text by reading. The limit SHALL be a constant of the judgment, stated in every judgment's record.

#### Scenario: A take whose transcript holds another word

- **WHEN** a take passes every other line and its transcript differs from its text by one unit by reading
- **THEN** the units line fails and the take is refused

#### Scenario: A take whose transcript is spelled otherwise

- **WHEN** a take's transcript differs from its text by three units and by none by reading
- **THEN** the units line passes

### Requirement: A take's clarity is judged only by a line the film declares for a single thought

Where a film declares a clarity floor and a thought margin, a take SHALL be refused when it reads under the floor, or under the floor less the margin for a thought the film declares as kept. Where a film declares a floor and no margin, a take's clarity SHALL be recorded and not judged, and the record SHALL say so. Where a film declares no floor, clarity SHALL NOT be measured. The rule SHALL be the one `preflight` asks.

#### Scenario: A film with a floor and no thought line

- **WHEN** a film declares a floor of 17.0 dB for an edition and no thought margin, and a take reads 15.0 dB
- **THEN** the take's record states 15.0 dB and that a single thought has no line, and the clarity line refuses nothing

#### Scenario: A kept thought above its line

- **WHEN** a film declares a floor of 17.0 dB and a margin of 1.0 dB, keeps one thought, and that thought's take reads 16.5 dB
- **THEN** the clarity line passes for it, and fails for a take of any other thought that reads 16.5 dB

### Requirement: An edition's narration is judged as a whole

`python -m filmkit.narration.judge` SHALL judge every thought of the receipt the edition's cast declares and write one record of each thought's measures, lines and verdict, bound to the receipt, the script and the cast by their digests. It SHALL refuse, before any model loads, a receipt that does not hold exactly the script's thoughts. It SHALL exit 1 and name each refused thought with every failing line. It SHALL generate nothing, and judging unchanged takes again SHALL write the same record.

#### Scenario: Two refused thoughts

- **WHEN** one thought of a receipt opens its recording in sound and another ends abruptly
- **THEN** the command exits 1, names both thoughts with their lines, and its record lists both

#### Scenario: An accepted narration

- **WHEN** no line refuses a thought
- **THEN** the command exits 0 and its record lists no refused thought

#### Scenario: A receipt that lacks a segment

- **WHEN** the script holds a segment the receipt does not
- **THEN** the command refuses and names the thoughts the receipt lacks

### Requirement: The selection's gates are asked about the narration

Where the narration's alignment of the receipt's recordings stands beside the receipt, a judgment SHALL ask the selection's own measure about each segment and SHALL refuse a thought whose pause or declared term it refuses, naming the gate. Where no such alignment stands, the record SHALL say that the gates were not asked. In a convergence such a thought SHALL get candidates like any refused thought.

#### Scenario: A pause only the segment's alignment shows

- **WHEN** a take alone is fluent and the segment's alignment places its words either side of 0.9 s of quiet with no mark
- **THEN** the thought is refused by the gate's pause, gets a candidate, and is settled when the narration that follows passes the gate

### Requirement: A refused thought gets candidates without a person's input

`python -m filmkit.narration.converge` SHALL, for each thought a line refuses, generate a round's candidates at the audition's seeds, counted on across rounds, and judge each by the same lines. It SHALL take no targets file, phrase or seed. It SHALL bind each choice into the cast's retakes, narrate and judge again, for the rounds asked for or until no thought is refused.

#### Scenario: One refused thought of two

- **WHEN** the second thought's take ends abruptly and the second of three candidates ends naturally
- **THEN** three candidates of that thought alone are generated, the second one's seed is bound, and the narration that follows is accepted

### Requirement: A choice takes the widest margin

Among the candidates no line refuses, the convergence SHALL choose the one with the widest margin from the lines that have one: its clarity above its line or floor, and its unmarked pause nearest its limit below that limit, each as a share of that line; then the quietest ending, then the lowest seed.

#### Scenario: Two accepted candidates

- **WHEN** two accepted candidates read 1.8 dB and 0.9 dB above an 18.0 dB line
- **THEN** the candidate 1.8 dB above the line is chosen, whichever was generated first

#### Scenario: A short pause near its limit

- **WHEN** a take holds an unmarked pause of 0.19 s under a limit of 0.2 s and one of 0.25 s under 0.4 s
- **THEN** its margin is taken from the first pause

### Requirement: A thought that stays refused ends as a question of its text

After its rounds, the convergence SHALL try run-on takes for each thought still refused that another thought follows. A thought that is then still refused after its candidates SHALL be recorded as not narratable as written, and one first refused when no round is left as refused with no candidate tried; the command SHALL exit 1 and name each with what each candidate failed. No line SHALL be lowered and no exception written for it.

#### Scenario: Candidates that all end abruptly

- **WHEN** every candidate of a thought ends abruptly and a take read on into the next thought ends naturally where it is cut
- **THEN** the run-on take's seed and run-on are bound and the thought is settled

#### Scenario: Nothing settles a thought

- **WHEN** every candidate of the film's last thought fails the ending line
- **THEN** the command exits 1, names the thought as not narratable as written and lists each candidate with its failing line, and the cast is unchanged

#### Scenario: A thought first refused by the last narration

- **WHEN** the narration after the last round makes another thought fail a line
- **THEN** that thought is named as refused with no candidate tried, not as not narratable, and the record holds its entry

### Requirement: A convergence keeps a record and repeats nothing

The convergence SHALL write a record that binds the receipt, the script and the cast by their digests, states the rounds and takes asked for, and holds, for each refused thought, the take it had, every candidate with its request's fingerprint and failing lines, every choice and the take it has now. A run with nothing missing and nothing refused SHALL generate nothing and leave the cast and the record as they are. A recording an earlier run left SHALL be judged again only under the same request.

#### Scenario: A second run

- **WHEN** the convergence runs again on an edition it settled
- **THEN** no take is generated, no narration runs, and the cast and the record are byte for byte the same

#### Scenario: A second run on an unsettled thought

- **WHEN** the convergence runs again after it named a thought as not narratable
- **THEN** it judges the candidates it left, generates none, and writes the same record

### Requirement: A convergence narrates what is due into the cast's receipt

The convergence SHALL narrate before it judges only when the receipt lacks a recording the cast asks for, or when a check's output is not of the receipt's recordings. It SHALL refuse a cast that declares another receipt than the narration writes. The narration from a bound seed SHALL give the candidate that was judged.

#### Scenario: A check's output of the recordings before

- **WHEN** the receipt holds every recording and the alignment beside it names another recording's digest
- **THEN** a narration is due

#### Scenario: The narration after a choice

- **WHEN** a candidate's seed is bound and its segment is narrated again
- **THEN** the thought's recording has the candidate's digest

### Requirement: A convergence that is asked to end leaves what it found

A request to end SHALL end the running narration first, by the engine's rules for a command with children. The record SHALL say that a run is under way from the run's first effect on, hold the candidates judged so far, and name no thought as unsettled. A next run SHALL narrate what the cast holds and go on. Where a narration was ended inside a thought and left its request started, the next run SHALL start nothing and SHALL name that file with the engine's refusal.

#### Scenario: Asked to end while it narrates

- **WHEN** the convergence is asked to end during the narration that follows a round
- **THEN** it ends that narration, says what asked, and its record holds the round's candidates and states that the run did not end

#### Scenario: Asked to end in its first narration

- **WHEN** a former record names a thought as not narratable and a new run is asked to end before it has judged
- **THEN** the record says that a run is under way and names no thought

#### Scenario: A request left started

- **WHEN** a narration was ended while it said a thought, and the convergence runs again
- **THEN** it exits 1 before any narration, names the thought's request file, and goes on once that file is removed
