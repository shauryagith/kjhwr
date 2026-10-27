import urllib.request
import json

# Check WINDFOR across a wider time range, e.g. a few days in Jan 2026
url = 'https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2026-01-01T00:00:00Z&publishDateTimeTo=2026-01-03T00:00:00Z'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

print("Total WINDFOR records in 2 days:", len(data))
# Check unique intervals between startTimes
pub_times = sorted(list(set(r['publishTime'] for r in data)))
print(f"Total distinct publish times in 48h: {len(pub_times)}")
print("Sample publish times:", pub_times[:10])

# Check for any :30 startTimes in WINDFOR
half_hour_starts = [r for r in data if ':30' in r['startTime']]
print(f"WINDFOR records with :30 startTime: {len(half_hour_starts)}")

# Check what the time horizon of each publication is
for pt in pub_times[:3]:
    sub = [r for r in data if r['publishTime'] == pt]
    st = sorted([r['startTime'] for r in sub])
    print(f"Publish {pt}: {len(sub)} forecasts, min start: {st[0]}, max start: {st[-1]}")
