"""Start Pydantic v2 naive app on port 8002."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON_MAIN = str(ROOT / ".venv" / "Scripts" / "python.exe")


def main():
    print("=" * 60)
    print("  Starting Pydantic v2 Naive App (Migrated)")
    print("=" * 60)
    print(f"  Port: 8002")
    print(f"  Python: {PYTHON_MAIN}")
    print(f"  Docs: http://localhost:8002/docs")
    print(f"  Health: http://localhost:8002/health")
    print("=" * 60)
    print("\nWARNING: This is the NAIVE migration")
    print("   Contains 4 behavioral traps:")
    print("   - TRAP 1: Enum serialization")
    print("   - TRAP 2: Decimal serialization")
    print("   - TRAP 3: __root__ model")
    print("   - TRAP 4: Validator loss")
    print("\nPress Ctrl+C to stop\n")

    try:
        subprocess.run(
            [
                PYTHON_MAIN,
                "-m", "uvicorn",
                "demo_target.pydantic_v2_naive.main:app",
                "--host", "0.0.0.0",
                "--port", "8002",
                "--reload",
            ],
            cwd=str(ROOT),
        )
    except KeyboardInterrupt:
        print("\n\nShutting down v2 app...")
        sys.exit(0)


if __name__ == "__main__":
    main()
