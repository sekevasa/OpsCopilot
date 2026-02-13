#!/usr/bin/env python3
"""
Quick start script for Manufacturing AI Copilot services.
Starts services without requiring PostgreSQL/Redis (mock mode).
"""

import os
import sys
import subprocess
import platform
import time
import signal
from pathlib import Path

# Get the workspace root
WORKSPACE_ROOT = Path(__file__).parent.absolute()
SERVICES_DIR = WORKSPACE_ROOT / "services"

# Service configurations
SERVICES = [
    {
        "name": "data-ingest-service",
        "port": 8001,
        "path": SERVICES_DIR / "data-ingest-service",
        "env_vars": {
            "PYTHONUNBUFFERED": "1",
            "SKIP_DB_INIT": "1",  # Skip database initialization
        }
    },
    {
        "name": "unified-data-service",
        "port": 8002,
        "path": SERVICES_DIR / "unified-data-service",
        "env_vars": {
            "PYTHONUNBUFFERED": "1",
            "SKIP_DB_INIT": "1",
        }
    },
    {
        "name": "ai-runtime-service",
        "port": 8003,
        "path": SERVICES_DIR / "ai-runtime-service",
        "env_vars": {
            "PYTHONUNBUFFERED": "1",
            "SKIP_DB_INIT": "1",
        }
    },
    {
        "name": "forecast-service",
        "port": 8004,
        "path": SERVICES_DIR / "forecast-service",
        "env_vars": {
            "PYTHONUNBUFFERED": "1",
            "SKIP_DB_INIT": "1",
        }
    },
    {
        "name": "notification-service",
        "port": 8005,
        "path": SERVICES_DIR / "notification-service",
        "env_vars": {
            "PYTHONUNBUFFERED": "1",
            "SKIP_DB_INIT": "1",
        }
    },
]


def main():
    """Start all services in separate terminal windows."""

    print("\n" + "="*70)
    print("  Manufacturing AI Copilot - Quick Start (No Database Required)")
    print("="*70)
    print("\nStarting services without PostgreSQL/Redis requirement...")
    print("Services will start in mock/in-memory mode.\n")

    processes = []

    try:
        for service in SERVICES:
            print(f"Starting {service['name']} on port {service['port']}...")

            # Prepare environment
            env = os.environ.copy()
            env.update(service["env_vars"])
            env["PYTHONPATH"] = str(WORKSPACE_ROOT)

            # Prepare command
            python_exe = sys.executable
            uvicorn_cmd = [
                python_exe,
                "-m", "uvicorn",
                "app.main:app",
                "--host", "0.0.0.0",
                "--port", str(service["port"]),
                "--reload",
            ]

            # Start service in new window
            if platform.system() == "Windows":
                # Windows: start in new PowerShell window
                cmd = f'start "OpsCopilot - {service["name"]}" powershell -NoExit -Command "cd {service["path"]}; {" ".join(uvicorn_cmd)}"'
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    env=env,
                )
            else:
                # Unix: start in background
                process = subprocess.Popen(
                    uvicorn_cmd,
                    cwd=service["path"],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

            processes.append((service["name"], process))
            time.sleep(0.5)  # Small delay between launches

        print("\n" + "="*70)
        print("  Services Started")
        print("="*70)
        print("\n✓ All services are starting in separate windows\n")
        print("Access Swagger UI at:")
        for service in SERVICES:
            print(
                f"  • {service['name']:30} http://localhost:{service['port']}/docs")

        print("\nHealth check endpoints:")
        for service in SERVICES:
            print(
                f"  • {service['name']:30} GET http://localhost:{service['port']}/api/v1/health")

        print("\n" + "="*70)
        print("  Database Setup (Optional)")
        print("="*70)
        print("\nTo enable database persistence:")
        print("  1. Install PostgreSQL 15+ and Redis 7+")
        print("  2. Create database: createdb -U copilot_user copilot_db")
        print("  3. Update .env with DB credentials")
        print("  4. Run: python run_services.py")

        print("\n" + "="*70)
        print("  Press Ctrl+C to stop (close service windows manually)")
        print("="*70 + "\n")

        # Wait for interruption
        for name, process in processes:
            if process.poll() is not None:
                print(f"⚠ Warning: {name} exited early")

        # Keep main process alive
        signal.pause() if platform.system() != "Windows" else input()

    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("  Shutting down services...")
        print("="*70)
        for name, process in processes:
            try:
                if process.poll() is None:
                    process.terminate()
                    print(f"  ✓ {name} stopped")
            except Exception as e:
                print(f"  ✗ Error stopping {name}: {e}")
        print("="*70 + "\n")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
