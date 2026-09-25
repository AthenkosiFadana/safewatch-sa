# User Guide — SafeWatch SA

## Getting started

1. Open the app (locally: http://localhost:5173).
2. Click **Register**, enter your name, email, password and community/area.
3. Log in — you now get the **Community Safety Dashboard**.

### Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@safewatch.co.za` | `Admin123!` |
| Member | `demo@safewatch.co.za` | `Demo123!` |

## Reporting an incident

1. Click **Report Incident**.
2. Choose the **incident type** (Theft, Robbery, Assault, Vandalism, Suspicious activity,
   Missing person, Road incident, Fire, Other).
3. Select your **area** (e.g. Central, Gqeberha).
4. Describe what happened (at least 10 characters).
5. Set the **coordinates** — or click *Use my current location*.
6. Choose a **severity**: 🟢 Low · 🟡 Medium · 🟠 High · 🔴 Critical.
7. Click **SUBMIT REPORT**.

Your report is stored with status **PENDING** and appears on the map and dashboard. If a very
similar report was already filed in the same area, yours is automatically flagged as possibly
related rather than counted twice.

> In a real emergency call **10111** or go to your nearest police station.

## Viewing the map

The **Map** page shows every non-rejected incident as a colour-coded marker:

| Colour | Severity |
| --- | --- |
| 🟢 Green | Low |
| 🟡 Yellow | Medium |
| 🟠 Orange | High |
| 🔴 Red | Critical |

Click a marker for details, or use the category / severity / area filters. Clicking a card in the
side panel selects that incident on the map.

## Safety alerts

The **Alerts** page shows community safety alerts. An alert is raised automatically when
**3 or more incidents** are reported in the same area within **2 hours**:

```
⚠️ SAFETY ALERT — Central Gqeberha
Multiple incidents have been reported in your area within the last 2 hours.
Incidents: 5   Primary category: Vehicle-related crime
Please exercise caution.
```

In AWS these alerts are published to an **Amazon SNS** topic (email/SMS subscribers).

## Analytics

The **Analytics** page shows:

- Incidents by category (bar chart)
- Severity split (donut chart)
- Incidents by time of day
- Hotspots by area
- 7-day trend line

## Admin dashboard (role: ADMIN)

- Platform totals: total / open / resolved / alerts
- Most reported categories with percentages
- **Moderation queue** — advance reports through
  `PENDING → UNDER REVIEW → VERIFIED → RESOLVED`, or **Reject** them
- **Reporter activity** — users with 5+ reports in 24 hours are flagged for review

### Moderation policy

| Status | Meaning |
| --- | --- |
| PENDING | Just submitted, not yet reviewed |
| UNDER REVIEW | A moderator is checking the report |
| VERIFIED | Confirmed as a legitimate community report |
| RESOLVED | The situation has been dealt with |
| REJECTED | Does not meet platform criteria (spam, duplicate, unverifiable) |
