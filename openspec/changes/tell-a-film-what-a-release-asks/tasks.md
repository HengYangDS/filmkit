## 1. The engine's record

- [x] 1.1 Name the three packages the engine runs in a film under `dependencies` in `package.json` and regenerate the lock; the lock's entries keep their versions and integrity.
- [x] 1.2 Add `filmkit.released` and its record `released.json`, written by the repository's fix task; verify `tests/test_adoption.py`: a record that differs from the manifest and the locks is refused.
- [x] 1.3 Read the canvas's version and integrity in `picture/renderer.py` from the record, and name the engine's manifest in the README as the versions' one source, with no number restated; verify `tests/test_adoption.py`: with the record moved, the renderer's pin is the moved record's.

## 2. The declaration

- [x] 2.1 `filmkit.film` reports every problem of a declaration and refuses with all of them; verify `tests/test_film.py`: its new cases fail on the loader as released.

## 3. The command

- [x] 3.1 `filmkit.picture.template` owns the anchors and staging reads them from it; verify `tests/picture/test_rendering.py`: the sample film's staged documents keep their bytes.
- [x] 3.2 `filmkit.adoption` answers its five questions; verify `tests/test_adoption.py`: its cases fail on the engine as released.
- [x] 3.3 The README's commands and its section on installing the engine name the command, and the Changelog states it.

## 4. Verification

- [ ] 4.1 Run the command on the three films at their release tags and keep its output in `build/evidence/tell-a-film-what-a-release-asks/`: each gap the whole-edition trial met in tracked files is listed.
- [ ] 4.2 The repository's check passes, and the sample film builds and verifies.
