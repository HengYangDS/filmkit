# narration-convergence Specification

## Purpose

Let an edition's narration settle by itself: judge every take by the lines the film already holds for a take, generate and choose candidates for what a line refuses, and name what cannot be settled as a question of the text.

## Requirements

### Requirement: Han characters are compared by reading

Where a transcript is compared with a take's text, two Han characters with the same reading, tone kept, SHALL count as the same unit. A character's reading SHALL be that of the declared word it stands in, or of the spoken form where a `homophone` rule respells its word, and otherwise the dictionary's in its context. 的, 地 and 得 SHALL count as one only where the text says a particle. A take's record SHALL state its differing units by reading beside those by unit.

#### Scenario: A homophone in the transcript

- **WHEN** a Chinese take's text holds 在 and its transcript holds 再 at that place
- **THEN** the take differs by one unit and by no unit by reading

#### Scenario: Another tone

- **WHEN** a take's text holds 买 and its transcript holds 卖
- **THEN** the take differs by one unit by reading

#### Scenario: A character that is no particle

- **WHEN** a take's text holds 土地 and its transcript holds 土的
- **THEN** the take differs by one unit by reading

#### Scenario: A respelled word written in its own characters

- **WHEN** the contract respells 去重 as 去虫, the take's spoken text holds 去虫 and its transcript holds 去重
- **THEN** the take differs by no unit by reading

#### Scenario: A respelled word where the text holds the reading respelled against

- **WHEN** the contract respells 去重 as 去虫, the take's text holds 去众 and its transcript holds 去重
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

### Requirement: What the count refuses is the edition's refusal

What the selection, the binding or the decoding of the count refuses SHALL end the command with exit 1 and one line that names the refusal, after the record is written as ended with it. With a thought unsettled the count SHALL NOT be asked. An edition whose cast declares no performance recording with its alignment, or whose script declares no pause policy, SHALL NOT be asked either, and the command's exit SHALL be as without the asking. The record SHALL say why the count was not asked.

#### Scenario: A recording changed since its receipt

- **WHEN** the binding refuses a recording whose waveform differs from its record
- **THEN** the command exits 1 with one line that names it, and the record is ended with that refusal

#### Scenario: The selection refuses two thoughts

- **WHEN** the selection's gates refuse two thoughts
- **THEN** the command's one line holds both refusals

#### Scenario: A recording that FFmpeg cannot decode

- **WHEN** FFmpeg ends with an error for a selected recording, whatever caused it
- **THEN** the record's fit says `refused`, and the command's one line names the command that failed and holds the last line of the error that FFmpeg wrote

#### Scenario: An error line that holds control characters

- **WHEN** the last line that FFmpeg wrote holds an escape, a bell or a tab
- **THEN** the command's one line holds a blank for each

#### Scenario: A thought unsettled

- **WHEN** a thought is still refused after its rounds
- **THEN** the count is not asked and the record says that thoughts are unsettled

#### Scenario: Nothing declared to count

- **WHEN** the cast declares no performance recording
- **THEN** the count is not asked, the record says so, and the command exits 0

### Requirement: A fault of the count ends the record and keeps its traceback

A fault of the count that is no refusal of the selection or the assembly SHALL be raised with its traceback, after the record is written as ended with the verdict `failed` and the fault's words. An error of the system that names no file by an absolute path, such as a decoder that is not installed, SHALL be such a fault. One that names a file by an absolute path, below the film's root or outside it, and a recording that is no WAV, SHALL be the edition's refusal, in one line.

#### Scenario: A record that lacks a segment

- **WHEN** the count ends in a `KeyError` for a segment that a record lacks
- **THEN** the command ends with that fault's traceback, and the record is ended with the fit `failed` and the fault's words

#### Scenario: A decoder that is not installed

- **WHEN** FFmpeg is not on the PATH when the recordings are decoded
- **THEN** the command ends with that fault's traceback, and the record's fit says `failed` and not `refused`

#### Scenario: A recording missing below the film's root

- **WHEN** a selected recording below the film's root is missing
- **THEN** the command exits 1 with one line that names the file, and the record's fit says `refused`

#### Scenario: A file named outside the film's root

- **WHEN** a recording or a receipt that the edition names by an absolute path outside the film's root is missing
- **THEN** the command exits 1 with one line that names the file, and the record's fit says `refused`

#### Scenario: A recording that is no WAV

- **WHEN** the selection reads a recording that is no WAV, or one that ends inside its header
- **THEN** the command exits 1 with one line, and the record's fit says `refused`

### Requirement: A declared term is one unit under both its forms

Where a transcript is compared with a take's text, a Latin unit whose whole word says a term the film declares, its display form or its spoken form in any case, SHALL count as that term, its possessive kept, in every edition; inside a compound its letters SHALL be compared as any other unit's. A Latin unit in other letters SHALL still differ in the English edition.

#### Scenario: A declared term in its display form

- **WHEN** a film declares the term NAME with the spoken form Naim, an English take's text holds "Naim's" and its transcript holds "Name's"
- **THEN** the take differs by one unit and by no unit by reading

#### Scenario: A declared term in other letters in English

- **WHEN** the same film's English take's text holds "Naim" and its transcript holds "Nime"
- **THEN** the take differs by one unit by reading

### Requirement: In Chinese speech one Latin unit of other letters may stand for a declared term

