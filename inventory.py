# ──────────────────────────────────────────────────────────────────────────────
# inventory.py   (full, production-ready)
# ──────────────────────────────────────────────────────────────────────────────
import streamlit as st
from supabase import create_client, Client
from datetime import date
import calendar
import pandas as pd
from typing import Any, List, Dict, Optional
import logging

# ────── Logging ──────
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ────── Supabase client ──────
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

# ────── Property synonym mapping ──────
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

# ────── MOP / MOB mappings ──────
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
    "Website": ["Stayflexi Booking Engine"],
}
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
    "Website": ["Stayflexi Booking Engine"],
}

# ────── CSS for scrollable tables ──────
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

# ────── Full inventory (room numbers) ──────
PROPERTY_INVENTORY = {
    "Le Poshe Beach view": {
        "all": [
            "101", "102", "201", "202", "203", "204",
            "301", "302", "303", "304",
            "Day Use 1", "Day Use 2", "No Show"
        ],
        "three_bedroom": ["203", "204"]
    },
    "La Millionaire Resort": {
        "all": [
            "101", "102", "103", "105",
            "201", "202", "203", "204", "205", "206", "207", "208",
            "301", "302", "303", "304", "305", "306", "307", "308",
            "401", "402",
            "Day Use 1", "Day Use 2", "Day Use 3", "Day Use 4", "Day Use 5",
            "No Show"
        ],
        "three_bedroom": ["203", "204"]
    },
    "Le Poshe Luxury": {
        "all": [
            "101&102", "101", "102",
            "201&202", "201", "202",
            "203to205", "203", "204", "205",
            "301&302", "301", "302",
            "303to305", "303", "304", "305",
            "401&402", "401", "402",
            "403to405", "403", "404", "405",
            "501",
            "Day Use 1", "Day Use 2", "No Show"
        ],
        "three_bedroom": ["203to205", "303to305", "403to405"]
    },
    "Le Poshe Suite": {
        "all": [
            "601&602", "601", "602", "603", "604",
            "701&702", "701", "702", "703", "704",
            "801",
            "Day Use 1", "Day Use 2", "No Show"
        ],
        "three_bedroom": []
    },
    "La Paradise Residency": {
        "all": [
            "101", "102", "103",
            "201", "202", "203",
            "301", "303", "304",
            "Day Use 1", "Day Use 2", "No Show"
        ],
        "three_bedroom": []
    },
    "La Paradise Luxury": {
        "all": [
            "101to103", "101", "102", "103",
            "201to203", "201", "202", "203",
            "Day Use 1", "Day Use 2", "No Show"
        ],
        "three_bedroom": ["101to103", "201to203"]
    },
    "La Villa Heritage": {
        "all": [
            "101", "102", "103",
            "201to203&301", "201", "202", "203", "301",
            "Day Use 1", "Day Use 2", "No Show"
        ],
        "three_bedroom": []
    },
    "Le Pondy Beach Side": {
        "all": [
            "101to104", "101", "102", "103", "104",
            "Day Use 1", "Day Use 2", "No Show"
        ],
        "three_bedroom": []
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# Helper functions (exported for other modules)
# ──────────────────────────────────────────────────────────────────────────────
def normalize_property(name: str) -> str:
    """Map any known synonym → canonical name."""
    return property_mapping.get(name.strip(), name.strip())

@st.cache_data(ttl=3600)
def load_properties() -> List[str]:
    """Return a sorted list of *canonical* property names that exist in the DB."""
    try:
        direct = supabase.table("reservations").select("property_name").execute()
        online = supabase.table("online_reservations").select("property").execute()

        direct_set = {r["property_name"] for r in direct.data if r.get("property_name")}
        online_set = {r["property"] for r in online.data if r.get("property")}

        all_props = {normalize_property(p) for p in direct_set.union(online_set)}
        return sorted(all_props)
    except Exception as e:
        logging.error(f"load_properties error: {e}")
        return []

@st.cache_data(ttl=300)
def load_combined_bookings(property: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """Fetch *direct* + *online* bookings that overlap the month **and** are Confirmed + Paid."""
    prop = normalize_property(property)
    combined: List[Dict[str, Any]] = []

    # ---------- Direct reservations ----------
    try:
        q = (
            supabase.table("reservations")
            .select("*")
            .eq("property_name", prop)
            .lte("check_in", str(end_date))
            .gte("check_out", str(start_date))
            .in_("booking_status", ["Confirmed", "Completed"])
            .in_("payment_status", ["Partially Paid", "Fully Paid"])
            .execute()
        )
        for r in q.data:
            norm = normalize_booking(r, source="direct")
            if norm:
                combined.append(norm)
        logging.info(f"Direct bookings for {prop}: {len(q.data)}")
    except Exception as e:
        logging.error(f"Direct query error ({prop}): {e}")

    # ---------- Online reservations ----------
    try:
        q = (
            supabase.table("online_reservations")
            .select("*")
            .eq("property", prop)
            .lte("check_in", str(end_date))
            .gte("check_out", str(start_date))
            .in_("status", ["Confirmed", "Completed"])
            .in_("payment_status", ["Partially Paid", "Fully Paid"])
            .execute()
        )
        for r in q.data:
            norm = normalize_booking(r, source="online")
            if norm:
                combined.append(norm)
        logging.info(f"Online bookings for {prop}: {len(q.data)}")
    except Exception as e:
        logging.error(f"Online query error ({prop}): {e}")

    combined.sort(key=lambda x: x.get("check_in", date.today()))
    return combined

def normalize_booking(booking: Dict[str, Any], source: str = "direct") -> Optional[Dict[str, Any]]:
    """Turn a raw DB row into the dict used everywhere else."""
    try:
        return {
            "booking_id": booking.get("booking_id") or booking.get("id"),
            "guest_name": (booking.get("guest_name") or "").strip(),
            "check_in": date.fromisoformat(booking["check_in"]),
            "check_out": date.fromisoformat(booking["check_out"]),
            "room_no": booking.get("room_no", ""),
            "room_type": booking.get("room_type", ""),
            "total_pax": int(booking.get("total_pax") or 0),
            "total_tariff": float(booking.get("total_tariff") or 0),
            "mob": booking.get("mob") or booking.get("source", ""),
            "mop": booking.get("mop") or booking.get("payment_method", ""),
            "plan": booking.get("plan", ""),
            "remarks": booking.get("remarks", ""),
            "mobile_no": booking.get("mobile_no", ""),
            "submitted_by": booking.get("submitted_by", ""),
            "modified_by": booking.get("modified_by", ""),
            "source": source,
        }
    except Exception as e:
        logging.warning(f"normalize_booking failed: {e}")
        return None

def filter_bookings_for_day(bookings: List[Dict], day: date) -> List[Dict]:
    """Return bookings that are active on *day* (check-in ≤ day < check-out)."""
    return [b for b in bookings if b["check_in"] <= day < b["check_out"]]

def assign_inventory_numbers(daily_bookings: List[Dict], property: str):
    """Allocate physical rooms; everything else → OVERBOOK."""
    inventory = PROPERTY_INVENTORY.get(property, {"all": []})["all"][:]
    assigned, overbookings = [], []
    used = set()

    for b in daily_bookings:
        room = b["room_no"]
        if room in inventory and room not in used:
            assigned.append({**b, "assigned_room": room})
            used.add(room)
        else:
            overbookings.append(b)
    return assigned, overbookings

def create_inventory_table(assigned: List[Dict], overbookings: List[Dict], property: str) -> pd.DataFrame:
    rows = []
    all_rooms = PROPERTY_INVENTORY.get(property, {"all": []})["all"]

    for room in all_rooms:
        if room == "No Show":
            rows.append({"Room No": room, "Guest Name": "No Show", "Booking ID": ""})
            continue

        match = next((a for a in assigned if a["assigned_room"] == room), None)
        if match:
            rows.append({
                "Room No": match["assigned_room"],
                "Guest Name": match["guest_name"],
                "Booking ID": f'<a href="#">{match["booking_id"]}</a>',
                "MOB": match["mob"],
                "Plan": match["plan"],
                "Remarks": match["remarks"],
                "Mobile No": match["mobile_no"],
                "Submitted by": match["submitted_by"],
                "Modified by": match["modified_by"],
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
            "Modified by": ob["modified_by"],
        })
    return pd.DataFrame(rows)

def compute_statistics(bookings: List[Dict], property: str, day: date, month_dates: List[date]):
    # D.T.D
    daily = [b for b in filter_bookings_for_day(bookings, day) if b["source"] == "direct"]
    dtd_df = pd.DataFrame(
        [{"MOB": mob, "Count": sum(1 for b in daily if b["mob"] in mob_mapping[mob])}
         for mob in mob_mapping]
    ).set_index("MOB")

    # M.T.D
    mtd = [b for b in bookings if b["source"] == "direct" and b["check_in"] <= day]
    mtd_df = pd.DataFrame(
        [{"MOB": mob, "Count": sum(1 for b in mtd if b["mob"] in mob_mapping[mob])}
         for mob in mob_mapping]
    ).set_index("MOB")

    # MOP
    mop_df = pd.DataFrame(
        [{"MOP": mop, "Count": sum(1 for b in daily if b["mop"] in mop_mapping[mop])}
         for mop in mop_mapping]
    ).set_index("MOP")

    # Summary numbers
    rooms_sold = len(daily)
    value = sum(b["total_tariff"] for b in daily)
    total_pax = sum(b["total_pax"] for b in daily)
    total_inventory = len(PROPERTY_INVENTORY.get(property, {"all": []})["all"]) - 1  # exclude No Show
    occ_percent = (rooms_sold / total_inventory * 100) if total_inventory else 0
    arr = value / rooms_sold if rooms_sold else 0

    # M.T.D aggregates
    mtd_rooms = sum(1 for b in mtd if b["check_in"] <= day < b["check_out"])
    mtd_value = sum(b["total_tariff"] for b in mtd if b["check_in"] <= day < b["check_out"])
    mtd_pax = sum(b["total_pax"] for b in mtd if b["check_in"] <= day < b["check_out"])
    mtd_occ = (mtd_rooms / total_inventory * 100) if total_inventory else 0

    summary = {
        "rooms_sold": rooms_sold,
        "value": value,
        "arr": arr,
        "occ_percent": occ_percent,
        "total_pax": total_pax,
        "total_inventory": total_inventory,
        "gst": value * 0.18,
        "commission": value * 0.10,
        "tax_deduction": value * 0.01,
        "mtd_occ_percent": mtd_occ,
        "mtd_pax": mtd_pax,
        "mtd_rooms": mtd_rooms,
        "mtd_gst": mtd_value * 0.18,
        "mtd_tax_deduction": mtd_value * 0.01,
        "mtd_value": mtd_value,
    }
    return dtd_df, mtd_df, summary, mop_df

# ──────────────────────────────────────────────────────────────────────────────
# UI – Daily Status page
# ──────────────────────────────────────────────────────────────────────────────
def show_daily_status():
    st.title("Daily Status")
    if st.button("Refresh Property List"):
        st.cache_data.clear()
        st.rerun()

    today = date.today()
    year = st.selectbox(
        "Select Year",
        list(range(today.year - 5, today.year + 6)),
        index=5,
    )
    month = st.selectbox(
        "Select Month",
        list(range(1, 13)),
        index=today.month - 1,
    )
    properties = load_properties()
    if not properties:
        st.info("No properties found in the database.")
        return

    st.subheader("Properties")
    st.markdown(TABLE_CSS, unsafe_allow_html=True)

    for prop in properties:
        with st.expander(prop):
            month_dates = [date(year, month, d) for d in range(1, calendar.monthrange(year, month)[1] + 1)]
            start_date, end_date = month_dates[0], month_dates[-1]

            bookings = load_combined_bookings(prop, start_date, end_date)

            for day in month_dates:
                daily = filter_bookings_for_day(bookings, day)
                st.subheader(f"{prop} – {day.strftime('%B %d, %Y')}")

                if daily:
                    assigned, over = assign_inventory_numbers(daily, prop)
                    df = create_inventory_table(assigned, over, prop)

                    # Shrink Booking ID
                    if "Booking ID" in df.columns:
                        df["Booking ID"] = df["Booking ID"].apply(
                            lambda x: f'<span style="font-size:0.75em;">{x.split(">")[1].split("</a>")[0] if ">" in str(x) else x}</span>'
                        )

                    # Tool-tips
                    tooltip_cols = ["Guest Name", "Room No", "Remarks", "Mobile No", "MOB", "Plan", "Submitted by", "Modified by"]
                    for c in tooltip_cols:
                        if c in df.columns:
                            df[c] = df[c].apply(
                                lambda v: f'<span title="{v}">{v}</span>' if isinstance(v, str) and v else v
                            )

                    st.markdown(
                        f'<div class="custom-scrollable-table">{df.to_html(escape=False, index=False)}</div>',
                        unsafe_allow_html=True,
                    )

                    dtd_df, mtd_df, summary, mop_df = compute_statistics(bookings, prop, day, month_dates)

                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.subheader("MOP Report")
                        st.dataframe(mop_df, use_container_width=True)
                    with c2:
                        st.subheader("D.T.D")
                        st.dataframe(dtd_df, use_container_width=True)
                    with c3:
                        st.subheader("M.T.D")
                        st.dataframe(mtd_df, use_container_width=True)
                    with c4:
                        st.subheader("Summary")
                        st.dataframe(
                            pd.DataFrame(
                                [
                                    {
                                        "Metric": k.replace("_", " ").title(),
                                        "Value": f"{v:.2f}" if isinstance(v, float) else v,
                                    }
                                    for k, v in summary.items()
                                ]
                            ),
                            use_container_width=True,
                        )
                else:
                    st.info("No active bookings on this day.")
