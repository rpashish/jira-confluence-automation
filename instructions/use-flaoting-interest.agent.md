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
