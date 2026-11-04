"""Parse search strings into free-text terms plus structured filters."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from importlib.resources import files
from typing import Any, Callable

from lark import Lark, Token, Transformer, v_args
from lark.exceptions import UnexpectedInput, VisitError


@dataclass(frozen=True)
class Filter:
    operator: str
    value: Any


@dataclass
class SearchQuery:
    terms: list[str] = field(default_factory=list)
    filters: list[Filter] = field(default_factory=list)


class SearchSyntaxError(ValueError):
    """Raised for input that doesn't parse, or has an invalid operator value."""


# How to interpret each operator's raw string value. Adding an operator means
# adding it to OPERATOR in search.lark *and* here.
VALUE_CONVERTERS: dict[str, Callable[[str], Any]] = {
    "created_before": date.fromisoformat,
    "created_after": date.fromisoformat,
    "author": str,
}


def _unquote(tok: Token) -> str:
    if tok.type == "ESCAPED_STRING":
        return json.loads(tok)  # handles \" and other escapes
    return str(tok)


class SearchTransformer(Transformer):
    """Turn the parse tree into a SearchQuery.

    Each method is named after a grammar rule and receives that rule's
    children (already transformed, bottom-up).
    """

    @v_args(inline=True)
    def term(self, tok: Token) -> str:
        return _unquote(tok)

    @v_args(inline=True)
    def operator(self, op: Token, value: Token) -> Filter:
        name = op[:-1]  # strip trailing colon
        raw = _unquote(value)
        try:
            converted = VALUE_CONVERTERS[name](raw)
        except ValueError as e:
            raise SearchSyntaxError(f"invalid value for {name}: {raw!r} ({e})") from e
        return Filter(name, converted)

    def start(self, clauses: list[str | Filter]) -> SearchQuery:
        query = SearchQuery()
        for c in clauses:
            if isinstance(c, Filter):
                query.filters.append(c)
            else:
                query.terms.append(c)
        return query


_parser = Lark(
    files(__package__).joinpath("search.lark").read_text(),
    parser="lalr",  # fast, and rejects ambiguous grammars at build time
)


def parse_tree(text: str):
    """Return the raw lark parse tree (handy for learning/debugging)."""
    return _parser.parse(text)


def parse(text: str) -> SearchQuery:
    try:
        return SearchTransformer().transform(_parser.parse(text))
    except UnexpectedInput as e:
        raise SearchSyntaxError(str(e)) from e
    except VisitError as e:  # exceptions inside the transformer get wrapped
        raise e.orig_exc from e
