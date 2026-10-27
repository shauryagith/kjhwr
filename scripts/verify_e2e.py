import threading
import time
import urllib.request
import json
import uvicorn
from app.main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8008, log_level="warning")

def verify():
    print("Starting background server on port 8008...")
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(2)

    endpoints = [
        "/",
        "/api/v1/health",
        "/api/v1/metadata",
        "/api/v1/analysis/summary?start_date=2026-01-01&end_date=2026-01-31&cutoff_preset=DA_1100",
        "/api/v1/analysis/timeseries?start_date=2026-01-01&end_date=2026-01-02&cutoff_preset=DA_1100",
        "/api/v1/analysis/daily?start_date=2026-01-01&end_date=2026-01-05&cutoff_preset=DA_1100",
        "/api/v1/analysis/diurnal?start_date=2026-01-01&end_date=2026-01-07&cutoff_preset=DA_1100",
        "/api/v1/analysis/errors?start_date=2026-01-01&end_date=2026-01-07&cutoff_preset=DA_1100",
        "/api/v1/analysis/forecast-table?start_date=2026-01-01&end_date=2026-01-02&page=1&page_size=5",
        "/api/v1/analysis/export-csv?start_date=2026-01-01&end_date=2026-01-02&cutoff_preset=DA_1100"
    ]

    base = "http://127.0.0.1:8008"
    all_ok = True
    for ep in endpoints:
        url = base + ep
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "E2E-Tester"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
                ct = resp.headers.get("Content-Type", "")
                data = resp.read()
                print(f"[{status}] {ep[:45]}... (size: {len(data)} bytes, type: {ct[:15]})")
        except Exception as e:
            print(f"[FAIL] {ep}: {e}")
            all_ok = False

    if all_ok:
        print("\nALL ENDPOINTS VERIFIED SUCCESSFULLY OVER REAL HTTP ON PORT 8008!")
    else:
        raise RuntimeError("One or more endpoint tests failed.")

if __name__ == "__main__":
    verify()
