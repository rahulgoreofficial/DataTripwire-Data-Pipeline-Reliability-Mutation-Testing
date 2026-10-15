#!/usr/bin/env python3
"""DataTripwire Local Development Orchestrator.

Manages the dual-process development environment:
- Verifies Python and Node.js environments and dependencies
- Launches the FastAPI backend (port 8000)
- Launches the Vite React frontend (port 5173)
- Polls real health endpoints until services are verified ready
- Automatically launches the default browser
- Supervise child processes with reliable, targeted cleanup on Ctrl+C
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
BACKEND_SRC = BACKEND_DIR / "src"
FRONTEND_DIR = REPO_ROOT / "frontend"

# Windows terminal UTF-8 encoding support
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    os.system("")

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def log(tag: str, msg: str, color: str = CYAN) -> None:
    timestamp = time.strftime("%H:%M:%S")
    print(f"{BOLD}{color}[{tag}]{RESET} {timestamp} - {msg}")


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def check_backend_running(port: int) -> bool:
    url = f"http://127.0.0.1:{port}/health"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DataTripwire-Supervisor"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                return data.get("app") == "DataTripwire"
    except Exception:
        return False
    return False


def verify_backend_environment() -> None:
    log("SETUP", "Verifying Python environment & backend dependencies...")
    sys.path.insert(0, str(BACKEND_SRC))
    required_modules = ["pydantic", "pandas", "fastapi", "uvicorn"]
    missing = []
    for mod in required_modules:
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(mod)

    if missing:
        log("SETUP", f"Missing Python packages: {', '.join(missing)}. Installing backend...", YELLOW)
        cmd = [sys.executable, "-m", "pip", "install", "-e", "backend"]
        res = subprocess.run(cmd, cwd=str(REPO_ROOT))
        if res.returncode != 0:
            log("ERROR", f"Failed to install backend packages (code {res.returncode}).", RED)
            sys.exit(1)
    else:
        log("SETUP", "Backend dependencies verified.")


def verify_frontend_environment() -> None:
    log("SETUP", "Verifying frontend environment & dependencies...")
    node_modules = FRONTEND_DIR / "node_modules"
    vite_bin = node_modules / "vite"

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    if not node_modules.is_dir() or not vite_bin.exists():
        log("SETUP", "Frontend dependencies not found. Installing via npm...", YELLOW)
        # Check if package-lock.json exists
        lockfile = FRONTEND_DIR / "package-lock.json"
        cmd = [npm_cmd, "ci"] if lockfile.exists() else [npm_cmd, "install"]
        res = subprocess.run(cmd, cwd=str(FRONTEND_DIR), shell=sys.platform == "win32")
        if res.returncode != 0:
            log("ERROR", f"npm installation failed with code {res.returncode}.", RED)
            sys.exit(1)
    else:
        log("SETUP", "Frontend dependencies verified.")


def kill_process_tree(proc: subprocess.Popen, name: str) -> None:
    if proc is None or proc.poll() is not None:
        return
    pid = proc.pid
    log("SHUTDOWN", f"Stopping {name} (PID: {pid})...")
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
        else:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
    except Exception as e:
        log("WARN", f"Error terminating {name} (PID {pid}): {e}", YELLOW)
        try:
            proc.kill()
        except Exception:
            pass


def wait_for_http(url: str, name: str, timeout_sec: float = 30.0) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout_sec:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DataTripwire-Supervisor"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status in (200, 304):
                    return True
        except (urllib.error.URLError, ConnectionError, socket.timeout):
            time.sleep(0.4)
        except Exception:
            time.sleep(0.4)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="DataTripwire Development Startup Orchestrator")
    parser.add_argument("--backend-port", type=int, default=int(os.getenv("BACKEND_PORT", "8000")), help="Backend port (default: 8000)")
    parser.add_argument("--frontend-port", type=int, default=int(os.getenv("VITE_PORT", "5173")), help="Frontend port (default: 5173)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    args = parser.parse_args()

    print(f"\n{BOLD}{CYAN}==========================================================={RESET}")
    print(f"{BOLD}{CYAN}  DATATRIPWIRE // THE DATA RELIABILITY LAB{RESET}")
    print(f"{BOLD}{CYAN}  One-Click Development Server Supervisor{RESET}")
    print(f"{BOLD}{CYAN}==========================================================={RESET}\n")

    verify_backend_environment()
    verify_frontend_environment()

    backend_port = args.backend_port
    frontend_port = args.frontend_port

    # Check for port conflicts
    if is_port_in_use(backend_port):
        if check_backend_running(backend_port):
            log("BACKEND", f"DataTripwire backend is already responding on port {backend_port}.", GREEN)
            backend_already_running = True
        else:
            log("ERROR", f"Port {backend_port} is occupied by an unrelated service. Please free port {backend_port} or specify another port.", RED)
            return 1
    else:
        backend_already_running = False

    backend_proc: subprocess.Popen | None = None
    frontend_proc: subprocess.Popen | None = None

    # Track processes for cleanup on interrupt
    def shutdown_all(*_args):
        print()
        log("SHUTDOWN", "Shutdown signal received. Stopping managed servers...", YELLOW)
        if frontend_proc:
            kill_process_tree(frontend_proc, "Frontend Vite server")
        if backend_proc:
            kill_process_tree(backend_proc, "Backend FastAPI server")
        log("SHUTDOWN", "DataTripwire has stopped cleanly. Goodbye!", GREEN)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_all)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown_all)

    try:
        # 1. Start Backend if not already running
        if not backend_already_running:
            log("BACKEND", f"Starting FastAPI backend server on http://127.0.0.1:{backend_port}...")
            env = os.environ.copy()
            env["PYTHONPATH"] = str(BACKEND_SRC) + os.pathsep + env.get("PYTHONPATH", "")
            env["BACKEND_PORT"] = str(backend_port)
            env["BACKEND_HOST"] = "127.0.0.1"

            backend_cmd = [
                sys.executable,
                "-m",
                "uvicorn",
                "datatripwire.api.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(backend_port),
            ]

            backend_proc = subprocess.Popen(
                backend_cmd,
                cwd=str(BACKEND_SRC),
                env=env,
            )

        # 2. Wait for Backend Readiness
        log("CHECK", f"Waiting for backend health check at http://127.0.0.1:{backend_port}/health...")
        if not wait_for_http(f"http://127.0.0.1:{backend_port}/health", "Backend", timeout_sec=20.0):
            log("ERROR", "Backend failed to report healthy within 20 seconds.", RED)
            if backend_proc and backend_proc.poll() is not None:
                log("ERROR", f"Backend process terminated prematurely with exit code {backend_proc.returncode}.", RED)
            shutdown_all()
            return 1

        log("READY", f"Backend API is healthy at http://127.0.0.1:{backend_port}", GREEN)
        log("READY", f"Interactive API Docs: http://127.0.0.1:{backend_port}/docs", GREEN)

        # 3. Start Frontend
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        log("FRONTEND", f"Starting Vite development server on port {frontend_port}...")
        frontend_cmd = [npm_cmd, "run", "dev", "--", "--host", "127.0.0.1", "--port", str(frontend_port)]

        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=str(FRONTEND_DIR),
            shell=sys.platform == "win32",
        )

        # 4. Wait for Frontend Readiness
        log("CHECK", f"Waiting for frontend dev server at http://127.0.0.1:{frontend_port}...")
        actual_frontend_url = f"http://localhost:{frontend_port}"
        # Poll 5173 or fallback ports
        frontend_ready = False
        for p in (frontend_port, frontend_port + 1, frontend_port + 2):
            if wait_for_http(f"http://127.0.0.1:{p}", f"Frontend port {p}", timeout_sec=10.0 if p == frontend_port else 2.0):
                actual_frontend_url = f"http://localhost:{p}"
                frontend_ready = True
                break

        if not frontend_ready:
            log("ERROR", "Frontend failed to respond within timeout.", RED)
            if frontend_proc and frontend_proc.poll() is not None:
                log("ERROR", f"Frontend process terminated with exit code {frontend_proc.returncode}.", RED)
            shutdown_all()
            return 1

        log("READY", f"Frontend application is live at {actual_frontend_url}", GREEN)

        # 5. Open browser automatically
        if not args.no_browser:
            log("READY", f"Opening {actual_frontend_url} in your default browser...", GREEN)
            try:
                webbrowser.open(actual_frontend_url)
            except Exception as e:
                log("WARN", f"Could not open browser automatically: {e}", YELLOW)

        print(f"\n{BOLD}{GREEN}==========================================================={RESET}")
        print(f"{BOLD}{GREEN}  DATATRIPWIRE IS RUNNING!{RESET}")
        print(f"  Web Application : {BOLD}{actual_frontend_url}{RESET}")
        print(f"  Backend API Docs: {BOLD}http://127.0.0.1:{backend_port}/docs{RESET}")
        print(f"  Health Check    : {BOLD}http://127.0.0.1:{backend_port}/health{RESET}")
        print(f"{BOLD}{GREEN}==========================================================={RESET}")
        print(f"{CYAN}Press Ctrl+C at any time in this window to stop all services.{RESET}\n")

        # 6. Supervise child processes
        while True:
            if backend_proc and backend_proc.poll() is not None:
                log("ERROR", f"Backend server crashed with exit code {backend_proc.returncode}!", RED)
                break
            if frontend_proc and frontend_proc.poll() is not None:
                log("ERROR", f"Frontend dev server crashed with exit code {frontend_proc.returncode}!", RED)
                break
            time.sleep(0.5)

    except KeyboardInterrupt:
        shutdown_all()
    except Exception as e:
        log("ERROR", f"Supervisor encountered unexpected error: {e}", RED)
    finally:
        if frontend_proc:
            kill_process_tree(frontend_proc, "Frontend Vite server")
        if backend_proc:
            kill_process_tree(backend_proc, "Backend FastAPI server")

    return 0


if __name__ == "__main__":
    sys.exit(main())
