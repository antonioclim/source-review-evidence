"""Executable specification for APEX2/P6; not a production replacement.

Only Python's standard library is used. This model exposes its exact arithmetic
so that P7 can test a separately integrated implementation against the contract.
Resource-limit engineering and the production wire format remain P7 obligations.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import math
from typing import Any

STATES = frozenset({'observed', 'not_applicable', 'insufficient_evidence', 'unavailable'})
CHECK_STATES = frozenset({'PASS', 'FAIL', 'NOT_EVALUATED'})

def rational(value: str | int | Decimal) -> Fraction:
    """Parse the existing declared lexical types without Decimal arithmetic."""
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise TypeError('expected a decimal string, int or Decimal; bool/float excluded')
    if isinstance(value, int):
        return Fraction(value)
    try:
        dec = value if isinstance(value, Decimal) else Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError('invalid decimal lexical value') from exc
    if not dec.is_finite():
        raise ValueError('finite values required')
    sign, digits, exponent = dec.as_tuple()
    coefficient = 0
    for digit in digits:
        coefficient = 10 * coefficient + digit
    coefficient = -coefficient if sign else coefficient
    if exponent >= 0:
        return Fraction(coefficient * 10**exponent)
    return Fraction(coefficient, 10**(-exponent))

def exact_text(value: Fraction) -> str:
    """Canonical terminating decimal; no Decimal context or rounding."""
    if not value:
        return '0'
    den = value.denominator
    twos = fives = 0
    while den % 2 == 0:
        den //= 2; twos += 1
    while den % 5 == 0:
        den //= 5; fives += 1
    if den != 1:
        raise ValueError('non-terminating decimal requires rational serialisation')
    places = max(twos, fives)
    coefficient = abs(value.numerator) * 2**(places-twos) * 5**(places-fives)
    digits = str(coefficient)
    if places:
        digits = digits.zfill(places+1)
        digits = (digits[:-places] + '.' + digits[-places:]).rstrip('0').rstrip('.')
    return ('-' if value < 0 else '') + digits

def decimal_comparison(left: Any, right: Any, at: Any, rt: Any) -> dict[str, Any]:
    a,b,ta,tr = (rational(v) for v in (left,right,at,rt))
    if ta < 0 or tr < 0:
        raise ValueError('tolerances must be non-negative')
    delta = abs(a-b); tol = max(ta, tr*max(abs(a),abs(b)))
    return {'status': 'within_tolerance' if delta <= tol else 'outside_tolerance',
            'left':exact_text(a),'right':exact_text(b),'delta':exact_text(delta),
            'tolerance':exact_text(tol),'absolute_tolerance':exact_text(ta),
            'relative_tolerance':exact_text(tr)}

def float_interval(x: float) -> tuple[Fraction,Fraction,Fraction,Fraction]:
    if type(x) is not float:
        raise TypeError('binary64 mode requires float operands')
    if not math.isfinite(x):
        raise ValueError('finite binary64 operands required')
    centre = Fraction(*x.as_integer_ratio())
    radius = Fraction(*math.ulp(x).as_integer_ratio())/2
    return centre-radius, centre+radius, centre, radius

def binary_bounds(left: float, right: float, at: Any, rt: Any) -> dict[str, Any]:
    _,_,a,ua=float_interval(left); _,_,b,ub=float_interval(right)
    ta,tr=rational(at),rational(rt)
    if ta < 0 or tr < 0:
        raise ValueError('tolerances must be non-negative')
    delta=abs(a-b); u=ua+ub
    dl,dh=max(Fraction(0),delta-u),delta+u
    mag=max(abs(a),abs(b)); um=max(ua,ub)
    tl=max(ta,tr*max(Fraction(0),mag-um)); th=max(ta,tr*(mag+um))
    status='within_tolerance' if dh<=tl else ('outside_tolerance' if dl>th else 'indeterminate_boundary')
    return {'status':status,'delta_low':dl,'delta_high':dh,'tolerance_low':tl,'tolerance_high':th}

def binary_comparison(left: float, right: float, at: Any, rt: Any) -> dict[str, Any]:
    obj=binary_bounds(left,right,at,rt)
    return {k: exact_text(v) if isinstance(v,Fraction) else v for k,v in obj.items()}

def valid_state_record(state: str, value: Any, reason: str | None = None) -> bool:
    """Necessary V2 projection invariant, not full producer schema validation."""
    return (state in STATES and ((state=='observed') == (value is not None))
            and (state=='observed' or (isinstance(reason,str) and bool(reason.strip()))))

def availability(g1: bool, state: str, value: Any, reason: str | None = None) -> str:
    if type(g1) is not bool:
        return 'INVALID_INPUT'
    if not g1:
        return 'NOT_EVALUATED'
    if not valid_state_record(state,value,reason):
        return 'INVALID_INPUT'
    return 'PASS' if state=='observed' else 'FAIL'

def consumer_full(admission: str, replay: str, same_context: bool) -> str:
    if type(same_context) is not bool or not same_context or admission not in CHECK_STATES or replay not in CHECK_STATES:
        return 'INVALID_INPUT'
    if 'FAIL' in (admission,replay):
        return 'FAIL'
    if admission==replay=='PASS':
        return 'PASS'
    return 'NOT_EVALUATED'

def threshold(x: int, lower: int, upper: int) -> frozenset[int]:
    if any(type(v) is not int for v in (x,lower,upper)) or x<0 or lower<0 or upper<lower:
        raise ValueError('nonnegative integer x and ordered integer 0<=L<=U required')
    return frozenset({0}) if x<=lower else (frozenset({1}) if x>upper else frozenset({0,1}))

def integer_radius(x: int, lower: int, upper: int) -> int:
    threshold(x,lower,upper)
    if x<=lower:return lower+1-x
    if x<=upper:return min(x-lower,upper+1-x)
    return x-upper
