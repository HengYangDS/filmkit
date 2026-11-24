## ADDED Requirements

### Requirement: English words are also compared by their pronunciation

In an edition whose language declares that its Latin-script words are heard by CMUdict's pronunciations, a text's Latin unit that says no declared term SHALL also count as the same by reading as a transcript's unit when the transcript unit's first pronunciation in the engine's pinned CMUdict is one of the text unit's own readings: those the edition's pronunciation declares for that word, else CMUdict's first. A word it declares by letter names SHALL be compared by its letters only.

#### Scenario: Another spelling of the same word

- **WHEN** an English take's text holds "labelled" and its transcript holds "labeled"
- **THEN** the take differs by one unit and by no unit by reading

#### Scenario: A spelling that has the text's sound only as a later pronunciation

- **WHEN** an English take's text holds "half tiers" and its transcript holds "half tears", whose first pronunciation CMUdict gives as the verb "tear"
- **THEN** the take differs by one unit by reading

#### Scenario: A homophone

- **WHEN** an English take's text holds "their" and its transcript holds "there"
- **THEN** the take differs by one unit and by no unit by reading

#### Scenario: A word of another sound

- **WHEN** an English take's text holds "an" and its transcript holds "and"
- **THEN** the take differs by one unit by reading

#### Scenario: Another word's weak form

- **WHEN** an English take's text holds "or" and its transcript holds "are", which shares only its weak form with "or"
- **THEN** the take differs by one unit by reading

#### Scenario: A declared reading

- **WHEN** the edition's pronunciation declares "read" by its present-tense reading alone and a take's text holds "read" where its transcript holds "red"
- **THEN** the take differs by one unit by reading, and with no declaration it differs by none, since CMUdict lists the past tense first

#### Scenario: A word declared by letter names

- **WHEN** the edition's pronunciation declares "AI" by its letter names and a take's text holds "AI" where its transcript holds "I", or "eye"
- **THEN** the take differs by one unit by reading, though CMUdict lists "ai" first as the word "eye"

#### Scenario: Letter names heard as letters

- **WHEN** the same text holds "AI" and its transcript holds "A I"
- **THEN** the take differs by no unit by reading

#### Scenario: A language that hears its Latin words by their letters

- **WHEN** Chinese declares that its Latin-script words are heard by their letters, and a Chinese take's text holds "their" where its transcript holds "there"
- **THEN** the take differs by one unit by reading

### Requirement: Pronunciations are compared with primary stress, secondary stress read as none

Two pronunciations SHALL be the same when their phones and primary stresses are, with secondary stress read as none.

#### Scenario: Secondary stress against none

- **WHEN** an English take's text holds "catalogue" and its transcript holds "catalog"
- **THEN** the take differs by one unit and by no unit by reading

#### Scenario: Primary stress kept

- **WHEN** an English take's text holds "a" and its transcript holds "uh", which CMUdict stresses where "a" is weak
- **THEN** the take differs by one unit by reading

### Requirement: A word the dictionary does not hold, and a declared term, are compared as before

A Latin unit SHALL be looked up in the dictionary as it is written and then by its letters alone. A unit that the dictionary does not hold SHALL be compared by its letters and digits only, and a unit that says a declared term SHALL be compared as that term and by its letters only.

#### Scenario: A word the dictionary does not hold

- **WHEN** an English take's text holds "delivery's" and its transcript holds "delivery"
- **THEN** the take differs by one unit by reading

#### Scenario: A declared term

- **WHEN** a film declares the term Git, an English take's text holds "Git" and its transcript holds "get", which CMUdict also pronounces as it pronounces git
- **THEN** the take differs by one unit by reading

### Requirement: A judgment reads only the pinned dictionary

For an edition whose language declares its Latin-script words heard by CMUdict's pronunciations, a judgment SHALL read only the dictionary file the supply step placed, at the pinned SHA-256; where it is missing or differs, `judge`, `converge` and `audition` SHALL stop before any model loads, with one line that names the supply step. Its record SHALL name the dictionary's source and SHA-256 and the pronunciation's SHA-256. An edition of another language SHALL read no dictionary.

#### Scenario: No dictionary in place

- **WHEN** the supplied dictionary file is missing, or holds other bytes than its pinned SHA-256, and `judge` is asked about an English edition
- **THEN** the command exits 1 before any model loads, with one line that names `python -m filmkit.supply`

#### Scenario: A language that reads no dictionary

