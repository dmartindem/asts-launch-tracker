"""Alert on US rocket launches happening within the next 24 hours.

Runs on a schedule (GitHub Actions). Keeps a state file of already-notified
launch IDs so each launch is only emailed once per scheduled NET time
(if a launch slips to a new day, it will be re-alerted).
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from common import (
    fetch_upcoming_launches,
    format_launch_html,
    format_launch_text,
    is_us_launch,
    send_email,
    summarize,
)

STATE_FILE = Path(__file__).resolve().parent.parent / "state" / "notified.json"
ALERT_WINDOW_HOURS = 24


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))


def main():
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=ALERT_WINDOW_HOURS)

    launches = fetch_upcoming_launches()
    state = load_state()

    to_alert = []
    for launch in launches:
        if not is_us_launch(launch):
            continue
        s = summarize(launch)
        if not s["net"] or not (now <= s["net"] <= window_end):
            continue
        # Key includes the NET date so a slipped launch re-alerts.
        key = f"{s['id']}::{s['net'].strftime('%Y-%m-%dT%H')}"
        if key in state:
            continue
        to_alert.append((key, s))

    # Prune state entries older than 14 days to keep the file small.
    cutoff = (now - timedelta(days=14)).isoformat()
    state = {k: v for k, v in state.items() if v >= cutoff}

    if not to_alert:
        print("No new US launches in the next 24 hours. Nothing to send.")
        save_state(state)
        return

    to_alert.sort(key=lambda kv: kv[1]["net"])
    count = len(to_alert)
    subject = f"🚀 Launch alert: {count} US launch{'es' if count > 1 else ''} in the next 24 hours"

    text_body = (
        f"US rocket launches scheduled within the next {ALERT_WINDOW_HOURS} hours:\n\n"
        + "\n\n".join(format_launch_text(s) for _, s in to_alert)
        + "\n\nData: Launch Library 2 (thespacedevs.com). Times are UTC and may slip."
    )
    html_body = (
        "<div style='max-width:640px;margin:0 auto;'>"
        f"<h2 style='font-family:Arial,sans-serif;color:#101828;'>🚀 US launches in the next {ALERT_WINDOW_HOURS} hours</h2>"
        + "".join(format_launch_html(s) for _, s in to_alert)
        + "<p style='font-family:Arial,sans-serif;font-size:12px;color:#98a2b3;'>"
        "Data: Launch Library 2 (thespacedevs.com). Times are UTC and may slip.</p></div>"
    )

    send_email(subject, text_body, html_body)

    for key, _ in to_alert:
        state[key] = now.isoformat()
    save_state(state)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # surface failures in the Actions log
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
