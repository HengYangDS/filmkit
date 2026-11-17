## Context

`filmkit.delivery.documents_folder` delivers both editions with rsync and reads them back. Its default destination was a constant built at import: the user's home, `Documents`, and the name the film declares as `documents_folder`. The proposal states the owner's question and the scope.

## Goals / Non-Goals

**Goals:**

- No path of a host stands in the engine or in a film's portable declaration.
- A delivery without any setting lands where a user keeps videos, and its record says where and by which rule.

**Non-Goals:**

- Moving or removing what earlier deliveries left in `~/Documents`.
- A destination for anything but the delivery: review previews and work folders are unchanged.

## Decisions

1. **The destination is resolved from the caller, the host and the platform, in that order.**
   - **Rests on:** the owner's two questions of 17 November 2026: whether the engine's default delivery path still says `~/Documents`, and why a path is hard-coded at all when, on this host, films belong below `~/Movies`. It did: `DESTINATION = Path.home() / "Documents" / FILM.documents_folder`. The films' folders had left `~/Documents` that day, rebuildable output of several gigabytes having no place in a cloud-synced folder; only the films' kit knew, by passing `--destination`, so a bare call of the engine's command would have made a folder in `~/Documents` again.
   - **Considered:** (a) `~/Documents` kept as the default beside the option, which is what stood: the wrong place for build output, and synced on the host that builds; (b) no default, a refusal unless the caller names a destination, which is safe and makes every film's task and every reader of the README carry a host's path somewhere; (c) a path in each film's declaration, which puts a host's fact into a portable repository; (d) the caller's folder, else a host's root joined with the film's declared name, else the platform's own videos folder joined with it.
   - **Chosen because:** (d). Each fact has one owner: the film declares its folder's name, the host may name the root below which its films lie, and the platform says where a user keeps videos. Films are videos; that folder is to them what `~/Documents` is to documents, and it is in no cloud-synced set by default. A command run with no setting still does something a user expects, and can be told otherwise in one place for a whole host.
   - **Applies to:** `python -m filmkit.delivery.folder`. `--destination DIR` is the folder itself. `FILMKIT_DELIVERY_ROOT` is joined with the declared name. The videos folder is `~/Movies` on macOS; elsewhere `XDG_VIDEOS_DIR` in the environment, else the `XDG_VIDEOS_DIR` line of `${XDG_CONFIG_HOME:-~/.config}/user-dirs.dirs` with `$HOME` read as the home folder, else `~/Videos`. Not covered: Windows, where the engine does not build; the XDG file is read by its one line and not by `xdg-user-dir`, which a host may lack.
2. **The delivery's record states the destination and the rule that gave it.**
   - **Rests on:** the same day's finding that a default nobody had read decided where gigabytes went. The readback already stated the destination.
   - **Considered:** the destination alone; the destination and the rule, in the readback and in the summary the command prints.
   - **Chosen because:** a reader of the record, or of a build's log, sees without the source why the films are where they are: `--destination`, `FILMKIT_DELIVERY_ROOT`, or the platform's rule by its name.
   - **Applies to:** `build/evidence/delivery/delivery-readback.json` (`destination`, `destination_rule`), a dry run's report and the command's printed summary. The binding the player check reads is unchanged.
3. **The key and the module are renamed, and the old key is refused.**
   - **Rests on:** the names said what the default was: the key `documents_folder`, the module `filmkit.delivery.documents_folder`, and "the film's Documents folder" in the texts. The module's callers are the three films' delivery tasks and the engine's own tests; adoption edits each film's declaration for the key in any case.
   - **Considered:** the key renamed and the module kept, which leaves `documents_folder` in every film's task list and in the usage line; both renamed with the old names still read, a second spelling to keep in step for ever; both renamed, the old key refused with the new one's name, and no alias for the module.
   - **Chosen because:** one name for one thing. A declaration with the old key is refused when it loads, before any work, by a message that names `delivery_folder`; a task that names the old module fails at once with Python's own message, which names the module it could not find.
   - **Applies to:** `content/film.toml` (`delivery_folder`), `python -m filmkit.delivery.folder`, the README and the sample film. The standing requirement of the declaration already says "delivery folder"; a requirement beside it names the key and the refusal.

## Risks / Trade-offs

- A film adopts the engine and keeps the old key or module. → Refused at load, naming the new key; the task fails naming the missing module. Neither delivers anywhere.
- A user expects the films in `~/Documents` after an upgrade. → The summary and the readback state the destination and the rule; an earlier folder is left as it was, and the Changelog says so.
- A Linux host's `user-dirs.dirs` uses a form this reader does not take. → The fallback is `~/Videos`, and the record names the rule that was used.

## Migration Plan

Each film renames `documents_folder` to `delivery_folder` in `content/film.toml` and `filmkit.delivery.documents_folder` to `filmkit.delivery.folder` in its delivery task. A host whose films lie elsewhere than its videos folder sets `FILMKIT_DELIVERY_ROOT`, or its callers keep passing `--destination`. Folders that earlier deliveries filled are not touched.

## Open Questions

None.
