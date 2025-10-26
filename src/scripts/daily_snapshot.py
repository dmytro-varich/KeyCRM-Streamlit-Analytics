import os
import json
from src.api.client import ApiClient
from datetime import datetime, timezone
from config.settings import SNAPSHOT_DIR
from src.utils.time_utils import today_date

SNAPSHOT_FILE = os.path.join(SNAPSHOT_DIR, f"base_snapshot_{today_date}.json")

def main():
    api = ApiClient()
    pipeline_ids = list(range(1, 18))

    cards = api.fetch_all_pipeline_cards(pipeline_ids, include="manager,custom_fields")
    cards = cards or []

    snapshot_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cards": cards
    }

    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(snapshot_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Snapshot saved to {SNAPSHOT_FILE}. Cards count: {len(cards)}")

if __name__ == "__main__":
    main()