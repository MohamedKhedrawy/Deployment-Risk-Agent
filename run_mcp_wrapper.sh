#!/bin/bash
export DT_MCP_DISABLE_TELEMETRY="true"
export NPM_CONFIG_LOGLEVEL="silent"
npx -y @dynatrace-oss/dynatrace-mcp-server@latest "$@" | awk '
/Initializing Dynatrace/ { next }
/Connecting Dynatrace/ { next }
/Testing connection/ { next }
/Client-Creds-Flow/ { next }
/Successfully retrieved/ { next }
/Successfully connected/ { next }
/Starting Dynatrace/ { next }
/Connecting server/ { next }
/running on stdio/ { next }
/\[EXPERIMENTAL\]/ { next }
{ print }
'
