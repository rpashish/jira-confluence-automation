# Validation rules — Markdown walkthroughs

Apply these checks to each `walkthrough.md`. A file fails a check when the condition is not met. Report the check id, the file path, and the failing line or the missing heading.

1. **VR-1 Title.** The first non-empty line is a level-1 heading (`# ...`). The file has exactly one level-1 heading.
2. **VR-2 Summary.** The file contains a level-2 heading whose text is `Summary`. At least one non-empty paragraph follows that heading before the next heading.
3. **VR-3 Quiz.** The file contains a level-2 heading whose text is `Quiz`. At least one numbered or bulleted question follows that heading before the next heading.
4. **VR-4 Order.** The `Summary` heading appears before the `Quiz` heading. Both appear after the level-1 title.
5. **VR-5 No empty sections.** Every heading is followed by at least one non-empty line of content before the next heading or the end of the file.
6. **VR-6 No placeholders.** The file does not contain `TODO`, `TBD`, `FIXME`, or `lorem ipsum` (any case).
