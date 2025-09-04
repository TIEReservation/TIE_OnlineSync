# inventory.py
import streamlit as st
import pandas as pd
from datetime import date, datetime
import calendar
import re
from directreservation import load_property_room_map
from supabase import create_client, Client
import toml
import os
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load Supabase credentials
try:
    # Attempt to load from Streamlit secrets
    SUPABASE_URL = st.secrets["supabase"]["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["supabase"]["SUPABASE_KEY"]
except (KeyError, AttributeError):
    # Fallback to config.toml
    try:
        config_path = "config.toml"
        if os.path.exists(config_path):
            config = toml.load(config_path)
            SUPABASE_URL = config["supabase"]["url"]
            SUPABASE_KEY = config["supabase"]["key"]
        else:
            st.error("Supabase credentials not found in secrets or config.toml.")
            logger.error("Supabase credentials not found in config.toml")
            SUPABASE_URL, SUPABASE_KEY = None, None
    except Exception as e:
        st.error(f"Failed to load config.toml: {str(e)}")
        logger.error(f"Failed to load config.toml: {str(e)}")
        SUPABASE_URL, SUPABASE_KEY = None, None

# Initialize Supabase client
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        st.error(f"Failed to initialize Supabase client: {str(e)}")
        logger.error(f"Failed to initialize Supabase client: {str(e)}")

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
    Fetch inventory numbers from Supabase inventory table, keep room numbers blank, and blanks for other details.
    """
    st.title("📅 Daily Status")

    # Get current year for default
    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year + 6))
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

    # Fetch inventory numbers from Supabase
    inventory_nos = []
    if supabase:
        try:
            # Basic query to fetch inventory_no
            response = supabase.table("inventory").select("inventory_no").execute()
            logger.debug(f"Supabase response: {response}")
            if response.data:
                inventory_nos = [str(row["inventory_no"]) for row in response.data]
                logger.info(f"Fetched {len(inventory_nos)} inventory numbers: {inventory_nos[:5]}")
            else:
                st.warning("No data returned from inventory table. Check RLS policies or table contents.")
                logger.warning("Supabase query returned empty data")
            # Optional: Filter by property_name if table has a property_name column
            # response = supabase.table("inventory").select("inventory_no").eq("property_name", property_name).execute()
            # inventory_nos = [str(row["inventory_no"]) for row in response.data]
        except Exception as e:
            st.error(f"Failed to fetch inventory numbers from Supabase: {str(e)}")
            logger.error(f"Supabase query error: {str(e)}")
    else:
        st.error("Supabase client not initialized. Check credentials.")
        logger.error("Supabase client not initialized")

    # For each day, create an expander with a table
    for day in days:
        with st.expander(f"{property_name} - {day.strftime('%B %d, %Y')}"):
            rooms = get_unique_rooms(property_name)
            if not rooms:
                st.warning("No rooms found for this property.")
                continue
            num_rooms = len(rooms)
            # Use inventory numbers from Supabase, or fallback to empty strings
            inventory_display = inventory_nos[:num_rooms] + [""] * (num_rooms - len(inventory_nos)) if inventory_nos else [""] * num_rooms
            data = {
                "Inventory No": inventory_display,  # Use fetched inventory numbers
                "Room No": [""] * num_rooms,  # Keep Room No column blank
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
