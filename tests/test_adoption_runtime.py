"""What a film states of the runtime and the credits that this release removes or moves: a
withdrawn key of a script or a cast, which the loader refuses and the adoption command's
`declaration` question names, and a line of the review prompt that ties the runtime to no one
edition, which its `runtime` question names, read as text."""

import json

import test_adoption as base

import filmkit.film as film
import filmkit.withdrawn as withdrawn

# A film that holds what the release asks, its findings, and the rewriting of one of its files.
project, found, rewrite = base.project, base.found, base.rewrite


def declare(path, **fields) -> None:
    """Add fields to a JSON file of the film."""
    path.write_text(json.dumps({**json.loads(path.read_text()), **fields}, ensure_ascii=False))


def test_a_film_that_declares_its_credits_once_and_no_runtime_has_no_finding(project):
    assert found(project)["runtime"] == []


def test_a_declaration_without_the_credits_is_one_finding_of_the_declaration_question(project):
    rewrite(project / film.DECLARATION, "credits_duration = 3\n", "")
    findings = found(project)
    named = [text for texts in findings.values() for text in texts if "credits_duration" in text]
    assert named == [
        "content/film.toml declares no credits_duration; declare the credits' length there once, "
        "in whole seconds"
    ]
    assert findings["runtime"] == []


def test_each_withdrawn_runtime_key_is_named_by_the_declaration_question_alone(project):
    declare(project / "content/zh/film-script.json", duration=1500, credits_duration=3)
    declare(project / "content/en/film-script.json", duration=1500)
    declare(project / "content/en/voice-reference.json", runtime_fit={"reserve_seconds": 0.5})
    # The loader reads the files whatever else the declaration holds: one that does not load is
    # no obstacle, and its problem stands beside them.
    rewrite(project / film.DECLARATION, 'slug = "sample-reel"', 'slug = "Two Words"')
    script, cast = withdrawn.keys("script"), withdrawn.keys("cast")
    findings = found(project)
    assert findings["declaration"][:4] == [
        f"content/zh/film-script.json declares duration; {script['duration']}",
        f"content/zh/film-script.json declares credits_duration; {script['credits_duration']}",
        f"content/en/film-script.json declares duration; {script['duration']}",
        f"content/en/voice-reference.json declares runtime_fit; {cast['runtime_fit']}",
    ]
    assert "\nslug\n" in findings["declaration"][4]
    assert findings["runtime"] == []
    assert script["duration"] == (
        "remove it: an edition lasts as long as its narration, which the assembly counts"
    )


# How the question names a line of the review prompt that cites the runtime for no one edition.
UNTIED = (
    'content/review/prompt.md:{line} cites {{duration}} in a line that does not say "This '
    "edition\"; {{duration}} is the runtime of the prompt's own edition, and the editions may "
    'differ in length: reword the line, as "This edition: exactly {{duration}} s"'
)


def test_a_review_prompt_that_states_one_runtime_for_both_editions_is_named(project):
    # The three films' prompts say "Each edition: exactly {duration} s", which each prompt now
    # fills with its own edition's runtime.
    prompt = project / "content/review/prompt.md"
    rewrite(prompt, "This edition: exactly {duration} s", "Each edition: exactly {duration} s")
    findings = found(project)
    assert findings["runtime"] == [UNTIED.format(line=9)]
    assert "{duration}" not in " ".join(findings["declaration"])
    # The reading fails closed: a line that cites the runtime and does not tie it to this
    # edition is named whatever it says, also with a format; an escaped brace cites nothing.
    rewrite(prompt, "Each edition: exactly {duration} s", "This edition: exactly {duration} s")
    prompt.write_text(
        prompt.read_text()
        + "The films last {duration:.0f} s.\nThis Edition lasts {duration} s.\n{{duration}}\n"
    )
    lines = len(prompt.read_text().splitlines())
    assert found(project)["runtime"] == [UNTIED.format(line=lines - 2)]
