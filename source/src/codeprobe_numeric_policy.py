"""Exact, context-independent numerical comparison for bounded source review.

The lexical route admits finite str/int/Decimal values and uses integer ratios.
The binary64 route supplies conservative sufficient conditions over closed
half-ULP enclosures. An indeterminate comparison is never an admitted pass.

An optional, explicitly supplied work budget can refuse an evaluation before
large integer expansion. It changes execution availability, not the mathematical
comparison. With no budget the original finite lexical domain is retained;
callers handling untrusted magnitudes should also impose process resource limits.
Historical result files are not reinterpreted by this implementation.
"""
from __future__ import annotations

import math
from decimal import Decimal, InvalidOperation, localcontext
from fractions import Fraction
from typing import Any

POLICY_ID = "codeprobe-numeric-comparison/2.0.0-a2p7a"
EQUALITY_RULE = "delta <= tolerance"
NumericInput = str | int | Decimal


class NumericResourceError(RuntimeError):
    """Evaluation was not completed; no comparison verdict is available."""
    status = "RESOURCE_REFUSED"


def _budget(value: int | None) -> int | None:
    if value is not None and (type(value) is not int or value < 1):
        raise ValueError("max_work_digits must be a positive integer or None")
    return value


def _capacity(digits: int, budget: int | None) -> None:
    if budget is not None and digits > budget:
        raise NumericResourceError("explicit decimal-work budget would be exceeded")


def _pow10(exponent: int) -> int:
    return 10 ** exponent


def _rational(value: NumericInput, budget: int | None) -> Fraction:
    if isinstance(value, (bool, float)) or not isinstance(value, (str, int, Decimal)):
        raise TypeError("canonical decimal comparison requires str, int or Decimal; binary float is not admitted")
    # Parsing is exact. A private context makes invalid-text refusal independent
    # of the caller's InvalidOperation trap and leaves its flags untouched.
    with localcontext() as context:
        context.traps[InvalidOperation] = True
        try:
            parsed = value if isinstance(value, Decimal) else Decimal(value)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("invalid decimal lexical value") from exc
    if not parsed.is_finite():
        raise ValueError("comparison values and tolerances must be finite")
    sign, digits, exponent = parsed.as_tuple()
    if not any(digits):
        return Fraction(0)
    _capacity(len(digits) + abs(exponent), budget)
    coefficient = 0
    for digit in digits:
        coefficient = coefficient * 10 + digit
    if sign:
        coefficient = -coefficient
    if exponent >= 0:
        return Fraction(coefficient * _pow10(exponent))
    return Fraction(coefficient, _pow10(-exponent))


def _work_capacity(values: tuple[Fraction, ...], budget: int | None) -> None:
    # Deliberately conservative upper estimate, not a claim about actual RAM.
    # A sum of bit lengths bounds product denominators/numerators used here;
    # using this sum as decimal-work units refuses earlier than necessary.
    estimate = 16 + sum(abs(v.numerator).bit_length() + v.denominator.bit_length() for v in values)
    _capacity(estimate, budget)


def _text(value: Fraction) -> str:
    """Serialise a terminating rational exactly, independent of Decimal context.

    Decimal(int).as_tuple() avoids Python's decimal int-to-str safety limit.
    The result preserves value; it need not preserve lexical spelling or -0.
    """
    if not value:
        return "0"
    denominator = value.denominator
    twos = (denominator & -denominator).bit_length() - 1
    denominator >>= twos
    fives = 0
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        raise ValueError("internal result has a non-terminating decimal expansion")
    places = max(twos, fives)
    coefficient = abs(value.numerator) * 2 ** (places - twos) * 5 ** (places - fives)
    digits = ''.join(chr(48 + d) for d in Decimal(coefficient).as_tuple().digits)
    if places:
        digits = digits.zfill(places + 1)
        text = (digits[:-places] + '.' + digits[-places:]).rstrip('0').rstrip('.')
    else:
        text = digits
    return ('-' if value < 0 else '') + text


