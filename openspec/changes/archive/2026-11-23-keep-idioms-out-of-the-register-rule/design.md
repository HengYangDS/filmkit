## Context

See [proposal.md](proposal.md). The rule `register.colloquial` (`src/filmkit/register/styles/register/colloquial.yml`)
is a Vale `existence` rule with `nonword: true`: each Chinese form that R3 of the standard lists is a token, matched
plainly wherever it stands, inside a longer word too. Decision 4 of the archived Change `check-the-formal-register`
chose that the engine hold no table of words that excuses a listed form, after two builds whose excuses failed: the
first build's lookarounds let colloquial sentences pass with no alert (不过其实没那么复杂, 先规划一下), and the second
build's table of 264 standard words lowered colloquial uses with them (喝点水吧 by 水吧, 一起跑测试 by 起跑, 其实效果一般
by 其实效). Its count then: one standard word, 名副其实, at five places in two films.

What the engine already does for a standard word is the film's declaration (`[[register.exceptions]]`,
`filmkit.film.Register`): a place, a form, the text the form stands `within` there and a reason. `register.check`
excuses exactly the occurrences inside that text at that place, refuses every other one, and refuses a declaration
whose place no longer holds its text, whose form stands there only as a warning, or that excuses no error-level
occurrence. This Change keeps all of that and takes one idiom out of the rule; it narrows decision 4, since the
engine now holds a list, of idioms only, admitted under decision 2 below.

## Goals / Non-Goals

**Goals:**

- 其实 inside 名副其实 is not reported; every other 其实 is, the one beside the idiom included.
- The idiom is stated once, beside the form in the rule, with what makes it formal; the rule's own cases pin it.

**Non-Goals:**

- The standard's text; standard words and quotations, which stay the film's to declare; idioms no film's text holds.
- A word segmenter, or any reading of word boundaries beyond the idiom's own characters.

## Decisions

1. **The rule's token for 其实 states the idiom by a lookbehind that the pinned Vale runs.** The token
   `其实(?<!名副其实)` matches 其实 unless the four characters that end at the match read 名副其实.
   - **Rests on:** runs of the pinned Vale 3.27.0 on 23 November 2026, with rules over plain text. The lookbehind
     token reported 其实 in 其实不难, in 名副其实，其实不难 the second only, in 名副其实其实 and in 其实名副其实 the one
     outside the idiom, and nothing in 这个示例名副其实; each alert's span is the form's two characters, which
     `register._alert` requires. The binary links `github.com/jdkato/regexp2/v2`, the regular-expression engine that
     runs the lookbehind. Vale's other means did not reach a form inside a longer Chinese run: with
     `exceptions: [名副其实]` beside the plain token, with `名副其实` in a vocabulary's `accept.txt`, and with
     `TokenIgnores = (名副其实)` for `*.txt`, the 其实 inside the idiom was reported in every text tried; `exceptions`
     is compared with the matched text alone.
   - **Considered:** (a) the lookbehind in the token; (b) `exceptions`, a vocabulary or `TokenIgnores`, which do not
     work here; (c) a table in `filmkit.register` of idioms with the form each holds, excusing an alert whose
     occurrence lies inside one, as `_within` does for a film's declaration.
   - **Chosen because:** (a) is Vale's own mechanism and keeps the idiom in the file that holds the form, under the
     cases that `vale test` runs; (c) would hold the fact apart from its rule and add code to the check.
   - **Applies to:** `colloquial.yml`: the token, a comment beside it that names the idiom, the form it holds and why
     it is formal, and a case that pins both.
   - **Reopened when:** the pinned Vale changes its regular-expression engine; the rule's cases run under every
     pinned Vale and would show it.
2. **An idiom joins the rule only where the listed word is not in it.** Three conditions: a film's text holds the
   idiom; within it the form's characters are not the word R3 lists (in 名副其实, 其 "its" and 实 "reality", where R3
   lists the adverb 其实 "actually"); and no sentence reads the idiom's characters with the listed word among them
   (名副 ends no phrase that the adverb 其实 can follow). The second and third are a reader's judgment of each entry;
   the entry's cases cannot prove them, and they hold the form beside the idiom to be reported. This answers decision
   4's objections: the lookbehind is the whole idiom, not a guess at a word boundary, and an entry is admitted by
   stated conditions, not by being a standard word.
   - **Considered:** (a) every standard word that holds a listed form, the failed table; (b) every fixed idiom that
     holds a listed form's characters, which would take 弄虚作假, where 弄 is the verb R3 lists; (c) the three
     conditions.
   - **Chosen because:** (c) relieves the matching only where it finds no listed word at all. Words whose characters
     can also be the listed word beside another word (水吧 in 喝点水吧, 酒吧 in 去喝酒吧, 起跑 in 一起跑测试), and an
     idiom that holds the listed word (弄虚作假), stay refused and stay the film's to declare.
   - **Applies to:** the comment beside the token, which states the conditions once.
3. **The standard's text stays as the owner approved it.** R3 lists the word 其实, and 名副其实 does not hold that
   word: the standard needs no exception, the matching does. Naming the idiom in R3 as well would state it twice and
   change the text that the requirement "The engine carries the formal register as approved" holds to the owner's
   approval of 20 November 2026.
4. **A film's declaration for a stated idiom is refused by the check as it stands, and no adoption question is
   added.** The check's existing refusal reads "The register exception of '其实' at <place> excuses no refusal: no
   error-level occurrence stands within '名副其实'".
   - **Considered:** (a) that refusal; (b) letting such a declaration pass silently, which would need the idiom in
     the check's code as well and would let a needless declaration stand; (c) the proposal's draft question of
     `filmkit.adoption`, which would read the rule's regexp2 pattern with Python's engine or run Vale where the
     adoption command needs none.
   - **Chosen because:** (a) names each declaration with its place and text before narration and before a render,
     from the one source, and costs nothing; (c) would add a second reader of the rule for a finding the check
     already gives.
   - **Applies to:** the requirement "A film excuses a form at one place", which gains the case and states the
     refusal of a declaration that excuses no refusal, which the check already makes; the Changelog's entry, marked
     breaking for a film that declares one.

## Risks / Trade-offs

- A later idiom entry chosen loosely would repeat the failed table. → Decision 2's conditions stand beside the token,
  and each entry comes with its cases, the form beside the idiom among them.
- The idiom parted by a character the viewer does not see, or across a line of its place. → The check removes such
  characters and joins Chinese lines by nothing before Vale reads them (`register._paragraph`), so the idiom is read
  as the viewer reads it; `tests/register/test_register_words.py` holds one such text.
- A film that declares 其实 within 名副其实 is refused when it adopts this release. → The refusal names each
  declaration; the Changelog says so.
- Released editions are not affected: they keep their tag's engine and are not rebuilt. No output bytes change.

## Migration Plan

A film adopts the release in its own lane: it removes each declaration of 其实 within 名副其实 that the check names,
and runs the check. Rollback is the token's previous text.
