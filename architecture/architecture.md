# Architecture — SafeWatch SA

## High-level flow

```
Browser (React + Vite + Tailwind)
   │  HTTPS
   ▼
Amazon API Gateway  ── throttling, routing, access logs
   │
   ▼
AWS Lambda (Python) ── create_incident / get_incidents / update_incident /
   │                   delete_incident / create_alert / analytics
   ├──────────────► Amazon DynamoDB   (SafeWatch incidents, users, alerts)
   ├──────────────► Amazon S3         (incident evidence images, encrypted)
   ├──────────────► Amazon SNS        (community safety alerts)
   └──────────────► Amazon CloudWatch (logs, metrics, traces)
```

Locally the identical service code runs in a Flask process against SQLite:

```
Browser ──(Vite proxy /api)──► Flask (app/) ──► SQLite (services/storage.py)
```

The switch between the two is one environment variable:

```bash
STORAGE_BACKEND=sqlite      # local development
STORAGE_BACKEND=dynamodb    # AWS
```

## Backend layering

```
backend/
├── app/                  # HTTP layer (Flask blueprints)
│   ├── routes/           # auth, incidents, alerts, analytics, admin
│   ├── auth.py           # PBKDF2 hashing + JWT issue/verify + @token_required
│   ├── validation.py     # input rules (categories, severities, SA bbox)
│   └── config.py         # environment-driven configuration
├── services/             # business layer (framework-agnostic)
│   ├── storage.py        # storage facade (sqlite | dynamodb)
│   ├── dynamodb.py       # DynamoDB implementation + GSI queries
│   ├── moderation.py     # rate limits, duplicate detection, cluster alerts
│   ├── notifications.py  # SNS publish (or local log)
│   └── storage_s3.py     # presigned evidence uploads
├── lambda/               # AWS Lambda adapters over the same services
└── tests/                # pytest suite
```

The `lambda/` handlers are thin adapters: parse the API Gateway event, call the same
`services/` code, return a proxy response. That keeps local and cloud behaviour identical.

## DynamoDB table design

### `SafeWatchIncidents`

| Attribute | Type | Notes |
| --- | --- | --- |
| `incidentId` | S (PK) | `INC-YYYYMMDD-XXXXXX` |
| `userId` | S | reporter |
| `category` | S | THEFT … OTHER |
| `description` | S | 10–1000 chars |
| `latitude` / `longitude` | N | within South Africa |
| `area` | S | e.g. `Central, Gqeberha` |
| `severity` | S | LOW / MEDIUM / HIGH / CRITICAL |
| `status` | S | PENDING … REJECTED |
| `source` | S | COMMUNITY / SAPS_OFFICIAL / DEMO |
| `duplicateOf` | S | links related reports |
| `createdAt` / `updatedAt` | S | ISO-8601 UTC |

Global secondary indexes:

- `area-createdAt-index` — hotspot queries by area
- `status-index` — admin queue queries by status

`BillingMode: PAY_PER_REQUEST` (on-demand), `SSEEnabled: true`.

## Moderation state machine

```
             ┌────────────┐      ┌──────────────┐      ┌──────────┐      ┌──────────┐
  report ───►│  PENDING   │─────►│ UNDER REVIEW │─────►│ VERIFIED │─────►│ RESOLVED │
             └─────┬──────┘      └──────┬───────┘      └────┬─────┘      └──────────┘
                   │                    │                   │
                   └──────────► REJECTED ◄───────────────────┘
```

- Illegal transitions return HTTP 409.
- Only `ADMIN` role may perform transitions.

## Alert detection

`services/moderation.py::evaluate_alerts()`:

1. Load incidents from the last 2 hours.
2. Group by `area`.
3. Any group with ≥ 3 incidents becomes an alert (primary category = most common).
4. One alert per area per hour (deduplicated).
5. `publish_alert()` → Amazon SNS (AWS) or structured log (local).

An EventBridge schedule (`rate(15 minutes)`) runs the same function in AWS.

## Analytics

`app/routes/analytics.py::build_analytics()` computes, from a single scan/query:

- category / severity / status / source percentages
- time-of-day buckets (00–06, 06–12, 12–18, 18–00)
- hourly histogram
- hotspot ranking by area
- 7-day daily trend

Rejected reports are excluded from all statistics.

## Frontend structure

```
frontend/src/
├── components/    Navbar, IncidentCard, IncidentMap, AlertCard,
│                  DashboardCard, Badges, ProtectedRoute, Footer
├── pages/         Home, Login, Register, Dashboard, ReportIncident,
│                  MapPage, IncidentDetail, Alerts, Analytics, Admin, Profile
├── context/       AuthContext (JWT in localStorage, /auth/me refresh)
├── services/      api.js (fetch wrapper, auth header, error normalisation)
└── constants.js   categories, severities, statuses, areas, formatters
```

## Environments

| | Local | AWS |
| --- | --- | --- |
| Frontend | Vite dev server (5173) | Amplify |
| API | Flask (5001) via Vite proxy | API Gateway |
| Compute | Flask process | Lambda (Python 3.12) |
| Database | SQLite | DynamoDB |
| Secrets | `.env` (git-ignored) | Secrets Manager |
| Alerts | log output | SNS topic |
| Monitoring | stdout | CloudWatch + X-Ray |
