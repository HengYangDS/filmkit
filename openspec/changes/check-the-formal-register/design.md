## Context

The films' owner made a standard of formal register final on 20 November 2026 at 19:42:52 (「照此定稿」): a film's
language as a whole follows formal standard written language under strict 信, 达 and 雅, rules R1 to R6 [S1]. This
Change carries the standard's text into the engine's own specification, so that it has a tracked home, and checks the
part a word-level rule can check. The engine already gathers the places a viewer meets a film's words for the concept
check [S2] and runs that check before narration (`narrate.gate`) and before a render (`preflight`) [S2]. ETHOS
supplies and pins Vale through Mise for its own `prose` gate [S3]. A research trial ran Vale on the three films [S4],
and an independent review of this design's first draft found two of its decisions wrong [S5]; this draft answers it.

## Goals / Non-Goals

**Goals:**

- The standard's text stands in the engine, once, as approved (`src/filmkit/register/standard.md`); the base style's
  forms and messages and the reviewers' prompt follow it.
- A film whose narration, titles, captions or release text holds an error-level form of R1, R3 or R5 is refused
  before it narrates and before it renders, naming each place and form at once.
- R2 and R4 are reported where a reviewer reads them: the review round's inputs.
- A film excuses a form at one place, with a reason, as it excuses a fast cue or a thought under its clarity line;
  an exception that excuses nothing is refused as stale.

**Non-Goals:**

- Judging R4 to R6 as a reviewer does, or how a sentence is organized.
- The picture's text in this Change: read only once the painted texts are recorded (decision 7).
- Changing any film's words.

## Decisions

1. **Vale carries the rules; the engine gathers the places, maps the alerts back and applies the film's exceptions.**
   - **Rests on:** the trial and the review [S4, S5]: with `nonword: true` and lookarounds, Vale's rules found the
     inventory's R1 and R2 forms and its 跑 (the trial did not run the whole R3 list or R5); `vale test --coverage` fails
     a rule that never fires; it reads plain text from stdin and counts the questions of one paragraph.
   - **Considered:** (a) a declared TOML table matched with Python `re`, with levels, pytest cases and place-bound
     exceptions [S5, note 16]: as able as Vale for Chinese, since Vale matches Chinese as plain patterns too; (b)
     textlint with `prh`; (c) LanguageTool's Chinese module [S4]; (d) a word segmenter before the rules, so
     that a rule matches whole words: fewer forms inside standard words, but a statistical dictionary would then decide
     a refusal, and every film's lock would gain a package [S6]. Read (d) again if the acceptance on the released
     films and the December texts shows more than a handful of false refusals.
   - **Chosen because:** the owner asked on 20 November for mature tools over hand-written code; Vale's rules are
     declarations with their own tests and messages, and are the same tool ETHOS uses for prose; the gain over (a) is
     the rule tests and the English side (word boundaries, case), not Chinese matching.
   - **Applies to:** `src/filmkit/register/` and its base style.
2. **One run over one text, one place a paragraph, mapped back by a table.** An empty place is skipped; a place's line
   breaks are joined by a space between Latin words and by nothing between Chinese characters. Vale runs with
   `--no-global --config <the engine's config> --ext=.txt --output=JSON`. The configuration is `register.ini` beside the
   check's module, a name of the engine's own: ETHOS takes a tracked file named `vale.ini` or `.vale.ini`, wherever it
   stands, for the repository's own prose policy and admits that at one place only [S10]. The entry page is one
   bilingual template: it is one place, read once for both editions.
3. **Levels follow who listed the form.** `error` refuses; `warning` is recorded.
   - **Rests on:** the owner approved the standard's text, lists included [S1]; the first style refused formal words
     at error level through forms the engine had added (不得由, 尽管用户, 进行到底), and no test held a level [S6].
   - **Considered:** every form of a rule's class at the rule's level (the first build); only the listed forms, with
     no additions.
   - **Chosen because:** an error is a form the standard's own text lists, or an inflection of one: R1's pronouns, R3's
     Chinese words and particles, English contractions, R5's marks. R2 and R4 are warnings, since the standard allows a
     我们 that names a party the film has named and a question the film answers; so is every other member of a rule's
     class that the engine adds (到底, 顺手, 靠得住, 提了个, 得由, 管用; 咱, 各位, 诸位, 朋友们). The engine may widen
     what reviewers are told, never what is refused. A test reads the lists from the document and requires each form
     to refuse; another holds each rule's level by behaviour; a third requires every error-level form of the two
     rules whose forms the document lists one by one (R1's pronouns, R3's Chinese words) to be a listed form or a
     declared inflection of one. English contractions and R5's marks are classes the document names: the style
     lists their members, and each of those rule files quotes the document's sentence it implements [S8, m5].
   - **Applies to:** the base style; `tests/register/`.
