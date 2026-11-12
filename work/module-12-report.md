# Module 12 Completion Report

## Instruction File
- Filename: instructions/use-flaoting-interest.agent.md

- Use this instruction when the user asks for a monthly EMI, an equated monthly installment, or a floating-interest payment on a principal.
- Run `tools/flaoting-interest.py`. Do not calculate the EMI by hand.
- Invoke from the project root:
  + `python3 tools/flaoting-interest.py TENURE ANNUAL_RATE PRINCIPAL`
- Pass the three arguments in that order:
  + `TENURE` — loan term in months, an integer of at least 1.
  + `ANNUAL_RATE` — decimal such as `0.092`, or a percent such as `9.2`. A value greater than 1 is a percent.
  + `PRINCIPAL` — loan amount, zero or positive.
- A zero annual rate divides the principal evenly across the tenure months.
- Present the tool's stdout as the result. Keep the printed line and the dollar amount:
  + `EMI per month`
- State the tenure, rate, and principal with that amount. Do not re-round.
- When the tool exits with an error, report that error. Do not invent an amount.
- Verified example: `python3 tools/flaoting-interest.py 12 10 100000` prints `EMI per month: $8,791.59`.

## Script File
- Filename: tools/flaoting-interest.py
- Language: Python

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

## Script Execution Output
usage: flaoting-interest.py [-h] tenure annual_rate principal

Calculate EMI per month.

positional arguments:
  tenure       Loan tenure in months
  annual_rate  Annual rate as a decimal (0.092) or percent (9.2)
  principal    Principal loan amount

optional arguments:
  -h, --help   show this help message and exit
