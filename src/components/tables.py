import pandas as pd
import streamlit as st
from io import BytesIO
from typing import Dict, Any, List, Optional
from src.utils.time_utils import format_duration
from src.utils.analytics import init_category, get_custom_field, define_pipeline


def render_manager_tables(manager_dict: Dict[str, Any], calls_total: Dict[str, int]) -> None:
    """
    Displays analytics as HTML tables with a grouped column "Closed from them".
    """
    default_categories = ["База", "Суміжні", "Алмази", "Діаманти"]
    custom_keys = ["Рефералка", "Зустріч", "Навчання", "Планування (надіслав)", "Планування (пообіцяв)"]

    for manager, categories in manager_dict.items():
        st.markdown(f"### 👤 {manager}")

        html = """
        <table style='border-collapse:collapse;width:100%;text-align:center;'>
        <tr style='font-weight:bold;'>
            <th rowspan='2'>Категорія</th>
            <th colspan='2'>Нові</th>
            <th colspan='2'>Попередні</th>
            <th rowspan='2'>Не кваліфіковані</th>
            <th colspan='5'>З них закрито:</th>
        </tr>
        <tr style='font-weight:bold;'>
            <th>Прогріті</th><th>Не прогріті</th>
            <th>Прогріті</th><th>Не прогріті</th>
            <th>Рефералка</th><th>Зустріч</th><th>Навчання</th><th>Планування (надіслав)</th><th>Планування (пообіцяв)</th>
        </tr>
        """

        total = init_category()

        for category in default_categories:
            stats = categories.get(category, init_category())

            html += "<tr>"
            html += f"<td>{category}</td>"
            html += f"<td>{stats['Нові']['Прогріті']}</td>"
            html += f"<td>{stats['Нові']['Не прогріті']}</td>"
            html += f"<td>{stats['Попередні']['Прогріті']}</td>"
            html += f"<td>{stats['Попередні']['Не прогріті']}</td>"
            html += f"<td>{stats['Не кваліфіковані']}</td>"
            html += f"<td>{stats['Рефералка']}</td>"
            html += f"<td>{stats['Зустріч']}</td>"
            html += f"<td>{stats['Навчання']}</td>"
            html += f"<td>{stats['Планування (надіслав)']}</td>"
            html += f"<td>{stats['Планування (пообіцяв)']}</td>"
            html += "</tr>"

            # totals
            for s in ["Нові", "Попередні"]:
                total[s]["Прогріті"] += stats[s]["Прогріті"]
                total[s]["Не прогріті"] += stats[s]["Не прогріті"]
            for key in ["Не кваліфіковані", *custom_keys]:
                total[key] += stats[key]

        # totals row
        html += "<tr style='font-weight:bold;'>"
        html += "<td>Всього</td>"
        html += f"<td>{total['Нові']['Прогріті']}</td>"
        html += f"<td>{total['Нові']['Не прогріті']}</td>"
        html += f"<td>{total['Попередні']['Прогріті']}</td>"
        html += f"<td>{total['Попередні']['Не прогріті']}</td>"
        html += f"<td>{total['Не кваліфіковані']}</td>"
        html += f"<td>{total['Рефералка']}</td>"
        html += f"<td>{total['Зустріч']}</td>"
        html += f"<td>{total['Навчання']}</td>"
        html += f"<td>{total['Планування (надіслав)']}</td>"
        html += f"<td>{total['Планування (пообіцяв)']}</td>"
        html += "</tr>"

        html += "<tr style='font-weight:bold;'>"
        html += "<td>Всього дозвонів за день</td>"
        html += f"<td colspan='11'>{calls_total.get(manager, 0)}</td>"
        html += "</tr>"
        html += "</table>"

        st.markdown(html, unsafe_allow_html=True)


