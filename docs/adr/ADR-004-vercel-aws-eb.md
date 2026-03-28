# ADR-004: Vercel (frontend) + AWS Elastic Beanstalk (backend)

**Status:** Accepted  
**Date:** Day 1

## Context

The app has two deployable units: a Next.js frontend and a FastAPI backend. Both need to be publicly accessible. AWS is a goal for this project — it should appear on the resume and be demonstrable in interviews.

The naive approach is to host everything on AWS (S3 + CloudFront for the frontend, Elastic Beanstalk for the API). But configuring S3 static hosting, CloudFront distributions, and cache invalidation adds significant complexity for a beginner AWS project where the main goal is demonstrating backend and infrastructure skills.

## Decision

Use **Vercel for the Next.js frontend** and **AWS Elastic Beanstalk for the FastAPI backend**.

- **Vercel** is purpose-built for Next.js. It auto-deploys on every push to `main`, requires zero configuration, handles SSL, and has a generous free tier. The frontend is live in minutes.
- **AWS Elastic Beanstalk** runs the FastAPI Docker container. This demonstrates AWS deployment, security groups, environment variables via SSM Parameter Store, and CloudWatch monitoring — the skills that matter for the resume.
- **AWS RDS** (PostgreSQL 15, `db.t3.micro`) stores all data. Security group restricts access to the EB instance only — not the public internet.

Alternatives considered:
- **S3 + CloudFront for frontend** — rejected because it adds CloudFront configuration complexity with no user-facing benefit. The resume already features AWS on the backend.
- **Heroku for backend** — rejected in favour of AWS, which is more relevant to the target job market.

## Consequences

- ✅ Frontend deploys automatically with zero config — no time lost on hosting setup
- ✅ AWS featured on the backend — EB + RDS + CloudWatch + SSM is a complete AWS story
- ✅ Both platforms have free tiers that cover the project lifetime
- ❌ Two hosting providers to manage and explain
- ❌ CORS must be configured to allow only the Vercel domain — small but necessary hardening step (Day 6)
