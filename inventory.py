import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta
import calendar
import pandas as pd
from typing import Any, List, Dict, Optional
import logging

# Configure file-based logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
}
reverse_mapping = {canonical: [] for canonical in set(property_mapping.values())}
for variant, canonical in property_mapping.items():
    reverse_mapping[canonical].append(variant)

# MOP (Mode of Payment) mapping
mop_mapping = {
    "UPI": ["UPI"],
    "Cash": ["Cash"],
    "Go-MMT": ["Goibibo", "MMT", "Go-MMT", "MAKEMYTRIP"],
    "Agoda": ["Agoda"],
    "NOT PAID": ["Not Paid"],
    "Bank Transfer": ["Bank Transfer"],
    "Stayflexi": ["STAYFLEXI_GHA"],
    "Card Payment": ["Card"],
    "Expedia": ["Expedia"],
    "Cleartrip": ["Cleartrip"],
    "Website": ["Stayflexi Booking Engine"]
}

# MOB (Mode of Booking) mapping
mob_mapping = {
    "Booking": ["BOOKING"],
    "Direct": ["Direct"],
    "Bkg-Direct": ["Bkg-Direct"],
    "Agoda": ["Agoda"],
    "Go-MMT": ["Goibibo", "MMT", "Go-MMT", "MAKEMYTRIP"],
    "Walk-In": ["Walk-In"],
    "TIE Group": ["TIE Group"],
    "Stayflexi": ["STAYFLEXI_GHA"],
    "Airbnb": ["Airbnb"],
    "Social Media": ["Social Media"],
    "Expedia": ["Expedia"],
    "Cleartrip": ["Cleartrip"],
    "Website": ["Stayflexi Booking Engine"]
}

# Table CSS
TABLE_CSS = """
<style>
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
    max-width: 150px;
    padding: 8px;
    border: 1px solid #ddd;
}
</style>
"""

