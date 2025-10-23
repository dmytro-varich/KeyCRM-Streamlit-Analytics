import sys
import streamlit as st
from pathlib import Path
from datetime import datetime

# Get today's date
TODAY = datetime.now().strftime("%Y-%m-%d")

# Add parent directory to sys.path for imports
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

from src.api.client import ApiClient
from config.settings import WEBHOOK_TEST_URL
from src.utils.data_processing import process_all_data
from src.components.tables import render_manager_tables, create_simple_dataframe


def main() -> None:
    """
    Main entry point for KeyCRM Analytics Streamlit app.
    Sets up UI and handles user actions.
    """
    st.set_page_config(
        page_title="KeyCRM Analytics",
        page_icon="📊",
        layout="wide"
    )
    st.title("📊 KeyCRM Analytics Dashboard")

    # Sidebar settings
    st.sidebar.header("⚙️ Settings")

    # Button to process all data (new leads + calls)
    if st.sidebar.button("🔄 Process all data", type="primary"):
        api_client = ApiClient()
        process_all_data(api_client)

    # Display results section
    display_results()


def display_results() -> None:
    """
    Display analytics results and cards table.
    """
    if 'all_data' in st.session_state:
        st.markdown("---")
        # st.header("📊 Manager Analytics")
        data = st.session_state['all_data']
        render_manager_tables(data['analytics'])
        with st.expander("📋 All cards"):
            df_cards = create_simple_dataframe(data['cards'])
            st.dataframe(df_cards, use_container_width=True)


if __name__ == "__main__":
    main()