import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta
import calendar
import pandas as pd
from typing import Any, List, Dict  # Type hints for function signatures

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

# Property synonym mapping
property_mapping = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
}
reverse_mapping = {}
for variant, canonical in property_mapping.items():
    reverse_mapping.setdefault(canonical, []).append(variant)

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

# Property inventory mapping
PROPERTY_INVENTORY = {
    "Le Poshe Beach view": {
        "all": ["101", "102", "201", "202", "203", "204", "301", "302", "303", "304", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204"]
    },
    "La Millionaire Resort": {
        "all": ["101", "102", "103", "105", "201", "202", "203", "204", "205", "206", "207", "208", "301", "302", "303", "304", "305", "306", "307", "308", "401", "402", "Day Use 1", "Day Use 2", "Day Use 3", "Day Use 4", "Day Use 5", "No Show"],
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
    "La Antilia Luxury": {
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

def initialize_property_inventory(properties: List[str]) -> None:
    """Add missing properties to PROPERTY_INVENTORY with fallback inventory."""
    fallback = {"all": ["Unknown"], "three_bedroom": []}
    for prop in properties:
        if prop not in PROPERTY_INVENTORY:
            PROPERTY_INVENTORY[prop] = fallback
            st.warning(f"Added fallback inventory for unknown property: {prop}")

def format_booking_id(booking: Dict) -> str:
    """Format booking ID as a clickable hyperlink."""
    booking_id = sanitize_string(booking.get('booking_id'))
    return f'<a target="_blank" href="/?edit_type={booking["type"]}&booking_id={booking_id}">{booking_id}</a>'

def load_properties() -> List[str]:
    """Load unique properties from reservations and online_reservations tables."""
    try:
        res_direct = supabase.table("reservations").select("property_name").execute().data
        res_online = supabase.table("online_reservations").select("property").execute().data
        properties = set()
        for r in res_direct:
            prop = r['property_name']
            if prop:
                canonical = property_mapping.get(prop, prop)
                properties.add(canonical)
        for r in res_online:
            prop = r['property']
            if prop:
                canonical = property_mapping.get(prop, prop)
                properties.add(canonical)
        properties = sorted(properties)
        initialize_property_inventory(properties)
        return properties
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []

def sanitize_string(value: Any, default: str = "Unknown") -> str:
    """Convert value to string, handling None and non-string types."""
    return str(value) if value is not None else default

def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to int, return default if conversion fails."""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float, return default if conversion fails."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def normalize_booking(booking: Dict, is_online: bool) -> Dict:
    """Normalize booking dict to common schema, silently skipping invalid bookings."""
    # Sanitize inputs to prevent f-string and HTML issues
    booking_id = sanitize_string(booking.get('booking_id'))
    payment_status = sanitize_string(booking.get('payment_status')).title()
    if payment_status not in ["Fully Paid", "Partially Paid"]:
        return None  # Silently skip invalid payment status
    booking_status_field = 'booking_status' if is_online else 'plan_status'
    booking_status = sanitize_string(booking.get(booking_status_field))
    try:
        check_in = date.fromisoformat(booking.get('check_in')) if booking.get('check_in') else None
        check_out = date.fromisoformat(booking.get('check_out')) if booking.get('check_out') else None
        # Calculate days from check_in and check_out if available
        days = None
        if check_in and check_out:
            days = (check_out - check_in).days
            if days < 0:
                return None  # Silently skip invalid dates
            if days == 0:
                days = 1  # Treat same-day bookings (e.g., Day Use) as 1 day
        # Unified field mapping
        property_name = sanitize_string(booking.get('property', booking.get('property_name', '')))
        property_name = property_mapping.get(property_name, property_name)
        guest_name = sanitize_string(booking.get('guest_name', ''))
        mobile_no = sanitize_string(booking.get('guest_phone', booking.get('mobile_no', '')))
        total_pax = safe_int(booking.get('total_pax', 0))
        room_no = sanitize_string(booking.get('room_no', ''))
        room_type = sanitize_string(booking.get('room_type', ''))
        mob = sanitize_string(booking.get('mode_of_booking', booking.get('mob', '')))
        plan = sanitize_string(booking.get('rate_plans', booking.get('plan', '')))
        submitted_by = sanitize_string(booking.get('submitted_by', ''))
        modified_by = sanitize_string(booking.get('modified_by', ''))
        remarks = sanitize_string(booking.get('remarks', ''))
        # Financial fields
        total_tariff = safe_float(booking.get('total_amount_with_services', booking.get('booking_amount', 0.0))) or safe_float(booking.get('total_tariff', 0.0))
        advance = safe_float(booking.get('total_payment_made', 0.0)) or safe_float(booking.get('advance_amount', 0.0))
        balance = safe_float(booking.get('balance_due', 0.0)) or safe_float(booking.get('balance_amount', 0.0))
        advance_mop = sanitize_string(booking.get('advance_mop', ''))
        balance_mop = sanitize_string(booking.get('balance_mop', ''))
        # Default values for missing fields
        room_charges = total_tariff  # Assume room_charges = total_tariff if not specified
        gst = safe_float(booking.get('ota_tax', 0.0)) if is_online else 0.0  # Extract ota_tax as GST for online bookings, default to 0 for direct
        commission = safe_float(booking.get('ota_commission', 0.0))
        receivable = room_charges - commission
        per_night = receivable / days if days > 0 else 0.0
        # Type indicator
        booking_type = "online" if is_online else "direct"
        normalized = {
            "type": booking_type,
            "property": property_name,
            "booking_id": booking_id,
            "guest_name": guest_name,
            "mobile_no": mobile_no,
            "total_pax": total_pax,
            "check_in": str(check_in) if check_in else "",
            "check_out": str(check_out) if check_out else "",
            "days": days or 0,
            "room_no": room_no,
            "room_type": room_type,
            "mob": mob,
            "room_charges": room_charges,
            "gst": gst,
            "total": total_tariff,
            "commission": commission,
            "receivable": receivable,
            "per_night": per_night,
            "advance": advance,
            "advance_mop": advance_mop,
            "balance": balance,
            "balance_mop": balance_mop,
            "plan": plan,
            "booking_status": booking_status,
            "payment_status": payment_status,
            "submitted_by": submitted_by,
            "modified_by": modified_by,
            "remarks": remarks
        }
        return normalized
    except ValueError:
        return None  # Silently skip date parsing errors

def load_combined_bookings(property: str, start_date: date, end_date: date) -> List[Dict]:
    """Load and combine bookings from both tables for the date range."""
    try:
        # Load online reservations
        online_response = supabase.table("online_reservations").select("*").eq("property", property).gte("check_in", str(start_date)).lte("check_in", str(end_date)).execute()
        online_bookings = [normalize_booking(b, True) for b in (online_response.data or []) if normalize_booking(b, True)]
        # Load direct reservations
        direct_response = supabase.table("reservations").select("*").eq("property_name", property).gte("check_in", str(start_date)).lte("check_in", str(end_date)).execute()
        direct_bookings = [normalize_booking(b, False) for b in (direct_response.data or []) if normalize_booking(b, False)]
        # Combine and filter out None
        combined = [b for b in online_bookings + direct_bookings if b]
        return combined
    except Exception as e:
        st.error(f"Error loading bookings for {property}: {e}")
        return []

def generate_month_dates(year: int, month: int) -> List[date]:
    """Generate list of dates for the month."""
    _, num_days = calendar.monthrange(year, month)
    return [date(year, month, day) for day in range(1, num_days + 1)]

def filter_bookings_for_day(bookings: List[Dict], target_date: date) -> List[Dict]:
    """Filter active bookings on target_date, adding target_date for financial display logic."""
    filtered = []
    for b in bookings:
        check_in_str = b["check_in"]
        check_out_str = b["check_out"]
        check_in = date.fromisoformat(check_in_str) if check_in_str else None
        check_out = date.fromisoformat(check_out_str) if check_out_str else None
        if check_in and check_out:
            if (check_in <= target_date < check_out) or (check_in == check_out and check_in == target_date):
                b_copy = b.copy()
                b_copy['target_date'] = target_date  # Add target_date for later use
                filtered.append(b_copy)
    return filtered

def assign_inventory_numbers(daily_bookings: List[Dict], property: str) -> tuple[List[Dict], List[Dict]]:
    """Assign inventory numbers, handling multi-room bookings by duplicating and apportioning total_pax, marking one room as primary for financial fields."""
    assigned = []
    overbookings = []
    inventory = PROPERTY_INVENTORY.get(property, {"all": []})["all"]
    for b in daily_bookings:
        room_no = b.get('room_no', '')
        inventory_no = [r.strip() for r in room_no.split(',') if r.strip()]
        if not inventory_no:
            overbookings.append(b)
            continue
        valid = all(inv in inventory for inv in inventory_no)
        if not valid:
            overbookings.append(b)
            continue
        num_rooms = len(inventory_no)
        # Sort inventory_no for consistent ordering
        inventory_no.sort()
        # Apportion pax
        base_pax = b['total_pax'] // num_rooms
        remainder_pax = b['total_pax'] % num_rooms
        # Calculate per-night rate per room based on receivable
        days = b.get('days', 1) or 1  # Avoid division by zero
        per_night_per_room = b.get('receivable', 0.0) / num_rooms / days
        if num_rooms == 1:
            b['inventory_no'] = inventory_no
            b['per_night'] = per_night_per_room
            b['is_primary'] = True  # Mark as primary for single-room bookings
            assigned.append(b)
        else:
            for idx, inv in enumerate(inventory_no):
                new_b = b.copy()
                new_b['inventory_no'] = [inv]
                new_b['room_no'] = inv  # Update room_no to reflect single room
                new_b['total_pax'] = base_pax + (1 if idx < remainder_pax else 0)
                new_b['per_night'] = per_night_per_room
                new_b['is_primary'] = (idx == 0)  # Only first room is primary
                assigned.append(new_b)
    return assigned, overbookings

def create_group_table(group_inventory: List[str], assigned: List[Dict], columns: List[str]) -> pd.DataFrame:
    """Create inventory table DataFrame for a specific group, showing financial fields only for primary room on first date."""
    if not group_inventory:
        return pd.DataFrame(columns=columns)
    
    # Initialize DataFrame with group inventory numbers
    df_data = [{col: "" for col in columns} for _ in group_inventory]
    for i, inv in enumerate(group_inventory):
        df_data[i]["Inventory No"] = inv

    # Financial fields to display only for primary room on first date
    financial_fields = ["Room Charges", "GST", "Total", "Commision", "Receivable", 
                        "Advance", "Advance Mop", "Balance"]

    # Fill assigned bookings that belong to this group
    for b in assigned:
        inventory_no = b.get('inventory_no', [])
        if not inventory_no or not isinstance(inventory_no, list):
            continue
        for inv in inventory_no:
            if inv not in group_inventory:
                continue
            # Find the matching row in df_data
            row_indices = [i for i, row in enumerate(df_data) if row["Inventory No"] == inv]
            if not row_indices:
                continue
            row = df_data[row_indices[0]]
            # Determine if this is the first date of the stay
            check_in = date.fromisoformat(b["check_in"]) if b["check_in"] else None
            target_date = b.get('target_date')
            is_first_date = check_in == target_date if check_in and target_date else False
            try:
                row.update({
                    "Inventory No": inv,
                    "Room No": sanitize_string(b.get("room_no", "")),
                    "Booking ID": format_booking_id(b),
                    "Guest Name": sanitize_string(b.get("guest_name", "")),
                    "Mobile No": sanitize_string(b.get("mobile_no", "")),
                    "Total Pax": sanitize_string(b.get("total_pax", "")),
                    "Check In": b.get("check_in", ""),
                    "Check Out": b.get("check_out", ""),
                    "Days": b.get("days", 0),
                    "MOB": sanitize_string(b.get("mob", "")),
                    "Per Night": f"{b.get('per_night', 0):.2f}" if b.get("per_night") is not None else "0.00",
                    "Plan": sanitize_string(b.get("plan", "")),
                    "Booking Status": sanitize_string(b.get("booking_status", "")),
                    "Payment Status": sanitize_string(b.get("payment_status", "")),
                    "Submitted by": sanitize_string(b.get("submitted_by", "")),
                    "Modified by": sanitize_string(b.get("modified_by", "")),
                    "Remarks": sanitize_string(b.get("remarks", ""))
                })
                # Only populate financial fields for primary room on the first date
                if b.get('is_primary', False) and is_first_date:
                    row.update({
                        "Room Charges": sanitize_string(b.get("room_charges", "")),
                        "GST": sanitize_string(b.get("gst", "")),
                        "Total": sanitize_string(b.get("total", "")),
                        "Commision": sanitize_string(b.get("commission", "")),
                        "Receivable": sanitize_string(b.get("receivable", "")),
                        "Advance": sanitize_string(b.get("advance", "")),
                        "Advance Mop": sanitize_string(b.get("advance_mop", "")),
                        "Balance": sanitize_string(b.get("balance", ""))
                    })
            except Exception as e:
                continue

    return pd.DataFrame(df_data, columns=columns)

def create_overbookings_row(overbookings: List[Dict], columns: List[str]) -> pd.DataFrame:
    """Create a DataFrame for overbookings."""
    if not overbookings:
        return pd.DataFrame(columns=columns)
    
    try:
        overbooking_ids = ", ".join(format_booking_id(b) for b in overbookings)
        overbooking_str = ", ".join(f"{sanitize_string(b.get('room_no', ''))} ({sanitize_string(b.get('booking_id', ''))}, {sanitize_string(b.get('guest_name', ''))})" for b in overbookings)
        over_data = {
            "Inventory No": "Overbookings",
            "Room No": overbooking_str,
            "Booking ID": overbooking_ids,
            "Guest Name": "",
            "Mobile No": "",
            "Total Pax": "",
            "Check In": "",
            "Check Out": "",
            "Days": "",
            "MOB": "",
            "Room Charges": "",
            "GST": "",
            "Total": "",
            "Commision": "",
            "Receivable": "",
            "Per Night": "",
            "Advance": "",
            "Advance Mop": "",
            "Balance": "",
            "Balance Mop": "",
            "Plan": "",
            "Booking Status": "",
            "Payment Status": "",
            "Submitted by": "",
            "Modified by": "",
            "Remarks": ""
        }
        return pd.DataFrame([over_data], columns=columns)
    except Exception as e:
        return pd.DataFrame(columns=columns)

@st.cache_data
def cached_load_properties():
    return load_properties()

@st.cache_data
def cached_load_bookings(property, start_date, end_date):
    return load_combined_bookings(property, start_date, end_date)

def show_daily_status():
    """Display daily status table with inventory and bookings."""
    st.title("📅 Daily Status")
    if st.button("🔄 Refresh Property List"):
        st.cache_data.clear()
        st.success("Cache cleared! Refreshing properties...")
        st.rerun()
    current_year = date.today().year
    year = st.selectbox("Select Year", list(range(current_year - 5, current_year + 6)), index=5)
    month = st.selectbox("Select Month", list(range(1, 13)), index=date.today().month - 1)
    properties = cached_load_properties()
    if not properties:
        st.info("No properties available.")
        return
    st.subheader("Properties")
    st.markdown(TABLE_CSS, unsafe_allow_html=True)
    for prop in properties:
        with st.expander(f"{prop}"):
            month_dates = generate_month_dates(year, month)
            start_date = month_dates[0]
            end_date = month_dates[-1] + timedelta(days=1)
            bookings = cached_load_bookings(prop, start_date, end_date - timedelta(days=1))
            st.info(f"Total bookings for {prop}: {len(bookings)}")
            for day in month_dates:
                daily_bookings = filter_bookings_for_day(bookings, day)
                st.subheader(f"{prop} - {day.strftime('%B %d, %Y')}")
                if daily_bookings:
                    assigned, overbookings = assign_inventory_numbers(daily_bookings, prop)
                    columns = [
                        "Inventory No", "Room No", "Booking ID", "Guest Name", "Mobile No",
                        "Total Pax", "Check In", "Check Out", "Days", "MOB", "Room Charges",
                        "GST", "Total", "Commision", "Receivable", "Per Night", "Advance",
                        "Advance Mop", "Balance", "Balance Mop", "Plan", "Booking Status",
                        "Payment Status", "Submitted by", "Modified by", "Remarks"
                    ]
                    inventory = PROPERTY_INVENTORY.get(prop, {"all": []})["all"]
                    inventory_groups = {
                        "Regular Inventory": [inv for inv in inventory if not (inv.startswith("Day Use") or inv == "No Show")],
                        "Day Use Inventory": [inv for inv in inventory if inv.startswith("Day Use")],
                        "No Show Inventory": [inv for inv in inventory if inv == "No Show"]
                    }
                    for group_name, group_inventory in inventory_groups.items():
                        if group_inventory:
                            st.markdown(f"**{group_name}**")
                            df = create_group_table(group_inventory, assigned, columns)
                            tooltip_columns = ['Guest Name', 'Room No', 'Remarks', 'Mobile No', 'MOB', 'Plan', 'Submitted by', 'Modified by']
                            for col in tooltip_columns:
                                if col in df.columns:
                                    df[col] = df[col].apply(lambda x: f'<span title="{x}">{x}</span>' if isinstance(x, str) else x)
                            table_html = df.to_html(escape=False, index=False)
                            st.markdown(f'<div class="custom-scrollable-table">{table_html}</div>', unsafe_allow_html=True)
                    if overbookings:
                        st.markdown("**Overbookings**")
                        df_over = create_overbookings_row(overbookings, columns)
                        tooltip_columns = ['Guest Name', 'Room No', 'Remarks', 'Mobile No', 'MOB', 'Plan', 'Submitted by', 'Modified by']
                        for col in tooltip_columns:
                            if col in df_over.columns:
                                df_over[col] = df_over[col].apply(lambda x: f'<span title="{x}">{x}</span>' if isinstance(x, str) else x)
                        table_html_over = df_over.to_html(escape=False, index=False)
                        st.markdown(f'<div class="custom-scrollable-table">{table_html_over}</div>', unsafe_allow_html=True)
                else:
                    st.info("No active bookings on this day.")
