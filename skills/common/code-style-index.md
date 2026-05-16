# Code Style — Section Index

> `code-style.md` is 48KB. Agents should load only the sections relevant to the current task.
> Use this index to determine which sections to reference.

---

## Quick Reference — Load by Task

| Task | Load sections |
|------|---------------|
| Writing any Python | §1 Toolchain, §2 Code Layout (first 50 lines) |
| Organizing imports | §3 Imports |
| Writing docstrings | §9 Docstrings |
| Naming things | §10 Naming Conventions |
| Adding type hints | §11 Type Annotations |
| Code review | §12 Programming Recommendations, §13 Anti-Patterns |
| Setting up tooling | §15 Toolchain Configuration |
| Version compatibility | §14 Version Compatibility Matrix |

---

## Section Map (line offsets in code-style.md)

| Section | Lines | Size | Content |
|---------|-------|------|---------|
| Prime Directive | 10–24 | ~15 lines | Priority rules for when to deviate |
| §1 Toolchain | 25–38 | ~14 lines | Ruff, mypy, pytest, pre-commit |
| §2 Code Layout | 39–209 | ~170 lines | Indentation, line length, blank lines, multiline |
| §3 Imports | 210–304 | ~95 lines | Import ordering, grouping, absolute vs relative |
| §4 Module Dunders | 305–323 | ~19 lines | `__all__`, `__version__` placement |
| §5 String Quotes | 324–345 | ~22 lines | Double quotes for strings |
| §6 Whitespace | 346–451 | ~106 lines | Spacing rules around operators, brackets |
| §7 Trailing Commas | 452–484 | ~33 lines | When to use trailing commas |
| §8 Comments | 485–550 | ~66 lines | Inline, block, TODO format |
| §9 Docstrings | 551–682 | ~132 lines | PEP 257, Google style, examples |
| §10 Naming | 683–832 | ~150 lines | Variables, classes, constants, private |
| §11 Type Annotations | 833–964 | ~132 lines | PEP 484, generics, Optional, Union |
| §12 Programming Recs | 965–1479 | ~515 lines | Best practices, idioms, pure functions |
| §13 Anti-Patterns | 1480–1639 | ~160 lines | Common production bugs |
| §14 Version Matrix | 1640–1663 | ~24 lines | Python 3.8–3.13 feature availability |
| §15 Toolchain Config | 1664–1763 | ~100 lines | pyproject.toml for ruff, mypy |
| Appendix | 1764–end | ~40 lines | Violations quick reference |

---

## Usage

Agents should load the full `code-style.md` only when performing a comprehensive code review.
For targeted tasks, read specific line ranges:

```
# Example: load only the imports section
Read skills/common/code-style.md lines 210-304
```
