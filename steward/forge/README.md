# Lucii Asset Forge — reusable atoms and quality gates

Status: committed to GitHub, but T530 execution is NOT verified. Python 3 standard library and SQLite only.

Capabilities:
- Assets: tokens, terms, components, templates, routes, sites, games, backends, frontends, concepts, workflows.
- Directed acyclic relationship graph (uses, wraps, depends-on, contains, extends, maps-to).
- Token starter set. Registry, JSON map, HTML gallery, Markdown contents.
- Quality checks, SQLite upgrade backlog and timestamped signals.
- No automatic rewrites, deletion, publishing, deploy, notifications, network calls, or privilege escalation.
- Scores are coverage heuristics. A score never proves runtime health. Stub/source records start PLACEHOLDER.
- `checks.has_real_tests` requires future evidence ingestion; this edition does not fabricate it or mark anyone TESTED.

Run from connected LS-lucii checkout:

```sh
python3 steward/forge/forge.py demo
python3 steward/forge/forge.py map
python3 steward/forge/forge.py status
python3 -m unittest steward/forge/test_forge.py
```

Output defaults under /root/lucii/forge (override LUCII_FORGE_HOME). No timer created. Integrate with existing Lucii microcrew/command/gapcrew after confirming their input formats. Do not add an overlapping cron.

Hard quality challenge: test wrong or missing dependencies, duplicate IDs, cycles, insufficient evidence, oversized assets, source drift, inaccessible routes, false runtime claims and rollback. Limit low-quality experiments explicitly; keep them labeled PLACEHOLDER rather than deleting history. Emit a work order when quality is below the target; require independent receipts to promote to TESTED or HARDENED.

"Watchers" and signals currently mean durable SQLite events, not external push notifications or audible bells.
