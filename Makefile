PYTHON    := .venv/Scripts/python
PYTHON_V1 := .venv-demo-v1/Scripts/python

.PHONY: help demo seed reset-demo reset-apps start-v1 start-v2 start-dashboard replay-v1 replay-v2 test lint

help:
	@grep -E '^[a-zA-Z_-]+:' Makefile | sed 's/://' | awk '{printf "  make %-20s\n", $$1}'

demo:
	$(PYTHON) demo_run.py

super-demo:
	$(PYTHON) scripts/super_demo.py

super-demo-bob:
	$(PYTHON) scripts/super_demo.py --bob-mode

super-demo-fast:
	$(PYTHON) scripts/super_demo.py --skip-capture --no-pause

start-v1:
	$(PYTHON_V1) -m uvicorn demo_target.pydantic_v1_app.main:app --host 0.0.0.0 --port 8001 --reload

start-v2:
	$(PYTHON) -m uvicorn demo_target.pydantic_v2_naive.main:app --host 0.0.0.0 --port 8002 --reload

start-dashboard:
	$(PYTHON) -m streamlit run dashboard/app.py --server.port 8501

seed:
	$(PYTHON) scripts/seed_demo_traffic.py

reset-apps:
	$(PYTHON) -c "import httpx; [print(url, httpx.post(url+'/admin/reset').status_code) for url in ['http://localhost:8001','http://localhost:8002']]"

reset-demo:
	$(PYTHON) scripts/reset_demo.py

replay-v1:
	$(PYTHON) -c "\
from pathlib import Path; import json;\
cassettes = sorted(Path('golden_cassettes').glob('run_*.yaml'), key=lambda p: p.stat().st_mtime);\
c = str(cassettes[-1]) if cassettes else exit(1);\
from twin_mcp.replay import replay_and_diff;\
r = replay_and_diff(c, '.', target_url='http://localhost:8001');\
print(json.dumps({k: r[k] for k in ('equivalence_score','passed','total','run_id')}, indent=2))"

replay-v2:
	$(PYTHON) -c "\
from pathlib import Path; import json;\
cassettes = sorted(Path('golden_cassettes').glob('run_*.yaml'), key=lambda p: p.stat().st_mtime);\
c = str(cassettes[-1]) if cassettes else exit(1);\
from twin_mcp.replay import replay_and_diff;\
r = replay_and_diff(c, '.', target_url='http://localhost:8002');\
print(json.dumps({k: r[k] for k in ('equivalence_score','passed','total','run_id')}, indent=2))"

test:
	$(PYTHON) -m pytest tests/ -v

lint:
	$(PYTHON) -m ruff check .
