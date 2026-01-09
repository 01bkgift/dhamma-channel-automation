#!/bin/bash
set -e

cd /opt/flowbiz-client-dhamma

echo "--- Configuring Soft-Live Unlisted ---"
sed -i 's/^SOFT_LIVE_ENABLED=.*/SOFT_LIVE_ENABLED=true/' .env
sed -i 's/^SOFT_LIVE_YOUTUBE_MODE=.*/SOFT_LIVE_YOUTUBE_MODE=unlisted/' .env

echo "--- Restarting Containers ---"
docker compose --env-file config/flowbiz_port.env up -d --remove-orphans

RUN_ID="smoke_unlisted_$(date +%Y%m%d_%H%M%S)"
echo "--- Starting Run: $RUN_ID ---"

# Background injection
(
  echo "Waiting to inject video (Host side)..."
  for i in {1..20}; do
    if [ -d "output/$RUN_ID/artifacts" ]; then
       if [ -f "video/test_short.mp4" ]; then
          cp video/test_short.mp4 "output/$RUN_ID/artifacts/video.mp4"
          echo "Video injected from video/test_short.mp4"
          break
       elif [ -f "data/verify_test.mp4" ]; then
          cp data/verify_test.mp4 "output/$RUN_ID/artifacts/video.mp4"
          echo "Video injected from data/verify_test.mp4"
          break
       fi
    fi
    sleep 3
  done
) &
BG_PID=$!

SERVICE_NAME="web"

echo "--- Initial Run (Trigger Pending) ---"
# We expect this to fail/exit due to Pending
docker compose --env-file config/flowbiz_port.env exec -T \
  -e APPROVAL_GRACE_MINUTES=1 \
  $SERVICE_NAME python3 orchestrator.py \
  --pipeline pipelines/youtube_upload_smoke_requires_quality.yaml \
  --run-id "$RUN_ID" || echo "Initial run exited (likely Pending)"

echo "--- Waiting for Grace Period (70s) ---"
sleep 70

echo "--- Second Run (Expect Approval & Upload) ---"
docker compose --env-file config/flowbiz_port.env exec -T \
  -e APPROVAL_GRACE_MINUTES=1 \
  $SERVICE_NAME python3 orchestrator.py \
  --pipeline pipelines/youtube_upload_smoke_requires_quality.yaml \
  --run-id "$RUN_ID"

echo "--- Pipeline Finished ---"
echo ""
echo "--- Summary Content ---"
if [ -f "output/$RUN_ID/artifacts/youtube_upload_summary.json" ]; then
    cat "output/$RUN_ID/artifacts/youtube_upload_summary.json"
else
    echo "ERROR: youtube_upload_summary.json not found on host."
fi

# Cleanup
kill $BG_PID 2>/dev/null || true
