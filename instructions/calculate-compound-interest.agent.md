- Use this instruction when the user asks for compound interest, a final amount, or interest earned on a principal.
- Run `tools/compound_interest.py`. Do not calculate the amount by hand. Do not use the project-root `compound_interest.py`.
- Invoke from the project root:
  + `python3 tools/compound_interest.py PRINCIPAL ANNUAL_RATE COMPOUNDS_PER_YEAR YEARS`
- Pass the four arguments in that order:
  + `PRINCIPAL` — starting amount, zero or positive.
  + `ANNUAL_RATE` — decimal such as `0.0734`, or a percent such as `7.34`. A value greater than 1 is a percent.
  + `COMPOUNDS_PER_YEAR` — integer of at least 1. Annually is `1`, quarterly is `4`, monthly is `12`.
  + `YEARS` — term in years, zero or positive. Add leftover months as `months/12`. Eight years and seven months is `8.583333333333333`.
- Present the tool's stdout as the result. Keep both lines and the printed dollar amounts:
  + `Final amount`
  + `Interest earned`
- State the principal, rate, compounding frequency, and term with those two amounts. Do not re-round.
- When the tool exits with an error, report that error. Do not invent an amount.
- Verified example: `python3 tools/compound_interest.py 15847 0.0734 12 8.583333333333333` prints `Final amount: $29,697.95` and `Interest earned: $13,850.95`.
