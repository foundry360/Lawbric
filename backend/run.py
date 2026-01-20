#!/usr/bin/env python
"""
Simple script to run the FastAPI server
"""

import sys
import json
import os
from datetime import datetime
from pathlib import Path

# #region agent log
# Use relative path that works in both Windows and Docker
log_path = Path("/tmp/debug.log") if os.path.exists("/tmp") else Path(".cursor/debug.log")
try:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"startup","hypothesisId":"A","location":"run.py:12","message":"Python interpreter found","data":{"python_version":sys.version,"executable":sys.executable},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
except: pass
# #endregion

try:
    import uvicorn
    from app.core.config import settings
    # #region agent log
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"startup","hypothesisId":"A","location":"run.py:20","message":"Imports successful","data":{"host":"0.0.0.0","port":9000,"environment":settings.ENVIRONMENT},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
    except: pass
    # #endregion
except ImportError as e:
    # #region agent log
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"startup","hypothesisId":"B","location":"run.py:26","message":"Import failed","data":{"error":str(e),"error_type":type(e).__name__},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
    except: pass
    # #endregion
    print(f"Error: Failed to import required modules: {e}")
    print("Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)

if __name__ == "__main__":
    # #region agent log
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"startup","hypothesisId":"A","location":"run.py:35","message":"About to call uvicorn.run","data":{"port":9000},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
    except: pass
    # #endregion
    
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=9000,
            reload=settings.ENVIRONMENT == "development",
            log_level="info"
        )
    except Exception as e:
        # #region agent log
        try:
            with open(log_path, "a") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"startup","hypothesisId":"B","location":"run.py:47","message":"Uvicorn.run failed","data":{"error":str(e),"error_type":type(e).__name__},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
        except: pass
        # #endregion
        raise




