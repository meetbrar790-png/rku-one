# RKU ONE — Global VIP payment policy (proposal)

Status: **DESIGN ONLY**. No checkout, provider credentials, payment capture, VIP reservation, or production deployment is enabled.

## Commercial rules
- VIP catalogue base list prices are denominated in **USD**.
- ID 1 (founder) and ID 11 (company) are **not for sale**.
- IDs 2–1000 are paid **only if never issued and not otherwise reserved**; IDs 13 and 786 are Special VVIP.
- IDs 1001+ are free under the proposed policy. Live allocation still needs a reviewed migration.
- Prefer customer **local-currency checkout** where supported by the payment provider. Fall back to USD where legally and technically supported.
- Prefer **AUD settlement** to the Australian company where supported; provider/account settlement configuration must be checked. USD list prices and AUD settlement are separate decisions.
- Display the provider-calculated final amount, currency, taxes, conversion markup and fees **before payment confirmation**. Never invent or hardcode an FX rate.
- Treat prices as one-time proposed list prices, not confirmed offers or inventory.

## Technical security requirements
1. The server, not the browser, chooses the authoritative USD price from `vip_pricing_policy.py` and checks live inventory in a transaction.
2. Place an expiring, owner-bound VIP hold in a database with a shared allocation lock; never reassign issued IDs.
3. Create checkout using server-side credentials and a unique order/payment reference.
4. Verify provider webhook signature and retrieve payment status server-side. A redirect/success page is not proof of payment.
5. Make fulfillment idempotent; match paid amount/currency, order, VIP number and buyer before issuing the ID once.
6. Handle asynchronous payment, failed payments, cancellations, refunds, chargebacks, tax and reconciliation.
7. Keep payment secrets out of GitHub, frontend and logs; do not store raw card data.
8. Run staging sandbox tests and legal/accounting review before any production release.

## Provider notes
Stripe Adaptive Pricing may display local-currency prices for supported Checkout flows, while settlement uses configured settlement currencies. FX conversion markup may apply. Verify current eligibility, fees, Australian account settlement currency, and supported markets before integration.

References:
- https://support.stripe.com/questions/adaptive-pricing?locale=en-GB
- https://stripe.com/resources/more/presentment-currency-and-settlement-currency-explained-what-every-business-needs-to-know

**Owner approval is required** before creating paid infrastructure, connecting a payment account, accepting money or changing live registration.