- **WHEN** no dictionary file is in place and `judge` is asked about the Chinese edition
- **THEN** the judgment runs as before and its record names no dictionary

#### Scenario: The record names the dictionary

- **WHEN** `judge` judges an English edition
- **THEN** its record names the dictionary's URL at its commit and its SHA-256, and the edition's pronunciation's SHA-256

### Requirement: The owner's hearing settles the lines it names for one take

A film MAY record in its declaration, outside each edition's pronunciation and cast, that its owner, the author it declares, heard one take of a thought, by the edition, the thought, the take's audio SHA-256, the lines settled (`units`, `clarity`), the listener, the date and a note. The judgment SHALL pass those lines of that take alone, judge every other line and take as before, keep the measures and name the listener and date; a line passed without the record SHALL record it as not needed.

#### Scenario: A take heard to say its words

- **WHEN** a take's transcript differs from its text by one unit by reading and the film records that the owner heard the take whose audio has that SHA-256, settling `units`
- **THEN** the units line passes, its record names the listener and the date, and the take's record still states one differing unit by reading

#### Scenario: A take heard clear

- **WHEN** a take reads 17.4 dB under an 18.0 dB thought line and the film records the owner's hearing of that take settling `clarity`
- **THEN** the clarity line passes, naming the listener and the date, and the take's record still states 17.4 dB

#### Scenario: A hearing of the words alone

- **WHEN** a heard take settles `units` alone and reads under its thought line
- **THEN** its units line passes and its clarity line names it for the ear

#### Scenario: A heard take that cuts a phrase end

- **WHEN** a take heard for its words and its clarity also cuts a phrase end
- **THEN** the take is refused by the phrase line alone

#### Scenario: Another take of the heard thought

- **WHEN** a convergence judges a candidate of a heard thought whose audio has another SHA-256
- **THEN** its units and clarity lines are judged as if no record stood

#### Scenario: A record the take does not need

- **WHEN** the film records a hearing that settles `units` for a take that differs from its text by no unit by reading
- **THEN** the take passes, and the units line's record says that the hearing was not needed

### Requirement: A malformed or stale record of hearing is refused

The loader SHALL refuse a record of an edition the film does not declare, a take that is no SHA-256, lines that are empty or name another line, a listener other than the film's declared author, and a second record of one take. The selection SHALL refuse, before it writes anything, each record whose take is not its thought's selected take, naming it. No convergence SHALL write a record.

#### Scenario: A listener who is not the owner

- **WHEN** a record names a listener other than the author the film declares
- **THEN** the loader refuses the declaration, naming the record and the author it expects

#### Scenario: A record that names no audio or no line

- **WHEN** a record's take is not 64 hexadecimal digits, its lines are empty or name `pause`, or a second record names the same take
- **THEN** the loader refuses the declaration, naming the record

#### Scenario: A record of another take at selection

- **WHEN** the film records a hearing of a thought whose selected take has another audio SHA-256
- **THEN** the selection exits 1, naming the record's edition, thought and take, and writes nothing

#### Scenario: A record of no thought

- **WHEN** the film records a hearing of the thought 14.9 and the edition's script holds no such thought
- **THEN** the selection exits 1, naming the record, and writes nothing

### Requirement: What judges a take binds no take's request

The pronunciations a judgment reads and the records of the owner's hearing SHALL enter no take's request, so every request and its fingerprint SHALL stay as they were before either existed.

#### Scenario: The sample's requests with both in place

- **WHEN** the engine plans every request of both sample editions with the dictionary in place and a record of hearing declared for one of the sample's thoughts
- **THEN** each segment's fingerprint and speech settings equal those recorded in the engine's golden requests, and a candidate's request SHA-256 equals the one planned without them

### Requirement: A thought for the ear waits for the owner's hearing

A thought for the ear SHALL get no candidate and SHALL wait for the owner's hearing: `judge` and `converge` SHALL exit 1 while one waits, naming it apart from the refused thoughts with its take's path, audio SHA-256, clarity and line.

#### Scenario: A thought for the ear in a judgment

- **WHEN** `judge` judges an edition in which no line refuses a thought and one take, heard by no one, reads under its thought line
- **THEN** the command exits 1 and names that thought for the ear, apart from the refused thoughts, with its take's path, audio SHA-256, clarity and line

## MODIFIED Requirements

### Requirement: A take is held to its words

A take SHALL be refused when a unit of its transcript differs from its text by reading, unless the owner's hearing settles its words. The limit SHALL be a constant of the judgment, stated in every judgment's record.

