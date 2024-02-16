from __future__ import annotations

from typing import Literal, TypeAlias

KEY = str | tuple
NO_KEY = tuple()
REGISTER_TYPE = Literal["var"]

AST_ID: TypeAlias = str
NO_AST_ID: AST_ID = ""

SCOPE: TypeAlias = tuple
NO_SCOPE: SCOPE = tuple()


def is_ast_same_or_ancestor_of(ancestor: AST_ID, descendant: AST_ID):
    """Check whether ast is an ancestor of self"""
    return ancestor == descendant or descendant.startswith(ancestor)
