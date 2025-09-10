import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta
import calendar
import pandas as pd

# Initialize Supabase client
supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

# Table CSS for non-wrapping, scrollable table
TABLE_CSS = """
<style>
/* Styles for non-wrapping, scrollable table in daily status */
.custom-scrollable-table {
    overflow-x: auto;
    max-width: 100%;
    min-width: 800px;
}
.custom-scrollable-table table {
    table-layout: auto;
    border-collapse: collapse;
}
.custom-scrollable-table td, .custom-scrollable-table th {
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
    max-width: 300px;
    padding: 8px;
    border: 1px solid #ddd;
}
</style>
"""

# Property inventory mapping: {"property": {"all": [all valid inventory numbers], "three_bedroom": [three bedroom numbers for D1-D5]}}
PROPERTY_INVENTORY = {
    "Le Poshe Beachview": {
        "all": ["101", "102", "201", "202", "203", "204", "301", "302", "303", "304", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204"]
    },
    "La Millionare Resort": {
        "all": ["101", "102", "103", "105", "201", "202", "203", "204", "205", "206", "207", "208", "301", "302", "303", "304", "305", "306", "307", "308", "401", "402", "Day Use 1", "Day Use 2", "Day Use 3", "Day Use 4", "No Show"],
        "three_bedroom": ["203", "204", "205"]
    },
    "Le Poshe Luxury": {
        "all": ["101", "102", "201", "202", "203", "204", "205", "301", "302", "303", "304", "305", "401", "402", "403", "404", "405", "501", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204", "205"]
    },
    "Le Poshe Suite": {
        "all": ["601", "602", "603", "604", "701", "702", "703", "704", "801", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    },
    "La Paradise Residency": {
        "all": ["101", "102", "103", "201", "202", "203", "301", "302", "303", "304", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203"]
    },
    "La Paradise Luxury": {
        "all": ["101", "102", "103", "201", "202", "203", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203"]
    },
    "La Villa Heritage": {
        "all": ["101", "102", "103", "201", "202", "203", "301", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203"]
    },
    "Le Pondy Beach Side": {
        "all": ["101", "102", "201", "202", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    },
    "Le Royce Villa": {
        "all": ["101", "102", "201", "202", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    },
    "La Tamara Luxury": {
        "all": ["101", "102", "103", "104", "105", "106", "201", "202", "203", "204", "205", "206", "301", "302", "303", "304", "305", "306", "401", "402", "403", "404", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204", "205", "206"]
    },
    "La Antilia": {
        "all": ["101", "201", "202", "203", "204", "301", "302", "303", "304", "401", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204"]
    },
    "La Tamara Suite": {
        "all": ["101", "102", "103", "104", "201", "202", "203", "204", "205", "206", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204", "205", "206"]
    },
    "Le Park Resort": {
        "all": ["111", "222", "333", "444", "555", "666", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    },
    "Villa Shakti": {
        "all": ["101", "102", "201", "201A", "202", "203", "301", "301A", "302", "303", "401", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203"]
    },
    "Eden Beach Resort": {
        "all": ["101", "102", "103", "201", "202", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    }
}

def load_properties() -> list[str]:
    """Load unique properties from both tables without merging variations."""
    try:
        res_direct = supabase.table("reservations").select("property_name").execute().data
        res_online = supabase.table("online_reservations").select("property").execute().data
        properties = set(r['property_name'] for r in res_direct if r['property_name']) | set(r['property'] for r in res_online if r['property'])
        return sorted(properties)
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []

def normalize_booking(booking: dict, is_online: bool) -> dict:
    """Normalize booking dict to common schema."""
    payment_status = booking.get('payment_status', '').title()
    if payment_status not in ["Fully Paid", "Partially Paid"]:
        st.warning(f"Skipping booking {booking.get('booking_id')} with invalid payment status: {payment_status}")
        return None
    try:
        normalized = {
            'booking_id': booking.get('booking_id'),
            'room_no': booking.get('room_no'),
            'guest_name': booking.get('guest_name'),
            'mobile_no': booking.get('guest_phone') if is_online else booking.get('mobile_no'),
            'total_pax': booking.get('total_pax'),
            'check_in': date.fromisoformat(booking.get('check_in')) if booking.get('check_in') else None,
            'check_out': date.fromisoformat(booking.get('check_out')) if booking.get('check_out') else None,
            'booking_status': booking.get('booking_status'),
            'payment_status': payment_status,
            'remarks': booking.get('remarks'),
            'type': 'online' if is_online else 'direct'
        }
        if not normalized['check_in'] or not normalized['check_out']:
            st.warning(f"Skipping booking {booking.get('booking_id')} with missing check-in/check-out dates")
            return None
        return normalized
    except Exception as e:
        st.error(f"Error normalizing booking {booking.get('booking_id')}: {e}")
        return None

def load_combined_bookings(property: str, start_date: date, end_date: date) -> list[dict]:
    """Load bookings overlapping the date range for the property with paid statuses."""
    try:
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()
        # Fetch direct bookings
        direct = supabase.table("reservations").select("*").eq("property_name", property)\
            .lte("check_in", end_str).gt("check_out", start_str)\
            .in_("payment_status", ["Fully Paid", "Partially Paid"]).execute().data
        st.info(f"Fetched {len(direct)} direct bookings for {property} from {start_str} to {end_str}")
        # Fetch online bookings
        online = supabase.table("online_reservations").select("*").eq("property", property)\
            .lte("check_in", end_str).gt("check_out", start_str)\
            .in_("payment_status", ["Fully Paid", "Partially Paid"]).execute().data
        st.info(f"Fetched {len(online)} online bookings for {property} from {start_str} to {end_str}")
        # Normalize and filter
        normalized = [b for b in [normalize_booking(b, False) for b in direct] + [normalize_booking(b, True) for b in online] if b]
        if len(normalized) < len(direct) + len(online):
            st.warning(f"Skipped {len(direct) + len(online) - len(normalized)} bookings with invalid data for {property}")
        return normalized
    except Exception as e:
        st.error(f"Error loading bookings for {property}: {e}")
        return []

def filter_bookings_for_day(bookings: list[dict], day: date) -> list[dict]:
    """Filter bookings active on the given day."""
    return [b for b in bookings if b['check_in'] and b['check_out'] and b['check_in'] <= day < b['check_out']]

def generate_month_dates(year: int, month: int) -> list[date]:
    """Generate all dates in the month."""
    _, num_days = calendar.monthrange(year, month)
    return [date(year, month, d) for d in range(1, num_days + 1)]

def is_special_category(room_no: str) -> bool:
    """Check if room number is a special category (No Show or Day Use)."""
    return room_no in ["No Show", "Day Use 1", "Day Use 2", "Day Use 3", "Day Use 4"]

def assign_inventory_numbers(bookings: list[dict], property: str) -> tuple[list[dict], list[dict]]:
    """Assign inventory numbers to bookings based on property rules, identifying overbookings.
    
    Args:
        bookings: List of booking dictionaries with room_no.
        property: Property name to determine inventory numbers.
    
    Returns:
        Tuple of (assigned bookings with inventory_no, overbookings list).
    """
    warnings = []
    assigned = []
    overbookings = []
    if property not in PROPERTY_INVENTORY:
        for booking in bookings:
            booking['inventory_no'] = booking['room_no']
            warnings.append(f"Unknown property {property} for booking {booking.get('booking_id', 'Unknown')}")
        if warnings:
            st.warning("\n".join(warnings))
        return bookings, []
    available = [n for n in PROPERTY_INVENTORY[property]["all"] if not is_special_category(n)]
    available_three_bedroom = sorted(PROPERTY_INVENTORY[property]["three_bedroom"])
    for booking in bookings:
        room_no = booking['room_no']
        booking_id = booking.get('booking_id', 'Unknown')
        if is_special_category(room_no):
            booking['inventory_no'] = room_no
            assigned.append(booking)
        elif room_no in ['D1', 'D2', 'D3', 'D4', 'D5'] and available_three_bedroom:
            booking['inventory_no'] = available_three_bedroom.pop(0)
            assigned.append(booking)
            if booking['inventory_no'] in available:
                available.remove(booking['inventory_no'])
        elif room_no in available:
            booking['inventory_no'] = room_no
            assigned.append(booking)
            available.remove(room_no)
        else:
            overbookings.append(booking)
    if warnings:
        st.warning("\n".join(warnings))
    return assigned, overbookings

def create_inventory_table(assigned: list[dict], overbookings: list[dict], property: str) -> pd.DataFrame:
    """Create a DataFrame with all inventory numbers for a property, mapping assigned bookings and overbookings.
    
    Args:
        assigned: List of bookings with assigned inventory numbers.
        overbookings: List of overbooked bookings.
        property: Property name to get inventory numbers.
    
    Returns:
        DataFrame with columns Inventory No, Room No, Booking ID, Guest Name.
    """
    # Initialize DataFrame with all inventory numbers
    df_data = [{"Inventory No": inv, "Room No": "", "Booking ID": "", "Guest Name": ""} for inv in PROPERTY_INVENTORY[property]["all"]]
    # Fill assigned bookings
    for b in assigned:
        for row in df_data:
            if row["Inventory No"] == b["inventory_no"]:
                row["Room No"] = b["room_no"]
                row["Booking ID"] = f'<a target="_blank" href="/?edit_type={b["type"]}&booking_id={b["booking_id"]}">{b["booking_id"]}</a>'
                row["Guest Name"] = b["guest_name"]
    # Add overbookings row if needed
    if overbookings:
        overbooking_str = ", ".join(f"{b['room_no']} ({b['booking_id']})" for b in overbookings)
        df_data.append({"Inventory No": "Overbookings", "Room No": overbooking_str, "Booking ID": "", "Guest Name": ""})
    return pd.DataFrame(df_data)

@st.cache_data
def cached_load_properties():
    return load_properties()

@st.cache_data
def cached_load_bookings(property, start_date, end_date):
    return load_combined_bookings(property, start_date, end_date)

def show_daily_status():
    """Main function to display daily status screen."""
    st.title("📅 Daily Status")

    # Cache-clearing button
    if st.button("🔄 Refresh Property List"):
        st.cache_data.clear()
        st.success("Cache cleared! Refreshing properties...")
        st.rerun()

    # Year and Month selection
    current_year = date.today().year
    year = st.selectbox("Select Year", list(range(current_year - 5, current_year + 6)), index=5)
    month = st.selectbox("Select Month", list(range(1, 13)), index=date.today().month - 1)

    properties = cached_load_properties()
    if not properties:
        st.info("No properties available.")
        return

    # List properties
    st.subheader("Properties")
    st.markdown(TABLE_CSS, unsafe_allow_html=True)  # Apply CSS once
    for prop in properties:
        with st.expander(f"{prop}"):
            month_dates = generate_month_dates(year, month)
            start_date = month_dates[0]
            end_date = month_dates[-1] + timedelta(days=1)  # For exclusive check_out
            bookings = cached_load_bookings(prop, start_date, end_date - timedelta(days=1))
            st.info(f"Total bookings for {prop}: {len(bookings)}")

            for day in month_dates:
                daily_bookings = filter_bookings_for_day(bookings, day)
                st.subheader(f"{prop} - {day.strftime('%B %d, %Y')}")
                if daily_bookings:
                    # Assign inventory numbers
                    daily_bookings, overbookings = assign_inventory_numbers(daily_bookings, prop)
                    # Create inventory table
                    df = create_inventory_table(daily_bookings, overbookings, prop)
                    # Add tooltips for specific columns
                    tooltip_columns = ['Guest Name', 'Room No']
                    for col in tooltip_columns:
                        if col in df.columns:
                            df[col] = df[col].apply(lambda x: f'<span title="{x}">{x}</span>' if isinstance(x, str) else x)
                    table_html = df.to_html(escape=False, index=False)
                    st.markdown(f'<div class="custom-scrollable-table">{table_html}</div>', unsafe_allow_html=True)
                else:
                    st.info("No active bookings on this day.")
