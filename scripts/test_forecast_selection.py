import urllib.request
import json
from datetime import datetime, timezone, timedelta
import pandas as pd

# Fetch WINDFOR for Jan 1-3
url_w = 'https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2025-12-30T00:00:00Z&publishDateTimeTo=2026-01-03T12:00:00Z'
req = urllib.request.Request(url_w, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    w_data = json.loads(resp.read())

df_w = pd.DataFrame(w_data)
df_w['publishTime'] = pd.to_datetime(df_w['publishTime'])
df_w['startTime'] = pd.to_datetime(df_w['startTime'])

print(f"Loaded {len(df_w)} WINDFOR forecasts.")

# Test delivery interval: 2026-01-02 12:00:00 UTC
target_delivery = pd.to_datetime('2026-01-02 12:00:00+00:00')
# D-1 11:00 cutoff:
cutoff = pd.to_datetime('2026-01-01 11:00:00+00:00')

forecasts_for_target = df_w[df_w['startTime'] == target_delivery]
print(f"Total forecasts for target delivery {target_delivery}: {len(forecasts_for_target)}")
print("All published times for this delivery:")
for _, row in forecasts_for_target.sort_values('publishTime').iterrows():
    is_eligible = row['publishTime'] <= cutoff
    print(f"  pub: {row['publishTime']} | gen: {row['generation']} MW | eligible (<={cutoff}): {is_eligible}")

eligible = forecasts_for_target[forecasts_for_target['publishTime'] <= cutoff]
if not eligible.empty:
    selected = eligible.sort_values('publishTime').iloc[-1]
    print(f"\nSELECTED as of D-1 11:00: pub={selected['publishTime']}, gen={selected['generation']} MW")
else:
    print("\nNo eligible forecast found before cutoff.")
