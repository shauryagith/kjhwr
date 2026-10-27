import urllib.request
import json
from datetime import datetime

url_f = 'https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream?publishDateTimeFrom=2026-01-01T00:00:00Z&publishDateTimeTo=2026-01-01T06:00:00Z'
req = urllib.request.Request(url_f, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    f_data = [r for r in json.loads(resp.read()) if r.get('fuelType') == 'WIND']

print("FUELHH (Wind):")
for r in sorted(f_data, key=lambda x: x['startTime']):
    print(f"  startTime: {r['startTime']}, publishTime: {r['publishTime']}, gen: {r['generation']} MW, SP: {r['settlementPeriod']}")

url_w = 'https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2026-01-01T02:00:00Z&publishDateTimeTo=2026-01-01T03:00:00Z'
req = urllib.request.Request(url_w, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    w_data = json.loads(resp.read())

print("\nWINDFOR:")
for r in sorted(w_data, key=lambda x: x['startTime'])[:10]:
    print(f"  startTime: {r['startTime']}, publishTime: {r['publishTime']}, gen: {r['generation']} MW")
