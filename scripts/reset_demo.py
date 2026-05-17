"""Reset v2 naive to broken state for next demo run."""

import subprocess
import sys

FILES = [
    "demo_target/pydantic_v2_naive/models.py",
    "demo_target/pydantic_v2_naive/routes.py",
]

def run() -> None:
    print("Resetting v2 naive to broken state...")
    for f in FILES:
        result = subprocess.run(
            ["git", "checkout", f],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"  OK  {f}")
        else:
            print(f"  FAIL {f}: {result.stderr.strip()}")
            sys.exit(1)
    print("\nDone! v2 naive is broken again (4 traps restored). Ready for next demo.")

if __name__ == "__main__":
    run()
