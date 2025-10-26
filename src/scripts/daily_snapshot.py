import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import json
from src.api.client import ApiClient
from config.settings import MONGODB_URI
from datetime import datetime
from src.utils.time_utils import today_date, SERVER_TZ
from src.utils.db_utils import init_mongo_client, get_database, get_collection

def main():
    api = ApiClient()
    pipeline_ids = list(range(1, 18))

    cards = api.fetch_all_pipeline_cards(pipeline_ids, include="manager,custom_fields")
    cards = cards or []
    cards = [card for card in cards if not card.get("is_finished", False)]
    
    snapshot_data = {
        "timestamp": datetime.now(SERVER_TZ).isoformat(),
        "date": str(today_date),
        "cards": cards, 
        "count": len(cards)
    }

    # os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    # with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
    #     json.dump(snapshot_data, f, ensure_ascii=False, indent=2)

    client = init_mongo_client(MONGODB_URI)
    db = get_database(client, "snapshots_db")
    collection = get_collection(db, "snapshots")
    collection.insert_one(snapshot_data)

    print(f"✅ Snapshot saved to MongoDB. Cards count: {len(cards)}")

if __name__ == "__main__":
    main()