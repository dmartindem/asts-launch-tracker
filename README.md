# ASTS Launch Tracker

Three systems in one free GitHub repository:

1. **Launch alerts** — every 6 hours, checks for US rocket launches in the next 24 hours and emails you a summary (provider, location, payload). Each launch is alerted once; if it slips to a new time, you get re-alerted.
2. **Weekly schedule** — every Monday at 8:00 AM Central, emails a forecast of all US launches in the coming 7 days, grouped by day.
3. **ASTS satellite tracker** — a live dashboard (GitHub Pages) tracking AST SpaceMobile's BlueWalker 3 and BlueBird satellites: real-time map positions, ground tracks, ticking telemetry (lat/lon/altitude/velocity), and pass predictions over your location.

**Data sources (all free, no API keys):**
- Launches: [Launch Library 2](https://thespacedevs.com/llapi) by The Space Devs (free tier: 15 requests/hour — this repo uses ~5/day)
- Satellites: [CelesTrak](https://celestrak.org) TLEs, propagated in-browser with satellite.js (SGP4)

---

## Setup (about 10 minutes)

### 1. Create the repo

Create a new GitHub repository (private is fine) and push these files to it:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/asts-launch-tracker.git
git push -u origin main
```

### 2. Create a Gmail app password

The alert emails are sent from your own Gmail account via SMTP.

1. Go to your Google Account → **Security** → enable **2-Step Verification** (required).
2. Go to https://myaccount.google.com/apppasswords
3. Create an app password named `launch-tracker`. Google shows you a 16-character password — copy it.

> An app password only grants SMTP send access and can be revoked anytime. Never commit it to the repo.

### 3. Add repository secrets

In your repo: **Settings → Secrets and variables → Actions → New repository secret**. Add three:

| Secret name | Value |
|---|---|
| `GMAIL_ADDRESS` | your Gmail address (the sender) |
| `GMAIL_APP_PASSWORD` | the 16-character app password |
| `ALERT_RECIPIENT` | where alerts go (can be the same address) |

### 4. Enable workflows and test

1. Go to the **Actions** tab and enable workflows if prompted.
2. Open **"Launch alerts (every 6 hours)"** → **Run workflow** to test immediately. Check the run log; if a US launch is inside the next 24 h you'll get an email, otherwise the log says nothing to send.
3. Optionally run **"Weekly launch schedule (Monday)"** manually — this one always sends an email, so it's the easiest end-to-end test.

After that, both run automatically on their schedules. Note: GitHub may pause scheduled workflows on repos with no activity for 60 days — the state-file commits from the alert job normally keep it active, but if it pauses, one click re-enables it.

### 5. Turn on the satellite tracker (GitHub Pages)

1. Repo **Settings → Pages**.
2. Source: **Deploy from a branch**, branch `main`, folder `/docs`. Save.
3. After a minute, your tracker is live at `https://YOUR_USERNAME.github.io/asts-launch-tracker/`

It defaults to passes over Dallas; click **"Use my location"** for predictions wherever you are. Note: GitHub Pages requires the repo to be **public** on a free plan (the dashboard contains no secrets, so this is safe — your email secrets stay encrypted in Actions either way).

---

## Tuning

| What | Where | Default |
|---|---|---|
| Alert frequency | `.github/workflows/launch-alerts.yml` cron | every 6 h |
| Alert look-ahead window | `ALERT_WINDOW_HOURS` in `scripts/launch_alerts.py` | 24 h |
| Weekly email day/time | `.github/workflows/weekly-schedule.yml` cron | Mon 13:00 UTC (8 AM CDT) |
| Pass elevation threshold | `el > 10` in `docs/index.html` | 10° |
| Observer default location | `observer` object in `docs/index.html` | Dallas, TX |

Cron times are UTC. Central time is UTC−5 (CDT) / UTC−6 (CST), so a fixed UTC cron drifts one hour across daylight-saving changes.

## Repo layout

```
.github/workflows/   launch-alerts.yml, weekly-schedule.yml
scripts/             common.py, launch_alerts.py, weekly_schedule.py
state/notified.json  dedupe state (auto-committed by the alert workflow)
docs/index.html      satellite tracker dashboard (GitHub Pages)
```
