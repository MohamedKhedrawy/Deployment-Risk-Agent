# The Canary Whisperer — Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 20+ (required for the Dynatrace MCP server via `npx`)
- A Dynatrace SaaS environment
- A Google Gemini API key

---

## Step 1 — Configure Dynatrace OAuth Scopes

Go to: **Dynatrace → Account Management → OAuth clients → your client → Edit**

Add **ALL** of the following scopes:

| Scope | Purpose |
|---|---|
| `app-engine:apps:run` | Run Dynatrace Apps (already have this) |
| `entities.read` | Read service topology |
| `problems.read` | Read incident history |
| `metrics.read` | Read performance metrics |
| `slo.read` | Read SLO status and error budgets |
| `storage:metrics:read` | Grail metrics queries |
| `storage:logs:read` | Grail log queries |
| `storage:events:write` | Push custom deployment events |
| `storage:events:read` | Read events via DQL |
| `storage:entities:read` | Grail entity queries |
| `document:documents:read` | Read Dynatrace Notebooks |
| `document:documents:write` | Create Dynatrace Notebooks |
| `automation:workflows:read` | Read workflows |
| `automation:workflows:write` | Trigger workflows |
| `davis-copilot:conversations:execute` | Davis AI queries |

> ⚠️ After adding scopes, **regenerate the client secret** and update your `.env` file.

---

## Step 2 — Configure Environment Variables

Copy `.env.example` to `.env` and fill in all values:

```bash
cp .env.example .env
```

Then edit `.env`:

```env
# Dynatrace Environment (no trailing slash)
DT_ENVIRONMENT=https://abc12345.apps.dynatrace.com

# OAuth Client credentials
OAUTH_CLIENT_ID=dt0s02.XXXXXXXXXXXX
OAUTH_CLIENT_SECRET=your_regenerated_secret_here

# Google Gemini API key
# Get yours at: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional: Slack channel for deployment notifications
SLACK_CHANNEL=#deployments

# Demo mode (set to true to use mock data instead of live Dynatrace)
DEMO_MODE=false
```

---

## Step 3 — Install Dependencies

```bash
# Python dependencies
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Node.js dependencies (for Dynatrace MCP server)
npm install

# React frontend dependencies
cd web-ui && npm install && cd ..
```

---

## Step 4 — Verify Connection

```bash
make health
```

Expected output when everything is configured correctly:
```json
{
  "status": "ok",
  "dynatrace": "connected",
  "gemini": "ok",
  "demo_mode": false
}
```

If you see `"dynatrace": "auth_error"`, double-check your OAuth scopes and regenerate the secret.

---

## Step 5 — Run the Stack

```bash
# Start both backend + frontend
make run-all

# Or start individually
make run-api   # FastAPI on :8080
make run-ui    # React on :5173
```

Visit http://localhost:5173 to use the UI.

---

## Demo Mode

To run with pre-configured mock scenarios (no live Dynatrace required):

```bash
make demo-mode
```

Or toggle "Demo Mode" in the UI header at any time without restarting.

---

## Seed Demo Data (Optional)

To inject realistic incident history into your Dynatrace environment for demo purposes:

```bash
make seed-demo
```

This creates historical events on `payment-service` and `auth-service` to make the RISKY and FATAL scenarios more realistic.

---

## Troubleshooting

| Error | Fix |
|---|---|
| `Missing OAuth scopes` | Add all scopes listed above, regenerate secret |
| `No GOOGLE_API_KEY` | Set `GOOGLE_API_KEY` in `.env` |
| `MCP server failed to start` | Ensure Node.js 20+ is installed: `node --version` |
| `npx not found` | Install Node.js from https://nodejs.org |
| `Port 8080 in use` | Kill existing process: `lsof -ti:8080 \| xargs kill` |
