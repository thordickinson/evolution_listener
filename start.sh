#!/bin/bash
cd /opt/harmony/listener
source .venv/bin/activate
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
