"""Test languages derived from the engine's own declarations, under codes BCP 47 does not assign.

`xa` holds Chinese's declaration and `xb` English's, with only their codes, tags and names
replaced (ISO 639-2 `qaa` and `qab`, codes reserved for local use). A step that branches on a
real language's code, name or tag gives one of them the other's behaviour, so every test that
runs a step for both of them refuses such a branch.
"""

import tomllib

import filmkit.languages as languages

# Each test language: the declaration it is derived from, and its code, tags and names.
DERIVED = {
    "xa": ("zh", {"tag": "xa", "iso639_2": "qaa", "english_name": "Xa", "name": "Xa"}),
    "xb": ("en", {"tag": "xb", "iso639_2": "qab", "english_name": "Xb", "name": "Xb"}),
}


def declaration(source: str) -> dict:
    """The data of one of the engine's declarations, as its file states it."""
    return tomllib.loads((languages.FOLDER / f"{source}.toml").read_text(encoding="utf-8"))


def derived(code: str) -> languages.Language:
    """A test language: its source's declaration under its own code, tags and names."""
    source, replaced = DERIVED[code]
    return languages.parse(code, {**declaration(source), **replaced})
