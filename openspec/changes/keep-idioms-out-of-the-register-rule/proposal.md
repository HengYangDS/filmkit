## Why

The register rule `register.colloquial` lists 其实 as colloquial (`src/filmkit/register/styles/register/colloquial.yml:19`,
standard R3). It matches inside the formal idiom 名副其实 ("true to its name"), which the formal-register standard does not
mean to touch. On 23 November 2026 the essentials film's December texts, approved by the owner, met it in three Chinese
places, and the trial copy had to declare three `[[register.exceptions]]` for an idiom that is formal in every film.
A film-level exception is the right tool for a film's own choice; for a fixed idiom of the language it repeats one fact
in every film that uses it.

## What Changes

- The rule does not report 其实 where it stands inside 名副其实 (and any further fixed idiom whose characters hold a
  listed form but not the listed word, stated once beside the rule with the form it contains and why it is formal;
  design decision 2 states when one joins).
- The rule's own test pins both: 其实 alone reported, 名副其实 not.
- A film's `[[register.exceptions]]` keep working for standard words and quotations.
- **BREAKING for a film that declares 其实 within 名副其实:** that declaration now excuses no refusal, and the check
  refuses it as such, as it refuses any declaration that excuses nothing, naming its place and text; the film removes
  it when it adopts this release.

Out of scope: the standard's text, which the owner approved and which lists the word 其实, not the idiom's characters;
standard words that hold a listed form (跑道, 酒吧, 迷你, 统一下发) and quotations, which stay the film's to declare;
idioms that no film's text holds; a question of `filmkit.adoption` (design decision 4).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `formal-register`: a listed form inside a fixed idiom that the engine's style states is not refused; a film's
  declaration for such an idiom excuses no refusal.

## Impact

- `src/filmkit/register/styles/register/colloquial.yml` and its cases; the register tests that held 名副其实 refused
  (`tests/register/test_register_words.py`, `tests/register/test_register_check.py`, `tests/review/test_prepare.py`);
  the module's docstring, the README and the Changelog. `src/filmkit/register/standard.md` and `filmkit.adoption` are
  unchanged (design decisions 3 and 4).
- No film's output bytes change; a check that refused only for 其实 in 名副其实 passes once the film declares nothing
  for it.
