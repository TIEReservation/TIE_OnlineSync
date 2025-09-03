# inventory.py
import streamlit as st
import pandas as pd
from datetime import date, datetime
import calendar
import re
from directreservation import load_property_room_map

# Static inventory data
INVENTORY_DATA = {
    "Eden Beach Resort": ["101", "102", "103", "201", "202", "Day Use 1", "Day Use 2", "No Show"],
    "La Antilia": ["101", "201", "202", "203", "204", "301", "302", "303", "304", "401", "404", "Day Use 1", "Day Use 2", "No Show"],
    "La Millionare Resort": ["101", "102", "103", "105", "201", "202", "203", "204", "205", "206", "207", "208", "301", "302", "303", "304", "305", "306", "307", "308", "401", "402", "day use1", "day use2", "day use3", "day use4", "No-Show5"],
    "La Paradise Luxury": ["101", "101to103", "102", "103", "201", "201to203", "202", "203", "Day Use 1", "Day Use 2", "No Show"],
    "La Paradise Residency": ["101", "102", "103", "201", "202", "203", "301", "302", "303", "304", "Day Use 1", "Day Use 2", "No Show"],
    "La Tamara Luxury": ["101", "101to103", "102", "103", "104", "104to106", "105", "106", "201", "201to203", "202", "203", "204", "204to206", "205", "206", "301", "301to303", "302", "303", "304", "304to306", "305", "306", "401", "401to404", "402"]
}

def parse_room_string(room_str: str) -> list[str]:
    """
    Parse a room string to a list of individual room numbers, handling ranges (e.g., '203to205') and splits (e.g., '101&102').
    """
    try:
        if 'to' in room_str:
            numbers = re.findall(r'\d+', room_str)
            if len(numbers) == 2:
                start, end = int(numbers[0]), int(numbers[1])
                if start <= end:
                    return [str(i) for i in range(start, end + 1)]
                else:
                    return []
        else:
            parts = re.split(r'[& ,]+', room_str)
            return [p.strip() for p in parts if p.strip().isdigit()]
    except ValueError:
        return []

def get_unique_rooms(property_name: str) -> list[str]:
    """
    Get sorted list of unique inventory numbers for a property from the static INVENTORY_DATA.
    """
    if property_name not in INVENTORY_DATA:
        return []
    all_rooms = set()
    for room in INVENTORY_DATA[property_name]:
        all_rooms.update(parse_room_string(room) if 'to' in room else [room])
    # Sort numerically if possible, else alphabetically
    try:
        return sorted(list(all_rooms), key=lambda x: int(x) if x.isdigit() else x)
    except ValueError:
        return sorted(list(all_rooms))

def show_daily_status():
    """
    Display the Daily Status screen in Streamlit, showing tables for each day in the selected month and property.
    Populate with static inventory numbers in Inventory No and leave Room No blank.
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

    # List properties
    properties = sorted(INVENTORY_DATA.keys())
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
            if not inventory_nums:
                st.warning("No inventory numbers found for this property.")
                continue
            num_inventory = len(inventory_nums)
            data = {
                "Inventory No": inventory_nums,  # Use inventory numbers directly
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
