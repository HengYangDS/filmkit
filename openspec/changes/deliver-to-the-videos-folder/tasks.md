## 1. The destination

- [x] 1.1 Resolve the delivery's destination from `--destination`, else `FILMKIT_DELIVERY_ROOT` joined with the film's declared folder, else the platform's videos folder joined with it (`~/Movies` on macOS; the XDG videos directory elsewhere), and name no folder of a host in the engine; verify `tests/delivery/test_destination.py` (the three rules in their order, the macOS and the XDG forms, every delivery below the test's own folder).
- [x] 1.2 State the destination and the rule that gave it in the readback, in a dry run's report and in the command's summary; verify `tests/delivery/test_destination.py` and `tests/delivery/test_folder.py`.
- [x] 1.3 Refuse, before the sources are looked for, the players read or rsync run, and in a dry run too, an empty `--destination`, a destination that on resolved paths is the film's root, holds it or lies inside it, by whichever of the three rules, and one that is no folder or holds entries and no `index.html` of an earlier delivery, naming the folder, the rule and what was found; verify `tests/delivery/test_refused_destinations.py` (films and folders below the test's own folder; the whole tree unchanged after each refusal; a folder with the preserved entries alone and one an earlier delivery filled are delivered to).
- [x] 1.4 Read the videos line of `user-dirs.dirs` as xdg-user-dirs writes it, the last such line, and use no value that is not an absolute path, from the file or from the environment, saying in the rule what was passed over; verify `tests/delivery/test_destination.py` (eleven lines that name a folder, eleven that name none, and a relative `XDG_VIDEOS_DIR` and `XDG_CONFIG_HOME` in the environment).

## 2. The names

- [x] 2.1 Declare the delivery folder as `delivery_folder` and refuse `documents_folder` with a message that names the new key; verify `tests/test_film.py`.
- [x] 2.2 Rename the module to `filmkit.delivery.folder`, with no alias, and say "delivery folder" in its texts, the README, the sample film's declaration and the Changelog; verify that no source, test fixture name or document of the engine names the old module or key except the refusal and the Changelog, and the repository's Markdown check.

## 3. Acceptance

- [ ] 3.1 Run every command of `mise run check` on the lane's head; verify that the dependency checks, the Node suite, the Markdown check, the Python suite and the lint pass.
