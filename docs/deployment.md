# Deployment Guide — SafeWatch SA

## Local development

### Backend (Flask, port 5001)

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate     # Windows
pip install -r requirements.txt
cp .env.example .env                                # optional
python ../scripts/seed_demo.py                      # demo data + accounts
python run.py
```

Verify: `curl http://127.0.0.1:5001/api/health`

### Frontend (Vite, port 5173)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the dev server proxies `/api` to Flask (see `vite.config.js`).

### Tests

```bash
cd backend
python -m pytest tests -q
```

## AWS deployment (SAM)

### Prerequisites

- AWS account + configured credentials (`aws configure`)
- AWS SAM CLI
- Python 3.12 runtime permissions in the target region

### Deploy

```bash
cd infrastructure
sam build
sam deploy --guided
```

Suggested answers for the guided deployment:

| Prompt | Value |
| --- | --- |
| Stack Name | `safewatch-sa` |
| AWS Region | `eu-west-1` |
| Parameter EnvironmentName | `dev` |
| Parameter AlertTopicEmail | your email (confirm the SNS subscription after deploy) |
| Confirm changeset | `Y` |
| Allow SAM CLI IAM role creation | `Y` |

### What gets created

| Resource | Purpose |
| --- | --- |
| `SafeWatchApi` | API Gateway REST stage with throttling + X-Ray |
| 7 Lambda functions | create/get/update/delete incidents, alerts, analytics, schedule |
| `IncidentsTable` | DynamoDB + `area-createdAt-index` + `status-index` GSIs |
| `UsersTable`, `AlertsTable` | DynamoDB user and alert storage |
| `AlertTopic` | SNS safety alerts (+ optional email subscription) |
| `EvidenceBucket` | Encrypted S3 bucket for incident images |
| `JwtSecret` | Secrets Manager generated secret |
| `ApiLogGroup` | CloudWatch access logs (30 days) |
| `AlertSchedule` | EventBridge rule running cluster detection every 15 minutes |

### Switching the backend to DynamoDB

Set in the Lambda environment (already set by the template):

```
STORAGE_BACKEND=dynamodb
INCIDENTS_TABLE=safewatch-dev-incidents
```

Locally keep `STORAGE_BACKEND=sqlite`.

## Frontend hosting (AWS Amplify)

```bash
cd frontend
npm run build
# Connect the repository in the Amplify Console, or:
amplify init
amplify add hosting
amplify publish
```

Point the frontend at the API:

```
# frontend/.env.local
VITE_API_URL=https://<api-id>.execute-api.eu-west-1.amazonaws.com/dev
```

## Monitoring

- **CloudWatch Logs** — `/aws/lambda/safewatch-<env>-*` function logs
- **API Gateway access logs** — `/aws/apigateway/safewatch-<env>`
- **X-Ray** — trace requests across API Gateway → Lambda → DynamoDB

Useful queries:

```
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 50
```

## Rollback

```bash
sam deploy --no-execute-changeset   # inspect the changeset first
aws cloudformation describe-stack-events --stack-name safewatch-sa
aws cloudformation cancel-update-stack --stack-name safewatch-sa
```
