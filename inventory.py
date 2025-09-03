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
    Get sorted list of unique room numbers for a property from the room map.
    """
    room_map = load_property_room_map()
    if property_name not in room_map:
        return []
    all_rooms = set()
    for room_types in room_map[property_name].values():
        for room in room_types:
            all_rooms.update(parse_room_string(room))
    # Sort numerically if possible, else alphabetically
    try:
        return sorted(list(all_rooms), key=lambda x: int(x))
    except ValueError:
        return sorted(list(all_rooms))

def show_daily_status():
    """
    Display the Daily Status screen in Streamlit, showing tables for each day in the selected month and property.
    For now, populate with room inventory and blanks for other details.
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
    properties = sorted(load_property_room_map().keys())
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
            rooms = get_unique_rooms(property_name)
            if not rooms:
                st.warning("No rooms found for this property.")
                continue
            num_rooms = len(rooms)
            data = {
                "Inventory No": list(range(1, num_rooms + 1)),
                "Room No": rooms,
                "Guest Name": [""] * num_rooms,
                "Mobile No": [""] * num_rooms,
                "Total Pax": [""] * num_rooms,
                "Check-in Date": [""] * num_rooms,
                "Check-out Date": [""] * num_rooms,
                "Days": [""] * num_rooms,
                "Booking Status": [""] * num_rooms,
                "Payment Status": [""] * num_rooms,
                "Remarks": [""] * num_rooms
            }
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
