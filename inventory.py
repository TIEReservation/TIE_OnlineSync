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
    Cached load of the full property inventory map from the database.
    """
    try:
        result = load_property_room_map()  # Call without arguments
        st.write("Debug: load_full_room_map returned:", result)  # Debug output to inspect data
        return result if result else []
    except Exception as e:
        st.error(f"Error loading full inventory map: {e}")
        return []

def parse_room_string(room_str: str) -> list[str]:
    """
    Parse a room string to a list of individual room numbers, handling only 'to' ranges.
    Preserves original value if no valid range.
    """
    try:
        room_str = str(room_str).strip()
        if 'to' in room_str.lower():  # Only handle 'to' ranges
            numbers = re.findall(r'\d+', room_str)
            if len(numbers) == 2:
                start, end = int(numbers[0]), int(numbers[1])
                if start <= end:
                    return [str(i) for i in range(start, end + 1)]
        return [room_str]  # Return original if no valid range or error
    except ValueError:
        return [room_str]  # Return original on error

def get_unique_rooms(property_name: str) -> list[str]:
    """
    Get sorted list of unique inventory numbers for a property from the full room map.
    """
    room_map = load_full_room_map()
    if not room_map:
        st.warning(f"No inventory data available for {property_name}")
        return []
    all_rooms = set()
    # Assuming room_map is a list of dicts: [{"property_name": "...", "inventory_no": "..."}, ...]
    for record in room_map:
        if record.get("property_name") == property_name:
            inventory_no = record.get("inventory_no", "")
            parsed_rooms = parse_room_string(inventory_no)
            all_rooms.update(parsed_rooms)
    # Sort with tuple key: numerics first (sorted numerically), then non-numerics (alphabetically)
    return sorted(list(all_rooms), key=lambda x: (0, int(x)) if x.isdigit() else (1, x))

def show_daily_status():
    """
    Display the Daily Status screen in Streamlit, showing tables for each day in the selected month and property.
    Populate with inventory numbers fetched once and displayed for all dates.
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
    properties = sorted(set(record.get("property_name") for record in room_map if record.get("property_name")) or [])
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
