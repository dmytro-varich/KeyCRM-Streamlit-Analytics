from pymongo import ASCENDING
from config.settings import MONGODB_URI
from src.db.db_utils import init_mongo_client, get_database

def main() -> None:
    client = init_mongo_client(MONGODB_URI)
    db = get_database(client, "snapshots_db")
    collection = db["analytics_results"]

    collection.create_index(
        [("createdAt", ASCENDING)],
        expireAfterSeconds=2592000
    )

if __name__ == '__main__': 
    main()