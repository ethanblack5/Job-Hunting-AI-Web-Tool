import re


CURRENCY_SYMBOLS = {
    "$": "$",
    "US$": "$",
    "USD": "$",
    "C$": "C$",
    "CAD": "C$",
    "A$": "A$",
    "AUD": "A$",
    "£": "£",
    "GBP": "£",
    "€": "€",
    "EUR": "€",
    "₹": "₹",
    "INR": "₹",
    "¥": "¥",
    "JPY": "¥",
}


SALARY_CONTEXT_PATTERN = re.compile(
    r"""
    salary|
    compensation|
    pay\s+range|
    base\s+pay|
    base\s+salary|
    annual\s+salary|
    annual\s+compensation|
    hourly\s+rate|
    remuneration
    """,
    re.IGNORECASE | re.VERBOSE,
)


EXCLUDED_CONTEXT_PATTERN = re.compile(
    r"""
    signing\s+bonus|
    annual\s+bonus|
    performance\s+bonus|
    commission|
    stipend|
    allowance|
    reimbursement|
    home\s+office|
    internet|
    401\s*\(?k\)?|
    revenue|
    funding|
    valuation|
    budget
    """,
    re.IGNORECASE | re.VERBOSE,
)


RANGE_PATTERN = re.compile(
    r"""
    (?P<currency1>
        US\$|C\$|A\$|\$|£|€|₹|¥|
        USD|CAD|AUD|GBP|EUR|INR|JPY
    )?
    \s*
    (?P<amount1>
        \d{1,3}(?:,\d{3})+
        |
        \d+(?:\.\d+)?
    )
    \s*
    (?P<suffix1>[kKmM])?
    \s*
    (?:-|–|—|to|through)
    \s*
    (?P<currency2>
        US\$|C\$|A\$|\$|£|€|₹|¥|
        USD|CAD|AUD|GBP|EUR|INR|JPY
    )?
    \s*
    (?P<amount2>
        \d{1,3}(?:,\d{3})+
        |
        \d+(?:\.\d+)?
    )
    \s*
    (?P<suffix2>[kKmM])?
    """,
    re.IGNORECASE | re.VERBOSE,
)


SINGLE_PATTERN = re.compile(
    r"""
    (?P<currency>
        US\$|C\$|A\$|\$|£|€|₹|¥|
        USD|CAD|AUD|GBP|EUR|INR|JPY
    )
    \s*
    (?P<amount>
        \d{1,3}(?:,\d{3})+
        |
        \d+(?:\.\d+)?
    )
    \s*
    (?P<suffix>[kKmM])?
    """,
    re.IGNORECASE | re.VERBOSE,
)


def normalize_amount(
    amount_text: str,
    suffix: str | None,
) -> int:
    value = float(amount_text.replace(",", ""))

    if suffix:
        suffix = suffix.lower()

        if suffix == "k":
            value *= 1_000
        elif suffix == "m":
            value *= 1_000_000

    return round(value)


def normalize_currency_symbol(
    currency: str | None,
) -> str | None:
    if not currency:
        return None

    normalized = currency.upper()

    return CURRENCY_SYMBOLS.get(
        normalized,
        CURRENCY_SYMBOLS.get(currency),
    )


def format_salary(
    amount: int,
    currency_symbol: str,
) -> str:
    return f"{currency_symbol}{amount:,}"


def is_plausible_salary(
    minimum: int,
    maximum: int,
    nearby_text: str,
) -> bool:
    if minimum <= 0 or maximum <= 0:
        return False

    if minimum > maximum:
        return False

    if EXCLUDED_CONTEXT_PATTERN.search(nearby_text):
        return False

    # Allows hourly, monthly, and annual values.
    if minimum < 5 or maximum > 10_000_000:
        return False

    return True


def extract_salary_bounds(
    description: str,
) -> tuple[str | None, str | None]:
    """
    Extract formatted salary bounds from a cleaned description.

    Returns:
        ("$80,000", "$110,000")
        ("£65,000", None)
        (None, None)
    """

    if not description:
        return None, None

    text = re.sub(r"\s+", " ", description).strip()

    range_candidates = []

    for match in RANGE_PATTERN.finditer(text):
        context_start = max(0, match.start() - 100)
        context_end = min(len(text), match.end() + 100)
        nearby_text = text[context_start:context_end]

        amount1 = normalize_amount(
            match.group("amount1"),
            match.group("suffix1"),
        )

        amount2 = normalize_amount(
            match.group("amount2"),
            match.group("suffix2"),
        )

        minimum = min(amount1, amount2)
        maximum = max(amount1, amount2)

        currency = (
            match.group("currency1")
            or match.group("currency2")
        )

        currency_symbol = normalize_currency_symbol(currency)

        if currency_symbol is None:
            continue

        if not is_plausible_salary(
            minimum,
            maximum,
            nearby_text,
        ):
            continue

        has_salary_context = bool(
            SALARY_CONTEXT_PATTERN.search(nearby_text)
        )

        range_candidates.append(
            (
                has_salary_context,
                match.start(),
                minimum,
                maximum,
                currency_symbol,
            )
        )

    if range_candidates:
        # Prioritize matches near words such as "salary" or "compensation".
        range_candidates.sort(
            key=lambda item: (
                not item[0],
                item[1],
            )
        )

        _, _, minimum, maximum, symbol = range_candidates[0]

        formatted_min = format_salary(minimum, symbol)

        if minimum == maximum:
            return formatted_min, None

        formatted_max = format_salary(maximum, symbol)

        return formatted_min, formatted_max

    single_candidates = []

    for match in SINGLE_PATTERN.finditer(text):
        context_start = max(0, match.start() - 100)
        context_end = min(len(text), match.end() + 100)
        nearby_text = text[context_start:context_end]

        amount = normalize_amount(
            match.group("amount"),
            match.group("suffix"),
        )

        currency_symbol = normalize_currency_symbol(
            match.group("currency")
        )

        if currency_symbol is None:
            continue

        if not is_plausible_salary(
            amount,
            amount,
            nearby_text,
        ):
            continue

        has_salary_context = bool(
            SALARY_CONTEXT_PATTERN.search(nearby_text)
        )

        single_candidates.append(
            (
                has_salary_context,
                match.start(),
                amount,
                currency_symbol,
            )
        )

    if single_candidates:
        single_candidates.sort(
            key=lambda item: (
                not item[0],
                item[1],
            )
        )

        _, _, amount, symbol = single_candidates[0]

        return format_salary(amount, symbol), None

    return None, None
