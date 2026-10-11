from __future__ import annotations
import math


def kg_to_g(kg: float) -> int:
    return round(kg * 1000)


def g_to_kg_str(g: int) -> str:
    kg = g / 1000
    return f"{kg:.3f}"


def m_to_cm(m: float) -> int:
    return round(m * 100)


def cm_to_m_str(cm: int) -> str:
    m = cm / 100
    return f"{m:.2f}"


def rupees_to_paise(rupees: float) -> int:
    return round(rupees * 100)


def paise_to_rupees_str(paise: int) -> str:
    rupees = paise / 100
    # Indian grouping: last 3 digits, then groups of 2
    sign = "-" if paise < 0 else ""
    paise = abs(paise)
    rupees_int = paise // 100
    paisa_part = paise % 100

    s = str(rupees_int)
    if len(s) > 3:
        last3 = s[-3:]
        rest = s[:-3]
        groups = []
        while len(rest) > 2:
            groups.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.append(rest)
        groups.reverse()
        formatted = ",".join(groups) + "," + last3
    else:
        formatted = s

    return f"{sign}₹{formatted}.{paisa_part:02d}"


_ONES = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen",
]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def _words_lt_1000(n: int) -> str:
    if n == 0:
        return ""
    elif n < 20:
        return _ONES[n]
    elif n < 100:
        t = _TENS[n // 10]
        o = _ONES[n % 10]
        return t + (" " + o if o else "")
    else:
        h = _ONES[n // 100] + " Hundred"
        rest = _words_lt_1000(n % 100)
        return h + (" " + rest if rest else "")


def amount_in_words_inr(paise: int) -> str:
    """Return e.g. 'Rupees One Lakh Twenty-Three Thousand Four Hundred and Fifty Paise Only'."""
    if paise < 0:
        return "Minus " + amount_in_words_inr(-paise)
    if paise == 0:
        return "Rupees Zero Only"

    rupees = paise // 100
    paisa = paise % 100

    parts: list[str] = []

    crore = rupees // 10_000_000
    rupees %= 10_000_000
    lakh = rupees // 100_000
    rupees %= 100_000
    thousand = rupees // 1000
    rupees %= 1000
    remainder = rupees

    if crore:
        parts.append(_words_lt_1000(crore) + " Crore")
    if lakh:
        parts.append(_words_lt_1000(lakh) + " Lakh")
    if thousand:
        parts.append(_words_lt_1000(thousand) + " Thousand")
    if remainder:
        parts.append(_words_lt_1000(remainder))

    rupee_words = " ".join(parts) if parts else "Zero"
    result = f"Rupees {rupee_words}"

    if paisa:
        result += f" and {_words_lt_1000(paisa)} Paise"

    return result + " Only"
