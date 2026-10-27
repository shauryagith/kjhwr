import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.ingestion import ingestion_service
from app.repositories.data_store import data_store

async def main():
    print("Starting full January 2026 Elexon ingestion...")
    act_count, fc_count = await ingestion_service.fetch_month_data(year=2026, month=1, force_refresh=True)
    print(f"Ingestion finished successfully!")
    print(f"Total FUELHH actual wind records cached: {act_count}")
    print(f"Total WINDFOR forecast records cached: {fc_count}")
    
    # Run test matching
    df_matched = ingestion_service.match_intervals(start_date="2026-01-01", end_date="2026-01-31")
    print(f"Total hourly intervals matched: {len(df_matched)}")
    valid = df_matched[df_matched['actualMW'].notna() & df_matched['forecastMW'].notna()]
    print(f"Valid matched intervals: {len(valid)} / {len(df_matched)} ({len(valid)/len(df_matched)*100:.1f}%)")
    if not valid.empty:
        err = valid['forecastMW'] - valid['actualMW']
        print(f"Mean Absolute Error (MAE): {err.abs().mean():.2f} MW")
        print(f"RMSE: {(err**2).mean()**0.5:.2f} MW")
        print(f"Mean Error (Bias): {err.mean():.2f} MW")

if __name__ == "__main__":
    asyncio.run(main())
