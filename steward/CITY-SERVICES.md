# Lucii City Services — local micro-crews

Source: city_services.py. State: committed and read back, live T530 test pending.

This is an evidence-backed coordinator with nine **role labels**, not nine background processes. It checks seven existing Lucii systemd units, verifies the previous steward receipt hash, classifies status anomalies, detects the inactive rotor timer for review, writes unique JSON observations and maintains a deduplicated SQLite workorder table.

Only local output state is written. No apt upgrade, sudo automation, Git pushes, container lifecycle changes, service restarts, or timer modifications. No API keys, pip, or AI models. An inactive service is not automatically an error. A receipt hash match establishes integrity, not independent truth.

Run: python3 city_services.py

Default state: /root/lucii/steward/city-services. Use LUCII_STEWARD_HOME to move it.

Next: correlate workorders with the existing gapcrew/commandcrew schemas after inspecting those live files. Do not assume they can consume this format, and do not add another timer before checking scheduling coverage.

Four tests passed for a closely related local reference implementation; the committed GitHub variant has not yet been tested on the T530.
