## 1. The rule

- [ ] 1.1 Add to the cases in `src/filmkit/register/styles/register/colloquial.yml` a case that holds 名副其实 alone,
      after a plain 其实 and before one, and wants 其实 reported outside the idiom only. Done when
      `tests/register/test_register_style.py` fails on that case with the token of `v0.29.0`.
- [ ] 1.2 Write the rule's 其实 token as `其实(?<!名副其实)`, with a comment beside it that names the idiom, the form
      it holds, why it is formal and the conditions under which an idiom joins (design decision 2). Done when
      `tests/register/test_register_style.py` passes.

## 2. The check's tests

- [ ] 2.1 In `tests/register/test_register_words.py`, move 这个示例名副其实 from the refused texts to the texts the check
      passes, with one more that parts the idiom by a zero-width space, and let the one-place count hold two plain
      其实. Done when the file passes, and fails with the rule of `v0.29.0`.
- [ ] 2.2 In `tests/register/test_register_check.py`, let the standard word that a film declares be 跑 within 跑道, and
      add a test that 名副其实 passes undeclared and that a declaration of 其实 within it is refused as one that
      excuses no refusal. Done when the file passes, and the new test fails with the rule of `v0.29.0`.
- [ ] 2.3 In `tests/review/test_prepare.py`, let the exception the round's report lists be 跑 within 跑道. Done when the
      file passes.

## 3. Documents

- [ ] 3.1 Say in the docstring of `filmkit.register`, the README's register paragraph and the Changelog under
      `[Unreleased]` that the rule states the idioms it does not refuse inside, and that a film's declaration of one
      is refused. Done when `npm run format:markdown:check` passes and `tests/register/` passes.

## 4. Acceptance

- [ ] 4.1 Run the check on the three films' December texts in throwaway copies, with and without their declarations of
      其实 within 名副其实. Done when, without them, no place is refused for 其实 in 名副其实 and every other refusal and
      warning equals the engine's at `v0.29.0`, and, with them, each is refused as one that excuses no refusal; the
      record stands in `build/evidence/keep-idioms-out-of-the-register-rule/acceptance/`.
