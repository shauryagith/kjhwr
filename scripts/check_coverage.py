import urllib.request
import json
from datetime import datetime, timedelta

def check_coverage():
    print("Checking January 2026 data availability in Elexon API...")
    
    # Check start of Jan 2026
    url_w_start = 'https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2025-12-30T00:00:00Z&publishDateTimeTo=2026-01-01T12:00:00Z'
    req = urllib.request.Request(url_w_start, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            print(f"WINDFOR around Jan 1: {len(data)} records")
            if data:
                starts = [r['startTime'] for r in data]
                print(f"  Earliest start: {min(starts)}, Latest start: {max(starts)}")
    except Exception as e:
        print("WINDFOR start error:", e)

    # Check mid Jan 2026
    url_w_mid = 'https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2026-01-15T00:00:00Z&publishDateTimeTo=2026-01-15T12:00:00Z'
    req = urllib.request.Request(url_w_mid, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            print(f"WINDFOR around Jan 15: {len(data)} records")
    except Exception as e:
        print("WINDFOR mid error:", e)

    # Check end of Jan 2026
    url_w_end = 'https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2026-01-31T00:00:00Z&publishDateTimeTo=2026-01-31T23:59:59Z'
    req = urllib.request.Request(url_w_end, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            print(f"WINDFOR around Jan 31: {len(data)} records")
    except Exception as e:
        print("WINDFOR end error:", e)

    # Check FUELHH start and end
    url_f_end = 'https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream?publishDateTimeFrom=2026-01-31T20:00:00Z&publishDateTimeTo=2026-01-31T23:59:59Z'
    req = urllib.request.Request(url_f_end, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = [r for r in json.loads(resp.read()) if r.get('fuelType') == 'WIND']
            print(f"FUELHH around Jan 31: {len(data)} wind records")
    except Exception as e:
        print("FUELHH end error:", e)

if __name__ == '__main__':
    check_coverage()
