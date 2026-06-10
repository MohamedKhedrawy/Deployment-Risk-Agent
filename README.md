# 🐤 The Canary Whisperer

> **Pre-deployment risk simulation** — Before you ship a feature, an agent simulates its rollout across production topology, predicts which users will be impacted, models the blast radius, and writes the go/no-go decision — with evidence.

Built for the [Google Cloud Rapid Agent Development Hackathon](https://rapid-agent.devpost.com/) on the **Dynatrace MCP** partner track.

## 🏗️ Architecture

```
Feature Description → Agent Pipeline → Risk Report
                         ↕
                   Dynatrace MCP
              (topology + incidents + SLOs)
```

**Stack:** Google ADK · Gemini · Dynatrace MCP · FastAPI · Streamlit · Cloud Run

## ⚡ Quick Start

### Prerequisites
- Python 3.12+
- Dynatrace environment with OAuth credentials (optional — mock mode works without it)

### Setup

```bash
# Clone and enter the project
git clone https://github.com/yourusername/canary-whisperer.git
cd canary-whisperer

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install .

# Copy and fill in your environment variables
cp .env.example .env
# Edit .env with your Dynatrace and Google API credentials
```

### Run the UI and API (Demo Mode)

```bash
make run-demo
```

Open http://localhost:5173 to view the React frontend.

Pick a scenario from the sidebar:
- 🟢 **Safe** — Add dark mode toggle to user preferences panel → GO
- 🟡 **Risky** — Integrate loyalty points into the checkout flow → GO WITH CONDITIONS
- 🔴 **Fatal** — Migrate authentication service to new OAuth2 provider → NO-GO

### Run the FastAPI API separately

```bash
make run-api
```

Open http://localhost:8000/docs for the Swagger UI.

### Run with Google ADK

```bash
cd canary-agent
adk web
```

### Run Tests

```bash
pip install ".[dev]"
pytest -v
```

## 🎯 How It Works

### The 4-Step Analysis Pipeline

| Step | What the Agent Does | Data Source |
|------|-------------------|-------------|
| **1. Map Topology** | Finds all services the feature touches and their dependencies | Dynatrace Smartscape |
| **2. Check Health** | Pulls recent incidents, error rates, SLO status per service | Dynatrace Problems + DQL |
| **3. Assess Risk** | Scores fragility, estimates blast radius, identifies top risks | Internal scoring algorithm |
| **4. GO/NO-GO** | Makes a deployment recommendation with conditions and evidence | Report builder |

### Risk Scoring Algorithm

Each service is scored on four factors:

```
fragility_score = (incident_history × 0.40) +
                  (current_error_rate × 0.25) +
                  (slo_burn_rate × 0.25) +
                  (dependency_depth × 0.10)
```

### Demo Moment

> "I want to deploy a new checkout feature that adds loyalty points calculation during payment."

The agent:
1. Pulls Dynatrace topology → finds `checkout-service` → `payment-service` → `loyalty-db`
2. Finds **3 historical incidents** on `payment-service` during peak load
3. `loyalty-db` SLO at **97.2%** (dangerously close to 97% target)
4. Blast radius: **23% of users** affected if payment-service degrades
5. **Output:** "GO WITH CONDITIONS — Ship after 8pm, cap at 5% canary rollout, monitor these 4 metrics"

## 📁 Project Structure

```
canary-whisperer/
├── agent/                  # Core agent logic and mock data
│   ├── orchestrator.py     # 4-step analysis pipeline
│   ├── tools.py            # ADK tool wrappers
│   ├── analyzer.py         # Fragility scorer
│   ├── mock_data.py        # Demo scenarios
│   └── report.py           # Report builder
├── dtmcp/                  # Dynatrace integration
│   ├── dynatrace_client.py # MCP client
│   └── schema.py           # Pydantic models
├── api/                    # FastAPI REST layer
│   ├── main.py             # Endpoints
│   ├── models.py           # Request/response models
│   └── dependencies.py     # Config + DI
├── web-ui/                 # React + Vite frontend
│   ├── src/                # UI source code and components
│   └── package.json        # Frontend dependencies
├── canary_agent/           # ADK agent definition
│   └── mcp_runner.py       # Root agent for MCP
├── tests/                  # Test suite
├── Dockerfile              # Cloud Run container
├── cloudbuild.yaml         # GCP CI/CD pipeline
└── .github/workflows/      # PR risk analysis bot
```

## 🚀 Deployment

### Cloud Run (Production)

```bash
# Build and deploy
gcloud builds submit --config cloudbuild.yaml

# Or deploy manually
docker build -t canary-whisperer .
docker run -p 8080:8080 canary-whisperer
```

### Environment Variables

| Variable | Description | Required |
|----------|------------|----------|
| `DT_ENVIRONMENT` | Dynatrace environment URL | For live mode |
| `OAUTH_CLIENT_ID` | Dynatrace OAuth client ID | For live mode |
| `OAUTH_CLIENT_SECRET` | Dynatrace OAuth secret | For live mode |
| `GOOGLE_API_KEY` | Google API key for Gemini | For ADK mode |
| `DEMO_MODE` | Use mock data (default: false) | No |

## 📜 License

MIT
