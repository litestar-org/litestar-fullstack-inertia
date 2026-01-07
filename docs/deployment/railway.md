# Deploying to Railway

This guide covers deploying the Litestar Fullstack Inertia application to [Railway](https://railway.app), a modern cloud platform with seamless Git integration and usage-based pricing.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Manual Setup](#manual-setup)
- [Service Architecture](#service-architecture)
- [Environment Variables](#environment-variables)
- [Email Configuration](#email-configuration)
- [Database Management](#database-management)
- [Monitoring and Logs](#monitoring-and-logs)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Railway Account

1. Sign up at [railway.app](https://railway.app)
2. Add a payment method to enable deployments

### Local Requirements

- **Node.js 18+**: Required for Railway CLI
- **Git**: For version control and deployment
- **OpenSSL**: For generating secret keys (optional)

### Email Credentials (Resend)

For email functionality, we recommend [Resend](https://resend.com):
- **Free tier**: 3,000 emails/month
- Simple API key authentication
- No SMTP ports required (works on any Railway plan)

Get your API key at: [resend.com/api-keys](https://resend.com/api-keys)

## Quick Start

The fastest way to deploy is using the provided setup scripts:

```bash
# Navigate to the railway deployment directory
cd tools/deploy/railway

# Run the setup script (creates project, provisions database)
./setup.sh my-demo-app

# Configure Resend for email (optional, interactive)
./env-setup.sh --email

# Deploy the application
./deploy.sh
```

After deployment, open your Railway dashboard:

```bash
railway open
```

## Manual Setup

If you prefer manual setup or need more control:

### 1. Install Railway CLI

```bash
npm install -g @railway/cli
```

### 2. Authenticate

```bash
railway login
```

### 3. Create Project

```bash
# From the project root directory
railway init --name litestar-fullstack-demo
```

### 4. Provision PostgreSQL

```bash
railway add --database postgres
```

### 5. Configure Environment Variables

```bash
# Generate a secret key
SECRET_KEY=$(openssl rand -base64 32)

# Set essential variables
railway variables set SECRET_KEY="${SECRET_KEY}"
railway variables set LITESTAR_DEBUG=false
railway variables set VITE_DEV_MODE=false

# For email (using Resend)
railway variables --set "EMAIL_ENABLED=true"
railway variables --set "EMAIL_BACKEND=resend"
railway variables --set "EMAIL_FROM=noreply@yourdomain.com"
railway variables --set "RESEND_API_KEY=re_xxxxxxxxxxxx"
```

### 6. Link and Deploy

```bash
railway link
railway up
```

### 7. Run Migrations

```bash
railway run litestar database upgrade --no-prompt
```

## Service Architecture

Railway deploys your application as a containerized service:

```
┌─────────────────────────────────────────────────────┐
│                   Railway Project                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────┐    ┌──────────────────┐       │
│  │   App Service    │───▶│   PostgreSQL     │       │
│  │  (Dockerfile)    │    │   (Database)     │       │
│  │                  │    │                  │       │
│  │  Port: $PORT     │    │  Port: 5432      │       │
│  │  /health         │    │                  │       │
│  └──────────────────┘    └──────────────────┘       │
│           │                                          │
│           ▼                                          │
│  ┌──────────────────┐                               │
│  │  Public Domain   │                               │
│  │  *.up.railway.app│                               │
│  └──────────────────┘                               │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### How It Works

1. **Build**: Railway uses the distroless Dockerfile for maximum security
2. **Database**: PostgreSQL is provisioned and `DATABASE_URL` is injected
3. **Pre-Deploy**: Migrations run automatically before the new version goes live
4. **Deploy**: Container starts with the configured start command
5. **Health**: Railway monitors `/health` endpoint for service health
6. **Routing**: Traffic is routed through Railway's edge network

### Configuration Files

| File | Purpose |
|------|---------|
| `railway.json` | Build and deploy configuration |
| `tools/deploy/docker/Dockerfile` | Container image definition |
| `.env.railway.example` | Environment variable template |

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Application secret for sessions/tokens | Auto-generated |
| `DATABASE_URL` | PostgreSQL connection string | Injected by Railway |

### Application Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LITESTAR_DEBUG` | `false` | Debug mode (always false in prod) |
| `LITESTAR_HOST` | `0.0.0.0` | Bind address |
| `LITESTAR_PORT` | `$PORT` | Port (injected by Railway) |
| `APP_NAME` | `"app"` | Application display name |
| `APP_URL` | - | Public URL of deployment |
| `VITE_DEV_MODE` | `false` | Vite development mode |

### Database Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | - | Full connection string (injected) |
| `DATABASE_POOL_SIZE` | `5` | Connection pool size |
| `DATABASE_POOL_MAX_OVERFLOW` | `10` | Max overflow connections |
| `DATABASE_POOL_TIMEOUT` | `30` | Connection timeout (seconds) |

### Email Variables (Resend)

| Variable | Default | Description |
|----------|---------|-------------|
| `EMAIL_ENABLED` | `false` | Enable email sending |
| `EMAIL_BACKEND` | `console` | Backend: `resend`, `console` |
| `EMAIL_FROM` | `noreply@example.com` | Sender address (must be verified in Resend) |
| `RESEND_API_KEY` | - | Your Resend API key |

### Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `REGISTRATION_ENABLED` | `true` | Allow new user registration |
| `MFA_ENABLED` | `false` | Enable MFA features |
| `CSRF_COOKIE_SECURE` | `false` | Secure CSRF cookies (set true) |

## Email Configuration

We recommend [Resend](https://resend.com) for email delivery:

- **Free tier**: 3,000 emails/month
- **Simple setup**: Just an API key
- **No SMTP ports**: Works on any Railway plan (uses HTTP API)

### Resend Setup

1. **Create Account** at [resend.com](https://resend.com)

2. **Verify Your Domain** (or use Resend's test domain for development):
   - Go to Domains → Add Domain
   - Add the DNS records to your domain

3. **Get API Key**:
   - Go to [API Keys](https://resend.com/api-keys)
   - Create a new API key

4. **Configure Railway**:

```bash
railway variables --set "EMAIL_ENABLED=true"
railway variables --set "EMAIL_BACKEND=resend"
railway variables --set "EMAIL_FROM=noreply@yourdomain.com"
railway variables --set "RESEND_API_KEY=re_xxxxxxxxxxxx"
```

Or use the interactive setup:

```bash
./env-setup.sh --email
```

### Testing Email

After configuring Resend, test email delivery:

```bash
# SSH into container
railway run bash

# Test using Python
python -c "
from app import config
from app.domain.web.email import EmailMessageService
import asyncio

async def test():
    async with config.email.provide_service() as mailer:
        service = EmailMessageService(mailer=mailer)
        result = await service.send_email(
            to_email='test@example.com',
            subject='Railway Test',
            html_content='<p>Email is working!</p>'
        )
        print('Sent:', result)

asyncio.run(test())
"
```

## Database Management

### Automatic Migrations

Migrations run automatically on each deployment via `preDeployCommand` in `railway.json`. This ensures your database schema is always up-to-date before the new version goes live.

### Manual Migrations (if needed)

```bash
# Via Railway CLI (for troubleshooting)
railway run litestar database upgrade --no-prompt
```

### Creating Migrations

```bash
# Locally (with DATABASE_URL set)
uv run app database make-migrations

# Commit and deploy
git add app/db/migrations/
git commit -m "Add migration"
railway up
```

### Database Backups

Railway doesn't include automatic backups. Consider:

1. **Manual Backups**:

```bash
# Get connection details
railway variables

# Backup using pg_dump
pg_dump $DATABASE_URL > backup.sql
```

2. **Automated Backups**: Use a service like [pgBackRest](https://pgbackrest.org/) or Railway's volume snapshots (Pro feature)

### Connection Pooling

For production, configure appropriate pool sizes:

```bash
railway variables set DATABASE_POOL_SIZE=10
railway variables set DATABASE_POOL_MAX_OVERFLOW=20
```

## Monitoring and Logs

### Viewing Logs

```bash
# Stream live logs
railway logs

# Follow logs
railway logs -f

# Filter by deployment
railway logs --deployment <deployment-id>
```

### Health Checks

The application exposes a `/health` endpoint:

```bash
curl https://your-app.up.railway.app/health
# Response: {"status": "ok"}
```

Railway uses this endpoint to:
- Determine when the service is ready to receive traffic
- Monitor ongoing health
- Trigger restarts on failures

### Railway Dashboard

Access monitoring via the Railway dashboard:

```bash
railway open
```

Features available:
- Deployment history
- Resource usage (CPU, Memory)
- Environment variables
- Log viewer
- Metrics (Pro plan)

### Setting Up Alerts

Railway supports alerts via integrations:
1. Go to Project Settings → Integrations
2. Connect Slack, Discord, or webhooks
3. Configure notification triggers

## Troubleshooting

### Common Issues

#### Deployment Fails

```bash
# Check build logs
railway logs --build

# Verify Dockerfile path in railway.json
cat railway.json

# Test Docker build locally
docker build -f tools/deploy/docker/Dockerfile -t test .
```

#### Database Connection Errors

```bash
# Verify DATABASE_URL is set
railway variables

# Test connection
railway run python -c "
from sqlalchemy import create_engine
import os
e = create_engine(os.environ['DATABASE_URL'].replace('+asyncpg', ''))
print(e.connect())
"
```

#### Email Not Working

1. **Check API Key**: Verify your Resend API key is correct
2. **Verify Domain**: Ensure your sending domain is verified in Resend
3. **Check From Address**: The FROM address must match a verified domain
4. **Review Logs**: Look for email-related errors in logs

#### Health Check Failures

```bash
# Test health endpoint locally
curl http://localhost:8000/health

# Check container startup
railway logs | grep -i health

# Verify PORT handling
railway run env | grep PORT
```

#### Out of Memory

```bash
# Check memory usage
railway status

# Optimize pool size
railway variables set DATABASE_POOL_SIZE=3
railway variables set DATABASE_POOL_MAX_OVERFLOW=5
```

### Debug Commands

```bash
# SSH into running container
railway run bash

# Check environment
railway run env

# Run Python shell
railway run python

# Test database connection
railway run litestar database show-current-revision

# Check installed packages
railway run pip list
```

### Getting Help

- **Railway Documentation**: [docs.railway.com](https://docs.railway.com)
- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)
- **Railway Status**: [status.railway.app](https://status.railway.app)

## Quick Reference

### Essential Commands

```bash
# Setup
railway login                    # Authenticate
railway init                     # Create project
railway add --database postgres  # Add PostgreSQL
railway link                     # Link to existing project

# Deploy
railway up                       # Deploy
railway up --detach              # Deploy without waiting

# Management
railway variables                # List variables
railway variables set KEY=value  # Set variable
railway logs                     # View logs
railway open                     # Open dashboard
railway run <command>            # Run command in container

# Database
railway run litestar database upgrade --no-prompt  # Migrate
```

### Files Reference

```
project-root/
├── railway.json                          # Railway configuration
├── tools/deploy/
│   ├── docker/
│   │   └── Dockerfile                    # Production Dockerfile
│   └── railway/
│       ├── setup.sh                      # Initial setup script
│       ├── deploy.sh                     # Deployment script
│       ├── env-setup.sh                  # Environment configuration
│       └── .env.railway.example          # Environment template
└── docs/deployment/
    └── railway.md                        # This guide
```
