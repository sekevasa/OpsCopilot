#!/usr/bin/env python3
"""Multi-service runner for Manufacturing AI Copilot.

This script starts all 5 microservices with proper environment setup.
Each service runs in its own subprocess with proper logging.
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path
from threading import Thread

# Service configuration
SERVICES = [
    {
        "name": "data-ingest-service",
        "port": 8001,
        "dir": "services/data-ingest-service",
    },
    {
        "name": "unified-data-service",
        "port": 8002,
        "dir": "services/unified-data-service",
    },
    {
        "name": "ai-runtime-service",
        "port": 8003,
        "dir": "services/ai-runtime-service",
    },
    {
        "name": "forecast-service",
        "port": 8004,
        "dir": "services/forecast-service",
    },
    {
        "name": "notification-service",
        "port": 8005,
        "dir": "services/notification-service",
    },
]

processes = []


def print_header(text):
    """Print colored header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_info(service_name, message, color="blue"):
    """Print info message with service name."""
    colors = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "red": "\033[91m",
    }
    reset = "\033[0m"
    color_code = colors.get(color, "")
    print(f"{color_code}[{service_name}]{reset} {message}")


def start_service(service_config):
    """Start a single service in a subprocess."""
    name = service_config["name"]
    port = service_config["port"]
    service_dir = service_config["dir"]

    # Prepare environment
    env = os.environ.copy()
    env["SERVICE_NAME"] = name
    env["ENVIRONMENT"] = "development"
    env["DEBUG"] = "true"
    env["LOG_LEVEL"] = "INFO"
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = str(Path.cwd())

    # Build command
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
    ]

    print_info(name, f"Starting on port {port}...", "yellow")
    print_info(name, f"Service directory: {service_dir}", "blue")

    try:
        # Create subprocess with proper output handling
        process = subprocess.Popen(
            cmd,
            cwd=service_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        processes.append((name, process))
        print_info(name, f"Process started (PID: {process.pid})", "green")

        # Thread to read stdout
        def read_stdout():
            for line in iter(process.stdout.readline, ""):
                if line:
                    print_info(name, line.rstrip(), "cyan")

        # Thread to read stderr
        def read_stderr():
            for line in iter(process.stderr.readline, ""):
                if line:
                    print_info(name, line.rstrip(), "red")

        Thread(target=read_stdout, daemon=True).start()
        Thread(target=read_stderr, daemon=True).start()

        return process

    except Exception as e:
        print_info(name, f"Failed to start: {e}", "red")
        return None


def wait_for_service(port, timeout=10):
    """Wait for a service to be ready."""
    import socket
    from time import sleep

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("localhost", port))
            sock.close()
            if result == 0:
                return True
        except:
            pass
        sleep(0.5)
    return False


def shutdown_handler(signum, frame):
    """Handle shutdown signal."""
    print_header("Shutting down services...")
    for name, process in processes:
        if process and process.poll() is None:
            print_info(name, "Terminating...", "yellow")
            process.terminate()
            try:
                process.wait(timeout=5)
                print_info(name, "Stopped", "green")
            except subprocess.TimeoutExpired:
                print_info(name, "Force killing...", "yellow")
                process.kill()
    sys.exit(0)


def main():
    """Main entry point."""
    # Check if running from project root
    if not Path("shared").exists():
        print("Error: Run this script from the project root directory")
        sys.exit(1)

    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    print_header("Manufacturing AI Copilot - Service Manager")

    # Start all services
    print("Starting services...\n")
    for service in SERVICES:
        start_service(service)
        time.sleep(1)  # Stagger starts

    # Wait for services to be ready
    print_header("Waiting for services to be ready")
    for service in SERVICES:
        print_info(service["name"],
                   f"Checking port {service['port']}...", "blue")
        if wait_for_service(service["port"]):
            print_info(service["name"], "Ready ✓", "green")
        else:
            print_info(
                service["name"], "Warning: Not responding (may still be starting)", "yellow")

    # Print endpoint information
    print_header("Service Endpoints")
    print("All services are running. Access them at:\n")
    for service in SERVICES:
        port = service["port"]
        name = service["name"]
        print(f"  ✓ {name:<30} http://localhost:{port}/docs")

    print("\nHealth checks:")
    for service in SERVICES:
        port = service["port"]
        print(f"  GET http://localhost:{port}/api/v1/health")

    print("\n" + "=" * 70)
    print("Press Ctrl+C to stop all services")
    print("=" * 70 + "\n")

    # Keep the process running
    try:
        while True:
            time.sleep(1)
            # Check if any process has died
            for name, process in processes:
                if process and process.poll() is not None:
                    print_info(
                        name, "Process died, waiting for restart...", "red")
    except KeyboardInterrupt:
        shutdown_handler(None, None)


if __name__ == "__main__":
    main()
