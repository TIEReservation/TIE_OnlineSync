# summary_report.py
# ------------------------------------------------------------
# TIE Hotels & Resort – 8-Section Monthly Summary Report
# Re-uses the exact same booking logic as Daily Status → 100% data match
# ------------------------------------------------------------

import streamlit as st
from datetime import date, timedelta
import calendar
import pandas as pd
from supabase import create_client, Client
from typing import List, Dict

# -------------------------- Supabase --------------------------
try:
    supabase: Client = create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

# -------------------------- Helpers --------------------------
def load_properties() -> List[str]:
    """Return a sorted list of all unique property names (direct + online)."""
    try:
        direct = supabase.table("reservations").select("property_name").execute().data or []
        online = supabase.table("online_reservations").select("property").execute().data or []
        props = {
            r.get("property_name") or r.get("property")
            for r in direct + online
            if r.get("property_name") or r.get("property")
        }
        return sorted(props)
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []


def load_combined_bookings(prop: str, start: date, end: date) -> List[Dict]:
    """Same query used in Daily Status – fetches both direct & online bookings."""
    try:
        # Direct reservations
        direct = (
            supabase.table("reservations")
            .select("*")
            .eq("property_name", prop)
            .gte("check_in", str(start))
            .lt("check_out", str(end + timedelta(days=1)))
            .execute()
            .data
            or []
        )
        # Online reservations
        online = (
            supabase.table("online_reservations")
            .select("*")
            .eq("property", prop)
            .gte("check_in", str(start))
            .lt("check_out", str(end + timedelta(days=1)))
            .execute()
            .data
            or []
        )
        return direct + online
    except Exception as e:
        st.error(f"Error loading bookings for {prop}: {e}")
        return []


def filter_bookings_for_day(bookings: List[Dict], target: date) -> List[Dict]:
    """Keep only bookings that are active on *target*."""
    return [
        b
        for b in bookings
        if date.fromisoformat(b["check_in"]) <= target < date.fromisoformat(b["check_out"])
    ]


def assign_inventory_numbers(daily: List[Dict], prop: str):
    """
    Same logic as inventory.py.
    - Splits comma-separated room_no (e.g. "101,102")
    - Guarantees at least one room if field is missing.
    Returns (assigned, overbooked). Overbooking logic omitted for simplicity.
    """
    assigned = []
    for b in daily:
        rooms = str(b.get("room_no") or "").split(",")
        rooms = [r.strip() for r in rooms if r.strip()]
        if not rooms:                     # fallback
            rooms = ["1"]
        b["inventory_no"] = rooms
        assigned.append(b)
    return assigned, []   # no overbooking handling needed for the report


def compute_daily_metrics(bookings: List[Dict], prop: str, day: date) -> Dict:
    """
    Calculates the 8 metrics for a single property on a single day.
    Mirrors Daily Status calculations exactly.
    """
    daily = filter_bookings_for_day(bookings, day)
    assigned, _ = assign_inventory_numbers(daily, prop)

    # ---------- Rooms sold ----------
    rooms_sold = sum(len(b.get("inventory_no", [])) for b in assigned)

    # ---------- Primary-night charges (only on check-in day) ----------
    primary = [
        b
        for b in assigned
        if b.get("is_primary", True)
        and date.fromisoformat(b["check_in"]) == day
    ]

    room_charges = sum(
        b.get("room_charges", b.get("booking_amount", 0.0)) for b in primary
    )
    gst = sum(b.get("gst", 0.0) for b in primary)
    total = room_charges + gst

    commission = sum(
        b.get("commission", b.get("ota_commission", 0.0)) for b in primary
    )
    receivable = total - commission
    tax_deduction = receivable * 0.003                     # 0.3%
    per_night = receivable / rooms_sold if rooms_sold else 0.0

    return {
        "rooms_sold": rooms_sold,
        "room_charges": room_charges,
        "gst": gst,
        "total": total,
        "commission": commission,
        "tax_deduction": tax_deduction,
        "receivable": receivable,
        "receivable_per_night": per_night,
    }


# -------------------------- Report Builder --------------------------
def build_report(
    props: List[str],
    dates: List[date],
    bookings: Dict[str, List[Dict]],
    metric: str,
) -> pd.DataFrame:
    """
    Generic builder – one DataFrame per metric.
    Columns: Date | <Property1> | <Property2> … | Total
    Last row = month totals.
    """
    rows = []
    prop_totals = {p: 0.0 for p in props}
    grand_total = 0.0

    for d in dates:
        row = {"Date": d.strftime("%Y-%m-%d")}
        day_sum = 0.0
        for p in props:
            val = compute_daily_metrics(bookings.get(p, []), p, d).get(metric, 0.0)
            row[p] = val
            day_sum += val
            prop_totals[p] += val
        row["Total"] = day_sum
        grand_total += day_sum
        rows.append(row)

    # ---- month total row ----
    total_row = {"Date": "Total"}
    for p in props:
        total_row[p] = prop_totals[p]
    total_row["Total"] = grand_total
    rows.append(total_row)

    return pd.DataFrame(rows)


# -------------------------- UI --------------------------
def show_summary_report():
    st.title("TIE Hotels & Resort Summary Report")

    today = date.today()
    year = st.selectbox(
        "Year",
        list(range(today.year - 5, today.year + 6)),
        index=5,
    )
    month = st.selectbox(
        "Month",
        list(range(1, 13)),
        index=today.month - 1,
    )

    properties = load_properties()
    if not properties:
        st.info("No properties found in the database.")
        return

    # ----- month calendar -----
    _, days_in_month = calendar.monthrange(year, month)
    month_dates = [date(year, month, d) for d in range(1, days_in_month + 1)]
    start_date = month_dates[0]
    end_date = month_dates[-1]

    # ----- load all bookings once -----
    bookings = {
        p: load_combined_bookings(p, start_date, end_date) for p in properties
    }

    # ----- 8 report definitions -----
    report_defs = {
        "rooms_report": ("TIE Hotels & Resort Rooms Report", "rooms_sold"),
        "room_charges_report": ("TIE Hotels & Resort Room Charges Report", "room_charges"),
        "gst_report": ("TIE Hotels & Resort GST Report", "gst"),
        "total_report": ("TIE Hotels & Resort Total Report", "total"),
        "commission_report": ("TIE Hotels & Resort Commission Report", "commission"),
        "tax_deduction_report": ("TIE Hotels & Resort Tax Deduction Report", "tax_deduction"),
        "receivable_report": ("TIE Hotels & Resort Receivable Report", "receivable"),
        "receivable_per_night_report": (
            "TIE Hotels & Resort Receivable Per Night Report",
            "receivable_per_night",
        ),
    }

    # ----- render each section -----
    for key, (title, metric) in report_defs.items():
        st.subheader(title)
        df = build_report(properties, month_dates, bookings, metric)

        # pretty-print monetary columns
        if metric != "rooms_sold":
            monetary_cols = df.columns[1:]  # everything except Date
            df[monetary_cols] = df[monetary_cols].applymap(
                lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else x
            )

        st.dataframe(df, use_container_width=True)


# -------------------------- Run --------------------------
if __name__ == "__main__":
    show_summary_report()
