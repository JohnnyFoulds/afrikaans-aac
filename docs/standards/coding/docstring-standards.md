# Docstring Standard

## Purpose

This document defines the docstring format and content requirements for all Python code across AIBooster+ GenAI repositories. Code that does not meet these requirements may be rejected during code review.

---

## Basic Conventions

All docstrings must follow [PEP 257](https://peps.python.org/pep-0257/) as a baseline.

### Rules

- Docstrings are **mandatory** for all modules, classes, functions, and methods — both public and non-public.
- One-line docstrings are only acceptable when a function, method, class, or module has **no parameters and no return value**. Everything else requires a multi-line docstring.
- The closing `"""` of a multi-line docstring must be on its own line.

---

## Docstring Format

All docstrings must use **reStructuredText / Sphinx-style** field lists. Do not use Google-style (`Args:`, `Returns:`) or NumPy-style (`Parameters\n----------`) formats.

### Fields

| Field | Usage |
| --- | --- |
| `:param <name>: <description>` | One entry per parameter |
| `:type <name>: <type>` | Optional — omit if a type hint is present |
| `:returns: <description>` | Describe the return value |
| `:rtype: <type>` | Optional — omit if a type hint is present |
| `:raises <ExceptionType>: <condition>` | One entry per exception that callers should handle |

### Example

```python
def get_session(self, session_id: str) -> Session:
    """
    Retrieve an active session by ID.

    :param session_id: The unique session identifier.
    :returns:          The Session object for the given ID.
    :raises SessionNotFoundError: If no session with the given ID exists.
    :raises SessionClosedError:   If the session has been terminated.
    """
```

### Tool Functions

Public entry points intended for external use must include an `example::` block demonstrating typical usage. The example must be minimal, complete, and valid Python:

```python
def load_documents(
    path: str,
    recursive: bool = False,
) -> list[Document]:
    """
    Load documents from the given directory path.

    example::

        from my_project.loaders import load_documents

        docs = load_documents("/data/reports", recursive=True)
        print(len(docs))

    :param path:       Path to the directory containing documents.
    :param recursive:  When ``True``, search subdirectories recursively.
    :returns:          A list of loaded ``Document`` objects.
    :raises ValueError: If ``path`` does not exist or is not a directory.
    """
```

---

## References

- [PEP 257 — Docstring Conventions](https://peps.python.org/pep-0257/)
- [PEP 287 — reStructuredText Docstring Format](https://peps.python.org/pep-0287/)
- [Sphinx — Writing docstrings](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html)
- [How to Write Docstrings in Python: reStructuredText](https://realpython.com/how-to-write-docstrings-in-python/#restructuredtext-docstrings)
- [Documenting Python Code: A Complete Guide](https://realpython.com/documenting-python-code/)
- [Napoleon — Marching toward legible docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/#id1)
