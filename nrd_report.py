"""
nrd_report.py - Night Report Dashboard for TIE Hotels & Resorts (Streamlit Integration)

This module provides a Streamlit interface for generating overall daily reports
across all TIE Hotels & Resorts properties.
"""

import streamlit as st
from datetime import date, timedelta
import pandas as pd
from typing import Dict, List, Any, Optional
import logging
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
import os
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ============================================================================
# CONFIGURATION
# ============================================================================

PROPERTY_SHORT_NAMES = {
    "Le Poshe Beach view": "LPBV",
    "La Millionaire Resort": "LMR",
    "Le Poshe Luxury": "LePL",
    "Le Poshe Suite": "LPS",
    "La Paradise Residency": "LPR",
    "La Paradise Luxury": "LaPL",
    "La Villa Heritage": "LVH",
    "Le Pondy Beachside": "LPB",
    "Le Royce Villa": "LRV",
    "La Tamara Luxury": "LTL",
    "La Antilia Luxury": "LAL",
    "La Tamara Suite": "LTS",
    "Le Park Resort": "LePR",
    "Villa Shakti": "VS",
    "Eden Beach Resort": "EBR",
    "Le Terra": "LT",
    "La Coromandel Luxury": "LCL",
    "Happymates Forest Retreat": "HFR"
}

PROPERTY_INVENTORY = {
    "Le Poshe Beach view": 10,
    "La Millionaire Resort": 22,
    "Le Poshe Luxury": 18,
    "Le Poshe Suite": 9,
    "La Paradise Residency": 10,
    "La Paradise Luxury": 6,
    "La Villa Heritage": 7,
    "Le Pondy Beachside": 4,
    "Le Royce Villa": 4,
    "La Tamara Luxury": 22,
    "La Antilia Luxury": 10,
    "La Tamara Suite": 11,
    "Le Park Resort": 6,
    "Villa Shakti": 11,
    "Eden Beach Resort": 5,
    "Le Terra": 7,
    "La Coromandel Luxury": 10,
    "Happymates Forest Retreat": 2
}

property_mapping = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view",
    "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Le Poshe Beachview": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
    "Le Pondy Beach Side": "Le Pondy Beachside",
    "Le Teera": "Le Terra"
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_property(name: str) -> str:
    """Normalize property name using mapping"""
    return property_mapping.get(name.strip(), name.strip())

def sanitize_string(v: Any, default: str = "") -> str:
    """Safely convert value to string"""
    return str(v).strip() if v is not None else default

def safe_int(v: Any, default: int = 0) -> int:
    """Safely convert value to integer"""
    try:
        return int(float(v)) if v not in [None, "", " "] else default
    except:
        return default

def safe_float(v: Any, default: float = 0) -> float:
    """Safely convert value to float"""
    try:
        return float(v) if v not in [None, "", " "] else default
    except:
        return default

# ============================================================================
# DATA NORMALIZATION
# ============================================================================

