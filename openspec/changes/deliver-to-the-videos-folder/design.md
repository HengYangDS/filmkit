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
   - **Applies to:** `python -m filmkit.delivery.folder`. `--destination DIR` is the folder itself. `FILMKIT_DELIVERY_ROOT` is joined with the declared name. The videos folder is `~/Movies` on macOS; elsewhere `XDG_VIDEOS_DIR` in the environment, else the `XDG_VIDEOS_DIR` line of `${XDG_CONFIG_HOME:-~/.config}/user-dirs.dirs` with `$HOME` read as the home folder, else `~/Videos`. The line is read as xdg-user-dirs writes it: the value in double quotes, where a backslash guards the next character, or in single quotes; `$HOME/...` or an absolute path; at most a comment after it; and the last such line counts, as for a shell that reads the file. The first form took whatever stood between the equals sign and the end of the line, so a relative value became a folder below the working directory and a line with a comment named a folder with the comment in its name (the review of `17cac49..4b50c34`, finding 6). A value that is no absolute path, in the file or in the environment, is not used, as the XDG base directory specification says of a relative path, and the rule the readback records then names what was passed over and that `~/Videos` applied. In single quotes `$HOME` is read as the home folder too, where a shell would take it as written: a line someone wrote by hand means the home folder either way. Not covered: Windows, where the engine does not build; the XDG file is read by its one line and not by `xdg-user-dir`, which a host may lack.
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
4. **A delivery refuses a destination that is not its own to empty.**
   - **Rests on:** the review of `17cac49..4b50c34`, finding 3. A delivery removes from its destination every entry that is no member, except `.DS_Store` and `/.claude/`, and moves it into the predecessors below the film's root; nothing compared the destination with that root. `--destination ""`, which an unset variable in a script gives, and `--destination .` at the root resolved to the working directory, and the delivery's own rsync options and filter, on a scratch tree, moved `.git`, `content` and `src` into the predecessors, which lie inside the tree being cleared and were nested into themselves until rsync stopped (the review's experiment 5). `--destination ~` would do the same to a home folder. Decision 1 added two more ways to name any folder and no refusal.
   - **Considered:** (a) the film's root and an empty name alone, the review's smallest change; (b) any existing folder that is not empty, which refuses every second delivery; (c) the film's root, what holds it and what lies inside it, on resolved paths, and an existing folder that holds entries without the entry page an earlier delivery left; (d) a marker of the delivery's own in the destination, a 26th entry that the readback would have to allow and that the films' existing folders lack.
   - **Chosen because:** (c). A delivery empties what it fills, so the question is whether the folder is the delivery's to empty: not the film's own tree in any relation to it, and not a folder that someone else filled. `index.html` is the first member of every delivery, so every folder a delivery filled holds it, and the films' existing folders pass without a migration. The rule of the root applies to all three routes because each can give the root: the caller names it; `FILMKIT_DELIVERY_ROOT` names the parent of a checkout whose folder has the name of the film's delivery folder, as the three films' checkouts below `~/projects` have; and a film that is checked out inside its own folder below the videos folder is given it by the platform's rule. The paths are compared resolved, so a symbolic link to the root and `build/..` are the root. An empty `--destination` is refused as it is given, before it becomes a path, since as a path it is the working directory.
   - **Applies to:** `filmkit.delivery.folder.deliver` and the command: first of all, before the sources are looked for, before the player check and before rsync, and in a dry run. The refusal names the folder, the rule that gave it and what was found. Not covered: a folder that holds an `index.html` of its own and was never a delivery's, the root of a website for one, is filled as a delivery folder is, and its other entries move into the predecessors, from where they can be put back.

## Risks / Trade-offs

- A film adopts the engine and keeps the old key or module. → Refused at load, naming the new key; the task fails naming the missing module. Neither delivers anywhere.
- A user expects the films in `~/Documents` after an upgrade. → The summary and the readback state the destination and the rule; an earlier folder is left as it was, and the Changelog says so.
- A Linux host's `user-dirs.dirs` uses a form this reader does not take. → The fallback is `~/Videos`, and the record names the rule that was used and quotes the line that was passed over.

## Migration Plan

Each film renames `documents_folder` to `delivery_folder` in `content/film.toml` and `filmkit.delivery.documents_folder` to `filmkit.delivery.folder` in its delivery task. A host whose films lie elsewhere than its videos folder sets `FILMKIT_DELIVERY_ROOT`, or its callers keep passing `--destination`. Folders that earlier deliveries filled are not touched.

## Open Questions

None.
