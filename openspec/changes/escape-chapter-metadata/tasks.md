## 1. The escape

- [ ] 1.1 A test in `tests/captions/test_documents.py` that the chapter metadata escapes `=`, `;`, `#`, the
      backslash and a newline in the title, the author, the comment and a chapter title; it failed before the repair.
- [ ] 1.2 `_metadata_value` escapes them, and `_chapter_metadata` writes the title, the author, the comment and each
      chapter title through it; the documents tests pass.
- [ ] 1.3 The Changelog's entry, after the release's other Changes.