def get_managers_excel_download(manager_dict: dict,
                                calls_total: dict,
                                manager_tables: Optional[Dict[str, Any]] = None,
                                manager_questions: Optional[Dict[str, Any]] = None) -> BytesIO:
    """
    Creates an Excel file with tables for all managers (each on a separate sheet).
    Also appends any edited manager tables and question tables found in
    manager_tables / manager_questions (both are dicts from session_state).
    """
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        for manager, categories in manager_dict.items():
            # --- existing analytics export (unchanged) ---
            default_categories = ["База", "Суміжні", "Алмази", "Діаманти"]
            custom_keys = ["Рефералка", "Зустріч", "Навчання", "Планування (надіслав)", "Планування (пообіцяв)"]
            total = init_category()
            export_rows = []
            for category in default_categories:
                stats = categories.get(category, init_category())
                export_rows.append({
                    "Категорія": category,
                    "Нові - Прогріті": stats.get('Нові', {}).get('Прогріті', 0),
                    "Нові - Не прогріті": stats.get('Нові', {}).get('Не прогріті', 0),
                    "Попередні - Прогріті": stats.get('Попередні', {}).get('Прогріті', 0),
                    "Попередні - Не прогріті": stats.get('Попередні', {}).get('Не прогріті', 0),
                    "Не кваліфіковані": stats.get('Не кваліфіковані', 0),
                    "Рефералка": stats.get('Рефералка', 0),
                    "Зустріч": stats.get('Зустріч', 0),
                    "Навчання": stats.get('Навчання', 0),
                    "Планування (надіслав)": stats.get('Планування (надіслав)', 0),
                    "Планування (пообіцяв)": stats.get('Планування (пообіцяв)', 0),
                })
                for s in ["Нові", "Попередні"]:
                    total[s]["Прогріті"] += stats[s]["Прогріті"]
                    total[s]["Не прогріті"] += stats[s]["Не прогріті"]
                for key in ["Не кваліфіковані", *custom_keys]:
                    total[key] += stats[key]
            export_rows.append({
                "Категорія": "Всього",
                "Нові - Прогріті": total['Нові']['Прогріті'],
                "Нові - Не прогріті": total['Нові']['Не прогріті'],
                "Попередні - Прогріті": total['Попередні']['Прогріті'],
                "Попередні - Не прогріті": total['Попередні']['Не прогріті'],
                "Не кваліфіковані": total['Не кваліфіковані'],
                "Рефералка": total['Рефералка'],
                "Зустріч": total['Зустріч'],
                "Навчання": total['Навчання'],
                "Планування (надіслав)": total['Планування (надіслав)'],
                "Планування (пообіцяв)": total['Планування (пообіцяв)'],
            })
            export_rows.append({
                "Категорія": "Всього дозвонів за день",
                "Нові - Прогріті": "",
                "Нові - Не прогріті": "",
                "Попередні - Прогріті": "",
                "Попередні - Не прогріті": "",
                "Не кваліфіковані": "",
                "Рефералка": "",
                "Зустріч": "",
                "Навчання": "",
                "Планування (надіслав)": "", 
                "Планування (пообіцяв)": calls_total.get(manager, 0),
            })
            df = pd.DataFrame(export_rows)
            sheet_name = manager[:31]
            df.to_excel(writer, index=False, sheet_name=sheet_name)

            # --- append edited manager tables if present ---
            if manager_tables:
                # common suffixes you use in app: "" (default), "_diamonds", "_calc", "_calculations"
                for suffix in ["", "_diamonds", "_calc", "_calculations"]:
                    key = f"{manager}{suffix}"
                    tbl = manager_tables.get(key)
                    if tbl:
                        try:
                            df_tbl = pd.DataFrame(tbl)
                            sheet = f"{manager[:20]} {('tbl' if suffix == '' else suffix.strip('_'))}"
                            sheet = sheet[:31]
                            df_tbl.to_excel(writer, index=False, sheet_name=sheet)
                        except Exception:
                            # ignore malformed table
                            pass

            # --- append questions/answers sheets if present ---
            if manager_questions:
                for q_suffix in ["calls_analysis", "tomorrow_plan", "tommorow_plan"]:
                    key = f"{manager}{q_suffix}"
                    qtbl = manager_questions.get(key)
                    if qtbl:
                        try:
                            df_q = pd.DataFrame(qtbl)
                            sheet = f"{manager[:20]} {q_suffix}"
                            sheet = sheet[:31]
                            df_q.to_excel(writer, index=False, sheet_name=sheet)
                        except Exception:
                            pass

    excel_buffer.seek(0)
    return excel_buffer


