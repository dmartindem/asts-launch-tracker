"""Email a 7-day forecast of upcoming US rocket launches.

Scheduled for Monday mornings via GitHub Actions.
"""

import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from common import (
    fetch_upcoming_launches,
    format_launch_html,
    format_launch_text,
    is_us_launch,
    send_email,
    summarize,
)

FORECAST_DAYS = 7


def main():
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=FORECAST_DAYS)

    launches = fetch_upcoming_launches()
    upcoming = []
    for launch in launches:
        if not is_us_launch(launch):
            continue
        s = summarize(launch)
        if s["net"] and now <= s["net"] <= window_end:
            upcoming.append(s)

    upcoming.sort(key=lambda s: s["net"])
    week_label = f"{now.strftime('%b %d')} – {window_end.strftime('%b %d, %Y')}"

    if not upcoming:
        subject = f"🗓️ US launch schedule, {week_label}: no launches currently scheduled"
        text_body = "No US launches are currently scheduled in the next 7 days.\n\nData: Launch Library 2."
        html_body = (
            "<p style='font-family:Arial,sans-serif;color:#344054;'>No US launches are "
            "currently scheduled in the next 7 days.</p>"
        )
        send_email(subject, text_body, html_body)
        return

    by_day = defaultdict(list)
    for s in upcoming:
        by_day[s["net"].strftime("%A, %B %d")].append(s)

    subject = f"🗓️ US launch schedule, {week_label}: {len(upcoming)} launch{'es' if len(upcoming) > 1 else ''}"

    text_parts = [f"Forecasted US launches for {week_label} (all times UTC):"]
    html_parts = [
        "<div style='max-width:640px;margin:0 auto;'>",
        f"<h2 style='font-family:Arial,sans-serif;color:#101828;'>🗓️ US launch schedule, {week_label}</h2>",
    ]
    for day, day_launches in by_day.items():
        text_parts.append(f"\n=== {day} ===")
        html_parts.append(
            f"<h3 style='font-family:Arial,sans-serif;color:#475467;border-bottom:1px solid #e4e7ec;"
            f"padding-bottom:4px;'>{day}</h3>"
        )
        for s in day_launches:
            text_parts.append("\n" + format_launch_text(s))
            html_parts.append(format_launch_html(s))

    text_parts.append("\nData: Launch Library 2 (thespacedevs.com). Schedules slip often — daily alerts will catch changes.")
    html_parts.append(
        "<p style='font-family:Arial,sans-serif;font-size:12px;color:#98a2b3;'>"
        "Data: Launch Library 2 (thespacedevs.com). Schedules slip often — daily alerts will catch changes.</p></div>"
    )

    send_email(subject, "\n".join(text_parts), "".join(html_parts))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
