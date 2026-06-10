"""Shared helpers: Launch Library 2 API, email delivery, formatting."""

import os
import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

LL2_UPCOMING = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/"


def fetch_upcoming_launches(limit=60):
    """Fetch upcoming launches from Launch Library 2 (free tier: 15 req/hr)."""
    params = {"limit": limit, "hide_recent_previous": "true", "mode": "detailed"}
    resp = requests.get(LL2_UPCOMING, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("results", [])


def is_us_launch(launch):
    """True if the launch pad is located in the United States."""
    try:
        return launch["pad"]["location"]["country_code"] == "USA"
    except (KeyError, TypeError):
        return False


def launch_net(launch):
    """Parse the NET (no-earlier-than) time as an aware UTC datetime."""
    net = launch.get("net")
    if not net:
        return None
    return datetime.fromisoformat(net.replace("Z", "+00:00")).astimezone(timezone.utc)


def summarize(launch):
    """Build a high-level summary dict: provider, location, payload, time."""
    provider = (launch.get("launch_service_provider") or {}).get("name", "Unknown provider")
    pad = launch.get("pad") or {}
    pad_name = pad.get("name", "Unknown pad")
    location = (pad.get("location") or {}).get("name", "Unknown location")

    mission = launch.get("mission") or {}
    payload = mission.get("name") or "Payload not announced"
    description = mission.get("description") or ""
    orbit = (mission.get("orbit") or {}).get("name") or ""
    mission_type = mission.get("type") or ""

    rocket = ((launch.get("rocket") or {}).get("configuration") or {}).get("full_name", "")
    status = (launch.get("status") or {}).get("name", "")

    net = launch_net(launch)
    net_str = net.strftime("%a %b %d, %Y %H:%M UTC") if net else "TBD"

    return {
        "id": launch.get("id"),
        "name": launch.get("name", "Unnamed launch"),
        "provider": provider,
        "rocket": rocket,
        "pad": pad_name,
        "location": location,
        "payload": payload,
        "description": description.strip(),
        "orbit": orbit,
        "mission_type": mission_type,
        "status": status,
        "net": net,
        "net_str": net_str,
    }


def format_launch_text(s):
    """Plain-text block for one launch summary."""
    lines = [
        f"{s['name']}",
        f"  When:     {s['net_str']}  ({s['status']})",
        f"  Provider: {s['provider']}" + (f" — {s['rocket']}" if s["rocket"] else ""),
        f"  Where:    {s['pad']}, {s['location']}",
        f"  Payload:  {s['payload']}"
        + (f" ({s['mission_type']}" + (f", {s['orbit']})" if s["orbit"] else ")") if s["mission_type"] else ""),
    ]
    if s["description"]:
        desc = s["description"]
        if len(desc) > 400:
            desc = desc[:397] + "..."
        lines.append(f"  Summary:  {desc}")
    return "\n".join(lines)


def format_launch_html(s):
    """HTML block for one launch summary."""
    desc = s["description"]
    if len(desc) > 400:
        desc = desc[:397] + "..."
    payload_extra = ""
    if s["mission_type"]:
        payload_extra = f" ({s['mission_type']}" + (f", {s['orbit']})" if s["orbit"] else ")")
    return f"""
    <div style="border:1px solid #d8dce5;border-radius:8px;padding:16px 18px;margin:0 0 14px 0;font-family:Arial,Helvetica,sans-serif;">
      <div style="font-size:16px;font-weight:bold;color:#101828;margin-bottom:6px;">{s['name']}</div>
      <table style="font-size:14px;color:#344054;border-collapse:collapse;">
        <tr><td style="padding:2px 12px 2px 0;color:#667085;">When</td><td>{s['net_str']} &middot; {s['status']}</td></tr>
        <tr><td style="padding:2px 12px 2px 0;color:#667085;">Provider</td><td>{s['provider']}{(' — ' + s['rocket']) if s['rocket'] else ''}</td></tr>
        <tr><td style="padding:2px 12px 2px 0;color:#667085;">Where</td><td>{s['pad']}, {s['location']}</td></tr>
        <tr><td style="padding:2px 12px 2px 0;color:#667085;">Payload</td><td>{s['payload']}{payload_extra}</td></tr>
      </table>
      {f'<p style="font-size:13px;color:#475467;margin:10px 0 0 0;">{desc}</p>' if desc else ''}
    </div>"""


def send_email(subject, text_body, html_body):
    """Send an email via Gmail SMTP using repo secrets."""
    sender = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ.get("ALERT_RECIPIENT", sender)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender, app_password)
        server.sendmail(sender, [recipient], msg.as_string())
    print(f"Email sent to {recipient}: {subject}")
