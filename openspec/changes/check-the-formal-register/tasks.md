## 1. The pin and the standard's places

- [x] 1.0 Write `src/filmkit/register/standard.md`: the scope, the order and R1 to R6 as the owner approved them
      (`build/evidence/formal-register/standard.md`), its words unchanged.
- [x] 1.1 Pin Vale 3.27.0 in `.config/mise/config.toml` and `mise.lock` under the repository's release age. Done when
      `mise install --locked` installs it and the engine's tests resolve it.
- [x] 1.2 `concepts.places()` gives each edition's places and the entry page once, for the concept check and the
      register check: each text run of the page a unit of its own, the words of `alt`, `title` and `aria-label` with it,
      a caption term's place named with its term. Done when the tests in `tests/test_concepts.py` pass and refuse a
      counterexample on the entry page, named once.

## 2. The base style and its tests

- [x] 2.1 Write the base style. Errors: `address` (R1's listed pronouns and their inflections), `colloquial` (R3's
      listed Chinese words and particles, each plainly, wherever it stands), `contractions` (R3 English), `marks` (R5 in
      both editions: exclamation marks, dashes and ellipses in their typed forms; an unspaced en dash and a command's
      flag pass). Warnings: `we` (R2), `questions` (R4: more than one question in a thought), and one rule each for the
      forms the engine adds to R1's and R3's classes. Done when `vale test --coverage` passes on every rule, with
      possessives and curly apostrophes as English cases.
- [x] 2.2 `tests/register/test_register_style.py` runs `vale test --coverage` on the base style with the pinned Vale
      and requires a firing case of every token of an error rule; PyYAML, with which it reads the rules, is declared in
      the `dev` group at the version the lock holds. Done when `uv lock --check` passes and the lock's change is the two
      `dev` lists alone.
- [x] 2.3 Tests in `tests/register/test_register_check.py` read the forms that
      `src/filmkit/register/standard.md` lists for R1 and R3 and require the check to refuse each; hold each rule's
      level by what the check does; and require every error-level form of the style to be a listed one or a declared
      inflection. Done when they fail for a listed form taken out of the style, for a level flipped and for an
      engine-added form raised to an error.
- [ ] 2.4 No table of standard words: the base style's Chinese rules hold the listed forms alone, and a listed form
      is refused wherever it stands. Done when `tests/register/test_register_words.py` states the grade of each of its
      sentences in the test itself, holds the colloquial sentences of the second and third reviews as refusals and each
      standard word that holds a listed form as a refusal that says how a film keeps it, and holds an English form
      joined by a hyphen or an underscore, an apostrophe written as an acute accent or a grave, and a form with an
      unseen character inside it as refusals.

## 3. The check

- [x] 3.1 Declare `[register]` with `[[register.exceptions]]` (`place`, `form`, `within`, `reason`) in the film model.
      Done when tests in `tests/register/test_register_check.py` cover a valid exception, a malformed one, and a text
      that does not hold its form, adds only marks to it, or is held by another declared text of the same place.
- [x] 3.2 `filmkit.register.check()`: render the places as one text, one place or one run of the entry page a
      paragraph, unseen characters left out; run the pinned Vale once; map each alert to its place by a table; excuse
      the occurrences of a form that lie inside a declared text at its place and refuse every other; refuse on errors,
      naming every place, on a stale exception, on a Vale whose version differs from the release record's, on rule
      files that are missing and on a run that cannot be read; return the warnings and the exceptions applied. Done
      when the tests in `tests/register/test_register_check.py` and `tests/register/test_register_words.py` cover an
      error, a warning, a standard word declared and undeclared, a quotation, an occurrence outside the declared text,
      a second listed form inside the declared text, the declared text at a second place, a stale exception, an
      exception for a warning, a form on the entry page and in a caption term and questions in two places; and the
      tests in `tests/register/test_register_runs.py` cover another Vale on the path, each abnormal run (a span beside
      the form, a status its output does not bear out, a rule file missing from an installed layout among them), and
      the checker's arguments and encoding.
- [ ] 3.3 Call the check from `narrate.gate` and `preflight` beside the concept check, and bind the entry page in the
      readiness receipt. Done when each refuses a film with an error-level form and `preflight` writes a refused
      receipt for it and for a Vale that is not the pinned one, by the tests in `tests/narration/test_narrate.py` and
      `tests/test_preflight.py`, `admitted` refuses both editions after the entry page changes, and an entry page that
      is no text ends both pre-render questions in a refused receipt, not a traceback.
- [ ] 3.4 `review.round prepare` writes the register report into the round and fills `{register}` with its path and
      the rules from `src/filmkit/register/standard.md`; a template without `{register}` is refused. Done when a prepared
      round holds both and a template without the field is refused, by the tests in `tests/review/test_prepare.py`.

## 4. The sample film, the release record and the documents

- [ ] 4.1 The sample film's words pass the check, its prompt template cites `{register}`, and its review declaration's
      `language_quality` and `雅` ask for formal standard written language. Done when `python -m filmkit.register` passes on
      the sample and a test in `tests/register/test_register_check.py` reads the two declarations.
- [ ] 4.2 The release record states Vale's version; the adoption reader reports a film that pins another or none.
      Done when the tests in `tests/test_adoption.py` cover both.
- [ ] 4.3 The README's command table, requirements and its sentence on what narration checks first, and the
      Changelog's adoption sentences: a film adopting this release passes the register check before it narrates and
      declares its exceptions by place; its entry page is now read by the concept check too.

## 5. Acceptance

- [ ] 5.1 The check run on every place of the three released films lists as errors the forms of the inventory's R1
      and R3 that the standard lists, with the standard words that hold one (名副其实 at five places in two films
      on 21 November 2026), and no other; run on the texts proposed for the December editions in throwaway copies, each
      with its declarations, it refuses nothing; the record stands in `build/evidence/check-the-formal-register/`.
