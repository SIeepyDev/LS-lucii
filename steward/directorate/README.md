# Lucii Action & Trust Directorate

Source: `steward/directorate/action.py`. GitHub state: committed and read-back pending; host runtime not yet verified.

## Concrete micro-specialists
- Authenticator: local target registration by explicit path; does **not** authenticate users or grant credentials
- Target registrar: SQLite records of private files, directories and Git worktrees
- Discoverer / inspector: file and directory metadata, size
- Forensic verifier: streaming SHA256 for local files up to 16 MiB
- Git scout: bounded read-only `git status --short`
- Publication planner / repair planner: returns PLAN_ONLY; no push, deployment, publication or mutation
- Evidence recorder: append-only local SQLite receipts
- Policy enforcer: fixed action allowlist; public registration blocked; no arbitrary shell
- Executor: only predefined local read-only actions; no autonomous network calls

## Run on approved Lucii/T530 host
```sh
python3 action.py register sample-file file /var/tmp/ls-worlds/latest.json
python3 action.py check sample-file hash
python3 action.py check sample-file publish-plan
python3 action.py status
```

Default state `/root/lucii/action/directorate.sqlite3`; override with LUCII_ACTION_HOME. Do not expose this SQLite database publicly. Publicizing anything requires a different reviewed execution path and explicit approval.

Current project claim: no user-supplied runtime receipt for this script yet. Commit verification and live tests must precede any "running" status.

## Future adaptations
Scoped capability tokens, independent rule evaluators, agent identity registry, public/private manifest review, connectors via permissioned adapters, violation quarantine, bounded retries, verifiable deployment receipts. "Hunters"/"snipers" refer solely to target-matching diagnostics and are not offensive or surveillance capabilities.
