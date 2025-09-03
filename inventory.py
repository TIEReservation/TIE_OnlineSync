# inventory.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from supabase import create_client, Client
import os
import calendar

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

# Configure logging and TTL
CONFIG = {"log_path": "error.log", "ttl": 300}  # 5-minute default TTL
def configure_logging(log_path=None):
    """Configure the logging file path and create it if it doesn't exist."""
    log_path = log_path or CONFIG["log_path"]
    if not os.path.exists(log_path):
        open(log_path, "a").close()

# Error logging function
def log_error(message):
    """Log an error message to the configured log file with a timestamp."""
    with open(CONFIG["log_path"], "a") as f:
        f.write(f"{datetime.now()}: {message}\n")

# Cached inventory fetch with configurable TTL
@st.cache_data(ttl=CONFIG["ttl"])
def fetch_inventory_numbers(property_name):
    """Fetch inventory numbers for a given property from Supabase."""
    try:
        response = supabase.table("inventory").select("inventory_no").eq("property_name", property_name).execute()
        if not response.data:
            st.warning(f"No inventory numbers found for {property_name}")
            return []
        return [record["inventory_no"] for record in response.data]
    except Exception as e:
        st.error(f"Error fetching inventory for {property_name}: {e}")
        log_error(f"Inventory fetch failed for {property_name}: {e}")
        return []

def validate_date_range(year, month_num):
    """Validate and return the date range for a given month."""
    _, last_day = calendar.monthrange(year, month_num)
    start_date = date(year, month_num, 1)
    end_date = date(year, month_num, last_day)
    return start_date, end_date

def generate_daily_tables(property_name, date_range):
    """Generate daily tables for a property with inventory numbers."""
    inventory_nums = fetch_inventory_numbers(property_name)
    if not inventory_nums:
        st.warning(f"No inventory data available for {property_name}")
        return
    for date in date_range:
        with st.expander(f"{property_name} - {date.strftime('%Y-%m-%d')}", key=f"{property_name}_{date}"):
            headers = ["Inventory No", "Room No", "Guest Name", "Mobile No", "Total Pax", "Check-in Date", "Check-out Date", "Days", "Booking Status", "Payment Status", "Remarks"]
            data = {header: [header] for header in headers}
            # Add property name and date as the first row
            data["Property Name"] = [property_name, ""]
            data["Date"] = [date.strftime('%Y-%m-%d'), ""]
            for inv_num in inventory_nums:
                for header in headers:
                    data[header].append(inv_num if header == "Inventory No" else "")
            df = pd.DataFrame(data)
            st.dataframe(df)

def clear_cache():
    """Clear the Streamlit cache."""
    st.cache_data.clear()
    st.success("Cache cleared!")

def show_daily_status():
    """Display the daily status screen with property and date-based tables."""
    st.title("📅 Daily Status")
    configure_logging()
    st.subheader("Select Month")
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    cols = st.columns(3)
    selected_month = st.session_state.get('selected_month', None)
    for i, month in enumerate(months):
        with cols[i % 3]:
            if st.button(month):
                st.session_state.selected_month = month
                selected_month = month

    if st.button("Clear Cache"):
        clear_cache()

    if selected_month:
        year = datetime.now().year  # Current year: 2025
        month_map = {m: i+1 for i, m in enumerate(months)}
        month_num = month_map[selected_month]
        start_date, end_date = validate_date_range(year, month_num)
        date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

        # Import or use fallback for load_property_room_map
        try:
            from directreservation import load_property_room_map
        except ImportError:
            def load_property_room_map():
                """Fallback implementation for property room mapping."""
                return {
                    "Le Poshe Beachview": {"Double Room": ["101", "102"]},
                    "La Millionare Resort": {"Double Room": ["101", "102", "103"]},
                    "Le Poshe Luxury": {"2BHA Appartment": ["101", "102"]},
                }

        property_map = load_property_room_map()
        for prop in sorted(property_map.keys()):
            with st.expander(prop, key=f"prop_{prop}"):
                generate_daily_tables(prop, date_range)

if __name__ == "__main__":
    show_daily_status()
