#!/usr/bin/env python3
"""DataTripwire Environment & Setup Diagnostic Utility.

Verifies prerequisites, dependencies, port availability, and project integrity
before launch.
"""

import importlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import urllib.request

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"
SAMPLE_CSV = BACKEND_DIR / "src" / "datatripwire" / "data" / "sample_sales.csv"

# Configure UTF-8 on Windows terminal if supported
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    os.system("")

# Terminal styling
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def check_mark(success: bool) -> str:
    try:
        "\u2713".encode(sys.stdout.encoding or "ascii")
        mark = "✓" if success else "✗"
    except Exception:
        mark = "OK" if success else "ERR"
    return f"{GREEN}{mark}{RESET}" if success else f"{RED}{mark}{RESET}"


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def run_cmd(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd or REPO_ROOT),
            capture_output=True,
            text=True,
            shell=sys.platform == "win32" and cmd[0] in ("npm", "npm.cmd", "npx", "npx.cmd"),
            timeout=15,
        )
        return proc.returncode, (proc.stdout + proc.stderr).strip()
    except Exception as e:
        return 1, str(e)


def main() -> int:
    print(f"\n{BOLD}{CYAN}==========================================================={RESET}")
    print(f"{BOLD}{CYAN}  DATATRIPWIRE // ENVIRONMENT DIAGNOSTIC CHECK{RESET}")
    print(f"{BOLD}{CYAN}==========================================================={RESET}\n")

    all_passed = True

    # 1. Python Check
    py_ver = sys.version_info
    py_ok = py_ver >= (3, 11)
    status_str = f"Python {py_ver.major}.{py_ver.minor}.{py_ver.micro}"
    print(f"[{check_mark(py_ok)}] {status_str} (>= 3.11 required)")
    if not py_ok:
        all_passed = False
        print(f"    {YELLOW}Action: Install Python 3.11+ from https://www.python.org/downloads/{RESET}")

    # 2. Node.js Check
    node_code, node_out = run_cmd(["node", "--version"])
    node_ok = False
    node_ver_str = "Not found"
    if node_code == 0 and node_out.startswith("v"):
        node_ver_str = node_out
        try:
            major = int(node_out.lstrip("v").split(".")[0])
            node_ok = major >= 18
        except Exception:
            pass

    print(f"[{check_mark(node_ok)}] Node.js {node_ver_str} (>= 18 required)")
    if not node_ok:
        all_passed = False
        print(f"    {YELLOW}Action: Install Node.js 18+ LTS from https://nodejs.org/{RESET}")

    # 3. npm Check
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    npm_code, npm_out = run_cmd([npm_cmd, "--version"])
    npm_ok = npm_code == 0
    npm_ver_str = npm_out.splitlines()[0] if npm_ok else "Not found"
    print(f"[{check_mark(npm_ok)}] npm {npm_ver_str}")
    if not npm_ok:
        all_passed = False
        print(f"    {YELLOW}Action: Reinstall Node.js to include npm.{RESET}")

    # 4. Backend Dependencies Check
    sys.path.insert(0, str(BACKEND_DIR / "src"))
    required_packages = ["pydantic", "pandas", "fastapi", "uvicorn", "dateutil", "multipart"]
    missing_packages = []
    for pkg in required_packages:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing_packages.append(pkg)

    backend_deps_ok = len(missing_packages) == 0
    print(f"[{check_mark(backend_deps_ok)}] Backend Python packages ({len(required_packages) - len(missing_packages)}/{len(required_packages)} present)")
    if missing_packages:
        all_passed = False
        print(f"    {YELLOW}Missing: {', '.join(missing_packages)}{RESET}")
        print(f"    {YELLOW}Action: Run 'pip install -e backend' from project root.{RESET}")

    # 5. Core DataTripwire Module Check
    try:
        import datatripwire.api.main
        dt_ok = True
    except Exception as e:
        dt_ok = False
        print(f"[{check_mark(False)}] DataTripwire module import: {e}")
        all_passed = False

    if dt_ok:
        print(f"[{check_mark(True)}] DataTripwire backend package loaded successfully")

    # 6. Sample Dataset Check
    sample_ok = SAMPLE_CSV.is_file()
    print(f"[{check_mark(sample_ok)}] Bundled sample dataset: {SAMPLE_CSV.name}")
    if not sample_ok:
        all_passed = False
        print(f"    {YELLOW}Warning: Sample CSV missing at {SAMPLE_CSV}{RESET}")

    # 7. Frontend Dependencies Check
    node_modules_dir = FRONTEND_DIR / "node_modules"
    vite_bin = node_modules_dir / "vite"
    frontend_deps_ok = node_modules_dir.is_dir() and vite_bin.exists()
    print(f"[{check_mark(frontend_deps_ok)}] Frontend dependencies (frontend/node_modules)")
    if not frontend_deps_ok:
        all_passed = False
        print(f"    {YELLOW}Action: Run 'npm install' or 'npm ci' in the frontend/ folder.{RESET}")

    # 8. Port Availability Check
    backend_port = int(os.getenv("BACKEND_PORT", "8000"))
    frontend_port = int(os.getenv("VITE_PORT", "5173"))

    b_in_use = is_port_in_use(backend_port)
    f_in_use = is_port_in_use(frontend_port)

    # Check if backend port is already serving DataTripwire
    b_is_datatripwire = False
    if b_in_use:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{backend_port}/health")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                data = json.loads(resp.read().decode())
                if data.get("app") == "DataTripwire":
                    b_is_datatripwire = True
        except Exception:
            pass

    if b_is_datatripwire:
        print(f"[{check_mark(True)}] Port {backend_port}: DataTripwire backend is already running")
    elif b_in_use:
        print(f"[{YELLOW}!{RESET}] Port {backend_port} is currently in use by another application.")
    else:
        print(f"[{check_mark(True)}] Port {backend_port} available for FastAPI backend")

    if f_in_use:
        print(f"[{YELLOW}!{RESET}] Port {frontend_port} is currently in use (Vite may select fallback port).")
    else:
        print(f"[{check_mark(True)}] Port {frontend_port} available for Vite frontend")

    print(f"\n{BOLD}{CYAN}-----------------------------------------------------------{RESET}")
    if all_passed:
        print(f"{BOLD}{GREEN}✓ ALL PREREQUISITES AND INTEGRITY CHECKS PASSED.{RESET}")
        print("  DataTripwire is ready to launch via 'start_datatripwire.bat'.\n")
        return 0
    else:
        print(f"{BOLD}{RED}✗ SOME CHECKS FAILED. Review the actions above before starting.{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
