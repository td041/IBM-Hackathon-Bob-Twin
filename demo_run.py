"""One-shot demo runner — start apps + seed + capture + replay + report + dashboard.

Usage:
    .venv\\Scripts\\python demo_run.py
"""

import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).parent.resolve()
PYTHON_MAIN   = str(ROOT / ".venv" / "Scripts" / "python.exe")
PYTHON_V1     = str(ROOT / ".venv-demo-v1" / "Scripts" / "python.exe")
V1_PORT, V2_PORT, DASH_PORT = 8001, 8002, 8501
V1_URL        = f"http://localhost:{V1_PORT}"
V2_URL        = f"http://localhost:{V2_PORT}"
DASH_URL      = f"http://localhost:{DASH_PORT}"

# Enable ANSI colors on Windows
if os.name == "nt":
    os.system("")

GREEN, RED, DIM, RESET = "\033[92m", "\033[91m", "\033[90m", "\033[0m"
_procs: list[subprocess.Popen] = []


# ── Helpers ──────────────────────────────────────────────────────────────────

def step(n: int, total: int, msg: str) -> None:
    print(f"\n{DIM}[{n}/{total}]{RESET} {msg}")


def _port_open(port: int) -> bool:
    """Quick TCP check — much faster than HTTP."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _kill_port(port: int) -> None:
    """Kill processes bound to the given port on Windows."""
    if not _port_open(port):
        return
    try:
        out = subprocess.run(
            ["cmd", "/c", f'netstat -ano | findstr ":{port} "'],
            capture_output=True, text=True, timeout=3,
        ).stdout
        pids = {p.split()[-1] for p in out.splitlines() if p.split() and p.split()[-1].isdigit()}
        for pid in pids:
            if pid != "0":
                subprocess.run(["taskkill", "/PID", pid, "/F"],
                               capture_output=True, timeout=3)
    except Exception:
        pass


def _wait_port(port: int, timeout: float = 15.0, label: str = "") -> bool:
    """Block until port responds or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_open(port):
            return True
        time.sleep(0.2)
    print(f"  {RED}WARNING{RESET} {label} did not respond on port {port}")
    return False


def _spawn(args: list[str], silent: bool = True) -> subprocess.Popen:
    proc = subprocess.Popen(
        args,
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL if silent else None,
        stderr=subprocess.DEVNULL if silent else None,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
    )
    _procs.append(proc)
    return proc


def _cleanup() -> None:
    for p in _procs:
        try:
            p.terminate()
        except Exception:
            pass


# ── Main ─────────────────────────────────────────────────────────────────────