#### Scenario: A take whose transcript holds another word

- **WHEN** a take passes every other line and its transcript differs from its text by one unit by reading
- **THEN** the units line fails and the take is refused

#### Scenario: A take whose transcript is spelled otherwise

- **WHEN** a take's transcript differs from its text by three units and by none by reading
- **THEN** the units line passes

### Requirement: A take's clarity is judged only by a line the film declares for a single thought

Where a film declares a clarity floor and a thought margin, a take that reads under the floor, or under the floor less the margin for a thought the film declares as kept, SHALL be named for the ear and not refused for its clarity, unless the owner's hearing settles its clarity. Where a film declares a floor and no margin, a take's clarity SHALL be recorded and not judged, and the record SHALL say so. Without a floor, clarity SHALL NOT be measured. The rule SHALL be the one `preflight` asks.

#### Scenario: A film with a floor and no thought line

- **WHEN** a film declares a floor of 17.0 dB for an edition and no thought margin, and a take reads 15.0 dB
- **THEN** the take's record states 15.0 dB and that a single thought has no line, and the clarity line refuses nothing

#### Scenario: A kept thought above its line

- **WHEN** a film declares a floor of 17.0 dB and a margin of 1.0 dB, keeps one thought, and that thought's take reads 16.5 dB
- **THEN** the clarity line passes for it, and a take of any other thought that reads 16.5 dB is named for the ear

#### Scenario: A thought under the line, heard by no one

- **WHEN** a thought's take passes every other line and reads 17.4 dB under an 18.0 dB thought line, and no record of hearing names it
- **THEN** the convergence generates no candidate for it, names it for the ear with its take's path, audio SHA-256, 17.4 dB and 18.0 dB, and exits 1, and the thought is not settled

#### Scenario: A thought under the line, heard on this take

- **WHEN** the film then records the owner's hearing of that take settling `clarity`
- **THEN** the thought is settled, and the judgment names nothing for the ear

#### Scenario: A thought under the line, heard on another take

- **WHEN** the film records a hearing settling `clarity` of another take of that thought
- **THEN** the thought is still named for the ear and is not settled

#### Scenario: A thought under the line that another line refuses

- **WHEN** a take reads under its thought line and also ends abruptly with no declared release
- **THEN** the take is refused by its ending line and its thought gets candidates, among which the convergence chooses by its margins as before

### Requirement: An edition's narration is judged as a whole

`python -m filmkit.narration.judge` SHALL judge every thought of the receipt the edition's cast declares and write one record of each thought's measures, lines and verdict, bound to the receipt, the script and the cast by their digests. It SHALL refuse, before any model loads, a receipt that does not hold exactly the script's thoughts. It SHALL exit 1 and name each refused thought with every failing line. It SHALL generate nothing, and judging unchanged takes again SHALL write the same record.

#### Scenario: Two refused thoughts

- **WHEN** one thought of a receipt opens its recording in sound and another ends abruptly
- **THEN** the command exits 1, names both thoughts with their lines, and its record lists both

#### Scenario: An accepted narration

- **WHEN** no line refuses a thought and no thought is for the ear
- **THEN** the command exits 0 and its record lists no refused thought

#### Scenario: A receipt that lacks a segment

- **WHEN** the script holds a segment the receipt does not
- **THEN** the command refuses and names the thoughts the receipt lacks

### Requirement: An audition qualifies a take by the judgment's lines

An audition SHALL propose only a take that no line of the judgment refuses, a take above its clarity line before one for the ear, and SHALL name a proposed take for the ear as such; it SHALL record each take's lines and its counts by unit and by reading. The required phrase and the preference for an ending or a length SHALL order the qualified takes within each of those two kinds and qualify none.

#### Scenario: A take that a line refuses

- **WHEN** one take ends most quietly and differs from its text by one unit by reading, and another passes every line
- **THEN** the audition proposes the other take

#### Scenario: The required phrase

- **WHEN** two takes pass every line and only one transcript holds the required phrase
- **THEN** the audition proposes that take, and proposes the other when it is the only one

#### Scenario: A clearer take and one for the ear

- **WHEN** one take passes every line and reads 18.3 dB, and another holds the required phrase, ends more quietly and reads 17.6 dB under its 18.0 dB line
- **THEN** the audition proposes the first; when the second is the only take no line refuses, it proposes the second and names it for the ear
