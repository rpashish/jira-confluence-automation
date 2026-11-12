# Status Report

**Project:** Checkout redesign
**Author:** Jordan Lee
**Period:** Nov 3–Nov 12, 2026
**Date:** Nov 12, 2026
**Status:** At risk

## Summary

The checkout redesign is at risk for the Nov 21 launch. Guest checkout and the new order summary shipped this period, and payment error states are in review. Address validation is still blocked on a vendor API key, which is the item most likely to move the date.

## Completed

- Shipped guest checkout so returning account creation is optional.
- Shipped the new order summary, including tax and shipping lines.
- Closed the accessibility bugs filed against the payment form in the Nov 3 audit.

## In progress

- Payment error states: copy is approved and the pull request is in review.
- Mobile order summary: layout is built and waiting on a design check for the collapsed state.

## Planned next

- Finish payment error states once review comments are in.
- Start saved-address editing after the vendor API key arrives. If the key slips past Nov 14, this moves to the following period.
- Run the launch checklist with support so macros match the new error copy.

## Risks and blockers

| Item | Impact | Owner | Mitigation |
| --- | --- | --- | --- |
| Vendor API key for address validation has not been issued | Launch date slips if validation is still manual on Nov 21 | Priya Shah | Escalate to the vendor account manager by Nov 13; fall back to manual review for launch if the key is not live by Nov 14 |
| Design check for the collapsed mobile summary is unscheduled | Mobile layout may ship with the expanded-only view | Jordan Lee | Book a 30-minute review on Nov 13 |

## Decisions needed

- Launch scope: Priya Shah to confirm by Nov 14 whether address validation is required for launch or can follow in a patch.
