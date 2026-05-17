"""Start Pydantic v1 app on port 8001."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON_V1 = str(ROOT / ".venv-demo-v1" / "Scripts" / "python.exe")


def main():
    print("=" * 60)
    print("  Starting Pydantic v1 App (Legacy)")
    print("=" * 60)
    print(f"  Port: 8001")
    print(f"  Python: {PYTHON_V1}")
    print(f"  Docs: http://localhost:8001/docs")
    print(f"  Health: http://localhost:8001/health")
    print("=" * 60)
    print("\nPress Ctrl+C to stop\n")

    try:
        subprocess.run(
            [
                PYTHON_V1,
                "-m", "uvicorn",
                "demo_target.pydantic_v1_app.main:app",
                "--host", "0.0.0.0",
                "--port", "8001",
                "--reload",
            ],
            cwd=str(ROOT),
        )
    except KeyboardInterrupt:
        print("\n\nShutting down v1 app...")
        sys.exit(0)


if __name__ == "__main__":
    main()
