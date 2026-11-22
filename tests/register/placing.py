"""Helpers of the register tests: the forms the standard lists, texts stood in as a film's
places, and the check's refusal."""

import re
from pathlib import Path

import pytest

import filmkit.concepts as concepts
import filmkit.register as register
from filmkit.register import RegisterError

STANDARD = Path(register.__file__).with_name("standard.md")


def listed() -> tuple[list[str], list[str]]:
    """The Chinese and the English forms that R1 and R3 of the standard list, from its text."""
    text = STANDARD.read_text(encoding="utf-8")
    rules = dict(re.findall(r"^- \*\*(R\d)\. .+?\*\* (.+?)(?=^- \*\*R|\Z)", text, re.M | re.S))
    r1, r3 = (" ".join(rules[name].split()) for name in ("R1", "R3"))
    chinese = re.search(r"No ([^;]+);", r1)[1].split("、")
    r3_chinese = re.sub(r" \([^)]*\)", "", re.search(r"Chinese: ([^;]+);", r3)[1])
    chinese += re.split(r"[、/]", r3_chinese)
    english = re.findall(r'"(\w+)"', r1)
    english += [quoted for quoted in re.findall(r'"([^"]+)"', r3) if "'" in quoted]
    return [form.strip() for form in chinese], list(dict.fromkeys(english))


def placed(monkeypatch, *texts: str) -> None:
    """Stand these texts in as the film's places, the Chinese thoughts 01.1, 01.2 and on."""
    held = [concepts.Place(f"zh 01.{index}", text) for index, text in enumerate(texts, 1)]
    monkeypatch.setattr(concepts, "places", lambda: {"zh": held})


def refused() -> RegisterError:
    """The check's refusal, which must come."""
    with pytest.raises(RegisterError) as refusal:
        register.check()
    return refusal.value


# What a refusal says once, after its lines, when a listed form of R1 or R3 is among them.
KEEP = (
    "A film keeps a standard word or a quotation at its place by declaring it in "
    "[[register.exceptions]]: its place, its form, the text the form stands within there "
    "(within) and a reason"
)


def refused_lines() -> list[str]:
    """The lines a caller counts in the check's refusal, one refusal a line."""
    return list(refused().lines)
