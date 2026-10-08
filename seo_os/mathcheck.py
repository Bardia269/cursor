"""Vérification Python (SymPy) des exercices de valeurs/vecteurs propres d'un article.

Un LLM bon marché extrait les matrices et les résultats annoncés ; le calcul et la comparaison
sont faits ici, sans IA.
"""

from __future__ import annotations

from collections import Counter

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from .schemas import MathExercise

_TRANSFORMS = standard_transformations + (implicit_multiplication_application, convert_xor)
_LATEX_REPLACEMENTS = {
    "\\sqrt": "sqrt",
    "\\frac": "",
    "\\cdot": "*",
    "\\times": "*",
    "\\left": "",
    "\\right": "",
    "{": "(",
    "}": ")",
    "−": "-",
    ",": ".",
}


def parse_number(raw: str) -> sp.Expr:
    text = raw.strip().strip("$").replace(" ", "")
    if "\\frac" in text:  # \frac{a}{b} -> (a)/(b)
        text = text.replace("\\frac", "").replace("}{", ")/(")
    for src, dst in _LATEX_REPLACEMENTS.items():
        text = text.replace(src, dst)
    return sp.nsimplify(parse_expr(text, transformations=_TRANSFORMS))


def _equal(a: sp.Expr, b: sp.Expr) -> bool:
    return sp.simplify(a - b) == 0


def check_exercise(ex: MathExercise) -> dict:
    report: dict = {"label": ex.label, "ok": False, "errors": []}
    try:
        matrix = sp.Matrix([[parse_number(x) for x in row] for row in ex.matrix])
    except (sp.SympifyError, SyntaxError, TypeError, ValueError) as e:
        report["errors"].append(f"matrice illisible : {e}")
        return report
    if not matrix.is_square:
        report["errors"].append("matrice non carrée")
        return report

    expected = Counter({sp.nsimplify(k): v for k, v in matrix.eigenvals().items()})
    report["computed_eigenvalues"] = {str(k): v for k, v in expected.items()}

    if ex.eigenvalues:
        try:
            claimed = [parse_number(v) for v in ex.eigenvalues]
        except (sp.SympifyError, SyntaxError, TypeError, ValueError) as e:
            report["errors"].append(f"valeurs propres illisibles : {e}")
            claimed = []
        remaining = Counter(expected)
        for value in claimed:
            match = next((k for k in remaining if remaining[k] > 0 and _equal(k, value)), None)
            if match is None:
                report["errors"].append(f"valeur propre annoncée incorrecte : {value}")
            else:
                remaining[match] -= 1
        distinct_claimed = {str(v) for v in claimed}
        if claimed and len(distinct_claimed) < len(expected):
            report["errors"].append("valeurs propres manquantes")

    for pair in ex.eigenpairs:
        try:
            value = parse_number(pair.eigenvalue)
            vector = sp.Matrix([parse_number(x) for x in pair.vector])
        except (sp.SympifyError, SyntaxError, TypeError, ValueError) as e:
            report["errors"].append(f"vecteur propre illisible : {e}")
            continue
        if vector.shape[0] != matrix.shape[0] or all(_equal(x, 0) for x in vector):
            report["errors"].append(f"vecteur invalide pour λ={value}")
            continue
        residual = sp.simplify(matrix * vector - value * vector)
        if any(not _equal(x, 0) for x in residual):
            report["errors"].append(f"A·v ≠ λ·v pour λ={value}, v={list(vector)}")

    report["ok"] = not report["errors"]
    return report


def check_exercises(exercises: list[MathExercise]) -> dict:
    results = [check_exercise(ex) for ex in exercises]
    return {
        "exercises_checked": len(results),
        "exercises_ok": sum(r["ok"] for r in results),
        "details": results,
    }
