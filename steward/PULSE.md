# Lucii Pulse — multi-speed coordinator

Status: committed to GitHub; T530 runtime NOT YET VERIFIED.

A Python 3 standard-library, SQLite-backed coordinator: second, minute, hour, day and nighttime lanes. Millisecond lane is intentionally a **bounded in-process demo idea generator**, not a busy-loop or an actual millisecond service. Registered worker role names are functions/specializations, not standalone daemons. Per-lane timestamps avoid repeated execution on each tick; SQLite stores observations; one OS file lock prevents overlapping coordinators. The long-running loop is bounded to at most 60 seconds, then exits.

## T530 run
python3 pulse.py demo
python3 pulse.py once
python3 pulse.py status

Optional short experiment:
python3 pulse.py loop --seconds 15

## Policies
Never start a second long-running scheduler before examining existing Lucii timers. To automate, reuse a current verified scheduling lane, with explicit configuration review. No unattended apt/sudo, Git push, public deployment, service restart, or container mutation. Simulated idea proposals are labelled IDEA_ONLY; not claims of research or tested software. Night lane uses *host local time* and 00:00-06:00. Day and night cadence persists in local SQLite, not externally synchronized. The current 24-hour cycle does NOT execute 1,104 NPC workers; it dispatches bounded observation functions.

Current connected source: LS-lucii repository, branch feature/steward-evidence-20261028.
