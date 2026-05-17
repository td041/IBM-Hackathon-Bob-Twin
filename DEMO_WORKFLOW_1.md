# Demo Workflow 1 — One-Shot Demo

> **Mục đích:** Chạy nhanh end-to-end để rehearsal, kiểm tra môi trường, CI smoke test, hoặc show broken state trước khi vào Workflow 2.
>
> **Thời lượng:** ~3-5 phút (không có pause).
>
> **Không cần Bob IDE** — chỉ cần Python venv và terminal.

---

## Khi nào dùng

- Rehearsal trước live demo
- Kiểm tra môi trường (v1, v2, dashboard, capture đều hoạt động)
- CI smoke test
- Show **broken state** (score 0.595) cho audience trước khi vào Workflow 2
- Demo cho team đã quen Bob's Twin, không cần show autonomy

---

## Pre-flight checklist

- [ ] Python 3.11/3.12 installed
- [ ] 2 venvs đã setup: `.venv` (Pydantic v2) và `.venv-demo-v1` (Pydantic v1)
- [ ] Dependencies installed: `pip install -e ".[dev]"`
- [ ] Port 8001, 8002, 8501 trống (kill nếu cần)
- [ ] Git status clean

---

## Steps

### Bước 1: Reset về broken state (optional)

Nếu chạy demo trước đó đã fix v2:

```powershell
cd d:\coding\IBM-Hackathon-Bob-Twin
make reset-demo
```

Lệnh này sẽ:
- `git checkout` `demo_target/pydantic_v2_naive/models.py` và `routes.py` về broken
- Xóa toàn bộ `audit_trail/` và `golden_cassettes/`

### Bước 2: Chạy demo

```powershell
.venv\Scripts\python demo_run.py
```

### Bước 3: Theo dõi terminal output

Script tự động:
1. Start v1 app (`:8001`)
2. Start v2 naive app (`:8002`)
3. Start Streamlit dashboard (`:8501`)
4. Seed 37 HTTP interactions vào v1
5. Capture golden cassette via VCR.py (~60-90s)
6. Replay vs v1 → expect **1.0**
7. Replay vs v2 naive → expect **~0.595** (4 traps detected)
8. Generate PDF audit report
9. Open dashboard ở browser tự động

---

## Expected output

```
[1/9] Starting v1 app on :8001...                 OK
[2/9] Starting v2 naive on :8002...               OK
[3/9] Starting dashboard on :8501...              OK
[4/9] Seeding 37 interactions...                  OK
[5/9] Capturing cassette via VCR.py...            OK (37 interactions)
[6/9] Replaying vs v1...                          score: 1.000 (37/37 passed)
[7/9] Replaying vs v2 naive...                    score: 0.595 (22/37 passed)
        FAIL  GET /users/1            type_changes
        FAIL  POST /orders/calculate  type_changes
        FAIL  POST /products/tags     status_code_changed (200 → 422)
        FAIL  POST /reviews/bulk      status_code_changed (200 → 422)
[8/9] Generating PDF audit report...              audit_trail/run_<id>.report.pdf
[9/9] Opening dashboard...                        http://localhost:8501
```

---

## Dashboard state sau Workflow 1

- **Cột v1:** score = **1.0** (xanh)
- **Cột v2:** score = **0.595** (đỏ), 4 endpoints fail
- **Phase timeline:** CAPTURE ✓, REPLAY ✓
- **Audit chain:** 3 entries với SHA-256 links

---

## Talking points (nếu có audience)

| Thời điểm | Nội dung |
|-----------|---------|
| Khi capture chạy | *"VCR.py đang record 37 request/response pairs từ v1. Đây là ground truth."* |
| Khi v1 replay = 1.0 | *"Cassette replay lại chính v1 ra 1.0 — sanity check, cassette không bị corrupt."* |
| Khi v2 replay = 0.595 | *"v2 mới chỉ pass 22/37. 4 endpoints behavioral diff — bump-pydantic không catch được."* |
| Khi PDF gen | *"Đây là evidence package, hash-chained, EU AI Act Article 12 ready."* |

---

## Troubleshooting nhanh

### Port already in use
```powershell
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```

### v1 score < 1.0
```powershell
make reset-apps
```

### Capture stuck > 120s
Kill `demo_run.py`, restart. VCR.py có thể bị stuck nếu v1 không trả response.

### Dashboard không tự mở
Mở thủ công: http://localhost:8501

---

## Sau Workflow 1

Nếu chuyển sang Workflow 2 (Bob Orchestration):
```powershell
make reset-demo   # quan trọng: xóa cassettes + audit để Bob bắt đầu fresh
```

Nếu kết thúc demo:
```powershell
Ctrl+C            # trong terminal demo_run.py
```
