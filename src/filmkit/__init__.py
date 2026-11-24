"""Rebuild narrated explainer films, one edition for each language a film declares, from their
declaration, scripts and composition.

When `FILMKIT_OPENS` names a file, every engine process records what each node's run opens there
(`filmkit.graph.opens`); otherwise nothing is installed."""

import os

if os.environ.get("FILMKIT_OPENS"):
    from filmkit.graph import opens

    opens.install()
