# Security Design — SafeWatch SA

Safety reports are sensitive data. This document describes the controls implemented in the
platform and the ones defined in `infrastructure/template.yaml`.

## Threat model (summary)

| Threat | Control |
| --- | --- |
| Anonymous flood of fake reports | JWT required to report + per-user hourly rate limit |
| Report spam from one account | `RATE_LIMIT_PER_HOUR` + admin reporter-activity view |
| Duplicate inflation of crime counts | Duplicate detection (same area + category + 15 min window) |
| Malicious/wrong data injection | Strict input validation (category, severity, length, SA bounding box) |
| A member tampering with moderation | Role check: only `ADMIN` can change status or delete |
| A member editing someone else's report | Ownership check on `PUT /incidents/{id}` |
| Secrets in source control | `.env` git-ignored, `.env.example` committed, JWT secret in Secrets Manager |
| Unencrypted data at rest | DynamoDB SSE, S3 SSE (AES256) |
| Public S3 bucket leak | BlockPublicAcls/BlockPublicPolicy/IgnorePublicAcls/RestrictPublicBuckets |
| API abuse / DoS | API Gateway throttling (burst 50, rate 100 rps) |
| Over-privileged cloud access | IAM least-privilege: DynamoDBCrudPolicy/SNS/S3 scoped per resource |

## Application layer

### Authentication
- Passwords hashed with **PBKDF2-HMAC-SHA256**, 120,000 iterations, per-user random salt.
- Sessions are **JWTs** (HS256) with an expiry (`TOKEN_EXPIRES_MINUTES`, default 12 hours).
- Failed logins return a generic `Invalid email or password` (no user enumeration).

### Authorisation
Two roles only:

| Capability | MEMBER | ADMIN |
| --- | --- | --- |
| View incidents/alerts/analytics | ✅ | ✅ |
| Submit report | ✅ | ✅ |
| Edit own report | ✅ | ✅ |
| Edit others' reports | ❌ | ✅ |
| Change incident status | ❌ | ✅ |
| Delete incident | ❌ | ✅ |
| View admin stats / reporter activity | ❌ | ✅ |

### Input validation (`app/validation.py`)
- Category must be one of the 9 allowed values.
- Severity must be `LOW|MEDIUM|HIGH|CRITICAL`.
- Description 10–1000 characters.
- Coordinates must fall inside the South Africa bounding box (lat −35…−22, lon 16…33).
- Area limited to 80 characters, email format checked, password minimum 8 characters.

### Anti-abuse
- `services/moderation.py` enforces a per-user hourly report limit.
- Duplicate detection flags related reports instead of counting them as separate incidents.
- The admin dashboard lists users with 5+ reports in 24 hours as "rate-limit watch".

### Data provenance
Every incident carries `source = COMMUNITY | SAPS_OFFICIAL | DEMO` so demo data can never be
mistaken for official statistics.

## Cloud layer (SAM template)

- **IAM**: each Lambda gets only the DynamoDB tables, SNS topic and S3 bucket it needs
  (`DynamoDBCrudPolicy`, `SNSPublishMessagePolicy`, `S3WritePolicy`).
- **Encryption at rest**: DynamoDB `SSEEnabled`, S3 `AES256`, JWT secret in Secrets Manager.
- **Transport**: API Gateway serves HTTPS only.
- **Storage hygiene**: S3 public access blocked entirely; evidence objects expire after 180 days.
- **Monitoring**: API access logs to CloudWatch (30-day retention), X-Ray tracing enabled.
- **Throttling**: `MethodSettings` burst/rate limits on every route.

## Responsible-use principles

- AI (future phase) may *suggest* classification for moderator review — it must never decide
  guilt or automatically accuse individuals.
- The platform does not publish personal identifying details of suspects.
- Emergency guidance (10111 / nearest SAPS station) is displayed wherever incidents are reported.
