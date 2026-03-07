#!/usr/bin/env bash
# Run from project root after: railway login
# Deploys Dealforge to Railway (init/link, configure build/start, then up).
set -e
SERVICE_NAME="${1:-web}"

if ! railway whoami &>/dev/null; then
  echo "Not logged in. Run: railway login"
  exit 1
fi

if ! railway status --json &>/dev/null || [ -z "$(railway status --json 2>/dev/null)" ]; then
  railway init --name dealforge
  railway add --service "$SERVICE_NAME"
fi

railway service link "$SERVICE_NAME"
railway variables --service "$SERVICE_NAME" --set "RAILPACK_BUILD_CMD=bash scripts/railway-build.sh"
railway variables --service "$SERVICE_NAME" --set "RAILPACK_START_CMD=uvicorn server:app --host 0.0.0.0 --port \$PORT --log-level warning --no-access-log"

echo "Ensure GOOGLE_API_KEY is set: railway variables --service $SERVICE_NAME --set \"GOOGLE_API_KEY=your_key\""

railway up --detach --service "$SERVICE_NAME"
echo "Done. Add a public domain in Railway dashboard (Settings → Networking) to get a URL."