def normalize_booking(row: Dict, is_online: bool) -> Optional[Dict]:
    """Normalize booking data from Supabase"""
    try:
        status_field = "booking_status" if is_online else "plan_status"
        status = sanitize_string(row.get(status_field, "")).title()
        if status not in ["Confirmed", "Completed"]:
            return None
        
        pay = sanitize_string(row.get("payment_status")).title()
        if pay not in ["Fully Paid", "Partially Paid"]:
            return None
        
        ci = date.fromisoformat(row["check_in"])
        co = date.fromisoformat(row["check_out"])
        if co <= ci:
            return None
        
        days_field = "room_nights" if is_online else "no_of_days"
        days = safe_int(row.get(days_field)) or (co - ci).days
        if days <= 0:
            days = 1
        
        p = normalize_property(
            row.get("property_name") if not is_online else row.get("property")
        )
        
        if is_online:
            total_amount = safe_float(row.get("booking_amount")) or 0.0
            gst = safe_float(row.get("gst")) or 0.0
            tax = safe_float(row.get("ota_tax")) or 0.0
            commission = safe_float(row.get("ota_commission")) or 0.0
            room_charges = total_amount - gst - tax
        else:
            total_amount = safe_float(row.get("total_tariff")) or 0.0
            gst = tax = commission = 0.0
            room_charges = total_amount
        
        receivable = total_amount - gst - tax - commission
        if receivable < 0:
            receivable = 0.0
        
        bid = sanitize_string(row.get("booking_id") or row.get("id"))
        
        return {
            "type": "online" if is_online else "direct",
            "property": p,
            "booking_id": bid,
            "guest_name": sanitize_string(row.get("guest_name")),
            "total_pax": safe_int(row.get("total_pax")),
            "check_in": str(ci),
            "check_out": str(co),
            "days": days,
            "room_no": sanitize_string(row.get("room_no")).title(),
            "room_charges": room_charges,
            "gst": gst,
            "tax": tax,
            "total_amount": total_amount,
            "commission": commission,
            "receivable": receivable,
        }
    except Exception as e:
        logging.warning(f"normalize_booking failed: {e}")
        return None

# ============================================================================
# DATA FETCHING
# ============================================================================

def fetch_bookings_from_supabase(supabase, property_name: str, start_date: date, end_date: date) -> List[Dict]:
    """Fetch and normalize bookings for a property from Supabase"""
    query_props = [property_name]
    for variant, normalized in property_mapping.items():
        if normalized == property_name:
            query_props.append(variant)
    
    combined: List[Dict] = []
    
    try:
        query = (
            supabase.table("reservations")
            .select("*")
            .in_("property_name", query_props)
            .lte("check_in", str(end_date))
            .gte("check_out", str(start_date))
            .in_("plan_status", ["Confirmed", "Completed"])
            .in_("payment_status", ["Partially Paid", "Fully Paid"])
        )
        result = query.execute()
        
        for row in result.data or []:
            normalized = normalize_booking(row, is_online=False)
            if normalized:
                combined.append(normalized)
    except Exception as e:
        logging.error(f"Error fetching direct bookings for {property_name}: {e}")
    
    try:
        query = (
            supabase.table("online_reservations")
            .select("*")
            .in_("property", query_props)
            .lte("check_in", str(end_date))
            .gte("check_out", str(start_date))
            .in_("booking_status", ["Confirmed", "Completed"])
            .in_("payment_status", ["Partially Paid", "Fully Paid"])
        )
        result = query.execute()
        
        for row in result.data or []:
            normalized = normalize_booking(row, is_online=True)
            if normalized:
                combined.append(normalized)
    except Exception as e:
        logging.error(f"Error fetching online bookings for {property_name}: {e}")
    
    return combined

def fetch_all_properties_data(supabase, target_date: date) -> Dict[str, List[Dict]]:
    """Fetch bookings for all properties"""
    start_date = target_date - timedelta(days=30)
    end_date = target_date + timedelta(days=30)
    
    all_data = {}
    
    for property_name in PROPERTY_SHORT_NAMES.keys():
        bookings = fetch_bookings_from_supabase(supabase, property_name, start_date, end_date)
        all_data[property_name] = bookings
    
    return all_data

# ============================================================================
# METRICS CALCULATION
# ============================================================================

