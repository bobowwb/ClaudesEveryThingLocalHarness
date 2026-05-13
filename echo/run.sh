#!/bin/bash
set -e
cd "\$(dirname "\$0")"
export OTEL_EXPORTER_OTLP_ENDPOINT="\${OTEL_EXPORTER_OTLP_ENDPOINT:-http://localhost:4318}"
export OTEL_SERVICE_NAME="ltm-chat-service"
export PORT="\${PORT:-5000}"
pip install -q -r requirements.txt
python app.py
