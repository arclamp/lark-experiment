"""Usage: python -m search_query 'cats created_before:2026-11-04 author:"Jane Doe"'"""

import sys

from .parser import parse, parse_tree

text = " ".join(sys.argv[1:])
print("--- parse tree ---")
print(parse_tree(text).pretty())
print("--- result ---")
print(parse(text))
