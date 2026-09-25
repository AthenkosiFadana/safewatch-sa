# 🇿🇦 SafeWatch SA

[![CI](https://github.com/AthenkosiFadana/safewatch-sa/actions/workflows/ci.yml/badge.svg)](https://github.com/AthenkosiFadana/safewatch-sa/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Community Crime & Safety Monitoring Platform**

> See it. Report it. Stay informed.

SafeWatch SA is a cloud-based community safety monitoring platform designed to help communities
report, visualise and monitor safety incidents while providing timely community alerts and
data-driven insights.

---

## Problem

Crime and safety concerns affect communities across South Africa. SAPS reported **664,758
contact-crime cases in 2024/25**, and its crime-statistics system exists to support planning and
policy through better crime data.

Residents often have no easy way to see what is happening around them in near-real time, or to
share safety information with their neighbours.

## Solution

SafeWatch SA gives communities one place to:

- 🚨 **Report** safety incidents (theft, robbery, vandalism, suspicious activity, and more)
- 🗺️ **Visualise** incidents on an interactive, severity-coloured map
- 🔔 **Receive** automatic community safety alerts when incidents cluster in an area
- 📊 **Analyse** crime patterns by category, time of day, severity and hotspot area
- 🛡️ **Moderate** reports through a PENDING → UNDER REVIEW → VERIFIED → RESOLVED workflow

> ⚠️ **SafeWatch SA does not replace SAPS.** In an emergency call **10111** or visit your nearest
> police station. SafeWatch SA is a community information, monitoring, alerting and analytics
> platform.

---

## Features

| Feature | Description |
| --- | --- |
| User accounts | Register, login, profile management, community/area selection (JWT auth) |
| Incident reporting | 9 incident categories, geolocation, severity, validation, rate limiting |
| Interactive map | Leaflet/OpenStreetMap markers coloured 🟢🟡🟠🔴 by severity |
| Safety alerts | Automatic cluster detection (3+ incidents / area / 2 hours) + SNS publishing |
| Moderation | Status workflow, duplicate detection, per-user report limits, admin queue |
| Analytics | Category splits, time-of-day buckets, hotspots, 7-day trend |
| Admin dashboard | Platform stats, moderation queue, reporter abuse flags |
| Data provenance | Every record tagged `source = COMMUNITY \| SAPS_OFFICIAL \| DEMO` |

---

## Architecture

```
                   ┌─────────────────┐
                   │      User       │
                   └────────┬────────┘
                            ▼
                  ┌──────────────────┐
                  │  React + Vite    │  Frontend
                  │  Tailwind CSS    │  (S3 static website)
                  │  Leaflet, Recharts
                  └────────┬─────────┘
                           ▼
                  ┌──────────────────┐
                  │   Amazon API     │  REST API + throttling
                  │   Gateway        │
                  └────────┬─────────┘
                           ▼
                  ┌──────────────────┐
                  │   AWS Lambda     │  Python handlers
                  │  (create/get/    │
                  │   update/delete/ │
                  │   alerts/analytics)
                  └───┬──────┬────┬──┘
                      ▼      ▼    ▼
              ┌──────────┐ ┌────┐ ┌──────────┐
              │DynamoDB  │ │ S3 │ │   SNS    │
              │incidents │ │evid│ │  alerts  │
              │users     │ │ence│ │          │
              │alerts    │ └────┘ └──────────┘
              └──────────┘
                      │
                      ▼
               ┌──────────────┐
               │ CloudWatch   │  logs, metrics, API tracing
               │ IAM          │  least-privilege execution roles
               └──────────────┘
```

Locally the same service code runs against **SQLite**, so the project runs with zero cloud
credentials (`STORAGE_BACKEND=sqlite`), and switches to DynamoDB with one environment variable
(`STORAGE_BACKEND=dynamodb`).

## AWS Services

| Service | What SafeWatch uses it for |
| --- | --- |
| Amazon S3 | Static website hosting for the React frontend |
| Amazon API Gateway | REST API, throttling, request routing |
| AWS Lambda | Python backend functions |
| Amazon DynamoDB | Incident, user and alert data (GSIs for hotspots/status) |
| Amazon S3 | Incident evidence images (encrypted, block-public-access) |
| Amazon Cognito | User authentication / federation (JWT authoriser) |
| Amazon SNS | Safety alert notifications (email/SMS) |
| Amazon CloudWatch | Logs, metrics, API access logs |
| AWS IAM | Least-privilege Lambda execution roles |
| AWS SAM / CloudFormation | Infrastructure as code (`infrastructure/template.yaml`) |

## Tech Stack

**Frontend:** React 19 + Vite, Tailwind CSS, React Router, Leaflet/OpenStreetMap, Recharts
**Backend:** Python 3.11, Flask, PyJWT, boto3
**Database:** SQLite (local) / Amazon DynamoDB (AWS)
**Cloud:** AWS (SAM, Lambda, API Gateway, SNS, S3, CloudWatch, IAM)

---

## Installation

### Prerequisites

- Node.js 20+
- Python 3.11+
- (Optional) AWS SAM CLI + AWS credentials for cloud deployment

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
python ../scripts/seed_demo.py        # demo data + test accounts
python run.py                         # API on http://127.0.0.1:5001
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                           # http://localhost:5173
```

The Vite dev server proxies `/api` to the Flask backend.

### Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@safewatch.co.za` | `Admin123!` |
| Member | `demo@safewatch.co.za` | `Demo123!` |

### 3. Tests

```bash
cd backend
python -m pytest tests -q
```

### 4. Deploy to AWS

```bash
cd infrastructure
sam build
sam deploy --guided
```

---

## API Reference

| Method | Endpoint | Auth | Description |
| --- | --- | --- | --- |
| GET | `/api/health` | – | Service health |
| POST | `/api/auth/register` | – | Create account |
| POST | `/api/auth/login` | – | Get JWT |
| GET | `/api/auth/me` | JWT | Current user |
| PUT | `/api/auth/profile` | JWT | Update profile |
| GET | `/api/incidents` | – | List/filter incidents |
| POST | `/api/incidents` | JWT | Report an incident |
| GET | `/api/incidents/{id}` | – | Incident detail |
| PUT | `/api/incidents/{id}` | JWT | Edit own report |
| PUT | `/api/incidents/{id}/status` | ADMIN | Moderate status |
| DELETE | `/api/incidents/{id}` | ADMIN | Remove report |
| GET | `/api/alerts` | – | List safety alerts |
| POST | `/api/alerts/check` | JWT | Run cluster detection |
| POST | `/api/alerts` | ADMIN | Publish manual alert |
| GET | `/api/analytics` | – | Crime analytics |
| GET | `/api/admin/stats` | ADMIN | Admin statistics |
| GET | `/api/admin/reports` | ADMIN | Reporter activity |

---

## Data sources

To stay honest about the data, every incident carries a `source` field:

| Source | Meaning |
| --- | --- |
| `COMMUNITY` | Reported by a SafeWatch SA user |
| `SAPS_OFFICIAL` | Imported published SAPS statistics (where appropriate) |
| `DEMO` | Synthetic development/test data |

Demo data is **not** official crime statistics and is never presented as such.

---

## Security

- **IAM least privilege** — the frontend never talks to DynamoDB directly; only Lambda roles can
- **JWT auth** with role-based authorisation (`MEMBER` / `ADMIN`)
- **Input validation** on every write endpoint (categories, severity, SA bounding box, lengths)
- **Rate limiting** — max reports per user per hour
- **Duplicate detection** — related reports are flagged instead of inflating counts
- **Encryption** — DynamoDB SSE, S3 SSE, Secrets Manager for the JWT secret
- **S3** — block public access, lifecycle expiry on evidence
- **API throttling** — burst/rate limits on API Gateway
- **CloudWatch** — logs, metrics and API access logs

See [docs/security.md](docs/security.md) for the full breakdown.

---

## Project roadmap

- [x] Phase 1 — Foundation & project structure
- [x] Phase 2 — Frontend (landing, auth, dashboard, report, map, alerts, admin)
- [x] Phase 3 — Backend Python API
- [x] Phase 4 — Database + demo seed data
- [x] Phase 5 — Authentication (JWT)
- [x] Phase 6 — Interactive map
- [x] Phase 7 — Alerts + analytics
- [x] Phase 8 — Admin moderation dashboard
- [x] Phase 9 — AWS SAM infrastructure as code
- [x] Phase 10 — Testing (pytest)
- [x] Phase 11 — Documentation
- [ ] Phase 12 — Live AWS deployment
- [ ] Phase 13 — Amazon Bedrock-assisted classification (assisted, not decisive)

## Future improvements

- Amazon Cognito user pools + federated sign-in
- Amazon Bedrock to *suggest* category/severity for moderator review
- Progressive Web App (PWA) + offline report queue
- SMS delivery of alerts via SNS for low-data areas
- Official SAPS statistics import pipeline with provenance metadata

---

## AWS re/Start skills demonstrated

| AWS re/Start skill | Demonstrated by SafeWatch SA |
| --- | --- |
| Linux | Development/deployment environment |
| Python | Lambda backend |
| Networking | API Gateway, HTTP, cloud architecture |
| Security | IAM, Cognito, least privilege, encryption |
| Databases | DynamoDB table + GSI design |
| Cloud Computing | Serverless AWS architecture |
| Automation | SAM / infrastructure as code |
| Monitoring | CloudWatch logs & metrics |
| Storage | S3 evidence bucket |
| Application development | React + Python |
| APIs | API Gateway + Lambda |
| Troubleshooting | CloudWatch log analysis |
| Git/GitHub | Version control |
| Documentation | Professional README + docs |

---

## Author

**Athenkosi Fadana**

## License

MIT — see [LICENSE](LICENSE).
