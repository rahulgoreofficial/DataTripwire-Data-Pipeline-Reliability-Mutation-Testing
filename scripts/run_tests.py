#!/usr/bin/env python3
"""DataTripwire Comprehensive Test & Verification Suite.

Executes backend pytest suite, frontend linter, TypeScript check, and
production build, providing a unified developer verification report.
"""

import os
from pathlib import Path
import subprocess
import sys
import time

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"

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


def run_stage(title: str, cmd: list[str], cwd: Path) -> tuple[bool, float, str]:
    print(f"\n{BOLD}{CYAN}-----------------------------------------------------------{RESET}")
    print(f"{BOLD}[STAGE] {title}{RESET}")
    print(f"Command: {' '.join(cmd)}")
    print(f"Directory: {cwd}")
    print(f"{CYAN}-----------------------------------------------------------{RESET}")

    start = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        shell=sys.platform == "win32" and cmd[0] in ("npm", "npm.cmd", "npx", "npx.cmd"),
    )
    elapsed = time.perf_counter() - start
    success = proc.returncode == 0
    return success, elapsed, title


def main() -> int:
    print(f"\n{BOLD}{CYAN}==========================================================={RESET}")
    print(f"{BOLD}{CYAN}  DATATRIPWIRE // FULL TEST & BUILD VERIFICATION SUITE{RESET}")
    print(f"{BOLD}{CYAN}==========================================================={RESET}")

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    stages = [
        ("Backend Tests (pytest)", [sys.executable, "-m", "pytest", "tests"], BACKEND_DIR),
        ("Frontend Lint (oxlint)", [npm_cmd, "run", "lint"], FRONTEND_DIR),
        ("Frontend Build & Typecheck (tsc + vite build)", [npm_cmd, "run", "build"], FRONTEND_DIR),
    ]

    results = []
    for title, cmd, cwd in stages:
        success, elapsed, name = run_stage(title, cmd, cwd)
        results.append((name, success, elapsed))
        if not success:
            print(f"\n{RED}[ERROR] Stage '{title}' failed.{RESET}")

    print(f"\n{BOLD}{CYAN}==========================================================={RESET}")
    print(f"{BOLD}{CYAN}  SUMMARY OF TEST & BUILD RESULTS{RESET}")
    print(f"{BOLD}{CYAN}==========================================================={RESET}")

    all_passed = True
    for name, success, elapsed in results:
        status_label = f"{GREEN}PASSED{RESET}" if success else f"{RED}FAILED{RESET}"
        if not success:
            all_passed = False
        print(f"  [{status_label}] {name} ({elapsed:.2f}s)")

    print(f"{CYAN}-----------------------------------------------------------{RESET}")
    if all_passed:
        print(f"{BOLD}{GREEN}✓ ALL TEST AND BUILD STAGES PASSED SUCCESSFULLY.{RESET}\n")
        return 0
    else:
        print(f"{BOLD}{RED}✗ ONE OR MORE STAGES FAILED. Review errors above.{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
