# inventory.py
import streamlit as st
import pandas as pd
from datetime import date, datetime
import calendar
import re
from directreservation import load_property_room_map

@st.cache_data
def load_full_room_map():
    """
    Cached load of the full property room/inventory map from the database.
    """
    try:
        return load_property_room_map()  # Call without arguments, assuming it loads all data
    except Exception as e:
        st.error(f"Error loading full inventory map: {e}")
        return {}

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
    Get sorted list of unique inventory numbers for a property from the full room map.
    """
    room_map = load_full_room_map()
    if not room_map or property_name not in room_map:
        st.warning(f"No inventory numbers found for {property_name}")
        return []
    all_rooms = set()
    # Assuming room_map[property_name] is a dict of room_types to list of inventory_no strings
    # Adjust if structure is list of records: e.g., [inv for inv in room_map if inv['property_name'] == property_name]
    for room_types in room_map.get(property_name, {}).values():
        for room in room_types:
            all_rooms.update(parse_room_string(room) if 'to' in room else [room])
    # Sort with tuple key: numerics first (sorted numerically), then non-numerics (alphabetically)
    return sorted(list(all_rooms), key=lambda x: (0, int(x)) if x.isdigit() else (1, x))

def show_daily_status():
    """
    Display the Daily Status screen in Streamlit, showing tables for each day in the selected month and property.
    Populate with static inventory numbers and blanks for other details.
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

    # List properties from the full map
    room_map = load_full_room_map()
    properties = sorted(room_map.keys()) if room_map else []
    property_name = st.selectbox("Select Property", [""] + properties)

    if not property_name:
        st.info("Please select a property to view daily status.")
        return

    # Fetch inventory numbers once
    inventory_nums = get_unique_rooms(property_name)
    if not inventory_nums:
        st.warning("No inventory numbers found for this property.")
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

    # For each day, create an expander with the table
    for day in days:
        with st.expander(f"{property_name} - {day.strftime('%B %d, %Y')}"):
            st.dataframe(df, use_container_width=True)
