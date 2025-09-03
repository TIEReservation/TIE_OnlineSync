# inventory.py
import streamlit as st
import pandas as pd
from datetime import date, datetime
import calendar
import re
from directreservation import load_property_room_map

def parse_room_string(room_str: str) -> list[str]:
    """
    Parse a room string to a list of individual room numbers, handling ranges (e.g., '203to205') and splits (e.g., '101&102').
    """
    try:
        if 'to' in str(room_str):  # Ensure room_str is treated as string
            numbers = re.findall(r'\d+', str(room_str))
            if len(numbers) == 2:
                start, end = int(numbers[0]), int(numbers[1])
                if start <= end:
                    return [str(i) for i in range(start, end + 1)]
                else:
                    return []
        else:
            parts = re.split(r'[& ,]+', str(room_str))
            return [p.strip() for p in parts if p.strip().isdigit()]
    except ValueError:
        return []

def get_unique_rooms(property_name: str) -> list[str]:
    """
    Fetch and return a sorted list of unique inventory numbers for a property from the database.
    """
    try:
        # Fetch data from the database
        response = load_property_room_map(property_name)
        if not response or not hasattr(response, 'data') or not response.data:
            st.warning(f"No inventory numbers found for {property_name}")
            return []
        all_rooms = set()
        for record in response.data:
            inventory_no = str(record.get("inventory_no", ""))  # Convert to string and handle missing keys
            all_rooms.update(parse_room_string(inventory_no) if 'to' in inventory_no else [inventory_no])
        # Sort all values as strings to avoid type mismatches
        return sorted(list(all_rooms))
    except Exception as e:
        st.error(f"Error fetching inventory for {property_name}: {e}")
        return []  # Return empty list to allow table display

def show_daily_status():
    """
    Display the Daily Status screen in Streamlit, showing tables for each day in the selected month and property.
    Populate with inventory numbers fetched from the database and leave Room No blank.
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

    # List properties (assuming these are available in the database)
    properties = sorted(["Eden Beach Resort", "La Antilia", "La Millionare Resort", "La Paradise Luxury", "La Paradise Residency", "La Tamara Luxury"])
    property_name = st.selectbox("Select Property", [""] + properties)

    if not property_name:
        st.info("Please select a property to view daily status.")
        return

    # Get days in month
    _, num_days = calendar.monthrange(year, month)
    days = [date(year, month, d) for d in range(1, num_days + 1)]

    # For each day, create an expander with a table
    for day in days:
        with st.expander(f"{property_name} - {day.strftime('%B %d, %Y')}"):
            inventory_nums = get_unique_rooms(property_name)
            num_inventory = len(inventory_nums) if inventory_nums else 1  # Ensure at least one row
            data = {
                "Inventory No": inventory_nums if inventory_nums else ["No data available"],
                "Room No": [""] * num_inventory,  # Leave Room No blank
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
            st.dataframe(df, use_container_width=True)
