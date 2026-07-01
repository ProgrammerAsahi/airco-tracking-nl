# Airco Tracker NL — current handoff

Last updated: 2026-07-01 (Europe/Amsterdam)

## Current objective

Expand reliable portable-air-conditioner coverage for Dutch delivery while keeping credentials out of source control. The immediate pending task is the official AliExpress Affiliate/Open Platform integration after API approval.

## Repository and production state

- Repository: `https://github.com/ProgrammerAsahi/airco-tracking-nl`
- Branch: `main`
- Last deployed commit: `8efaec7` (`Add five portable airco retailers`)
- GitHub workflow: `Deploy to Azure`
- Azure resource group: `airco-tracker-nl-rg`
- Azure Container Apps job: `airco-tracker-job`
- Schedule: every 10 minutes
- Current deployed image tag: full SHA for commit `8efaec7`
- State: Azure Blob Storage (`airco-tracker/state.json`)
- Notifications: Azure Communication Services Email
- Secrets: Azure Key Vault through Managed Identity
- Last verified production execution after commit `8efaec7`: succeeded; all five newly added adapters ran without errors and no false stock email was sent.

## Supported retailers

Active without private credentials:

- Coolblue
- MediaMarkt NL
- EP.nl
- Electro World
- Wehkamp
- Lidl Netherlands
- GAMMA
- KARWEI
- Praxis
- Alternate.nl
- Trotec
- Klarstein
- FlinQ
- Action Webshop

Optional/credential-gated:

- bol.com: official Marketing Catalog API adapter exists but production remains disabled until official API credentials are configured. Do not restore webpage scraping; Azure IPs receive 403 and the search route is robots-restricted.
- AliExpress: no adapter has been implemented yet. Use the official Affiliate/Open Platform API only.

## AliExpress external status

- Affiliate account approved on 2026-07-01.
- Open Platform developer type selected: `Dropshipping/Affiliates Developer` → `Affiliates (individual)`.
- API application submitted on 2026-07-01.
- Current portal status: `Under Review` with an estimated review time of 2–5 working days.
- Intended data scope: public affiliate product catalog/offer data only (title, URL, price, availability, promotion/tracking link, and minimal API metadata).
- Do not request or retain buyer, order, payment, or other personal data.
- Runtime processing is hosted on Microsoft Azure. Core compute/storage is Azure West Europe; Azure Communication Services is configured with the Europe data location.

## Next steps after AliExpress approval

1. Ask the user to open the API page and identify the approved app/key screen. Do not request screenshots containing an App Secret.
2. Verify the current official Affiliate API authentication/signing and product-search endpoints from primary AliExpress documentation.
3. Design an `AliExpressAdapter` that searches portable/compressor air conditioners, filters out air coolers/accessories, enforces Dutch deliverability when the API exposes it, and uses the existing `MAX_PRICE_EUR`/`MIN_BTU` alert filters.
4. Add configuration fields and validation with a disabled-by-default backend, similar to bol.com.
5. Add a hidden-input setup script (for example `scripts/configure-aliexpress-api.sh`) that writes secrets directly to Azure Key Vault and configures only non-sensitive GitHub Actions variables.
6. Add parser/API tests using synthetic responses; never put real credentials or captured private responses in fixtures.
7. Run the full test suite and local live dry-run, then deploy through the existing GitHub Actions pipeline if the user authorizes it.
8. Confirm the production image SHA and inspect one Container Apps job execution for the AliExpress retailer count.

## Known behavior and safeguards

- Retailers are isolated: one failure does not stop other checks.
- Missing seasonal products are marked unavailable only when that retailer completed successfully, allowing a later restock transition without treating a failed request as stock loss.
- Trotec multi-week lead times are not immediate stock.
- Action expired deals are kept as known URLs so reactivation can be detected.
- All adapters must exclude air coolers, fans, and accessories.
- Production credentials must remain in Key Vault; configuration maps environment variable names to secret names.

## Verification snapshot

- Unit tests after the latest retailer expansion: 26 passed.
- Live local dry-run after commit `8efaec7`: Alternate 0, Trotec 13, Klarstein 18, FlinQ 2, Action Webshop 1; all five reported zero immediate stock at that time.
- GitHub Actions deployment run for commit `8efaec7`: succeeded.
- Azure job provisioning state: succeeded; scheduled trigger active.

## Updating this handoff

Replace stale status rather than appending a diary. Always update the date, deployed commit, external review state, next concrete action, and verification evidence. Never include secret values, tokens, passwords, or unnecessary personal information.
