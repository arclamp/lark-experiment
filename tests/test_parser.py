from datetime import date

import pytest

from search_query import Filter, SearchSyntaxError, parse


def test_plain_terms():
    q = parse("cats dogs")
    assert q.terms == ["cats", "dogs"]
    assert q.filters == []


def test_empty():
    q = parse("")
    assert q.terms == [] and q.filters == []


def test_operator_with_date():
    q = parse("cats created_before:2026-11-04")
    assert q.terms == ["cats"]
    assert q.filters == [Filter("created_before", date(2026, 11, 4))]


def test_mixed_order_and_quotes():
    q = parse('author:"Jane Doe" "big dogs" created_after:2020-01-01 fish')
    assert q.terms == ["big dogs", "fish"]
    assert q.filters == [
        Filter("author", "Jane Doe"),
        Filter("created_after", date(2020, 1, 1)),
    ]


def test_operator_keyword_without_colon_is_a_term():
    assert parse("author").terms == ["author"]


def test_unknown_operator_is_a_term():
    assert parse("foo:bar").terms == ["foo:bar"]


def test_bad_date():
    with pytest.raises(SearchSyntaxError, match="created_before"):
        parse("created_before:yesterday")


def test_operator_missing_value():
    with pytest.raises(SearchSyntaxError):
        parse("cats author:")
