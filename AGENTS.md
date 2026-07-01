# Airco Tracker NL — shared agent instructions

## Mission

Maintain a reliable, low-cost stock tracker for real portable compressor air conditioners that can be delivered to a Dutch address. Notify only when a product is newly available or changes from unavailable to available.

## Read first

1. Read `docs/HANDOFF.md` for the current state and next task.
2. Read the relevant adapter, tests, and infrastructure files before editing.
3. Use the language-specific README only for user-facing setup details (`README.md`, `README.en.md`, `README.nl.md`). Keep all three synchronized when behavior changes.

## Non-negotiable rules

- Never commit or print API keys, client secrets, passwords, access tokens, SMTP credentials, or Key Vault secret values.
- Third-party credentials belong in Azure Key Vault and are read through Managed Identity.
- Prefer official APIs. Otherwise use public server-rendered pages or robots-advertised sitemaps. Respect robots.txt and terms; never bypass CAPTCHA, 403 protections, login barriers, or anti-bot controls.
- Track genuine compressor air conditioners. Exclude air coolers, evaporative coolers, fans, hoses, window kits, remotes, filters, and other accessories.
- `available=True` means currently orderable for delivery to a Netherlands address. Store-only stock, pickup-only stock, expired deals, presales, and multi-week lead times must not trigger alerts.
- One retailer failure must not stop the remaining retailers. Do not turn a failed check into an out-of-stock transition.
- Tests and dry-runs must not send email or update production state.
- Do not read order, buyer, payment, or other personal data when product-catalog and affiliate-offer scopes are sufficient.
- Preserve unrelated user changes in a dirty worktree.

## Architecture

- Python package: `airco_tracker/`
- Retailer integrations: `airco_tracker/adapters/`
- CLI/orchestration: `airco_tracker/cli.py`
- State transitions: `airco_tracker/state.py`
- Azure infrastructure: `infra/`
- Deployment scripts: `scripts/`
- Tests: `tests/`
- Production: Azure Container Apps scheduled job, Blob Storage state, Communication Services Email, Key Vault, and Managed Identity.
- CI/CD: a push to `main` runs tests, builds an immutable image tagged with the commit SHA, deploys it, and starts one verification execution.

## Standard verification

Run from the repository root:

```bash
.venv/bin/python -m unittest discover -v
PYTHONPYCACHEPREFIX=/tmp/airco-pycache .venv/bin/python -m compileall -q airco_tracker tests
git diff --check
.venv/bin/python -m airco_tracker check --dry-run
```

The live dry-run performs network reads but must not send mail or mutate state. If a local installed `airco-tracker` entry point is stale, reinstall with `.venv/bin/pip install --no-deps --force-reinstall .` or use `python -m airco_tracker`.

## Change workflow

1. Inspect `git status` and recent history.
2. Make the smallest coherent change and add focused parser/state tests.
3. Run unit tests, compile checks, and `git diff --check`.
4. For retailer changes, perform a live `--dry-run` and inspect retailer counts/errors.
5. Update all three READMEs when supported sites, configuration, or deployment behavior changes.
6. Update `docs/HANDOFF.md` whenever current status, deployed commit, external review state, next task, or blockers change.
7. Commit, push, deploy, or start production jobs only when the user's request authorizes those actions.

## Handoff quality

Keep `docs/HANDOFF.md` factual and compact. Record the date, deployed commit, completed work, current blocker, next concrete steps, and verification evidence. Never place secrets or unnecessary personal data in it.
