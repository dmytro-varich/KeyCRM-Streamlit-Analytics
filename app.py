
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
from src.utils.time_utils import today_date, KYIV_TZ
from src.utils.data_processing import process_all_data
from src.utils.db_utils import init_mongo_client, get_database, get_collection
from src.components.texts import introduce_text, how_to_use_text, how_to_work_text
from src.components.tables import render_manager_tables, create_simple_dataframe, get_managers_excel_download


def main() -> None:
    """
    Main entry point for KeyCRM Analytics Streamlit app.
    Sets up UI and handles user actions.
    """
    api_client = ApiClient()
    pipeline_ids = [1, 3, 16, 20, 31, 2, 4, 15, 19, 32, 22, 24, 26, 30, 33, 46, 18] 

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
    snapshot = collection.find_one(sort=[("createdAt", -1)])
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
        for key in ["loading", "all_data"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state["loading"] = True
        st.rerun()
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

    st.sidebar.header("⚙️ Налаштування")
    if st.sidebar.button("💾 Оновити вручну стан карток у воронках", type="primary"):
        try:
            with st.spinner("Оновлення та збереження карток у базі..."):
                cards = api_client.fetch_all_pipeline_cards(pipeline_ids, include="manager,custom_fields")
                cards = cards or []
                cards = [card for card in cards if not card.get("is_finished", False)]
                
                now_kyiv = datetime.now(KYIV_TZ)
                snapshot_data = {
                    "timestamp": now_kyiv.isoformat(),           # Human-readable Kyiv time
                    "date": str(today_date),                     # Date as string (Kyiv)
                    "createdAt": now_kyiv,                       # For MongoDB TTL index (must be datetime object)
                    "cards": cards,
                    "count": len(cards)
                }

                collection.insert_one(snapshot_data)
            st.success("✅ Стан карток успішно оновлено та збережено в базі!")
            st.rerun()
        except Exception as e:
            st.error(f"🚫 Помилка при оновленні та збереженні карток: {e}")


def display_results() -> None:
    """
    Display analytics results and cards table.
    """
    if "all_data" in st.session_state:
        data = st.session_state["all_data"]
        st.header("📑 Аналітика менеджерів")
        # Button to download an excel file with all manager tables
        excel_buffer = get_managers_excel_download(data["analytics"])
        st.download_button(
            label="⬇️ Завантажити всі таблиці",
            data=excel_buffer,
            file_name=f"keycrm_analytics_all_managers_{today_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Render manager analytics tables
        render_manager_tables(data["analytics"])

        # Show all cards in an expandable dataframe
        with st.expander("📋 Усі картки"):
            df_cards = create_simple_dataframe(data["cards"])
            st.dataframe(df_cards, width="stretch")


if __name__ == "__main__":
    main()