4. **A listed form is never silent, and the engine holds no table of words that excuse it.** Every occurrence of a
   listed form is refused unless the film excuses it at its place (decision 6).
   - **Rests on:** the second review [S7]: the lookarounds that stopped the first build's false refusals excused
     listed forms in ordinary colloquial sentences with no alert at all (通过大家的努力, 不过其实没那么复杂, 先规划
     一下, 测试跑通了). The third review [S8]: the second build's table of 264 "standard words", which lowered a
     form inside one of them to a warning, lowered the standard's own colloquial uses the same way (喝点水吧 by 水吧,
     一起跑测试 by 起跑, 其实效果一般 by 其实效, 看一下发布记录 by 一下发): 13 of the 52 sentences its own test held, 9
     of the 29 refusals the build before it had held; 44 entries were joins of two words and 82 more a form and one more
     character; and no test could see the
     table widen. Plain text cannot tell 水吧 from 水 and 吧: every entry is a judgment about a word boundary that the
     matching cannot make. Counted by the check itself on 21 November 2026 over every place of the three released films
     (824 places) and the sentences proposed for December (137) [S8]: one standard word holds a listed form,
     名副其实, at five places in two films (a chapter title and the synopsis of one; a segment title, the synopsis
     and the player summary of the other); no other error stands inside a longer standard word, and the proposed
     sentences hold no error.
   - **Considered:** (a) longer lookarounds (the first review's advice, which led to the silent misses); (b) the
     table pruned to idioms a film is known to use (one entry today): the mechanism stays, each later entry is the
     same unverifiable judgment, and the reviewers read a standing warning for 名副其实 in every round; (c) a word
     segmenter (decision 1); (d) no table: the film that says a standard word states, at that place, the text the
     form stands within, and the engine verifies it.
   - **Chosen because:** (d). The fact "this 其实 is the idiom's" is stated once, where it holds, by the film that
     says the word, and is checked against the place's text; nothing in the engine can excuse a form a film did not
     declare; a later colloquial use at the same place is refused, since it does not stand within the declared
     text. The cost today is five declarations in two films.
   - **Applies to:** the base style's Chinese rules hold the listed forms alone, each plainly, wherever it stands;
     `register.check` has no word table. A refusal of a listed form says how a film keeps a standard word.
5. **Vale is pinned in the engine's Mise configuration and lock**, under the same 24-hour release age as every tool.
   - **Rests on:** hosted CI installs tools only by `mise install --locked` and never runs the supply [S5, finding 3];
     ETHOS pins Vale the same way [S3]; `filmkit.supply` hands the browser to its own locked installer, and Vale has
     none [S2].
   - **Considered:** the supply step with hand-written download and digest checks (the first draft; refused by the
     review: CI never runs it, and it would bypass the release age).
   - **Chosen because:** one pin, held by the tool that holds every other pin.
   - **Applies to:** `.config/mise/config.toml`, `mise.lock`, pinned at 3.27.0, the version ETHOS pins (it has
     `vale test --coverage`; one Vale on the host for both). The engine's release record states Vale's version beside its
     npm packages; the adoption reader reports a film whose Mise pins another or none; and the check itself compares
     `vale --version` with the record and refuses a difference, since another Vale may stand first on the path. The
     record takes the version from the Mise configuration when the engine is released (`released.compute`): an installed engine
     ships no Mise configuration, so the check reads the record, and the record's own test refuses a stale one.
6. **A film excuses an error-level form at a place by naming the text it stands within**
   (`[[register.exceptions]]`: `place`, `form`, `within`, `reason`), as `rate_exceptions` and `clarity_exceptions`
   name the cue or the thought they keep.
   - **Rests on:** Vale's vocabulary does not suppress a Chinese form inside a longer word (迷你 did not excuse 你), and
     its rejected words match whole words only [S5, finding 1]; a quotation such as 「帮我搞定」 in ddwg-film 19.6 must
     be excusable by the film, not by an engine release; the first build let an exception take a warning out of the
     reviewers' list and keep any number of questions [S6, m4]; the second build's exception stated a count, a number
     that restates the text beside it and that excused, at a place with one standard word and one colloquial use,
     either both or neither [S8, m4].
   - **Considered:** the count of the form's occurrences at the place (the second build).
   - **Chosen because:** `within` is the text the place holds around the form (名副其实 for 其实, 帮我搞定 for 搞): the
     engine excuses exactly the occurrences that lie inside an occurrence of that text at that place and refuses
     every other one, so a later use is never excused silently; an exception whose text the place no longer holds is
     refused as stale; `within` must hold a letter or a digit beyond its form, so no declaration excuses a form wherever it stands (a
     form and a mark, 吧。 for 吧, would keep every sentence-final 吧 of the place) [S9, m3]; two declarations at
     one place of which one text holds the other are refused as one too many [S9, n4].
     No number is kept by hand. An exception answers error-level alerts only; a warning always reaches the
     reviewers. The report lists every exception it applied, with its text and its reason.
   - **Applies to:** the film model (`[register]`), `register.check`.
7. **The places are the edition's words, not the picture's source lines.** Titles, chapter and segment titles,
   thoughts, caption terms, release prose, the player summary and the entry page's text. The picture's text sources
   are code; their lines hold regular expressions, ternaries and comments [S5, finding 2]. The picture's words join the
   check once the geometry check records the texts it paints: the Change `record-the-painted-texts`, owner this session,
   proposed after this one lands and before the films' December editions. Until then the reviewers read the picture's
   words against the standard (the round's prompt says so). The entry page is one place, read once for both editions; each of
   its text runs is a paragraph of its own. A run ends where a block element begins or ends; every other element,
   known to the engine or not, is read as inline, since a longer run can add an alert and cannot hide one; a line
   break (`br`, in either spelling) is read as a space inside its run, so that two lines never join into a form
   [S8, m1]. Characters a viewer does not see (Unicode's format characters, its variation selectors and its other
   default-ignorable code points, as `PropList.txt` of Unicode 16 lists them [S9, n3]) are left out
   of every place before the forms are sought [S8, m2]; the words of `alt`, `title` and `aria-label` are
   read with it [S6, m2]. What a page hides by `hidden` counts as shown: HTML lets an end tag be left out, and a
   reading that guesses where a hidden element ends hides what follows it [S7, m7]; only `script`, `style` and
   `template`, whose end tags are required, are left out. A caption term's place carries its term.
8. **One gatherer of places.** `concepts.places()` gives each edition's places and the entry page once, for both
   checks; the register check does not copy it.
9. **The warnings and the standard reach the reviewers** through the round's preparation: `review.round prepare`
   writes the register report into the round and fills `{register}` with its path and the rules R1 to R6 from the one
   source, `src/filmkit/register/standard.md`; a template without `{register}` is refused, as one without the concept
   contract's field is. The films' review declarations then need not restate the standard.
10. **The forms are the engine's, the exceptions the film's.** One base style for every film, as the watched characters
    of the readings check are the engine's; a film adds no forms of its own and excuses by place.
11. **A checker's run that cannot be read is a refusal, in one line.** Output that is no JSON object, an alert on a
    line no place holds, a run that outlives its deadline, an executable that is no program, and a status that its
    output does not bear out each refuse by name; none ends in a traceback and none passes [S6, m1]. The pre-render
    check therefore still writes its receipt.

## Risks / Trade-offs

- A listed form inside a standard word (其实 in 名副其实, 一下 in 统一下发, 弄 in 弄虚作假, 吧 in 酒吧, 你 in 迷你) → refused
  until the film declares the place and the word (decisions 4 and 6); the refusal says so. Counted on the released
  films: five declarations in two films.
- An English form joined by a hyphen or an underscore ("a thank-you note") → refused like any occurrence and kept by
  the same declaration; a letter sequence that only contains the form (young, you2) is no occurrence [S8, m3].
- Not read, by decision: characters of another script that spell a listed form (其實, full-width ｙｏｕ), and the
  attributes of the entry page other than `alt`, `title` and `aria-label` [S8, n6, n7].
- On the entry page a ruby's reading (`rt`, `rp`) is an annotation and is left out of its run, so that it does not
  part the form it annotates; an English form whose letters continue in the next inline element (`you` and `ng` in
  two spans) is the word the viewer reads, and is no occurrence [S9, n1].
- An installed engine that lost one of its rule files is refused by the installation record's own lines, and an
  engine without its Vale configuration by the file's name; a file changed in place is not detected at run time
  [S9, m1].
- A new pinned binary → held by Mise's lock and release age; CI installs it as it installs every tool.
- Every released film is refused after adopting → by design; each film's December edition fixes its words with its
  owner's approval, and declares an exception where a form is a quotation.

## Sources

- [S1] The standard, `build/evidence/formal-register/standard.md`, made final by the owner on 20 November 2026 at
  19:42:52 (C-4 in `build/evidence/owner-words.md`); its scope, order and rules move verbatim into the engine's
  `src/filmkit/register/standard.md`, their one source, which the specification names.
- [S2] The engine at `54383d9`: `concepts.py` (`edition_places`, `check`), `narration/narrate.py` (`gate`),
  `preflight.py` (`concept_check`), `supply.py`.
- [S3] ETHOS at beta.10: `.config/mise/config.toml` (`"github:vale-cli/vale" = "3.27.0"`), `system/gates.toml`
  (`prose`).
- [S4] `build/evidence/tooling-assessment-2026-11-20/prose-tools.md`.
- [S5] `build/evidence/formal-register/design-review-1.md`, the independent review of the first draft, 20 November
  2026: material findings 1 to 5, answered by decisions 5 to 9; and its second pass of 21 November 2026 00:00
  (`design-review-2.md`): the deltas, the runtime version check, the marks and the standard's verbatim text.
- [S6] `build/evidence/formal-register/code-review-1.md`, the independent review of the first build, 21 November
  2026: three material findings (formal words refused, levels untested, two specifications without a delta) and
  nine minor ones, answered by decisions 3, 6, 7 and 11 and by two more deltas.
- [S7] `build/evidence/formal-register/code-review-2.md`, the second review, 21 November 2026: one material finding
  (listed forms excused in silence, answered by decision 4) and thirteen minor ones.
- [S8] `build/evidence/formal-register/code-review-3.md`, the third review, 21 November 2026: two material findings
  (the lock; the word table, answered by decisions 4 and 6 as they now stand) and eight minor ones; with the count
  of listed forms over every place of the three released films and the proposed sentences, taken the same day by
  the repaired check (`build/evidence/check-the-formal-register/repair-3/measure-1.json` and its README). A first
  count by hand over the scripts' fields had found four places and missed the player summary.
- [S9] `build/evidence/formal-register/code-review-4.md`, the fourth review, 21 November 2026: land; five minor
  findings and seven notes, repaired in the stage clone before the lane (the installation check, a test for an
  exception's own form and place, `within` and its mark, the applied exceptions in the round, unseen characters).
  Its note n5 (`tests/test_preflight.py` at exactly 500 effective lines) is answered by the repository's ceiling, 500
  effective lines a file by ETHOS's measure (`code_effective_lines`), not by raw lines: the register cases moved to
  `tests/test_preflight_register.py` for that reason, and `tests/test_preflight.py` stays at 266 statements (447
  effective lines, 530 lines; the new file 55, 63 and 78). Measured the same day, statements, effective lines and lines:
  `test_film.py` 320, 499, 649; `test_adoption.py` 346, 472, 609; `test_ending.py` 281, 474, 604;
  `test_child_processes.py` 255, 386, 521; `test_preflight.py` 266, 447, 530.
- [S10] ETHOS 0.2.0-beta.11's readiness on the lane's head `4469f39`, 22 November 2026
  (`build/evidence/check-the-formal-register/readiness/`): refused before any gate ran, with
  `native_tool_configuration_location_invalid:vale`. Its rule, read in the installed product
  (`repository/policy/quality/tool_configuration.py` and the paradigm's `vale` entry): a tracked path whose file name is
  `vale.ini` or `.vale.ini` is the prose gate's configuration, whose place is `.config/checks/vale/vale.ini`. The
  engine's file was `src/filmkit/register/vale.ini` until that day; Vale reads any file that `--config` names.
