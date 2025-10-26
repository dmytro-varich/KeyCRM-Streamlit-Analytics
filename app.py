
# Standard library imports
import sys
from pathlib import Path
from datetime import datetime

# Third-party imports
import streamlit as st

# Add parent directory to sys.path for module imports
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

# Project-specific imports
from src.api.client import ApiClient
from config.settings import MONGODB_URI 
from src.utils.time_utils import today_date
from src.utils.file_utils import load_json_file
from src.utils.data_processing import process_all_data
from src.utils.db_utils import init_mongo_client, get_database, get_collection
from src.components.tables import render_manager_tables, create_simple_dataframe
from src.components.texts import introduce_text, how_to_use_text, how_to_work_text


def main() -> None:
    """
    Main entry point for KeyCRM Analytics Streamlit app.
    Sets up UI and handles user actions.
    """
    api_client = ApiClient()
    pipeline_ids = list(range(1, 18))  # List of pipeline IDs to fetch

    # Initialize MongoDB client and get collection
    client = init_mongo_client(MONGODB_URI)
    db = get_database(client, "snapshots_db")
    collection = get_collection(db, "snapshots")

    # Streamlit page configuration
    st.set_page_config(
        page_title="KeyCRM Analytics",
        page_icon="📊",
        layout="wide"
    )
    st.title("📊 KeyCRM Аналітична Панель")
    st.markdown(introduce_text)

    # Show usage instructions
    with st.expander("ℹ️ Як користуватись панеллю аналітики?"):
        st.markdown(how_to_use_text)

    # Show analytics classification explanation
    with st.expander("📘 Як працює класифікація аналітики?"):
        st.markdown(how_to_work_text)

    # Load latest snapshot from MongoDB
    snapshot = collection.find_one(sort=[("date", -1)])
    if snapshot:
        base_cards = snapshot.get("cards", [])
        last_updated = snapshot.get("timestamp")
        if last_updated:
            dt = datetime.fromisoformat(last_updated)
            formatted = dt.strftime("%d.%m.%Y о %H:%M")
            st.info(f"⏰ Базовий стан карток оновлено {formatted}")
        else:
            st.warning("⚠️ У знімку відсутнє поле часу оновлення.")
    else:
        st.warning("⚠️ Сьогоднішній знімок ще не створено.")
        base_cards = []

    # Button to trigger analytics generation
    if st.button("🔎 Переглянути аналітику", type="primary"):
        st.session_state["loading"] = True  # Set loading flag
        st.session_state["all_data"] = None

    st.markdown("---")

    # If loading flag is set, show loading status and process data
    if st.session_state.get("loading", False):
        with st.status("🔎 Генеруємо аналітику...", expanded=False) as status:
            msg_placeholder = st.empty()

            # Inform user about data loading
            msg_placeholder.write("Будь ласка, зачекайте, поки ми завантажимо дані з KeyCRM...")
            status.update(label="📦 Завантаження карток...", state="running")

            # Fetch all cards for all pipelines
            all_cards = api_client.fetch_all_pipeline_cards(
                pipeline_ids,
                include="manager, custom_fields",
            )

            if not all_cards:
                status.update(label="⚠️ Не знайдено карток для аналізу.", state="error")
                msg_placeholder.write("Будь ласка, перевірте підключення до KeyCRM та наявність карток.")
            else:
                msg_placeholder.write("Аналітика формується... Це може зайняти кілька секунд ⏳")
                status.update(label="🧮 Обробка даних...", state="running")

                # Process all data and store results in session state
                filtered_all_cards, manager_dict = process_all_data(api_client, all_cards, base_cards)
                st.session_state["all_data"] = {
                    "cards": filtered_all_cards,
                    "analytics": manager_dict,
                    "count": len(filtered_all_cards)
                }
                msg_placeholder.write("Підготовка результатів...")

                # Clear loading messages and mark as complete
                msg_placeholder.empty()
                status.update(label="✅ Аналітику згенеровано!", state="complete")

        st.session_state["loading"] = False  # Remove loading flag
        st.rerun()

    # Show results only if analytics data is available and not loading
    elif "all_data" in st.session_state and st.session_state["all_data"]:
        display_results()


def display_results() -> None:
    """
    Display analytics results and cards table.
    """
    if "all_data" in st.session_state:
        data = st.session_state["all_data"]
        st.header("📑 Аналітика менеджерів")
        # Render manager analytics tables
        render_manager_tables(data["analytics"])

        # Show all cards in an expandable dataframe
        with st.expander("📋 Усі картки"):
            df_cards = create_simple_dataframe(data["cards"])
            st.dataframe(df_cards, width="stretch")


if __name__ == "__main__":
    main()