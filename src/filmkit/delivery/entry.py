"""The rule of a film's entry page, `content/index.html`, which leads to every edition's player.

The page's root states `lang="mul"`, BCP 47's tag for several languages, since it is no one
edition's; it holds, inside its `<nav>`, one link to each declared edition's player,
`<code>/index.html`, in the declared order, each carrying its edition's language tag as its
`lang`; and it holds no `<base>`, which would choose one language for every link. The film's
loader asks this rule of the declared page (`filmkit.film.read`), so a page that breaks it is
refused at load, beside the declaration's other problems, and packaging writes the page as it
stands. The module loads no declaration: it takes the declared codes and their tags.

A bridge, deleted in R6 (0.37.0), when the engine renders the entry page itself and a film no
longer tracks one.
"""

from __future__ import annotations

import re

# The root a page of several languages states.
ROOT_LANGUAGE = "mul"
# The page each edition's link leads to, below the folder of its code.
PAGE = "index.html"
_ROOT = re.compile(r"<html\b[^>]*>", re.I)
_LANG = re.compile(r"""\blang\s*=\s*["']([^"']*)["']""", re.I)
_LINK = re.compile(r"<a\b[^>]*>", re.I)
_HREF = re.compile(r"""\bhref\s*=\s*["']([^"']*)["']""", re.I)


def problems(page: str, editions: dict[str, str], name: str) -> list[str]:
    """Each fault of an entry page against its rule, by the page's `name`, for `editions`, each
    declared edition's code with its language tag in the declared order."""
    found = []
    root = _ROOT.search(page)
    declared = _LANG.search(root[0]) if root else None
    if declared is None or declared[1] != ROOT_LANGUAGE:
        stated = f'lang="{declared[1]}"' if declared else "no lang"
        found.append(f'{name} opens with {stated}; its root is <html lang="{ROOT_LANGUAGE}">')
    start = page.find("<nav")
    nav = page[start : page.find("</nav>", start)] if start >= 0 else ""
    links = []
    for tag in _LINK.findall(nav):
        href, lang = _HREF.search(tag), _LANG.search(tag)
        links.append((href[1] if href else "", lang[1] if lang else None))
    targets = [f"{code}/{PAGE}" for code in editions]
    linked = [href for href, _ in links if href in targets]
    found += [
        f"{name} links no {code}/{PAGE} in its <nav>"
        for code in editions
        if f"{code}/{PAGE}" not in linked
    ]
    found += [
        f"{name} links {target} {linked.count(target)} times in its <nav>; link each edition once"
        for target in targets
        if linked.count(target) > 1
    ]
    found += [
        f"{name} links {href}, which names no declared edition"
        for href, _ in links
        if href not in targets and re.fullmatch(rf"[^/]+/{re.escape(PAGE)}", href)
    ]
    # The order is that of each edition's first link, judged once every edition is linked.
    first = list(dict.fromkeys(linked))
    if sorted(first) == sorted(targets) and first != targets:
        found.append(f"{name} links the editions as {', '.join(first)}, not in the declared order")
    found += [
        f'{name} links {href} with {f"lang={lang!r}" if lang else "no lang"}, not lang="{tag}"'
        for href, lang in links
        for code, tag in editions.items()
        if href == f"{code}/{PAGE}" and lang != tag
    ]
    if re.search(r"<base\b", page, re.I):
        found.append(f"{name} holds a <base>, which would choose one language for every link")
    return found
