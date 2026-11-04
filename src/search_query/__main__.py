"""Usage: python -m search_query 'cats created_before:2026-11-04 author:"Jane Doe"'"""

import sys

from .parser import SearchSyntaxError, parse, parse_tree


def main() -> int:
    text = " ".join(sys.argv[1:])
    try:
        tree = parse_tree(text)
        print("--- parse tree ---")
        print(tree.pretty())
        print("--- result ---")
        print(parse(text))
    except SearchSyntaxError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


sys.exit(main())
