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
- Python 3.11 runtime permissions in the target region

### Template parameters

| Parameter | Default | Purpose |
| --- | --- | --- |
| `EnvironmentName` | `dev` | Suffix for resource names (`safewatch-dev-*`) |
| `JwtSecretValue` | *(empty)* | JWT signing secret — pass `openssl rand -hex 32` |
| `LambdaRoleArn` | *(empty)* | Reuse an existing execution role (e.g. a pre-provisioned lab role) instead of creating one |
| `ApiMode` | `apigateway` | `apigateway` = REST API; `functionurl` = one Lambda Function URL serving the whole Flask app (for accounts where `apigateway:POST` is denied) |
| `EnableAlertSchedule` | `true` | EventBridge rule for cluster detection — set `false` in accounts where `events:DeleteRule` is denied so the stack stays deletable |
| `AlertTopicEmail` | *(empty)* | Optional SNS email subscription |

### Deploy

```bash
cd infrastructure
sam build
sam deploy --stack-name safewatch-sa --region us-west-2 \
  --capabilities CAPABILITY_NAMED_IAM --resolve-s3 \
  --parameter-overrides EnvironmentName=dev \
    JwtSecretValue=$(openssl rand -hex 32) \
    LambdaRoleArn=arn:aws:iam::<account>:role/<existing-role> \
    ApiMode=functionurl EnableAlertSchedule=false
```

### What gets created

| Resource | Purpose |
| --- | --- |
| `SafeWatchApi` *(ApiMode=apigateway)* | API Gateway REST stage with throttling + X-Ray |
| `ApiRouterFunction` + `ApiRouterUrl` *(ApiMode=functionurl)* | Single Lambda running the full Flask app behind a public Function URL (CORS `*`) |
| 6–7 Lambda functions | create/get/update/delete incidents, alerts, analytics, schedule |
| `IncidentsTable` | DynamoDB + `area-createdAt-index` + `status-index` GSIs |
| `UsersTable`, `AlertsTable` | DynamoDB user storage (+ `email-index` GSI for logins) and alert storage |
| `AlertTopic` | SNS safety alerts (+ optional email subscription) |
| `EvidenceBucket` | Encrypted S3 bucket for incident images |
| `JwtSecretValue` | JWT secret supplied as a NoEcho parameter (no Secrets Manager dependency) |
| `ApiLogGroup` | CloudWatch access logs (30 days) |
| `AlertSchedule` *(EnableAlertSchedule=true)* | EventBridge rule running cluster detection every 15 minutes |

### Verify a deployment

```bash
curl https://<function-url>/api/health
curl -X POST https://<function-url>/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@safewatch.co.za","password":"Demo123!"}'
```

### Seed the cloud database

```bash
$env:STORAGE_BACKEND="dynamodb"          # PowerShell
$env:AWS_REGION="us-west-2"
$env:INCIDENTS_TABLE="safewatch-dev-incidents"
$env:USERS_TABLE="safewatch-dev-users"
$env:ALERTS_TABLE="safewatch-dev-alerts"
python scripts/seed_demo.py
```

### Switching the backend to DynamoDB

Set in the Lambda environment (already set by the template):

```
STORAGE_BACKEND=dynamodb
INCIDENTS_TABLE=safewatch-dev-incidents
USERS_TABLE=safewatch-dev-users
ALERTS_TABLE=safewatch-dev-alerts
```

Locally keep `STORAGE_BACKEND=sqlite`.

## Frontend hosting (S3 static website)

The stack creates `FrontendBucket` — a public S3 static website with
`index.html` as both the index and error document (SPA routing).

```bash
cd frontend
npm run build
aws s3 sync dist s3://<FrontendBucket> --delete
```

The bucket name is in the stack output `FrontendWebsiteUrl`, e.g.
`http://safewatch-sa-frontendbucket-<id>.s3-website-<region>.amazonaws.com`.

The production bundle reads `VITE_API_URL` at **build** time, so set it (or
`frontend/.env.local`) before running `npm run build`:

```
VITE_API_URL=https://<function-url>            # ApiMode=functionurl
VITE_API_URL=https://<api-id>.execute-api.<region>.amazonaws.com/dev   # ApiMode=apigateway
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
