#!/usr/bin/env python3
"""
Simple script to run the API server
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )