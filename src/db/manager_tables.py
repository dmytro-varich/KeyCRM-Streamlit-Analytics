from src.utils.time_utils import get_utc_now

def save_manager_data_to_mongo(collection, manager_name, manager_tables, manager_questions):
    doc = {
        "manager_name": manager_name,
        "manager_tables": manager_tables,
        "manager_questions": manager_questions,
        "saved_at": get_utc_now()
    }
    collection.replace_one({"manager_name": manager_name}, doc, upsert=True)


def save_all_managers_to_mongo(collection, all_manager_tables, all_manager_questions):
    for manager_name in all_manager_tables.keys():
        save_manager_data_to_mongo(
            collection,
            manager_name,
            all_manager_tables.get(manager_name, {}),
            all_manager_questions.get(manager_name, {})
        )