def run() -> None:
    print(f"\n{GREEN}{'='*54}{RESET}")
    print(f"  Bob's Twin — One-shot Demo")
    print(f"{GREEN}{'='*54}{RESET}")

    # Verify venvs exist
    for label, path in [("main .venv", PYTHON_MAIN), (".venv-demo-v1", PYTHON_V1)]:
        if not Path(path).exists():
            print(f"{RED}[ERROR]{RESET} {label} not found at {path}")
            print(f"        Run {GREEN}setup.bat{RESET} first.")
            sys.exit(1)

    # ── 1. Start all services in parallel ────────────────────────────────────
    step(1, 6, "Starting v1 app, v2 naive app, and dashboard in parallel...")
    for port in (V1_PORT, V2_PORT, DASH_PORT):
        _kill_port(port)
    time.sleep(0.3)

    _spawn([PYTHON_V1, "-m", "uvicorn",
            "demo_target.pydantic_v1_app.main:app",
            "--host", "127.0.0.1", "--port", str(V1_PORT)])
    _spawn([PYTHON_MAIN, "-m", "uvicorn",
            "demo_target.pydantic_v2_naive.main:app",
            "--host", "127.0.0.1", "--port", str(V2_PORT)])
    _spawn([PYTHON_MAIN, "-m", "streamlit", "run", "dashboard/app.py",
            "--server.headless", "true",
            "--server.port", str(DASH_PORT),
            "--browser.gatherUsageStats", "false"])

    # Wait for v1 + v2 before doing HTTP work (dashboard waits in background)
    _wait_port(V1_PORT, label="v1 app")
    _wait_port(V2_PORT, label="v2 naive")
    print(f"  {GREEN}v1 :{V1_PORT}{RESET}  {GREEN}v2 :{V2_PORT}{RESET}  dashboard starting...")

    sys.path.insert(0, str(ROOT))
    import httpx as _httpx

    # ── 2. Seed (only if not already seeded) ─────────────────────────────────
    step(2, 6, "Checking seed state...")
    try:
        _users_resp = _httpx.get(f"{V1_URL}/users", timeout=5)
        _users_resp.raise_for_status()
        _already_seeded = len(_users_resp.json()) > 3
    except Exception:
        _already_seeded = False

    if _already_seeded:
        print(f"  {DIM}v1 app already seeded — skipping{RESET}")
    else:
        print(f"  Seeding v1 app...")
        from scripts.seed_demo_traffic import run as _seed
        _seed()

    # ── 3. Capture baseline ──────────────────────────────────────────────────
    # Always reset to clean state before capture so cassette IDs are deterministic
    step(3, 6, "Capturing baseline cassette...")
    try:
        _httpx.post(f"{V1_URL}/admin/reset", timeout=5).raise_for_status()
    except Exception as _e:
        print(f"  {RED}[ERROR]{RESET} Could not reset v1 app: {_e}")
        _cleanup(); sys.exit(1)
    from twin_mcp.capture import capture_baseline
    cap = capture_baseline(".", ["scripts/seed_demo_traffic.py"])
    if not cap.get("ok"):
        print(f"  {RED}[ERROR]{RESET} Capture failed: {cap}")
        _cleanup(); sys.exit(1)
    run_id, cassette = cap["run_id"], cap["cassette_path"]
    print(f"  run_id: {run_id}  |  {cap['n_interactions']} interactions  |  {cassette}")

    # ── 4. Replay vs v1 ──────────────────────────────────────────────────────
    step(4, 6, "Replaying cassette vs v1 (expect 1.0)...")
    from twin_mcp.replay import replay_and_diff
    r1 = replay_and_diff(cassette, ".", target_url=V1_URL)
    s1 = r1["equivalence_score"]
    col = GREEN if s1 >= 0.95 else RED
    print(f"  score: {col}{s1}{RESET}  ({r1['passed']}/{r1['total']} passed)")

    # ── 5. Replay vs v2 ──────────────────────────────────────────────────────
    step(5, 6, "Replaying cassette vs v2 naive (expect < 1.0)...")
    r2 = replay_and_diff(cassette, ".", target_url=V2_URL)
    s2 = r2["equivalence_score"]
    col = GREEN if s2 >= 0.95 else RED
    print(f"  score: {col}{s2}{RESET}  ({r2['passed']}/{r2['total']} passed)")
    fails: dict[str, bool] = {}
    for d in r2["diffs_per_endpoint"]:
        if d["status"] == "fail" and d["endpoint"] not in fails:
            fails[d["endpoint"]] = True
            print(f"    {RED}FAIL{RESET}  {d['endpoint']}")

    # ── 6. PDF report ────────────────────────────────────────────────────────
    step(6, 6, "Generating PDF audit report...")
    from twin_mcp.reports import generate_audit_report
    rep = generate_audit_report(run_id, "pdf")
    if rep.get("ok"):
        print(f"  PDF: {rep['path']}")
    else:
        print(f"  {DIM}(skipped: {rep.get('error', 'unknown')}){RESET}")

    # ── Open dashboard ───────────────────────────────────────────────────────
    print(f"\n  Waiting for dashboard...", end="", flush=True)
    if _wait_port(DASH_PORT, timeout=20, label="dashboard"):
        time.sleep(1)  # give Streamlit a moment to fully render
        print(f" {GREEN}ready{RESET}")
        webbrowser.open(DASH_URL)

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{GREEN}{'='*54}{RESET}")
    print(f"  DEMO COMPLETE — run_id: {run_id}")
    print(f"{GREEN}{'='*54}{RESET}")
    print(f"  v1 score  : {GREEN}{s1}{RESET}   (baseline — same app)")
    print(f"  v2 score  : {RED}{s2}{RESET}   ({len(fails)} endpoints failing)")
    print(f"  Dashboard : {DASH_URL}")
    print(f"  v1 app    : {V1_URL}/docs")
    print(f"  v2 app    : {V2_URL}/docs")
    print(f"\n  {DIM}Press Ctrl+C to stop all services.{RESET}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n  Shutting down...")
        _cleanup()


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        _cleanup()
        sys.exit(0)
    except Exception as exc:
        print(f"\n{RED}[FATAL]{RESET} {exc}")
        _cleanup()
        sys.exit(1)
