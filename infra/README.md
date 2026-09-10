# Infra — Wealth Intelligence AI

Deployment targets AWS, multi-AZ, with **region-parameterized** IaC so Qatari
client data can be pinned in-region (see docs/01-architecture.md §1.4).

## Topology (target)

```
Route 53 ── CloudFront ── ALB
                           ├── ECS/Fargate: backend (FastAPI)  [multi-AZ]
                           └── ECS/Fargate: frontend (Next.js) [multi-AZ]
Backend →  RDS Postgres (Multi-AZ)         raw facts + entities
        →  ElastiCache Redis               rate limits, cache, queues
        →  S3                              data lake (raw docs, filings)
        →  OpenSearch / pgvector           RAG vector index (region-partitioned)
        →  SQS + workers                   async reports, monitoring agents
        →  Secrets Manager + KMS           secrets, encryption keys
        →  CloudWatch + OpenTelemetry      logs, traces, metrics
Audit  →  WORM-configured store (S3 Object Lock)  immutable audit records
```

## Region & residency

- `region` is a variable. A Qatar deployment pins storage + compute to an
  in-region zone; `data_region` on each `Organization` routes its data.
- The RAG vector index and the raw stores are partitioned by `data_region` so a
  tenant's data never crosses its residency boundary.

## Environments

`dev` (docker-compose, in-memory/stub) → `staging` → `prod`. Promotion is
image-based; migrations run as a pre-deploy step.

## What's here

This directory holds IaC **stubs and notes** only. Add Terraform/CDK modules
per component as the platform hardens (MVP uses docker-compose locally; see the
repo-root `docker-compose.yml`).

## Security controls (SOC 2 / ISO 27001 direction)

- Encryption at rest (KMS) and in transit (TLS 1.2+).
- Least-privilege IAM per service; no long-lived keys in images.
- RBAC enforced in the API (scopes/roles); audit log immutable (Object Lock).
- Secrets only via Secrets Manager; never in env files committed to git.
