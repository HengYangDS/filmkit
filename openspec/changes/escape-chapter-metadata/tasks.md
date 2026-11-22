## 1. The escape

- [x] 1.1 A test in `tests/captions/test_documents.py` that the chapter metadata escapes `=`, `;`, `#`, the
      backslash and a newline in the title, the author, the comment and a chapter title; it failed before the repair.
- [x] 1.2 `_metadata_value` escapes them, and `_chapter_metadata` writes the title, the author, the comment and each
      chapter title through it. Done when the tests in `tests/captions/test_documents.py` pass.
- [ ] 1.3 The Changelog's entry, after group 2 and the release's other Changes. It says that each English edition's
      `chapters.ffmeta` gains a backslash before its comment's semicolon and that its player page, which holds that
      file, changes with it; that the edition's film package is stale and is built again, with the records that
      follow; and that a value that ends in a backslash is refused.

## 2. What the review found

- [x] 2.1 A carriage return is escaped with the five marks. Done when the test of the escape in
      `tests/captions/test_documents.py` holds one in the title, the author, the comment and a chapter title; it
      failed before the repair.
- [x] 2.2 A value that ends in a backslash is refused before a document is written, and `assemble` and
      `refresh-captions` ask the refusal before they write. Done when the tests in `tests/captions/test_documents.py`,
      `tests/soundtrack/test_assembly.py` and `tests/captions/test_refresh.py` pass; each failed before the repair.
- [ ] 2.3 A test in `tests/captions/test_documents.py` reads the written metadata back with FFmpeg and compares each
      value, and is skipped by name where the host has no FFmpeg. Done when it passes on a host that has FFmpeg.
