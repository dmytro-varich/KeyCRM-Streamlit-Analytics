
# Standard library imports
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Third-party imports
import pandas as pd
import streamlit as st

# Add parent directory to sys.path for module imports
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

# Project-specific imports
from src.api.client import ApiClient
from src.components.tables import *
from src.utils.data_processing import process_all_data
from config.settings import MONGODB_URI, WEBHOOK_PROD_URL
from src.db.db_utils import init_mongo_client, get_database, get_collection
from src.components.texts import introduce_text, how_to_use_text, how_to_work_text
from src.utils.time_utils import get_utc_now, get_now_kyiv_iso, get_today_date_kyiv
from src.db.manager_tables import save_all_managers_to_mongo, save_manager_data_to_mongo

# Initialize api_client 
api_client = ApiClient()

# Initialize MongoDB client and get collection
client = init_mongo_client(MONGODB_URI)
db = get_database(client, "snapshots_db")

def main() -> None:
    """
    Main entry point for KeyCRM Analytics Streamlit app.
    Sets up UI and handles user actions.
    """
    pipeline_ids = [1, 3, 16, 20, 31, 2, 4, 15, 19, 32, 22, 24, 26, 30, 33, 46, 18] 

    # Get collection
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

    # Button to trigger analytics generation & Clear the data from tables
    col1, col2, col3, col4, _ = st.columns([1, 1, 1, 1, 7])
    with col1:
        if st.button("🔎 Переглянути аналітику", type="primary"):
            st.session_state["loading"] = True
            st.cache_data.clear()
            st.cache_resource.clear()
    with col2:
        if st.button("🧹 Очистити всі таблиці"):
            for k in list(st.session_state.keys()):
                if (
                    isinstance(k, str)
                    and (
                        k.startswith("manager_table_")
                        or k.startswith("manager_questions_")
                        or k.startswith("manager_tables")
                        or k.startswith("manager_questions")
                    )
                ):
                    del st.session_state[k]
    with col3:
        if st.button("💾 Зберегти всі таблиці"):
            pass
            # manager_tables = st.session_state.get("manager_tables", {})
            # manager_questions = st.session_state.get("manager_questions", {})
            # save_all_managers_to_mongo(collection, manager_tables, manager_questions)
            # st.success("Дані всіх менеджерів збережено в базі!")
    with col4: 
        if st.button("📥 Завантажити Excel"): 
            pass

    st.markdown("---")

    # If loading flag is set, show loading status and process data
    if st.session_state.get("loading", False):
        with st.status("🔎 Генеруємо аналітику...", expanded=False) as status:
            msg_placeholder = st.empty()

            # Inform user about data loading
            msg_placeholder.write("Будь ласка, зачекайте, поки ми завантажимо дані з KeyCRM...")
            status.update(label="📦 Завантаження карток...", state="running")

            # Fetch all cards for all pipelines
            today_date = get_today_date_kyiv()
            filters = {}
            filters['updated_between'] = f"{today_date} 00:00:00, {today_date} 23:59:59"
            all_cards = api_client.fetch_all_pipeline_cards(
                pipeline_ids,
                include="manager, custom_fields",
                filters=filters   
            ) or []

            # cards_from_n8n = get_n8n_webhook_data("WEBHOOK_PROD_URL") or []
            # if cards_from_n8n:
            #     msg_placeholder.write(f"Отримано {len(cards_from_n8n)} карток з n8n вебхука.")
            #     all_cards.extend(cards_from_n8n)

            if not all_cards:
                status.update(label="⚠️ Не знайдено карток для аналізу.", state="error")
                msg_placeholder.write("Будь ласка, перевірте підключення до KeyCRM та наявність карток.")
            else:
                msg_placeholder.write("Аналітика формується... Це може зайняти кілька секунд ⏳")
                status.update(label="🧮 Обробка даних...", state="running")

                # Process all data and store results in session state
                filtered_all_cards, manager_dict, calls_total, calls_mgr_stats = process_all_data(api_client, all_cards, base_cards)
                
                now_kyiv = get_now_kyiv_iso()
                created_at = get_utc_now()   
                today_date = get_today_date_kyiv()

                result = {
                    "timestamp": now_kyiv,
                    "createdAt": created_at,
                    "cards": filtered_all_cards,
                    "analytics": manager_dict,
                    "count": len(filtered_all_cards), 
                    "calls_total": calls_total, 
                    "calls_mgr_stats": calls_mgr_stats
                }

                # analytics_collection = get_collection(db, "analytics_results")
                # analytics_collection.insert_one(result)
                st.session_state["all_data"] = result
                msg_placeholder.write("Підготовка результатів...")

                # Clear loading messages and mark as complete
                msg_placeholder.write("Вже скоро аналітика по менеджерам буде готово!")
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
                now_kyiv = get_now_kyiv_iso()
                created_at = get_utc_now()   
                today_date = get_today_date_kyiv()

                snapshot_data = {
                    "timestamp": now_kyiv,           # Human-readable Kyiv time
                    "date": str(today_date),         # Date as string (Kyiv)
                    "createdAt": created_at,         # For MongoDB TTL index (must be datetime object)
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
    if "all_data" in st.session_state and st.session_state["all_data"]:
        all_data = st.session_state["all_data"]
        analytics_data = all_data.get("analytics")
        calls_total = all_data.get("calls_total")
        calls_mgr_stats = all_data.get("calls_mgr_stats")
        if not analytics_data:
            st.warning("⚠️ Немає даних аналітики для завантаження або відображення.")
            return
        today_date = get_today_date_kyiv()
        st.header(f"📑 Аналітика менеджерів ({today_date})")
        
        # Button to download an excel file with all manager tables
        managers = sorted(analytics_data.keys())
        if not managers:
            st.info("⚠️ Немає даних по менеджерам для відображення.")
        else:
            mgr_collection = get_collection(db, 'manager_tables')
            tabs = st.tabs(managers)
            for tab, mgr in zip(tabs, managers):
                with tab:
                    # Prepare single-manager structures expected by render/get_excel
                    mgr_analytics = {mgr: analytics_data[mgr]}
                    mgr_calls_total = {mgr: calls_total.get(mgr, 0) if calls_total else 0}

                    # Render the manager's analytics table(s)
                    render_manager_tables(mgr_analytics, mgr_calls_total)

                    # -------------------------------
                    # 📋 Section: Manager's Cards
                    # -------------------------------
                    raw_cards = all_data.get("cards", [])

                    def _get_manager_full_name(card: Any) -> Any:
                        if not isinstance(card, dict):
                            return None
                        m = card.get("manager")
                        if isinstance(m, dict):
                            return m.get("full_name")
                        return m

                    manager_cards_by_state: Dict[str, List[Dict[str, Any]]] = {}

                    # If cards stored as dict(state -> list), preserve states
                    if isinstance(raw_cards, dict):
                        for state_key, lst in raw_cards.items():
                            if not isinstance(lst, list):
                                continue
                            for c in lst:
                                if _get_manager_full_name(c) == mgr:
                                    manager_cards_by_state.setdefault(state_key, []).append(c)
                    elif isinstance(raw_cards, list):
                        # fallback: no state info, put everything to "Усі"
                        for c in raw_cards:
                            if _get_manager_full_name(c) == mgr:
                                manager_cards_by_state.setdefault("Усі", []).append(c)

                    if manager_cards_by_state:
                        total = sum(len(v) for v in manager_cards_by_state.values())
                        with st.expander(f"💳 Картки менеджера — {mgr} ({total})"):
                            df_cards = create_simple_dataframe(manager_cards_by_state)
                            st.dataframe(df_cards, width="stretch")

                    if calls_mgr_stats and calls_mgr_stats.get(mgr):
                        st.subheader("☎️ Статистика дзвінків")
                        render_manager_calls_stats(mgr, calls_mgr_stats)
                        render_manager_calls_details({mgr: calls_mgr_stats[mgr]})

                    # Retrieve saved manager tables from the session
                    manager_saved_tables = get_tables_from_session('manager_tables').get(mgr)

                    st.markdown('---')
                    st.markdown("> В наступному оновленні: редагуючі таблиці.")
                    # if st.button(f"💾 Зберегти", key=f"save_{mgr}"):
                    #     try:
                    #         manager_tables = {}
                    #         manager_questions = {}

                    #         diamonds_key = f"manager_table_{mgr.replace(' ', '_')}_diamonds"
                    #         if diamonds_key in st.session_state:
                    #             data = st.session_state[diamonds_key]

                    #             # ✅ Если это DataFrame — просто конвертируем
                    #             if isinstance(data, pd.DataFrame):
                    #                 manager_tables["diamonds"] = data.to_dict(orient="records")

                    #             # ✅ Если это структура Streamlit редактора
                    #             elif isinstance(data, dict) and set(data.keys()) >= {"edited_rows", "added_rows", "deleted_rows"}:
                    #                 # Преобразуем все изменения в единый список
                    #                 rows = []
                    #                 # Извлекаем edited_rows
                    #                 for _, v in data.get("edited_rows", {}).items():
                    #                     rows.append(v)
                    #                 # Добавляем added_rows
                    #                 rows.extend(data.get("added_rows", []))
                    #                 manager_tables["diamonds"] = rows

                    #             # ✅ Если это уже list of dict
                    #             elif isinstance(data, list):
                    #                 manager_tables["diamonds"] = data

                    #             else:
                    #                 manager_tables["diamonds"] = []

                    #         save_manager_data_to_mongo(mgr_collection, mgr, manager_tables, manager_questions)
                    #         st.success(f"✅ Дані для {mgr} успішно збережено!")

                    #     except Exception as e:
                    #         st.error(f"🚫 Помилка при збереженні: {e}")
                    # # -------------------------------
                    # # 💎 Section: New Diamonds
                    # # -------------------------------
                    # diamonds_columns = [
                    #     "Опис (місто, вид діяльності)", 
                    #     "URL на лід", 
                    #     "Який наступний крок", 
                    #     "Які складнощі виникли", 
                    #     "Яка допомога треба", 
                    #     "Хто може допомогти", 
                    #     "Коментар"
                    # ]
                    
                    # diamonds_key = f"manager_table_{mgr.replace(' ', '_')}_diamonds"

                    # if manager_saved_tables and "diamonds" in manager_saved_tables:
                    #     initial_df = pd.DataFrame(manager_saved_tables["diamonds"])
                    # else:
                    #     initial_df = default_table_template(rows=5, columns=diamonds_columns)

                    # # Инициализация таблицы (один раз)
                    # init_manager_table(diamonds_key, initial_df)

                    # st.subheader("💎 Нові Діаманти")
                    # diamonds_edited_df = render_editable_manager_table(
                    #     mgr,
                    #     key_suffix="_diamonds",
                    #     initial_df=initial_df
                    # )


                    

                    
if __name__ == "__main__":
    main()