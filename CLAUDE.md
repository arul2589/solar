# Solar Platform

Read `SPEC.md` first; it is the source of truth for scope, rules and phases.

## Working rules
- Build in the phases listed in SPEC.md section 11. Finish and test one phase before starting the next.
- Multi-tenant from day one: every table has `installer_id`; every query is tenant-scoped; keep tenant-isolation tests passing.
- Calculation logic lives in a pure library with unit tests, using the worked examples in SPEC.md section 6. No rates, prices, GST or yield values hard-coded; they come from per-installer settings.
- Customers never see a price automatically; staff review and send quotations.
- Anything marked **VERIFY** in SPEC.md needs the owner's confirmation. Stop and ask rather than guessing.
- Do not store bank account numbers or government IDs. Do not build the subsidy workflow yet (placeholder only).
- Reference files are in `reference/`. Treat them as read-only inputs.
- Ask before choosing a stack different from the one suggested in SPEC.md section 3.

## Autonomous mode
- Work through Phase 1, then 2, then 3 from SPEC.md without waiting for approval between phases.
- Do not stop to ask about items marked **VERIFY**. Use the placeholder defaults, show a visible "placeholder - owner must confirm" note in the admin Settings page, and record each one in `DECISIONS.md`.
- Keep `DECISIONS.md` (assumptions made) and `PROGRESS.md` (what is done, what is next, how to run it) up to date after each phase.
- Commit to git after every working milestone with a clear message.
- Before finishing each phase: run all tests, start the app, and smoke-test the full flow (submit request -> acknowledgement email logged -> admin sees analysis -> quotation PDF -> customer accepts).
- Only stop for a real blocker (missing credential, failing test you cannot fix, destructive action).
