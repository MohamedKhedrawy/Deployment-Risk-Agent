FROM python:3.12-slim

WORKDIR /app

# Install Node.js 20 (required for the Dynatrace MCP server via npx)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Install Dynatrace MCP server (Node.js)
COPY package.json package-lock.json* ./
RUN npm install --omit=dev

# Copy application code
COPY agent/ agent/
COPY dtmcp/ dtmcp/
COPY api/ api/
COPY canary_agent/ canary_agent/
COPY run_mcp_wrapper.sh .

# Build React frontend and copy static files
COPY web-ui/ web-ui/
RUN cd web-ui && npm install && npm run build

# Expose FastAPI port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

ENV PORT=8080
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
