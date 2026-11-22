## Why

A film whose pronunciation contract respells a word cannot be narrated by the engine's own command. The contract's normalization writes a word for the narrator in another spelling: a Han word in another character of the same sound, a Latin name as it should be said. The judge compares a take's transcript with that spoken text (`narration/judgment.py`, `measured`) and allows no unit to differ by reading (`UNIT_LIMIT` 0). A recognizer mostly writes the word in its own spelling, so a take that says its text is refused:

- **English.** The pinned recognizer wrote a film's respelled name in its display spelling in all 93 recorded occurrences and in the respelling in none.
- **Chinese, Han words.** It wrote the display word in all 30 takes of three thoughts that say a respelled Han word; the dictionary reads those characters the way the film respells them against, and a film cannot declare their reading, because the readings check reads the spoken text.
- **Chinese, the name.** Inside Chinese speech the recognizer has no steady spelling for a foreign name: of 227 recorded occurrences it wrote the display form 74 times and nine other spellings 153 times, one spelling throughout a transcript. The film's owner heard takes in the three common spellings as the name said correctly.

On 22 November 2026, with the approved December texts on filmkit 0.26.1, that film's Chinese edition ended two rounds and the run-on round with 23 of 57 thoughts unsettled after 216 candidates, and its English edition with 24 of 57 after 84. All 23 Chinese thoughts stand at a respelling. Of the 24 English ones, 20 are the name alone.

The engine has a judge of how a Latin name is said: a term a film declares in `[[narration.terms]]` has the first vowel of each occurrence compared with a reference occurrence's (`narration/terms.py`). No film declares one, and nothing asks a film that respells a name to declare it.

## What Changes

- **A Han word that the contract respells is compared as one word.** Where a `homophone` rule respells a word, the comparison reads that word, in a text and in a transcript, as its spoken form reads. One case that passes today is refused: a transcript that writes the display word where the text holds another character with the reading the film respells against.
- **A declared term is one unit under its display form and its spoken form**, in any case, a possessive kept, in both editions.
- **In the Chinese edition, a declared term's unit is also alike one Latin unit of other letters that holds a letter and is no other Latin unit of the edition's script.** A Han character in its place, another of the edition's names as the script spells it, digits, a repeat, a trailing Latin word and a missing unit still differ. A take's record names each unit that stood for a term in other letters. How the term is said stays with the term line, which holds its first vowel to the reference's.
- **A Latin name that the contract respells with other letters is a declared term, and every command that would load a speech model refuses first where it is not:** the readings check before a narration, whatever the contract's schema version, and `judge`, `converge` and `audition` before a model loads, each naming the name, its spoken form and the thoughts that say it. Whether the letters are other letters is asked of the comparison itself; a rule that only spaces or recases a name asks for no term. **BREAKING** for a film that respells a Latin name and declares no term: one film today.
- **A reference occurrence that shows no two formants is refused in one line** that names the reference and says to declare another occurrence, in `judge`, `converge` and `audition`, on the take alone and in its segment's alignment, before any candidate is asked. Today the first is a traceback in all three commands and the second ends a convergence refused with no thought named.
- The limit stays zero. No exception is added, and `converge`'s rounds do not change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `narration-convergence`: four requirements beside "Han characters are compared by reading" and "Latin units are compared by their letters and digits", which stand as they are: a respelled Han word reads as its spoken form; a declared term is one unit under both its forms; in Chinese speech one Latin unit of other letters may stand for a declared term, and the take's record names it; a reference without two formants stops the command in one line. "A take is held to its words" keeps its limit and is not changed.
- `spoken-readings`: two requirements beside "A film declares how its Latin-script terms are said" and "Every language speaks a declared term by its declared form": a Latin name respelled in other letters is a declared term, which the readings check asks; and a command that loads a speech model asks for the term first.

`engine-distribution`, which owns the adoption command, does not change: that command reads tracked files without a declaration that loads, and the finding needs the loaded terms, the contract and the scripts.

## Impact

- `src/filmkit/narration/recognition.py` (a term's unit in both editions and in Chinese speech), `readings.py` (one function for the words the comparison reads by; the new refusal's place in the check), `terms.py` (the refusal; one function for which form a unit says and whether it is possessive), `judgment.py` (the bench's one value for the comparison; the ask in `studio`; the two refusal lines; the record of a unit that stood for a term), `audition.py` (the ask), and their tests: `tests/narration/test_recognition.py`, `test_readings.py`, `test_terms.py`, `test_judgment.py`, `test_audition.py`. Every test string is written for the tests. The README's paragraph on the limit of the third rule, and the CHANGELOG.
- **Acceptance:** the built functions are run over the recorded transcripts of the six editions of the trials of 22 November (1,109 takes) and over the trial clones' records of that evening, and the Change states, edition by edition, the takes that pass the `units` line before and after, and that none which passes before is refused after.
- **The film that respells its name** declares it as a term with a reference occurrence in each edition, five lines in its declaration. Its recordings are not narrated again for the declaration. A person hears the two reference occurrences before either edition is accepted. On the recorded takes its Chinese edition then settles if the term line agrees, which is measured before the release; its English edition ends with four thoughts unsettled until the Change below.
- **The other films and the sample film**: no take's verdict changes on the recorded takes.
- **What the Change gives up**: in the Chinese edition the letters that the recognizer writes for a declared term no longer refuse a take. A take that says another word that is no Latin unit of the edition, or another of its names spelled otherwise than the script spells it, passes the `units` line where the recognizer writes it in Latin letters; the term line then holds only its first vowel.
- **Before the release, by measurement:** what the term line says of whole editions, by `python -m filmkit.narration.judge` with the term declared in a trial clone, under one host ticket, on filmkit 0.26.1 as it is. The width of the third rule was measured on 22 November on the voice chosen that day: one unit in all 89 of the name's occurrences.

## Not in this Change

- **Words heard as another where the contract respells nothing**: nine thoughts in the trials, seven English and two Chinese. A Change of its own, with the two decisions of the archived Change `judge-and-converge-narration` that the trials' figures reopen by their own conditions (the comparison by reading; the limit of zero, which the owner decided on 18 November 2026), the recognizer told a film's names as vocabulary, and the help of `--rounds 0`, which does not say that the run-on round still runs.
- **Binding a term's reference to the take a person heard.** The owner's to decide.
- **A wider third rule** (two units for one name): only if the takes of the voice that will narrate need it, with its price stated: a repeat and a trailing Latin word then pass.
- **Whether a term's declaration still states its spoken form**, or reads it from the contract's rule: the Change planned for 26 November 2026, since a check between two hand-kept copies is not a source. This Change keeps the declaration form as it is.