def calculate_property_metrics(bookings: List[Dict], property_name: str, target_date: date) -> Dict[str, Any]:
    """Calculate all metrics for a single property"""
    rooms_available = PROPERTY_INVENTORY.get(property_name, 0)
    
    daily_bookings = [
        b for b in bookings 
        if date.fromisoformat(b["check_in"]) <= target_date < date.fromisoformat(b["check_out"])
    ]
    
    if not daily_bookings:
        return {
            "rooms_available": rooms_available,
            "rooms_sold": 0,
            "occupancy": 0.0,
            "gst": 0.0,
            "commission": 0.0,
            "receivable": 0.0,
            "receivable_per_night": 0.0,
            "arr": 0.0
        }
    
    total_rooms_sold = 0
    total_gst = 0.0
    total_commission = 0.0
    total_receivable = 0.0
    total_per_night = 0.0
    
    for booking in daily_bookings:
        check_in = date.fromisoformat(booking["check_in"])
        is_check_in_day = (target_date == check_in)
        
        room_no = str(booking.get("room_no", "")).strip()
        if room_no:
            num_rooms = len([r for r in room_no.split(",") if r.strip()])
            total_rooms_sold += num_rooms
        else:
            total_rooms_sold += 1
        
        days = max(booking.get("days", 1), 1)
        receivable = booking.get("receivable", 0.0)
        per_night = receivable / days if days > 0 else 0.0
        total_per_night += per_night
        
        if is_check_in_day:
            total_gst += booking.get("gst", 0.0)
            total_commission += booking.get("commission", 0.0)
            total_receivable += receivable
    
    occupancy = (total_rooms_sold / rooms_available * 100) if rooms_available > 0 else 0.0
    arr = total_per_night / total_rooms_sold if total_rooms_sold > 0 else 0.0
    
    return {
        "rooms_available": rooms_available,
        "rooms_sold": total_rooms_sold,
        "occupancy": occupancy,
        "gst": total_gst,
        "commission": total_commission,
        "receivable": total_receivable,
        "receivable_per_night": total_per_night,
        "arr": arr
    }

