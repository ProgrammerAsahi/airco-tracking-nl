@AGENTS.md
@docs/HANDOFF.md

# Claude Code notes

- Treat `AGENTS.md` as the stable project contract and `docs/HANDOFF.md` as the current operational handoff.
- Start work from the repository root (`~/airco-tracking-nl`) and verify the current branch, working tree, and latest commit before changing files.
- Handoff facts can become stale. Re-check live GitHub/Azure/external-review state before acting on time-sensitive claims.
- Never ask the user to paste an API secret into chat. Use a hidden terminal prompt and Azure Key Vault for credentials.
- If the requested work reaches an external submission, purchase, permission change, credential creation, or production mutation not already authorized by the user, pause immediately before that action.
- After completing a meaningful milestone or discovering a blocker, update `docs/HANDOFF.md` in the same change.