# Property inventory
PROPERTY_INVENTORY = {
    "Le Poshe Beach view": {
        "all": ["101", "102", "201", "202", "203", "204", "301", "302", "303", "304", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204"]
    },
    "La Millionaire Resort": {
        "all": ["101", "102", "103", "105", "201", "202", "203", "204", "205", "206", "207", "208", "301", "302", "303", "304", "305", "306", "307", "308", "401", "402", "Day Use 1", "Day Use 2", "Day Use 3", "Day Use 4", "Day Use 5", "No Show"],
        "three_bedroom": ["203", "204"]
    },
    "Le Poshe Luxury": {
        "all": ["101&102", "101", "102", "201&202", "201", "202", "203to205", "203", "204", "205", "301&302", "301", "302", "303to305", "303", "304", "305", "401&402", "401", "402", "403to405", "403", "404", "405", "501", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203to205", "303to305", "403to405"]
    },
    "Le Poshe Suite": {
        "all": ["601&602", "601", "602", "603", "604", "701&702", "701", "702", "703", "704", "801", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    },
    "La Paradise Residency": {
        "all": ["101", "102", "103", "201", "202", "203", "301", "303", "304", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    },
    "La Paradise Luxury": {
        "all": ["101to103", "101", "102", "103", "201to203", "201", "202", "203", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["101to103", "201to203"]
    },
    "La Villa Heritage": {
        "all": ["101", "102", "103", "201to203&301", "201", "202", "203", "301", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    },
    "Le Pondy Beach Side": {
        "all": ["101to104", "101", "102", "103", "104", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    }
}

# === Helper Functions ===
def normalize_property(name: str) -> str:
    return property_mapping.get(name.strip(), name.strip())

@st.cache_data(ttl=3600)
def cached_load_properties() -> List[str]:
    try:
        response = supabase.table("reservations").select("property_name").execute()
        direct_props = {r["property_name"] for r in response.data if r["property_name"]}
        response = supabase.table("online_reservations").select("property").execute()
        online_props = {r["property"] for r in response.data if r["property"]}
        all_props = {normalize_property(p) for p in direct_props.union(online_props)}
        return sorted(all_props)
    except Exception as e:
        logging.error(f"Error loading properties: {e}")
        return []

def generate_month_dates(year: int, month: int) -> List[date]:
    _, num_days = calendar.monthrange(year, month)
    return [date(year, month, day) for day in range(1, num_days + 1)]

@st.cache_data(ttl=300)
def load_combined_bookings(property: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
    prop = normalize_property(property)
    combined = []

    # === Direct Reservations (Overlap + Status Filter) ===
    try:
        direct_query = (
            supabase.table("reservations")
            .select("*")
            .eq("property_name", prop)
            .lte("check_in", str(end_date))
            .gte("check_out", str(start_date))
            .in_("booking_status", ["Confirmed", "Completed"])
            .in_("payment_status", ["Partially Paid", "Fully Paid"])
            .execute()
        )
        for res in direct_query.data:
            norm = normalize_booking(res, source="direct")
            if norm:
                combined.append(norm)
        logging.info(f"Loaded {len(direct_query.data)} direct bookings for {prop}")
    except Exception as e:
        logging.error(f"Error loading direct bookings: {e}")

    # === Online Reservations (Overlap + Status Filter) ===
    try:
        online_query = (
            supabase.table("online_reservations")
            .select("*")
            .eq("property", prop)
            .lte("check_in", str(end_date))
            .gte("check_out", str(start_date))
            .in_("status", ["Confirmed", "Completed"])
            .in_("payment_status", ["Partially Paid", "Fully Paid"])
            .execute()
        )
        for res in online_query.data:
            norm = normalize_booking(res, source="online")
            if norm:
                combined.append(norm)
        logging.info(f"Loaded {len(online_query.data)} online bookings for {prop}")
    except Exception as e:
        logging.error(f"Error loading online bookings: {e}")

    combined.sort(key=lambda x: x.get("check_in", date.today()))
    return combined

def normalize_booking(booking: Dict[str, Any], source: str = "direct") -> Optional[Dict[str, Any]]:
    try:
        normalized = {
            "booking_id": booking.get("booking_id") or booking.get("id"),
            "guest_name": booking.get("guest_name", "").strip(),
            "check_in": date.fromisoformat(booking["check_in"]),
            "check_out": date.fromisoformat(booking["check_out"]),
            "room_no": booking.get("room_no", ""),
            "room_type": booking.get("room_type", ""),
            "total_pax": int(booking.get("total_pax", 0) or 0),
            "total_tariff": float(booking.get("total_tariff", 0) or 0),
            "mob": booking.get("mob") or booking.get("source", ""),
            "mop": booking.get("mop") or booking.get("payment_method", ""),
            "plan": booking.get("plan", ""),
            "remarks": booking.get("remarks", ""),
            "mobile_no": booking.get("mobile_no", ""),
            "submitted_by": booking.get("submitted_by", ""),
            "modified_by": booking.get("modified_by", ""),
            "source": source
        }
        return normalized
    except Exception as e:
        logging.warning(f"Failed to normalize booking {booking.get('booking_id')}: {e}")
        return None

def filter_bookings_for_day(bookings: List[Dict], day: date) -> List[Dict]:
    return [
        b for b in bookings
        if b["check_in"] <= day < b["check_out"]
    ]

def assign_inventory_numbers(daily_bookings: List[Dict], property: str) -> tuple:
    inventory = PROPERTY_INVENTORY.get(property, {"all": []})["all"][:]
    assigned = []
    overbookings = []
    used_rooms = set()

    for booking in daily_bookings:
        room = booking["room_no"]
        if room in inventory and room not in used_rooms:
            assigned.append({**booking, "assigned_room": room})
            used_rooms.add(room)
        else:
            overbookings.append(booking)
    return assigned, overbookings

def create_inventory_table(assigned: List[Dict], overbookings: List[Dict], property: str) -> pd.DataFrame:
    rows = []
    inventory = PROPERTY_INVENTORY.get(property, {"all": []})["all"]

    for room in inventory:
        if room == "No Show":
            rows.append({"Room No": room, "Guest Name": "No Show", "Booking ID": ""})
            continue
        found = next((a for a in assigned if a["assigned_room"] == room), None)
        if found:
            rows.append({
                "Room No": found["assigned_room"],
                "Guest Name": found["guest_name"],
                "Booking ID": f'<a href="#">{found["booking_id"]}</a>',
                "MOB": found["mob"],
                "Plan": found["plan"],
                "Remarks": found["remarks"],
                "Mobile No": found["mobile_no"],
                "Submitted by": found["submitted_by"],
                "Modified by": found["modified_by"]
            })
        else:
            rows.append({"Room No": room, "Guest Name": "", "Booking ID": ""})

    for ob in overbookings:
        rows.append({
            "Room No": "OVERBOOK",
            "Guest Name": ob["guest_name"],
            "Booking ID": f'<a href="#">{ob["booking_id"]}</a>',
            "MOB": ob["mob"],
            "Plan": ob["plan"],
            "Remarks": ob["remarks"],
            "Mobile No": ob["mobile_no"],
            "Submitted by": ob["submitted_by"],
            "Modified by": ob["modified_by"]
        })
    return pd.DataFrame(rows)

def compute_statistics(bookings: List[Dict], property: str, day: date, month_dates: List[date]) -> tuple:
    # D.T.D
    daily = [b for b in filter_bookings_for_day(bookings, day) if b["source"] == "direct"]
    dtd_df = pd.DataFrame([
        {"MOB": mob, "Count": sum(1 for b in daily if b["mob"] in mob_mapping[mob])}
        for mob in mob_mapping
    ]).set_index("MOB")

    # M.T.D
    mtd = [b for b in bookings if b["source"] == "direct" and b["check_in"] <= day]
    mtd_df = pd.DataFrame([
        {"MOB": mob, "Count": sum(1 for b in mtd if b["mob"] in mob_mapping[mob])}
        for mob in mob_mapping
    ]).set_index("MOB")

    # MOP Report
    mop_df = pd.DataFrame([
        {"MOP": mop, "Count": sum(1 for b in daily if b["mop"] in mop_mapping[mop])}
        for mop in mop_mapping
    ]).set_index("MOP")

    # Summary
    rooms_sold = len(daily)
    value = sum(b["total_tariff"] for b in daily)
    total_pax = sum(b["total_pax"] for b in daily)
    total_inventory = len(PROPERTY_INVENTORY.get(property, {"all": []})["all"]) - 1  # exclude No Show
    occ_percent = (rooms_sold / total_inventory * 100) if total_inventory > 0 else 0
    arr = value / rooms_sold if rooms_sold > 0 else 0

    # M.T.D Summary
    mtd_rooms = sum(1 for b in mtd if b["check_in"] <= day < b["check_out"])
    mtd_value = sum(b["total_tariff"] for b in mtd if b["check_in"] <= day < b["check_out"])
    mtd_pax = sum(b["total_pax"] for b in mtd if b["check_in"] <= day < b["check_out"])
    mtd_occ = (mtd_rooms / total_inventory * 100) if total_inventory > 0 else 0

    summary = {
        "rooms_sold": rooms_sold,
        "value": value,
        "arr": arr,
        "occ_percent": occ_percent,
        "total_pax": total_pax,
        "total_inventory": total_inventory,
        "gst": value * 0.18,  # example
        "commission": value * 0.1,
        "tax_deduction": value * 0.01,
        "mtd_occ_percent": mtd_occ,
        "mtd_pax": mtd_pax,
        "mtd_rooms": mtd_rooms,
        "mtd_gst": mtd_value * 0.18,
        "mtd_tax_deduction": mtd_value * 0.01,
        "mtd_value": mtd_value
    }

    return dtd_df, mtd_df, summary, mop_df

# === Main UI ===
def show_daily_status():
    st.title("Daily Status")
    if st.button("Refresh Property List"):
        st.cache_data.clear()
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
            end_date = month_dates[-1]
            bookings = load_combined_bookings(prop, start_date, end_date)

            for day in month_dates:
                daily_bookings = filter_bookings_for_day(bookings, day)
                st.subheader(f"{prop} - {day.strftime('%B %d, %Y')}")

                if daily_bookings:
                    assigned, overbookings = assign_inventory_numbers(daily_bookings, prop)
                    df = create_inventory_table(assigned, overbookings, prop)

                    if 'Booking ID' in df.columns:
                        df['Booking ID'] = df['Booking ID'].apply(
                            lambda x: f'<span style="font-size: 0.75em;">{x.split(">")[1].split("</a>")[0] if ">" in str(x) else x}</span>'
                        )
                    tooltip_cols = ['Guest Name', 'Room No', 'Remarks', 'Mobile No', 'MOB', 'Plan', 'Submitted by', 'Modified by']
                    for col in tooltip_cols:
                        if col in df.columns:
                            df[col] = df[col].apply(lambda x: f'<span title="{x}">{x}</span>' if isinstance(x, str) and x else x)

                    table_html = df.to_html(escape=False, index=False)
                    st.markdown(f'<div class="custom-scrollable-table">{table_html}</div>', unsafe_allow_html=True)

                    dtd_df, mtd_df, summary, mop_df = compute_statistics(bookings, prop, day, month_dates)
                    col1, col2, col3, col4 = st.columns(4)
                    with col1: st.subheader("MOP Report"); st.dataframe(mop_df, use_container_width=True)
                    with col2: st.subheader("D.T.D"); st.dataframe(dtd_df, use_container_width=True)
                    with col3: st.subheader("M.T.D"); st.dataframe(mtd_df, use_container_width=True)
                    with col4:
                        st.subheader("Summary")
                        st.dataframe(pd.DataFrame([
                            {"Metric": k.replace("_", " ").title(), "Value": f"{v:.2f}" if isinstance(v, float) else v}
                            for k, v in summary.items()
                        ]), use_container_width=True)
                else:
                    st.info("No active bookings on this day.")
