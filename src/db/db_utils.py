from pymongo import MongoClient

def init_mongo_client(uri: str) -> MongoClient:
    """
    Initialize and return a MongoDB client.

    Args:
        uri (str): MongoDB connection URI.

    Returns:
        MongoClient: An instance of MongoDB client.
    """
    client = MongoClient(uri)
    return client


def get_database(client: MongoClient, db_name: str):
    """
    Retrieve a database from the MongoDB client.

    Args:
        client (MongoClient): The MongoDB client instance.
        db_name (str): Name of the database to retrieve.
    Returns:
        Database: The requested database instance.
    """
    return client[db_name]

def get_collection(db, collection_name: str):
    """
    Retrieve a collection from the database.

    Args:
        db: The database instance.
        collection_name (str): Name of the collection to retrieve.

    Returns:
        Collection: The requested collection instance.
    """
    return db[collection_name]


def get_latest_snapshot(collection):
    """
    Retrieve the latest snapshot from the collection.

    Args:
        collection: The MongoDB collection instance.

    Returns:
        dict: The latest snapshot document.
    """
    snapshot = collection.find_one(sort=[("date", -1)])
    return snapshot