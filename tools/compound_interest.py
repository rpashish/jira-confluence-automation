"""Calculate compound interest from command-line inputs.

Usage:
    python tools/compound_interest.py PRINCIPAL ANNUAL_RATE COMPOUNDS_PER_YEAR YEARS

ANNUAL_RATE is a decimal (0.0734 for 7.34%). A value greater than 1 is treated
as a percent (7.34 for 7.34%).
"""

import argparse
from decimal import Decimal, ROUND_HALF_UP


def compound_interest(
    principal: Decimal,
    annual_rate: Decimal,
    compounds_per_year: int,
    years: Decimal,
) -> tuple[Decimal, Decimal]:
    """Return (final amount, interest earned), rounded to cents."""
    growth = (1 + annual_rate / compounds_per_year) ** (compounds_per_year * years)
    amount = (principal * growth).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    interest = (amount - principal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return amount, interest


def parse_rate(value: str) -> Decimal:
    """Parse an annual rate as a decimal, or as a percent when greater than 1."""
    rate = Decimal(value)
    if rate > 1:
        rate = rate / Decimal(100)
    return rate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calculate compound interest.")
    parser.add_argument("principal", type=Decimal, help="Starting principal")
    parser.add_argument(
        "annual_rate",
        type=parse_rate,
        help="Annual rate as a decimal (0.0734) or percent (7.34)",
    )
    parser.add_argument(
        "compounds_per_year",
        type=int,
        help="Number of compounding periods per year",
    )
    parser.add_argument("years", type=Decimal, help="Length of the term in years")
    args = parser.parse_args()

    if args.principal < 0:
        parser.error("principal must be zero or positive")
    if args.annual_rate < 0:
        parser.error("annual rate must be zero or positive")
    if args.compounds_per_year < 1:
        parser.error("compounds per year must be at least 1")
    if args.years < 0:
        parser.error("years must be zero or positive")
    return args


def main() -> None:
    args = parse_args()
    amount, interest = compound_interest(
        args.principal,
        args.annual_rate,
        args.compounds_per_year,
        args.years,
    )
    print(f"Final amount:    ${amount:,.2f}")
    print(f"Interest earned: ${interest:,.2f}")


if __name__ == "__main__":
    main()