def create_simple_dataframe(cards: Dict[str, List[Dict[str, Any]]]) -> pd.DataFrame:
    """
    Create a combined DataFrame from {"Нові": [...], "Попередні": [...]}.
    """
    rows: List[Dict[str, Any]] = []

    for state, card_list in cards.items():
        for card in card_list:
            created = (card.get("created_at") or "")[:10]
            updated = (card.get("updated_at") or "")[:10]
            pipeline_id = card.get("pipeline_id")
            if pipeline_id is None:
                pipeline_label = "N/A"
            else:
                try:
                    pipeline_label = define_pipeline(int(pipeline_id))
                except (TypeError, ValueError):
                    pipeline_label = "N/A"

            row = {
                "Тип": state,
                "ID": card.get("id"),
                "Назва": card.get("title"),
                "Воронка": pipeline_label or "N/A",
                "Менеджер": card.get("manager", {}).get("full_name", "N/A"),
                "Прогрітий (готовий працювати)": get_custom_field(card, "ПРОГРІТИЙ (готовий працювати)"),
                "Закр. Зустріч КИЇВ": get_custom_field(card, "Закр. Зустріч КИЇВ"),
                "Закр. Зустріч ONLINE": get_custom_field(card, "Закр. Зустріч ONLINE"),
                "Закр. Навчання В ЗАПИСІ": get_custom_field(card, "Закр. Навчання В ЗАПИСІ"),
                "Кваліфікований повністю": get_custom_field(card, "Кваліфікований повністю"),
                "Створено": created,
                "Оновлено": updated,
            }
            rows.append(row)

    return pd.DataFrame(rows)


def render_manager_calls_stats(manager: str, calls_mgr_stats: Dict[str, List[Dict[str, int]]]) -> None:
    """
    Render an HTML table with columns: Менеджер, Успішні дзвінки, Duration (ч:хв:сек).
    calls_mgr_stats: {manager_name: [{"external_number": ..., "duration": ...}, ...], ...}
    duration — в секундах!
    """
    if manager in calls_mgr_stats:
        stats = {manager: calls_mgr_stats[manager]}
    else:
        stats = calls_mgr_stats

    html = """
    <table style='border-collapse:collapse;width:100%;text-align:center;'>
        <tr style='font-weight:bold;'>
            <th>Менеджер</th>
            <th>Успішні дзвінки</th>
            <th>Загальна тривалість</th>
        </tr>
    """

    for mgr, calls in stats.items():
        total_calls = len(calls)
        total_duration_sec = sum(call.get("duration", 0) for call in calls)
        duration_str = format_duration(total_duration_sec)
        if manager == mgr:
            html += f"<tr><td>{mgr}</td><td>{total_calls}</td><td>{duration_str}</td></tr>"

    html += "</table>"

    st.markdown(html, unsafe_allow_html=True)


def render_manager_calls_details(calls_mgr_stats: Dict[str, List[Dict[str, int]]]) -> None:
    """
    For each manager, displays a drop-down list with a table:
    external_number | number of calls | total duration (h:hv:sec)
    """
    for manager, calls in calls_mgr_stats.items():
        number_stats = {}
        for call in calls:
            num = call.get("external_number")
            dur = call.get("duration", 0)
            if num not in number_stats:
                number_stats[num] = {"count": 0, "duration": 0}
            number_stats[num]["count"] += 1
            number_stats[num]["duration"] += dur

        with st.expander(f"📞 Деталізація дзвінків менеджера {manager}"):
            html = """
            <table style='border-collapse:collapse;width:100%;text-align:center;'>
                <tr style='font-weight:bold;'>
                    <th>Номер</th>
                    <th>Кількість дзвінків</th>
                    <th>Загальна тривалість</th>
                </tr>
            """
            for num, stat in number_stats.items():
                html += (
                    f"<tr><td>{num}</td>"
                    f"<td>{stat['count']}</td>"
                    f"<td>{format_duration(stat['duration'])}</td></tr>"
                )
            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)


