"""Calculate the monthly EMI from command-line inputs.

Usage:
    python tools/flaoting-interest.py TENURE ANNUAL_RATE PRINCIPAL

TENURE is the loan term in months.
ANNUAL_RATE is a decimal (0.092 for 9.2%). A value greater than 1 is treated
as a percent (9.2 for 9.2%).
PRINCIPAL is the loan amount.
"""

import argparse
from decimal import Decimal, ROUND_HALF_UP


def monthly_emi(principal: Decimal, annual_rate: Decimal, tenure_months: int) -> Decimal:
    """Return the equated monthly installment, rounded to cents.

    Uses EMI = P * r * (1 + r)^n / ((1 + r)^n - 1), where r is the monthly
    rate and n is the tenure in months. A zero rate is principal divided by n.
    """
    if annual_rate == 0:
        payment = principal / Decimal(tenure_months)
    else:
        monthly_rate = annual_rate / Decimal(12)
        growth = (1 + monthly_rate) ** tenure_months
        payment = principal * monthly_rate * growth / (growth - 1)
    return payment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def parse_rate(value: str) -> Decimal:
    """Parse an annual rate as a decimal, or as a percent when greater than 1."""
    rate = Decimal(value)
    if rate > 1:
        rate = rate / Decimal(100)
    return rate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calculate EMI per month.")
    parser.add_argument("tenure", type=int, help="Loan tenure in months")
    parser.add_argument(
        "annual_rate",
        type=parse_rate,
        help="Annual rate as a decimal (0.092) or percent (9.2)",
    )
    parser.add_argument("principal", type=Decimal, help="Principal loan amount")
    args = parser.parse_args()

    if args.tenure < 1:
        parser.error("tenure must be at least 1 month")
    if args.annual_rate < 0:
        parser.error("annual rate must be zero or positive")
    if args.principal < 0:
        parser.error("principal must be zero or positive")
    return args


def main() -> None:
    args = parse_args()
    emi = monthly_emi(args.principal, args.annual_rate, args.tenure)
    print(f"EMI per month: ${emi:,.2f}")


if __name__ == "__main__":
    main()
