import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from supabase import create_client, Client
import os
import calendar
from typing import List

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

# Configure logging and TTL
CONFIG = {"log_path": "error.log", "ttl": 300}  # 5-minute default TTL

# Constants for table structure
COLUMN_HEADERS = [
    "Inventory No", "Room No", "Guest Name", "Mobile No", "Total Pax", 
    "Check-in Date", "Check-out Date", "Days", "Booking Status", 
    "Payment Status", "Remarks"
]
COLUMN_COUNT = 11

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
def fetch_inventory_numbers(property_name: str) -> List[str]:
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

def validate_date_range(year: int, month_num: int):
    """Validate and return the date range for a given month."""
    _, last_day = calendar.monthrange(year, month_num)
    start_date = date(year, month_num, 1)
    end_date = date(year, month_num, last_day)
    return start_date, end_date

def format_inventory_row(inventory_no: str) -> List[str]:
    """Format a single inventory row with blank fields for future data."""
    return [inventory_no] + [""] * (COLUMN_COUNT - 1)

def create_daily_table_data(property_name: str, target_date: date, inventory_numbers: List[str]) -> List[List[str]]:
    """Create structured table data for a single day with proper rows and columns."""
    # Create metadata row (Property name and date in first few columns, rest empty)
    metadata_row = [
        property_name, 
        target_date.strftime('%Y-%m-%d')
    ] + [""] * (COLUMN_COUNT - 2)
    
    # Create header row
    header_row = COLUMN_HEADERS.copy()
    
    # Create data rows for each inventory number
    data_rows = []
    if inventory_numbers:
        for inv_no in inventory_numbers:
            data_rows.append(format_inventory_row(inv_no))
    else:
        # If no inventory numbers, create at least one empty row
        data_rows.append(["No inventory found"] + [""] * (COLUMN_COUNT - 1))
    
    # Combine all rows
    table_data = [metadata_row, header_row] + data_rows
    return table_data

def generate_daily_tables(property_name: str, date_range: List[date]):
    """Generate daily tables for a property with inventory numbers for each date."""
    inventory_nums = fetch_inventory_numbers(property_name)
    
    for target_date in date_range:
        # Create expander for each date
        with st.expander(
            f"{property_name} - {target_date.strftime('%Y-%m-%d')}", 
            expanded=False,
            key=f"{property_name}_{target_date}"
        ):
            # Generate table data
            table_data = create_daily_table_data(property_name, target_date, inventory_nums)
            
            # Create DataFrame from structured data
            df = pd.DataFrame(table_data)
            
            # Display the table without headers (since our data includes headers)
            st.dataframe(
                df, 
                use_container_width=True,
                hide_index=True,
                column_config={i: None for i in range(COLUMN_COUNT)}  # Hide column labels
            )

def clear_cache():
    """Clear the Streamlit cache."""
    st.cache_data.clear()
    st.success("Cache cleared!")

def show_daily_status():
    """Display the daily status screen with property and date-based tables."""
    st.title("📅 Daily Status")
    configure_logging()
    
    st.subheader("Select Month")
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    
    # Create month selection buttons in a 3-column layout
    cols = st.columns(3)
    selected_month = st.session_state.get('selected_month', None)
    
    for i, month in enumerate(months):
        with cols[i % 3]:
            if st.button(month):
                st.session_state.selected_month = month
                selected_month = month

    # Cache clear button
    if st.button("Clear Cache"):
        clear_cache()

    # Process selected month
    if selected_month:
        year = datetime.now().year  # Current year
        month_map = {m: i+1 for i, m in enumerate(months)}
        month_num = month_map[selected_month]
        
        start_date, end_date = validate_date_range(year, month_num)
        date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
        
        st.success(f"Showing daily tables for {selected_month} {year} ({len(date_range)} days)")

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
        
        # Generate tables for each property
        for prop in sorted(property_map.keys()):
            with st.expander(f"🏨 {prop}", expanded=True, key=f"prop_{prop}"):
                st.write(f"Generating {len(date_range)} daily tables for {prop}")
                generate_daily_tables(prop, date_range)

if __name__ == "__main__":
    show_daily_status()
