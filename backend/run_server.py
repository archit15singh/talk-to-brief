#!/usr/bin/env python3
"""
Main script to run the API server from backend root
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