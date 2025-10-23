import streamlit as st
import pandas as pd
from typing import Dict, Any, List

def render_manager_tables(manager_dict: Dict[str, Any]) -> None:
    """
    Render manager analytics tables with visual cell merging.
    Table headers and labels are in Ukrainian.
    Args:
        manager_dict (dict): Nested analytics by manager and category.
    """
    default_categories: List[str] = ["Не Алмази", "Алмази", "Діаманти"]
    custom_keys: List[str] = ["Закр. Зустріч КИЇВ", "Закр. Навчання В ЗАПИСІ", "Закр. Зустріч ONLINE"]
    for manager, categories in manager_dict.items():
        st.markdown(f"### 👤 {manager}")
        html = "<table border='1' style='border-collapse:collapse;width:100%;'>"
        html += (
            "<tr>"
            "<th rowspan='2'>Категорія</th>"
            "<th colspan='2'>Нові</th>"
            "<th colspan='2'>Попередні</th>"
            "<th rowspan='2'>Не кваліфіковані</th>"
            f"<th rowspan='2'>{custom_keys[0]}</th>"
            f"<th rowspan='2'>{custom_keys[1]}</th>"
            f"<th rowspan='2'>{custom_keys[2]}</th>"
            "</tr>"
            "<tr>"
            "<th>Прогріті</th><th>Не прогріті</th>"
            "<th>Прогріті</th><th>Не прогріті</th>"
            "</tr>"
        )
        # Calculate totals for 'Всього' category
        total_stats = {
            "Нові": {"Прогріті": 0, "Не прогріті": 0},
            "Попередні": {"Прогріті": 0, "Не прогріті": 0},
            "Не кваліфіковані": 0,
            custom_keys[0]: 0,
            custom_keys[1]: 0,
            custom_keys[2]: 0
        }
        for category in default_categories:
            stats = categories.get(category, None)
            if stats is None:
                stats = {
                    "Нові": {"Прогріті": 0, "Не прогріті": 0},
                    "Попередні": {"Прогріті": 0, "Не прогріті": 0},
                    "Не кваліфіковані": 0,
                    custom_keys[0]: 0,
                    custom_keys[1]: 0,
                    custom_keys[2]: 0
                }
            # Sum each column for totals
            total_stats["Нові"]["Прогріті"] += stats["Нові"]["Прогріті"]
            total_stats["Нові"]["Не прогріті"] += stats["Нові"]["Не прогріті"]
            total_stats["Попередні"]["Прогріті"] += stats["Попередні"]["Прогріті"]
            total_stats["Попередні"]["Не прогріті"] += stats["Попередні"]["Не прогріті"]
            total_stats["Не кваліфіковані"] += stats.get("Не кваліфіковані", 0)
            total_stats[custom_keys[0]] += stats.get(custom_keys[0], 0)
            total_stats[custom_keys[1]] += stats.get(custom_keys[1], 0)
            total_stats[custom_keys[2]] += stats.get(custom_keys[2], 0)
        for category in default_categories:
            stats = categories.get(category, None)
            if stats is None:
                stats = {
                    "Нові": {"Прогріті": 0, "Не прогріті": 0},
                    "Попередні": {"Прогріті": 0, "Не прогріті": 0},
                    "Не кваліфіковані": 0,
                    custom_keys[0]: 0,
                    custom_keys[1]: 0,
                    custom_keys[2]: 0
                }
            html += "<tr>"
            html += f"<td>{category}</td>"
            html += f"<td>{stats['Нові']['Прогріті']}</td>"
            html += f"<td>{stats['Нові']['Не прогріті']}</td>"
            html += f"<td>{stats['Попередні']['Прогріті']}</td>"
            html += f"<td>{stats['Попередні']['Не прогріті']}</td>"
            html += f"<td>{stats.get('Не кваліфіковані', 0)}</td>"
            html += f"<td>{stats.get(custom_keys[0], 0)}</td>"
            html += f"<td>{stats.get(custom_keys[1], 0)}</td>"
            html += f"<td>{stats.get(custom_keys[2], 0)}</td>"
            html += "</tr>"
        # Add totals row for 'Всього'
        html += "<tr style='font-weight:bold;'>"
        html += f"<td>Всього</td>"
        html += f"<td>{total_stats['Нові']['Прогріті']}</td>"
        html += f"<td>{total_stats['Нові']['Не прогріті']}</td>"
        html += f"<td>{total_stats['Попередні']['Прогріті']}</td>"
        html += f"<td>{total_stats['Попередні']['Не прогріті']}</td>"
        html += f"<td>{total_stats['Не кваліфіковані']}</td>"
        html += f"<td>{total_stats[custom_keys[0]]}</td>"
        html += f"<td>{total_stats[custom_keys[1]]}</td>"
        html += f"<td>{total_stats[custom_keys[2]]}</td>"
        html += "</tr>"
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)

def convert_manager_dict_to_df(manager_dict: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert manager analytics dict to DataFrame.
    Args:
        manager_dict (dict): Nested analytics by manager and category.
    Returns:
        pd.DataFrame: Analytics table.
    """
    rows: List[Dict[str, Any]] = []
    for manager, categories in manager_dict.items():
        for category, states in categories.items():
            for state, programs in states.items():
                for program, count in programs.items():
                    rows.append({
                        'Менеджер': manager,
                        'Категорія': category,
                        'Статус': state,
                        'Параметр': program,
                        'Кількість': count
                    })
    return pd.DataFrame(rows) if rows else pd.DataFrame()

def create_simple_dataframe(cards: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Create a simple DataFrame for cards.
    Args:
        cards (list): List of card dicts.
    Returns:
        pd.DataFrame: Table of cards.
    """
    if not cards:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for card in cards:
        row = {
            'ID': card.get('id'),
            'Назва': card.get('title'),
            'Контакт': card.get('contact', {}).get('full_name', 'N/A') if card.get('contact') else 'N/A',
            'Телефон': card.get('contact', {}).get('phone', 'N/A') if card.get('contact') else 'N/A',
            'Статус': card.get('status', {}).get('name', 'N/A') if card.get('status') else 'N/A',
            'Менеджер': card.get('manager', {}).get('full_name', 'N/A') if card.get('manager') else 'N/A',
            'Створено': card.get('created_at'),
        }
        rows.append(row)
    return pd.DataFrame(rows)

