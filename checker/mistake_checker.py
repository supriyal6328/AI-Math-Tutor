"""
Enhanced mistake detection heuristics for algebra problems.

This module inspects both the original LaTeX/OCR expression and the
SymPy representation to detect common algebra mistakes such as:

- Distribution errors
- Sign mistakes
- Transposition errors
- Divide-by-zero risks
- OCR parsing issues
"""

import logging
from sympy import simplify, Eq, expand

logger = logging.getLogger(__name__)


def detect_mistakes(latex_str: str, sym_obj):
    """
    Detect common algebra mistakes.

    Parameters
    ----------
    latex_str : str
        The cleaned math string extracted from OCR.
    sym_obj : sympy expression or Eq
        Parsed symbolic object from SymPy.

    Returns
    -------
    list[str]
        List of possible mistakes detected.
    """

    mistakes = []

    try:

        # --------------------------------
        # Case 1: Equation (lhs = rhs)
        # --------------------------------
        if isinstance(sym_obj, Eq):

            L = sym_obj.lhs
            R = sym_obj.rhs

            # --------------------------------
            # Distribution check
            # --------------------------------
            try:
                if "(" in str(L):
                    if expand(L) != L:
                        mistakes.append(
                            "Possible distribution mistake on the left side."
                        )

                if "(" in str(R):
                    if expand(R) != R:
                        mistakes.append(
                            "Possible distribution mistake on the right side."
                        )
            except Exception:
                pass

            # --------------------------------
            # Sign / transposition check
            # --------------------------------
            try:
                combined = simplify(L - R)

                s = str(combined)

                if s.count("-") > s.count("+") + 2:
                    mistakes.append(
                        "Possible sign mistake during transposition."
                    )

            except Exception:
                pass

            # --------------------------------
            # Check divide by zero risk
            # --------------------------------
            try:
                if "/0" in latex_str:
                    mistakes.append(
                        "Division by zero detected in the equation."
                    )
            except Exception:
                pass


        # --------------------------------
        # Case 2: Expression only
        # --------------------------------
        else:

            try:
                simplified = simplify(sym_obj)

                if simplified is None:
                    mistakes.append(
                        "Expression simplification failed."
                    )

            except Exception:
                mistakes.append(
                    "Expression parsing may be incorrect. Check OCR result."
                )

    except Exception as e:
        logger.exception("Mistake detection failed: %s", e)

    return mistakes