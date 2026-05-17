"""Reset v2 naive to broken state for next demo run."""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FILES = [
    "demo_target/pydantic_v2_naive/models.py",
    "demo_target/pydantic_v2_naive/routes.py",
]


def run() -> None:
    print("Resetting v2 naive to broken state...")
    for f in FILES:
        result = subprocess.run(
            ["git", "checkout", f],
            capture_output=True, text=True, cwd=str(ROOT)
        )
        if result.returncode == 0:
            print(f"  OK  {f}")
        else:
            print(f"  FAIL {f}: {result.stderr.strip()}")
            sys.exit(1)

    # Clear audit trail and cassettes so dashboard starts fresh
    for folder in ["audit_trail", "golden_cassettes"]:
        d = ROOT / folder
        if d.exists():
            removed = 0
            for p in d.iterdir():
                if p.is_file() and p.name != ".gitkeep":
                    p.unlink()
                    removed += 1
                elif p.is_dir():
                    shutil.rmtree(p)
                    removed += 1
            print(f"  OK  cleared {folder}/ ({removed} files)")

    print("\nDone! v2 naive is broken again (4 traps restored). Ready for next demo.")

if __name__ == "__main__":
    run()
