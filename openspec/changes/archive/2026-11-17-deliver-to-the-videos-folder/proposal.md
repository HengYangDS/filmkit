## Why

The engine's delivery command fills a folder in `~/Documents` unless the caller names another: `filmkit.delivery.documents_folder` holds `Path.home() / "Documents"` and the declaration key is `documents_folder`. On 17 November 2026 the owner asked why the engine hard-codes that path, and why films on this host do not go below `~/Movies`. A delivery is several gigabytes of rebuildable films; `~/Documents` is the user's place for documents and, on the host that builds the films, a cloud-synced folder. The films' own folders left it that day, and only the films' kit, which passes `--destination`, knew.

## What Changes

- **The engine names no folder of a host.** A delivery's destination is, in this order: the folder `--destination` names; the film's declared folder name below the root that `FILMKIT_DELIVERY_ROOT` names, a host's setting; that name below the user's videos folder as the platform defines it, `~/Movies` on macOS and the XDG videos directory elsewhere.
- **The delivery records where it went and why**: the readback and the command's summary state the destination and the rule that gave it.
- **BREAKING: the declaration key `documents_folder` becomes `delivery_folder`.** A declaration that still holds the old key is refused with the new key's name; no second spelling is read.
- **BREAKING: the module `filmkit.delivery.documents_folder` becomes `filmkit.delivery.folder`**, with no alias. A film's task list names the new module.
- **BREAKING: a delivery without `--destination` and without `FILMKIT_DELIVERY_ROOT` no longer goes to `~/Documents/<folder>`** but to the user's videos folder.

Out of scope: moving a folder an earlier delivery filled, which stays where it is until its owner moves or removes it; the preview copies a review round reads, whose folder the caller names.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `film-package`: where a delivery goes, and what its record says of that.
- `film-engine`: the declaration names the delivery folder by `delivery_folder`, and the key it replaces is refused.

## Impact

- `src/filmkit/delivery/folder.py` (renamed from `documents_folder.py`), `src/filmkit/film.py`, the sample film's declaration, their tests, the README and the Changelog.
- Each adopting film renames one key in `content/film.toml` and one module in its delivery task; a host that wants its films elsewhere than the videos folder sets `FILMKIT_DELIVERY_ROOT` or keeps passing `--destination`.