def aggregate_totals(property_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate DTD and MTD totals"""
    dtd_totals = {
        "rooms_available": 0,
        "rooms_sold": 0,
        "gst": 0.0,
        "commission": 0.0,
        "receivable": 0.0,
        "receivable_per_night": 0.0
    }
    
    for prop_metrics in property_data.values():
        dtd_totals["rooms_available"] += prop_metrics["rooms_available"]
        dtd_totals["rooms_sold"] += prop_metrics["rooms_sold"]
        dtd_totals["gst"] += prop_metrics["gst"]
        dtd_totals["commission"] += prop_metrics["commission"]
        dtd_totals["receivable"] += prop_metrics["receivable"]
        dtd_totals["receivable_per_night"] += prop_metrics["receivable_per_night"]
    
    dtd_totals["occupancy"] = (
        dtd_totals["rooms_sold"] / dtd_totals["rooms_available"] * 100
        if dtd_totals["rooms_available"] > 0 else 0.0
    )
    dtd_totals["arr"] = (
        dtd_totals["receivable_per_night"] / dtd_totals["rooms_sold"]
        if dtd_totals["rooms_sold"] > 0 else 0.0
    )
    
    mtd_totals = dtd_totals.copy()
    
    return {"dtd": dtd_totals, "mtd": mtd_totals}

# ============================================================================
# DATAFRAME BUILDER
# ============================================================================

def build_report_dataframe(property_data: Dict[str, Dict[str, Any]], totals: Dict[str, Any]) -> pd.DataFrame:
    """Build the final report dataframe"""
    sorted_props = sorted(property_data.keys(), key=lambda x: PROPERTY_SHORT_NAMES.get(x, x))
    
    rows = {
        "Rooms Available": {},
        "Rooms Sold": {},
        "Occ %": {},
        "GST": {},
        "Commission": {},
        "Receivable": {},
        "Receivable Per Night": {},
        "ARR": {}
    }
    
    for prop in sorted_props:
        short_name = PROPERTY_SHORT_NAMES.get(prop, prop)
        metrics = property_data[prop]
        
        rows["Rooms Available"][short_name] = metrics["rooms_available"]
        rows["Rooms Sold"][short_name] = metrics["rooms_sold"]
        rows["Occ %"][short_name] = f"{metrics['occupancy']:.0f}%"
        rows["GST"][short_name] = int(metrics["gst"])
        rows["Commission"][short_name] = int(metrics["commission"])
        rows["Receivable"][short_name] = int(metrics["receivable"])
        rows["Receivable Per Night"][short_name] = int(metrics["receivable_per_night"])
        rows["ARR"][short_name] = int(metrics["arr"])
    
    dtd = totals["dtd"]
    mtd = totals["mtd"]
    
    for key in rows:
        if key == "Rooms Available":
            rows[key]["D.T.D"] = dtd["rooms_available"]
            rows[key]["M.T.D"] = mtd["rooms_available"]
        elif key == "Rooms Sold":
            rows[key]["D.T.D"] = dtd["rooms_sold"]
            rows[key]["M.T.D"] = mtd["rooms_sold"]
        elif key == "Occ %":
            rows[key]["D.T.D"] = f"{dtd['occupancy']:.0f}%"
            rows[key]["M.T.D"] = f"{mtd['occupancy']:.0f}%"
        elif key == "GST":
            rows[key]["D.T.D"] = int(dtd["gst"])
            rows[key]["M.T.D"] = int(mtd["gst"])
        elif key == "Commission":
            rows[key]["D.T.D"] = int(dtd["commission"])
            rows[key]["M.T.D"] = int(mtd["commission"])
        elif key == "Receivable":
            rows[key]["D.T.D"] = int(dtd["receivable"])
            rows[key]["M.T.D"] = int(mtd["receivable"])
        elif key == "Receivable Per Night":
            rows[key]["D.T.D"] = int(dtd["receivable_per_night"])
            rows[key]["M.T.D"] = int(mtd["receivable_per_night"])
        elif key == "ARR":
            rows[key]["D.T.D"] = int(dtd["arr"])
            rows[key]["M.T.D"] = int(mtd["arr"])
    
    df = pd.DataFrame(rows).T
    df.index.name = ""
    
    return df

# ============================================================================
# EXCEL EXPORT
# ============================================================================

def export_to_excel(df: pd.DataFrame, report_date: date) -> bytes:
    """Export dataframe to Excel and return as bytes"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Daily Report"
    
    header_fill = PatternFill(start_color="00B8A9", end_color="00B8A9", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    title_font = Font(bold=True, size=14, color="FFFFFF")
    date_font = Font(bold=True, size=11, color="FFFFFF")
    date_fill = PatternFill(start_color="00B8A9", end_color="00B8A9", fill_type="solid")
    
    center_align = Alignment(horizontal="center", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")
    
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    ws.merge_cells('A1:Z1')
    title_cell = ws['A1']
    title_cell.value = "TIE Hotels & Resorts"
    title_cell.font = title_font
    title_cell.alignment = center_align
    title_cell.fill = header_fill
    
    ws.merge_cells('A2:Z2')
    report_cell = ws['A2']
    report_cell.value = "Overall Report for the day"
    report_cell.alignment = center_align
    
    date_col = len(df.columns) + 2
    date_cell = ws.cell(row=1, column=date_col)
    date_cell.value = report_date.strftime("%d-%b-%y")
    date_cell.font = date_font
    date_cell.fill = date_fill
    date_cell.alignment = center_align
    
    start_row = 4
    
    ws.cell(row=start_row, column=1, value="")
    for col_idx, col_name in enumerate(df.columns, start=2):
        cell = ws.cell(row=start_row, column=col_idx, value=col_name)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    
    for row_idx, (idx, row) in enumerate(df.iterrows(), start=start_row + 1):
        label_cell = ws.cell(row=row_idx, column=1, value=idx)
        label_cell.font = Font(bold=True)
        label_cell.border = thin_border
        
        for col_idx, value in enumerate(row, start=2):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = thin_border
            
            if idx == "Occ %":
                cell.alignment = center_align
            elif isinstance(value, (int, float)):
                cell.alignment = right_align
                if value > 0:
                    cell.number_format = '#,##0'
            else:
                cell.alignment = center_align
    
    ws.column_dimensions['A'].width = 22
    for col in df.columns:
        col_letter = ws.cell(row=start_row, column=list(df.columns).index(col) + 2).column_letter
        ws.column_dimensions[col_letter].width = 12
    
    total_fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
    dtd_col = list(df.columns).index("D.T.D") + 2 if "D.T.D" in df.columns else None
    mtd_col = list(df.columns).index("M.T.D") + 2 if "M.T.D" in df.columns else None
    
    for row_idx in range(start_row + 1, start_row + len(df) + 1):
        if dtd_col:
            ws.cell(row=row_idx, column=dtd_col).fill = total_fill
        if mtd_col:
            ws.cell(row=row_idx, column=mtd_col).fill = total_fill
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()

# ============================================================================
# STREAMLIT UI
# ============================================================================

def show_nrd_report():
    """Display the Night Report Dashboard in Streamlit"""
    st.header("📊 Night Report Dashboard (NRD)")
    st.markdown("Generate overall daily report for all TIE Hotels & Resorts properties")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        target_date = st.date_input(
            "Select Report Date",
            value=date.today(),
            max_value=date.today(),
            help="Select the date for which to generate the report"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        generate_btn = st.button("🔄 Generate Report", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    if generate_btn:
        with st.spinner(f"Fetching data for {target_date.strftime('%d-%b-%Y')}..."):
            try:
                supabase = st.session_state.get('supabase_client')
                
                if supabase is None:
                    from supabase import create_client
                    supabase_url = os.getenv("SUPABASE_URL", "https://oxbrezracnmazucnnqox.supabase.co")
                    supabase_key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94YnJlenJhY25tYXp1Y25ucW94Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM3NjUxMTgsImV4cCI6MjA2OTM0MTExOH0.nqBK2ZxntesLY9qYClpoFPVnXOW10KrzF-UI_DKjbKo")
                    supabase = create_client(supabase_url, supabase_key)
                
                all_bookings = fetch_all_properties_data(supabase, target_date)
                
                property_data = {}
                progress_bar = st.progress(0)
                total_props = len(PROPERTY_SHORT_NAMES)
                
                for idx, (property_name, bookings) in enumerate(all_bookings.items()):
                    metrics = calculate_property_metrics(bookings, property_name, target_date)
                    property_data[property_name] = metrics
                    progress_bar.progress((idx + 1) / total_props)
                
                progress_bar.empty()
                
                totals = aggregate_totals(property_data)
                df = build_report_dataframe(property_data, totals)
                
                dtd = totals["dtd"]
                
                st.success(f"✅ Report generated successfully for {target_date.strftime('%d-%b-%Y')}")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Total Rooms Sold",
                        f"{dtd['rooms_sold']}/{dtd['rooms_available']}",
                        f"{dtd['occupancy']:.1f}% Occupancy"
                    )
                
                with col2:
                    st.metric("Total Revenue", f"₹{dtd['receivable']:,.0f}")
                
                with col3:
                    st.metric("Average ARR", f"₹{dtd['arr']:,.0f}")
                
                with col4:
                    st.metric("Total GST", f"₹{dtd['gst']:,.0f}")
                
                st.markdown("---")
                st.subheader("📋 Overall Report")
                
                def highlight_totals(s):
                    if s.name in ['D.T.D', 'M.T.D']:
                        return ['background-color: #E8F5E9'] * len(s)
                    return [''] * len(s)
                
                styled_df = df.style.apply(highlight_totals, axis=0)
                st.dataframe(styled_df, use_container_width=True, height=400)
                
                excel_data = export_to_excel(df, target_date)
                filename = f"TIE_Daily_Report_{target_date.strftime('%Y-%m-%d')}.xlsx"
                
                st.download_button(
                    label="📥 Download Excel Report",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"❌ Error generating report: {str(e)}")
                logging.error(f"NRD Report Error: {e}", exc_info=True)
    
    else:
        st.info("👆 Select a date and click 'Generate Report' to view the overall daily report")
        
        with st.expander("📍 Properties Included in Report"):
            cols = st.columns(3)
            properties = list(PROPERTY_SHORT_NAMES.keys())
            
            for idx, prop in enumerate(properties):
                short_name = PROPERTY_SHORT_NAMES[prop]
                cols[idx % 3].write(f"✓ **{short_name}**: {prop}")
