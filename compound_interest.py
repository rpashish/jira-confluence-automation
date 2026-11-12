"""Compound interest for a fixed principal, rate, and term."""

from decimal import Decimal, ROUND_HALF_UP


def compound_interest(
    principal: Decimal,
    annual_rate: Decimal,
    years: int,
    months: int,
    compounds_per_year: int = 12,
) -> tuple[Decimal, Decimal]:
    """Return (final amount, total interest), rounded to cents."""
    periods = years * compounds_per_year + months
    growth = (1 + annual_rate / compounds_per_year) ** periods
    amount = (principal * growth).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    interest = (amount - principal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return amount, interest


def main() -> None:
    principal = Decimal("15847")
    annual_rate = Decimal("0.0734")
    years, months = 8, 7

    amount, interest = compound_interest(principal, annual_rate, years, months)

    print(f"Principal:      ${principal:,.2f}")
    print(f"Annual rate:    {annual_rate * 100}%")
    print(f"Compounding:    monthly")
    print(f"Term:           {years} years {months} months")
    print(f"Final amount:   ${amount:,.2f}")
    print(f"Total interest: ${interest:,.2f}")


if __name__ == "__main__":
    main()
