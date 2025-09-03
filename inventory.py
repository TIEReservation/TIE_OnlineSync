# inventory.py
import streamlit as st
import pandas as pd
from datetime import date, datetime
import calendar
import psycopg2
from psycopg2 import Error

# Database connection configuration (replace with your credentials)
DB_CONFIG = {
    "dbname": "your_database",
    "user": "your_username",
    "password": "your_password",
    "host": "your_host",
    "port": "your_port"
}

@st.cache_data
def get_inventory_data():
    """
    Fetch all inventory data from the Inventory table.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT property_name, inventory_no FROM Inventory")
        rows = cursor.fetchall()
        return {row[0]: list(set(row[1] for row in rows if row[0] == row[0])) for row in rows}  # Group by property
    except Error as e:
        st.error(f"Database error: {e}")
        return {}
    finally:
        if conn:
            cursor.close()
            conn.close()

def get_unique_rooms(property_name: str) -> list[str]:
    """
    Get sorted list of unique inventory_no values for a property.
    """
    inventory_data = get_inventory_data()
    rooms = inventory_data.get(property_name, [])
    return sorted(rooms, key=lambda x: (0, int(x)) if x.isdigit() else (1, x))

def show_daily_status():
    """
    Display the Daily Status screen in Streamlit, showing tables for each day with inventory_no.
    """
    st.title("📅 Daily Status")

    # Get current year for default
    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year + 5))
    year = st.selectbox("Select Year", years, index=5)  # Default to current

    months = list(range(1, 13))
    month_names = [calendar.month_name[m] for m in months]
    month_index = st.selectbox("Select Month", range(len(month_names)), format_func=lambda x: month_names[x])
    month = months[month_index]

    # List properties from inventory data
    inventory_data = get_inventory_data()
    properties = sorted(inventory_data.keys())
    property_name = st.selectbox("Select Property", [""] + properties)

    if not property_name:
        st.info("Please select a property to view daily status.")
        return

    # Fetch inventory numbers once
    inventory_nums = get_unique_rooms(property_name)
    if not inventory_nums:
        st.warning(f"No inventory numbers found for {property_name}.")
        return

    # Get days in month
    _, num_days = calendar.monthrange(year, month)
    days = [date(year, month, d) for d in range(1, num_days + 1)]

    # Create DataFrame once
    num_inventory = len(inventory_nums)
    data = {
        "Inventory No": inventory_nums,
        "Room No": [""] * num_inventory,  # Blank as required
        "Guest Name": [""] * num_inventory,
        "Mobile No": [""] * num_inventory,
        "Total Pax": [""] * num_inventory,
        "Check-in Date": [""] * num_inventory,
        "Check-out Date": [""] * num_inventory,
        "Days": [""] * num_inventory,
        "Booking Status": [""] * num_inventory,
        "Payment Status": [""] * num_inventory,
        "Remarks": [""] * num_inventory
    }
    df = pd.DataFrame(data)

    # Display the same table for each day
    for day in days:
        with st.expander(f"{property_name} - {day.strftime('%B %d, %Y')}"):
            st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    show_daily_status()
