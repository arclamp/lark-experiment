# lark-experiment
A test project for the lark parsing library

It implements a small grammar for search strings: free-text search terms mixed
with *operators* that restrict the results, for example:

```
cats "big dogs" created_before:2026-11-04 author:"Jane Doe"
```

Parsing this gives a `SearchQuery` with two parts:

- `terms`: the plain search terms (`["cats", "big dogs"]`)
- `filters`: the operators and their converted values
  (`created_before` → `date(2026, 11, 4)`, `author` → `"Jane Doe"`)

## Layout

| File | What it is |
| --- | --- |
| `src/search_query/search.lark` | **The grammar.** Lark's EBNF-style rules (lowercase) and terminals/tokens (UPPERCASE). |
| `src/search_query/parser.py` | **The parser.** Builds the `Lark` parser from the grammar, uses a `Transformer` to turn the parse tree into `SearchQuery`/`Filter` objects, and holds the table of valid operators (`VALUE_CONVERTERS`). |
| `src/search_query/__main__.py` | **The driver.** A command-line entry point that prints the parse tree and the final result, or prints an error and exits with status 1. |
| `tests/test_parser.py` | pytest tests for the parser. |

### How a search string is processed

1. **Lexing and parsing** (`search.lark`). The input is split into tokens:
   - `OPERATOR`: an identifier immediately followed by a colon, such as `author:`
   - `WORD`: a run of characters with no whitespace or double quotes
   - `ESCAPED_STRING`: a double-quoted string

   The parser then builds a tree of `term` and `operator` nodes. This stage
   checks syntax only. For example, an operator with no value is an error.
2. **Transforming** (`SearchTransformer` in `parser.py`). The tree is walked
   from the bottom up. Each `term` becomes a string. Each `operator` is checked
   against `VALUE_CONVERTERS` and its value is converted, so dates become
   `datetime.date` objects. An unknown operator or a value that fails
   conversion raises `SearchSyntaxError`.

## Usage

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync                      # create .venv and install dependencies
uv run pytest                # run the tests
uv run python -m search_query 'cats created_before:2026-11-04 author:"Jane Doe"'
```

Put the whole search in single quotes so that your shell passes any double
quotes through to the program.

From Python:

```python
from search_query import parse, SearchSyntaxError

q = parse('cats author:"Jane Doe"')
q.terms    # ['cats']
q.filters  # [Filter(operator='author', value='Jane Doe')]
```

### Search syntax

- `word` or `"quoted phrase"`: a search term.
- `name:value` or `name:"quoted value"`: an operator. The current operators are
  `author`, `created_before` and `created_after`. The two date operators take
  ISO dates (`YYYY-MM-DD`).
- An unknown operator (e.g. `foo:bar`) is an error. To search for text that
  contains a colon, put it in double quotes: `"foo:bar"`.
- A colon that doesn't follow an identifier (e.g. `12:30`) is part of an
  ordinary term. URLs such as `http://...` look like an operator, so they must
  be quoted.
- Operator names are case-sensitive.

## Adding a new operator

Add an entry to `VALUE_CONVERTERS` in `src/search_query/parser.py`. The key is
the operator name and the value is a function that converts the raw string,
raising `ValueError` if the value is invalid:

```python
VALUE_CONVERTERS: dict[str, Callable[[str], Any]] = {
    "created_before": date.fromisoformat,
    "created_after": date.fromisoformat,
    "author": str,
    "max_size": int,  # new: max_size:1000
}
```

You don't need to change the grammar, because it already accepts any
`identifier:value` as an operator. If the converter raises `ValueError`, the
user sees a message like
`invalid value for max_size: 'big' (...)`.

Add a test for the new operator in `tests/test_parser.py`.

If an operator's value needs its own *syntax* (for example a range such as
`size:10..20`), you can either parse it in the converter function, or add a
dedicated rule and terminal to `search.lark` and a matching method to
`SearchTransformer`.