In the Chinese edition a declared term SHALL also count as the same as one Latin unit of other letters that holds a letter, says no declared term and is no other Latin unit of the edition's script. Two or more units, digits alone, a Han character and another Latin unit of the script SHALL still differ. The take's record SHALL name each unit that stood for a term, with its term.

#### Scenario: A declared term in other letters in Chinese speech

- **WHEN** the film's Chinese take's text holds "Naim 走的是另一条路。", its script's other Latin units are agent and git, and its transcript holds "Nime走的是另一条路。"
- **THEN** the take differs by no unit by reading, and its record names nime for NAME

#### Scenario: What still differs in Chinese speech

- **WHEN** that Chinese transcript holds, in the term's place, "Agent", "2024", "内姆", "Nime Nime", "Nime OK" or nothing
- **THEN** the take differs by at least one unit by reading

### Requirement: A reference that gives no first vowel stops the command in one line

Where a declared term's reference occurrence shows no two formants on its take, or shows none or does not stand as the selection aligns its segment, `judge`, `converge` and `audition` SHALL stop before they judge a thought against it or ask a candidate, with one line that names the reference and says to declare another occurrence, and with no traceback.

#### Scenario: On its take

- **WHEN** a film's reference occurrence 26.1 #0 of NAME shows no two formants on the receipt's take
- **THEN** `judge` exits with the one line "en: the NAME reference 26.1 #0 shows no two formants on its take; declare another occurrence of NAME as its en reference in [[narration.terms]]"

#### Scenario: In its segment

- **WHEN** the take alone shows two formants and the segment's alignment beside the receipt shows none at the reference
- **THEN** `judge` exits with one line that names the reference, says that the selection aligns its segment, and says to declare another occurrence, and writes no judgment record

#### Scenario: Not in its segment

- **WHEN** the take alone holds the reference and the segment's alignment places no word that says the term there
- **THEN** `judge` exits with one line that names the reference as not in the narration as the selection aligns its segment, says to declare another occurrence, and writes no judgment record

### Requirement: A settled edition is counted for its runtime

When its rounds end with no thought refused, the convergence SHALL count the edition by the functions that `produce select` and `produce fit` run, and the record's fit SHALL state, as counted, the runtime the assembly would give and the seconds of the rounding's fraction that the gaps and the credits take. An edition whose allocation the assembly accepts SHALL be recorded as `fits`, with exit 0. No count SHALL be said as a miss, nor a thought pause named to reach a runtime.

#### Scenario: An edition counted

- **WHEN** no thought is refused and the speech with its designed thought pauses, its designed gaps and its closing quiet comes to 1472.14 s, with 3 s of credits
- **THEN** the command exits 0, and the record's fit states `fits`, a runtime of 1476 s and 0.86 s taken by the gaps

#### Scenario: A long narration

- **WHEN** a settled edition's speech alone comes to 1590.79 s
- **THEN** the command exits 0, and the record's fit states the runtime its count gives, with no seconds missing and no thought pause named

#### Scenario: A fraction the gaps cannot take

- **WHEN** every gap with a weight already stands at the top of its range and the rounding leaves 0.40 s
- **THEN** the command exits 0, and the record's fit states `fits`, the runtime in whole seconds, no seconds taken by the gaps and 0.40 s by the credits

### Requirement: An edition that the assembly refuses is refused

An edition whose clips or gaps cannot be designed under the script's pause policy SHALL end the command with exit 1 and one line that names that refusal, after the record is written as ended with the verdict `refused`.

#### Scenario: Clips that cannot be designed

- **WHEN** the edition's clips cannot be designed for their thought levels
- **THEN** the command exits 1 with one line that names the design's refusal, and the record's fit says `refused`

### Requirement: The count changes nothing and keeps nothing

The count SHALL replace no take, change no pause policy and write no tracked file. Below `build/` it SHALL write only what `produce select` and `produce fit` write for the edition: the selection's two records and the assembly's decode work files. A run SHALL keep nothing of the count for the next: a second run SHALL say the same lines and write the same record. `produce fit` SHALL print and refuse as the runtime fit states.

#### Scenario: The files written

- **WHEN** a settled edition is counted
- **THEN** the cast, the script and every recording are byte for byte as they were, and the files written, duration records apart, are the judgment's and the convergence's records, the selection's two records and the decode work files

#### Scenario: A second run on a counted edition

- **WHEN** the convergence runs again on an edition it counted, with nothing changed
- **THEN** it counts again, says the same line and writes the same record

#### Scenario: A run killed while it counts

- **WHEN** a run is killed between the selection and the end of the count
- **THEN** the record says that a run is under way and holds no fit, and the next run selects and counts again

### Requirement: A declaration the count does not take is refused before the run's first effect

The convergence SHALL refuse in one line, before it writes its record or narrates, a cast that declares `runtime_fit`, which nothing reads since an edition lasts as long as its narration, and a script whose pause policy the assembly refuses.

#### Scenario: A cast that still declares a reserve

- **WHEN** the cast declares `runtime_fit` with `reserve_seconds` of 0.5 s, or with no field
- **THEN** the command exits 1 naming the declaration, and no record is written

#### Scenario: A script that declares no thought range

- **WHEN** the script's pause policy declares no `thought_pause_range`
- **THEN** the command exits 1 with the policy's refusal in one line, and nothing has run

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
