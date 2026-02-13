#!/usr/bin/env python3
"""
Quick start services without database.
This runs the services in mock/demo mode for testing the APIs.
"""

import subprocess
import sys
import time
import os
from pathlib import Path


def print_header(text):
    """Print colored header."""
    print("\n" + "=" * 80)
    print(f"  {text:^76}")
    print("=" * 80 + "\n")


def main():
    """Start services without database dependency."""
    print_header("Manufacturing AI Copilot - Quick Start (Mock Mode)")

    print("""
NOTE: Services will start WITHOUT database connectivity in mock mode.
This is suitable for:
  ✓ Testing API endpoints and schemas
  ✓ Exploring Swagger UI documentation
  ✓ Integration testing with mocked database

To use with PostgreSQL, set these environment variables:
  DB_HOST=localhost
  DB_PORT=5432
  DB_USER=copilot_user
  DB_PASSWORD=copilot_password
  DB_NAME=copilot_db

Then start services normally with: python run_services.py

Proceeding to start services in mock mode...
    """)

    time.sleep(2)

    # Service configuration
    services = [
        ("data-ingest-service", 8001),
        ("unified-data-service", 8002),
        ("ai-runtime-service", 8003),
        ("forecast-service", 8004),
        ("notification-service", 8005),
    ]

    print_header("Starting Services")

    for service_name, port in services:
        print(f"Starting {service_name} on port {port}...")
        service_dir = f"services/{service_name}"

        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
            "--reload",
            "--log-level",
            "info",
        ]

        # Set environment
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        env["SERVICE_NAME"] = service_name
        env["PYTHONUNBUFFERED"] = "1"

        try:
            subprocess.Popen(
                cmd,
                cwd=service_dir,
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
            )
        except Exception as e:
            print(f"Failed to start {service_name}: {e}")
            continue

        time.sleep(1)

    print_header("Services Started")
    print("""
Swagger UI (API Documentation):
  ✓ Data Ingest:    http://localhost:8001/docs
  ✓ Unified Data:   http://localhost:8002/docs
  ✓ AI Runtime:     http://localhost:8003/docs
  ✓ Forecast:       http://localhost:8004/docs
  ✓ Notification:   http://localhost:8005/docs

Health Checks:
  $ curl http://localhost:8001/api/v1/health
  $ curl http://localhost:8002/api/v1/health
  $ curl http://localhost:8003/api/v1/health
  $ curl http://localhost:8004/api/v1/health
  $ curl http://localhost:8005/api/v1/health

Each service opens in its own window.
Close any window to stop that service.
Press Ctrl+C in a service window to gracefully shutdown that service.

Note: Services may show startup errors related to database connection.
This is expected in mock mode - APIs will still work.

To properly test database functionality, install PostgreSQL and update:
  - .env file with your database credentials
  - docker-compose.yml to spin up PostgreSQL
    """)


if __name__ == "__main__":
    main()