def default_table_template(rows: int = 5, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """Return default empty dataframe for manager editable table."""
    if columns is None:
        columns = ["ID", "Назва", "Менеджер", "Створено", "Оновлено"]
    data = {col: ["" for _ in range(rows)] for col in columns}
    return pd.DataFrame(data)

def init_manager_table(key: str, df: pd.DataFrame):
    if key not in st.session_state:
        st.session_state[key] = df.copy()

def render_editable_manager_table(manager: str,
                                  key_suffix: str = "",
                                  initial_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:

    key = f"manager_table_{manager.replace(' ', '_')}{key_suffix}"

    if key not in st.session_state:
        st.session_state[key] = initial_df.copy() if initial_df is not None else default_table_template()

    edited = st.data_editor(
        st.session_state[key],
        width='stretch',
        num_rows="dynamic",
        key=key + "_editor"
    )

    # 3) Обновление state
    st.session_state[key] = edited

    return edited


def get_tables_from_session(table_key: str) -> Dict[str, Any]:
    """Return data_tables from session as dict manager -> list-of-records."""
    return st.session_state.get(table_key, {})


def render_editable_manager_table(
    manager: str,
    key_suffix: str = "",
    initial_df: pd.DataFrame = None
) -> pd.DataFrame:
    key = f"manager_table_{manager.replace(' ', '_')}{key_suffix}"
    
    # Получаем данные из session_state
    if key in st.session_state:
        data = st.session_state[key]
        # Проверяем тип и конвертируем в DataFrame, если нужно
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            df = initial_df if initial_df is not None else pd.DataFrame()
    else:
        df = initial_df if initial_df is not None else pd.DataFrame()
    
    edited = st.data_editor(df, width='stretch', num_rows="dynamic", key=key)
    return edited

def persist_data_table(manager: str, table_key: str, key_suffix: str = "", columns: Optional[List[str]] = None) -> None:
    key = f"{table_key}_{manager.replace(' ', '_')}{key_suffix}"
    if key not in st.session_state:
        return

    val = st.session_state.get(key)
    df = None

    # Robust conversion to DataFrame
    if isinstance(val, pd.DataFrame):
        df = val
    elif isinstance(val, list):
        try:
            df = pd.DataFrame(val)
        except Exception:
            df = None
    elif isinstance(val, dict):
        # Try as dict-of-lists (columns), else as list-of-dicts (rows)
        try:
            df = pd.DataFrame.from_dict(val)
            # If only one row, may need to transpose
            if df.shape[0] == 1 and len(val) > 1:
                df = df.transpose()
        except Exception:
            try:
                df = pd.DataFrame([val])
            except Exception:
                df = None
    else:
        try:
            df = pd.DataFrame(val)
        except Exception:
            df = None

    if df is None:
        from .tables import default_table_template  
        df = default_table_template(rows=5, columns=columns)

    mts = st.session_state.get(table_key, {})
    mts[f"{manager}{key_suffix}"] = df.to_dict(orient="records")
    st.session_state[table_key] = mts


def create_full_managers_excel(
    analytics_data: dict,
    calls_mgr_stats: dict,
    manager_tables: dict,
    manager_questions: dict,
    calls_total: dict = None
) -> BytesIO:
    """
    Создает Excel-файл, где для каждого менеджера отдельная вкладка с:
    - аналитикой (категории)
    - статистикой звонков
    - редактируемыми таблицами
    - вопросами/ответами
    """
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        for mgr in analytics_data.keys():
            # 1. Аналитика по категориям
            analytics_df = pd.DataFrame.from_dict(analytics_data[mgr], orient="index").reset_index()
            analytics_df.rename(columns={"index": "Категорія"}, inplace=True)
            analytics_df.to_excel(writer, index=False, sheet_name=f"{mgr[:28]}_аналітика")

            # 2. Статистика звонков
            calls = calls_mgr_stats.get(mgr, [])
            if calls:
                calls_stats_df = pd.DataFrame(calls)
                # Можно добавить агрегацию по номерам, если нужно
                calls_stats_df.to_excel(writer, index=False, sheet_name=f"{mgr[:28]}_дзвінки")

            # 3. Редактируемые таблицы (manager_tables)
            for key, tbl in manager_tables.items():
                if key.startswith(mgr):
                    df = pd.DataFrame(tbl)
                    sheet = key.replace(mgr, f"{mgr[:20]}_", 1)[:31]
                    df.to_excel(writer, index=False, sheet_name=sheet)

            # 4. Вопросы/ответы (manager_questions)
            for key, tbl in manager_questions.items():
                if key.startswith(mgr):
                    df = pd.DataFrame(tbl)
                    sheet = key.replace(mgr, f"{mgr[:20]}_", 1)[:31]
                    df.to_excel(writer, index=False, sheet_name=sheet)
    excel_buffer.seek(0)
    return excel_buffer