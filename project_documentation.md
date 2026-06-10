# The Canary Whisperer: Comprehensive Project Documentation

**The Canary Whisperer** is a pre-deployment risk simulation agent designed for the Google Cloud Rapid Agent Development Hackathon. Its primary goal is to assess the risk of rolling out a new feature before it reaches production. It accomplishes this by mapping the production topology, assessing the historical and current health of affected services, simulating the potential blast radius of a failure, and issuing a GO/NO-GO deployment decision.

---

## 1. Project Architecture

The project employs a multi-layered architecture:

1. **Agent Definition Layer (`canary-agent/`)**: Contains the Google Cloud ADK (Agent Development Kit) agent definition, using the Gemini model and connected to a Dynatrace MCP (Model Context Protocol) toolset.
2. **Business Logic Layer (`agent/`)**: The core programmatic implementation of the 4-step risk analysis pipeline (Orchestrator, Analyzer, Simulator, Report Builder).
3. **Data Integration Layer (`dtmcp/`)**: Handles communication with Dynatrace (either live via OAuth or using rich mock data) to retrieve topology, metrics, incidents, and SLO status.
4. **API Layer (`api/`)**: A FastAPI REST interface that exposes the analysis pipeline to external clients.
5. **UI Layer (`ui/`)**: A Streamlit dashboard that provides an interactive, visual interface for users (and hackathon judges) to evaluate different deployment scenarios.

---

## 2. The 4-Step Analysis Pipeline

The core logic of The Canary Whisperer operates in a strict 4-step pipeline, implemented programmatically in `agent/orchestrator.py` (`AnalysisPipeline`) and instructively in the LLM prompt (`canary-agent/agent.py`).

### Step 1: Map the Topology
- **Goal**: Identify the specific services that the new feature will touch and their downstream dependencies.
- **How it works**: The Orchestrator receives a feature description. It uses keyword/phrase heuristics (e.g., matching "checkout" to `SERVICE-CHECKOUT`) to find the primary affected services. It then queries the `DynatraceClient`'s topology data to find all dependencies (e.g., database services, payment gateways).

### Step 2: Check Historical Health
- **Goal**: Evaluate the stability of the affected services.
- **How it works**: For every service identified in Step 1, the pipeline fetches:
  - **Incidents**: Recent problems (last 30 days) and currently active/open incidents.
  - **Metrics**: Current error rates and response times.
  - **SLOs (Service Level Objectives)**: Current SLO compliance and remaining error budgets.

### Step 3: Assess the Risk
- **Goal**: Quantify the risk using a scoring algorithm and simulate the blast radius.
- **How it works**: 
  - **Fragility Scorer (`agent/analyzer.py`)**: Calculates a score for each service based on incident history (40%), current error rate (25%), SLO burn rate (25%), and dependency depth (10%).
  - **Blast Radius Simulator (`agent/simulator.py`)**: Estimates the impact if the primary service were to fail. It calculates the total number of affected downstream services and estimates the percentage of users impacted based on the critical path.

### Step 4: GO/NO-GO Decision
- **Goal**: Synthesize findings into an actionable deployment recommendation.
- **How it works**: The **Report Builder (`agent/report.py`)** aggregates the scores. Depending on the highest service risk score and active incidents:
  - `GO`: Everything is safe.
  - `GO_WITH_CONDITIONS`: Safe, but requires safeguards (e.g., 5% canary rollout, specific time windows).
  - `NO_GO`: Critical risks found (e.g., active incidents, breached SLOs). Do not deploy.

---

## 3. Code Walkthrough by Directory

### `canary-agent/agent.py`
This is the root agent definition for the Google ADK. It connects to the Dynatrace MCP server (`@dynatrace-oss/dynatrace-mcp-server@latest`) and defines the system prompt. The prompt acts as the "brain" when running in pure LLM mode, instructing the Gemini model to follow the 4-step process and formatting its output to provide a clear decision and summary.

### `agent/orchestrator.py`
The `AnalysisPipeline` class is the programmatic heart of the system. It asynchronously executes the 4 steps:
1. `_identify_affected_services()`: Parses the feature description.
2. Fetches incidents, SLOs, and metrics from the `DynatraceClient`.
3. Calls the `FragilityScorer` and `BlastRadiusSimulator`.
4. Uses `ReportBuilder` to construct a final `RiskReport` object containing the decision and reasoning chain.

### `dtmcp/` (Dynatrace Integration)
- **`dynatrace_client.py`**: The client that fetches data. It supports a `mock_mode` which is crucial for predictable hackathon demos.
- **`mock_data.py`**: Contains hardcoded scenarios (Safe, Risky, Fatal). For example, the "Risky" scenario simulates deploying loyalty points to a payment service with an unstable database, ensuring the system outputs a `GO_WITH_CONDITIONS` result.
- **`schema.py`**: Pydantic models (e.g., `RiskReport`, `ServiceTopology`, `Incident`) that enforce a strict structure across the application, ensuring the API and UI receive predictable data shapes.

### `api/main.py`
A standard FastAPI application. It initializes the `AnalysisPipeline` and exposes endpoints:
- `GET /scenarios`: Lists available demo scenarios.
- `POST /analyze`: Accepts a feature description (and optional scenario ID), runs the `AnalysisPipeline`, and returns the structured `RiskReport` JSON.

### `ui/app.py`
A Streamlit dashboard that serves as the frontend demo. It allows users to pick a pre-defined scenario or type a custom feature description. When "Analyze" is clicked, it runs the `AnalysisPipeline` locally (bypassing the API for speed in a single-container setup) and visualizes the output using custom components:
- A risk gauge (Low, Medium, High, Critical).
- A blast radius breakdown.
- A service topology graph.
- The detailed step-by-step reasoning chain.

---

## 4. How Data Flows

1. **Input**: A user types "I want to deploy a new checkout feature" into the Streamlit UI.
2. **Orchestration**: The UI passes this text to `AnalysisPipeline.run()`.
3. **Topology Matching**: The Orchestrator matches "checkout" to `SERVICE-CHECKOUT` and identifies it depends on `SERVICE-PAYMENT` and `SERVICE-USER-DB`.
4. **Data Retrieval**: `DynatraceClient` returns metrics/incidents for these three services.
5. **Scoring**: `FragilityScorer` notices `SERVICE-PAYMENT` had 3 recent incidents and gives it a high fragility score.
6. **Decision**: `ReportBuilder` sees the high fragility score, downgrades the decision from `GO` to `GO_WITH_CONDITIONS`, and suggests a 5% canary rollout.
7. **Output**: The Streamlit UI receives the `RiskReport` object and renders the red/yellow/green gauges and textual evidence to the user.

---

## 5. Deployment

The project is packaged for deployment via Docker and Google Cloud Run.
- **`Dockerfile`**: Packages the Python environment, installing dependencies and running the Streamlit app.
- **`cloudbuild.yaml`**: Standard Google Cloud Build pipeline for CI/CD.
- **Environment Variables**: Can be run entirely offline/mocked (`USE_MOCK=true`) or connected to a live Dynatrace environment using OAuth credentials.