def compare_decimal(left: NumericInput, right: NumericInput, *,
                    absolute_tolerance: NumericInput, relative_tolerance: NumericInput,
                    max_work_digits: int | None = None) -> dict[str, Any]:
    """Compare exact finite quantities, admitting equality at the tolerance.

    NumericResourceError means no verdict. The optional work budget is neither
    an input-validity judgement nor an automatic change to the admitted domain.
    """
    budget = _budget(max_work_digits)
    try:
        a, b, at, rt = (_rational(v, budget) for v in
                        (left, right, absolute_tolerance, relative_tolerance))
        if at < 0 or rt < 0:
            raise ValueError("tolerances must be non-negative")
        _work_capacity((a, b, at, rt), budget)
        delta = abs(a - b)
        tolerance = max(at, rt * max(abs(a), abs(b)))
        status = "within_tolerance" if delta <= tolerance else "outside_tolerance"
        return {
            "policy_id": POLICY_ID, "representation": "decimal_lexical", "status": status,
            "left": _text(a), "right": _text(b), "delta": _text(delta),
            "tolerance": _text(tolerance), "absolute_tolerance": _text(at),
            "relative_tolerance": _text(rt), "equality_rule": EQUALITY_RULE,
        }
    except (MemoryError, OverflowError) as exc:
        raise NumericResourceError("runtime allocation or representability limit; comparison not completed") from exc


def compare_binary64(left: float, right: float, *,
                     absolute_tolerance: NumericInput, relative_tolerance: NumericInput,
                     max_work_digits: int | None = None) -> dict[str, Any]:
    """Sound sufficient conditions over conservative symmetric half-ULP sets.

    Marginal interval overlap may remain indeterminate even when a more precise
    dependency-aware method would decide. The closed sets over-approximate the
    rounding preimage at binade transitions and are not an exact tie policy.
    """
    budget = _budget(max_work_digits)
    if type(left) is not float or type(right) is not float:
        raise TypeError("binary64 mode requires Python float operands")
    if not math.isfinite(left) or not math.isfinite(right):
        raise ValueError("binary64 operands must be finite")
    try:
        at, rt = (_rational(v, budget) for v in (absolute_tolerance, relative_tolerance))
        if at < 0 or rt < 0:
            raise ValueError("tolerances must be non-negative")
        a, b = Fraction(*left.as_integer_ratio()), Fraction(*right.as_integer_ratio())
        ua, ub = Fraction(*math.ulp(left).as_integer_ratio()) / 2, Fraction(*math.ulp(right).as_integer_ratio()) / 2
        _work_capacity((a, b, ua, ub, at, rt), budget)
        delta, uncertainty = abs(a - b), ua + ub
        low, high = max(Fraction(0), delta - uncertainty), delta + uncertainty
        magnitude, mu = max(abs(a), abs(b)), max(ua, ub)
        tlo = max(at, rt * max(Fraction(0), magnitude - mu))
        thi = max(at, rt * (magnitude + mu))
        if high <= tlo:
            status = "within_tolerance"
        elif low > thi:
            status = "outside_tolerance"
        else:
            status = "indeterminate_boundary"
        return {
            "policy_id": POLICY_ID, "representation": "binary64_interval", "status": status,
            "left_exact": _text(a), "right_exact": _text(b),
            "delta_interval": [_text(low), _text(high)],
            "tolerance_interval": [_text(tlo), _text(thi)],
            "absolute_tolerance": _text(at), "relative_tolerance": _text(rt),
            "equality_rule": EQUALITY_RULE,
            "pass_admission": "indeterminate_boundary is not a pass",
        }
    except (MemoryError, OverflowError) as exc:
        raise NumericResourceError("runtime allocation or representability limit; comparison not completed") from exc


__all__ = ["POLICY_ID", "EQUALITY_RULE", "NumericResourceError", "compare_decimal", "compare_binary64"]
