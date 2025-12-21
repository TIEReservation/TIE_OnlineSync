import streamlit as st
from datetime import date, timedelta
import pandas as pd
from typing import Dict, List, Any, Optional
import logging
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
import os
import io
import calendar

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ============================================================================
# CONFIGURATION (matching inventory.py)
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

# Full inventory from inventory.py
PROPERTY_INVENTORY = {
    "Le Poshe Beach view": {"all": ["101","102","201","202","203","204","301","302","303","304","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204"]},
    "La Millionaire Resort": {"all": ["101","102","103","105","201","202","203","204","205","206","207","208","301","302","303","304","305","306","307","308","401","402","Day Use 1","Day Use 2","Day Use 3","Day Use 4","Day Use 5","No Show"],"three_bedroom":["203","204","205"]},
    "Le Poshe Luxury": {"all": ["101","102","201","202","203","204","205","301","302","303","304","305","401","402","403","404","405","501","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204","205"]},
    "Le Poshe Suite": {"all": ["601","602","603","604","701","702","703","704","801","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "La Paradise Residency": {"all": ["101","102","103","201","202","203","301","302","303","304","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203"]},
    "La Paradise Luxury": {"all": ["101","102","103","201","202","203","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203"]},
    "La Villa Heritage": {"all": ["101","102","103","201","202","203","301","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203"]},
    "Le Pondy Beachside": {"all": ["101","102","201","202","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "Le Royce Villa": {"all": ["101","102","201","202","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "La Tamara Luxury": {"all": ["101","102","103","104","105","106","201","202","203","204","205","206","301","302","303","304","305","306","401","402","403","404","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204","205","206"]},
    "La Antilia Luxury": {"all": ["101","201","202","203","204","301","302","303","304","401","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204"]},
    "La Tamara Suite": {"all": ["101","102","103","104","201","202","203","204","205","206","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203","204","205","206"]},
    "Le Park Resort": {"all": ["111","222","333","444","555","666","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "Villa Shakti": {"all": ["101","102","201","201A","202","203","301","301A","302","303","401","Day Use 1","Day Use 2","No Show"],"three_bedroom":["203"]},
    "Eden Beach Resort": {"all": ["101","102","103","201","202","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "Le Terra": {"all": ["101","102","103","104","105","106","107","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "La Coromandel Luxury": {"all": ["101","102","103","201","202","203","204","205","206","301","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]},
    "Happymates Forest Retreat": {"all": ["101","102","Day Use 1","Day Use 2","No Show"],"three_bedroom":[]}  
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

reverse_mapping = {c: [] for c in set(property_mapping.values())}
for v, c in property_mapping.items():
    reverse_mapping[c].append(v)

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

# ============================================================================
# HELPER FUNCTIONS (from inventory.py)
# ============================================================================

def normalize_property(name: str) -> str:
    return property_mapping.get(name.strip(), name.strip())

def sanitize_string(v: Any, default: str = "") -> str:
    return str(v).strip() if v is not None else default

def safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(float(v)) if v not in [None, "", " "] else default
    except:
        return default

def safe_float(v: Any, default: float = 0) -> float:
    try:
        return float(v) if v not in [None, "", " "] else default
    except:
        return default

# ============================================================================
# DATA NORMALIZATION (from inventory.py)
# ============================================================================

def normalize_booking(row: Dict, is_online: bool) -> Optional[Dict]:
    """Normalize booking data - EXACT copy from inventory.py"""
    try:
        bid = sanitize_string(row.get("booking_id") or row.get("id"))
        status_field = "booking_status" if is_online else "plan_status"
        status = sanitize_string(row.get(status_field, "")).title()
        if status not in ["Confirmed", "Completed"]: return None
        pay = sanitize_string(row.get("payment_status")).title()
        if pay not in ["Fully Paid", "Partially Paid"]: return None
        ci = date.fromisoformat(row["check_in"])
        co = date.fromisoformat(row["check_out"])
        if co <= ci: return None
        days_field = "room_nights" if is_online else "no_of_days"
        days = safe_int(row.get(days_field)) or (co - ci).days
        if days <= 0: days = 1
        p = normalize_property(row.get("property_name") if not is_online else row.get("property"))

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
        if receivable < 0: receivable = 0.0

        identifier = row.get("id") if is_online else row.get("booking_id")
        identifier_str = str(identifier) if identifier is not None else ""

        return {
            "type": "online" if is_online else "direct",
            "property": p,
            "booking_id": bid,
            "guest_name": sanitize_string(row.get("guest_name")),
            "mobile_no": sanitize_string(row.get("guest_phone") if is_online else row.get("mobile_no")),
            "total_pax": safe_int(row.get("total_pax")),
            "check_in": str(ci),
            "check_out": str(co),
            "days": days,
            "room_no": sanitize_string(row.get("room_no")).title(),
            "mob": sanitize_string(row.get("mode_of_booking") if is_online else row.get("mob")),
            "plan": sanitize_string(row.get("rate_plans") if is_online else row.get("breakfast")),
            "room_charges": room_charges,
            "gst": gst,
            "tax": tax,
            "total_amount": total_amount,
            "commission": commission,
            "receivable": receivable,
            "advance": safe_float(row.get("total_payment_made") if is_online else row.get("advance_amount")),
            "advance_mop": sanitize_string(row.get("advance_mop")),
            "balance": safe_float(row.get("balance_due") if is_online else row.get("balance_amount")),
            "balance_mop": sanitize_string(row.get("balance_mop")),
            "booking_status": status,
            "payment_status": pay,
            "submitted_by": sanitize_string(row.get("submitted_by")),
            "modified_by": sanitize_string(row.get("modified_by")),
            "remarks": sanitize_string(row.get("remarks")),
            "db_id": identifier_str,
        }
    except Exception as e:
        logging.warning(f"normalize failed: {e}")
        return None

# ============================================================================
# DATA FETCHING (from inventory.py)
# ============================================================================

def load_combined_bookings(supabase, property: str, start_date: date, end_date: date) -> List[Dict]:
    """EXACT copy from inventory.py"""
    prop = normalize_property(property)
    query_props = [prop] + reverse_mapping.get(prop, [])
    combined: List[Dict] = []

    try:
        q = supabase.table("reservations").select("*").in_("property_name", query_props).lte("check_in", str(end_date)).gte("check_out", str(start_date)).in_("plan_status", ["Confirmed", "Completed"]).in_("payment_status", ["Partially Paid", "Fully Paid"]).execute()
        for r in q.data or []:
            norm = normalize_booking(r, is_online=False)
            if norm: combined.append(norm)
    except Exception as e:
        logging.error(f"Direct query error: {e}")

    try:
        q = supabase.table("online_reservations").select("*").in_("property", query_props).lte("check_in", str(end_date)).gte("check_out", str(start_date)).in_("booking_status", ["Confirmed", "Completed"]).in_("payment_status", ["Partially Paid", "Fully Paid"]).execute()
        for r in q.data or []:
            norm = normalize_booking(r, is_online=True)
            if norm: combined.append(norm)
    except Exception as e:
        logging.error(f"Online query error: {e}")

    return combined

# ============================================================================
# FILTERING & ASSIGNMENT (from inventory.py)
# ============================================================================

def filter_bookings_for_day(bookings: List[Dict], day: date) -> List[Dict]:
    """EXACT copy from inventory.py"""
    return [b.copy() for b in bookings if date.fromisoformat(b["check_in"]) <= day < date.fromisoformat(b["check_out"])]

def assign_inventory_numbers(daily_bookings: List[Dict], property: str):
    """EXACT copy from inventory.py"""
    assigned, over = [], []
    inv = PROPERTY_INVENTORY.get(property, {"all": []})["all"]
    inv_lookup = {i.strip().lower(): i for i in inv}
    
    room_bookings = {}
    sorted_bookings = sorted(daily_bookings, key=lambda x: (x.get("check_in", ""), x.get("booking_id", "")))

    for b in sorted_bookings:
        raw_room = str(b.get("room_no", "") or "").strip()
        booking_id = b.get("booking_id", "Unknown")
        
        if not raw_room:
            over.append(b)
            continue

        requested = [r.strip() for r in raw_room.split(",") if r.strip()]
        assigned_rooms = []
        is_overbooking = False

        for r in requested:
            key = r.lower()
            if key not in inv_lookup:
                is_overbooking = True
                break
            room_name = inv_lookup[key]
            
            if room_name in room_bookings and room_bookings[room_name] != booking_id:
                is_overbooking = True
                break
            assigned_rooms.append(room_name)

        if is_overbooking or not assigned_rooms:
            over.append(b)
            continue

        for room in assigned_rooms:
            room_bookings[room] = booking_id

        days = max(b.get("days", 1), 1)
        receivable = b.get("receivable", 0.0)
        num_rooms = len(assigned_rooms)
        total_nights = days * num_rooms
        per_night = receivable / total_nights if total_nights > 0 else 0.0
        base_pax = b["total_pax"] // num_rooms if num_rooms else 0
        rem = b["total_pax"] % num_rooms if num_rooms else 0

        for idx, room in enumerate(assigned_rooms):
            nb = b.copy()
            nb["assigned_room"] = room
            nb["room_no"] = room
            nb["total_pax"] = base_pax + (1 if idx < rem else 0)
            nb["per_night"] = per_night
            nb["is_primary"] = (idx == 0)
            assigned.append(nb)

    return assigned, over

# ============================================================================
# STATISTICS EXTRACTION (from inventory.py)
# ============================================================================

def extract_stats_from_assigned(assigned: List[Dict], target_date: date, mob_types: List[str]) -> Dict:
    """Extract stats matching inventory.py logic"""
    
    def to_float(val):
        try:
            return float(val) if val not in [None, "", " "] else 0.0
        except:
            return 0.0
    
    def to_int(val):
        try:
            return int(val) if val not in [None, "", " "] else 0
        except:
            return 0
    
    dtd = {m: {"rooms":0,"value":0.0,"comm":0.0,"gst":0.0,"tax":0.0,"pax":0} for m in mob_types}
    dtd_rooms = 0
    dtd_value = 0.0
    dtd_comm = 0.0
    dtd_gst = 0.0
    dtd_tax = 0.0
    dtd_pax = 0

    for booking in assigned:
        check_in_date = date.fromisoformat(booking["check_in"])
        is_check_in_day = (target_date == check_in_date)
        is_primary = booking.get("is_primary", False)
        
        # Count rooms
        dtd_rooms += 1
        
        # Per night value
        per_night = to_float(booking.get("per_night", 0))
        dtd_value += per_night
        
        # Only count full amounts on check-in day for primary booking
        if is_check_in_day and is_primary:
            dtd_comm += to_float(booking.get("commission", 0))
            dtd_gst += to_float(booking.get("gst", 0))
            dtd_tax += to_float(booking.get("tax", 0))
        
        # Pax
        dtd_pax += to_int(booking.get("total_pax", 0))
        
        # MOB breakdown
        mob_raw = sanitize_string(booking.get("mob", ""))
        mob = next((m for m, vs in mob_mapping.items() if mob_raw.upper() in [v.upper() for v in vs]), "Booking")
        
        dtd[mob]["rooms"] += 1
        dtd[mob]["value"] += per_night
        dtd[mob]["pax"] += to_int(booking.get("total_pax", 0))
        
        if is_check_in_day and is_primary:
            dtd[mob]["comm"] += to_float(booking.get("commission", 0))
            dtd[mob]["gst"] += to_float(booking.get("gst", 0))
            dtd[mob]["tax"] += to_float(booking.get("tax", 0))
    
    # Calculate ARR for each MOB
    for m in mob_types:
        r = dtd[m]["rooms"]
        dtd[m]["arr"] = dtd[m]["value"] / r if r > 0 else 0.0

    dtd["Total"] = {
        "rooms": dtd_rooms,
        "value": dtd_value,
        "arr": dtd_value / dtd_rooms if dtd_rooms > 0 else 0.0,
        "comm": dtd_comm,
        "gst": dtd_gst,
        "tax": dtd_tax,
        "pax": dtd_pax
    }

    return dtd

# ============================================================================
# PROPERTY METRICS CALCULATION
# ============================================================================

def calculate_property_metrics_for_day(supabase, property_name: str, target_date: date, mob_types: List[str]) -> Dict[str, Any]:
    """Calculate metrics for a property on a specific day using inventory.py logic"""
    
    # Get total inventory (excluding Day Use and No Show)
    inv_data = PROPERTY_INVENTORY.get(property_name, {"all": []})
    all_rooms = inv_data["all"]
    total_inventory = len([i for i in all_rooms if not i.startswith(("Day Use", "No Show"))])
    
    # Load bookings
    start_date = target_date
    end_date = target_date + timedelta(days=1)
    bookings = load_combined_bookings(supabase, property_name, start_date, end_date)
    
    # Filter for target day
    daily = filter_bookings_for_day(bookings, target_date)
    
    if not daily:
        return {
            "rooms_available": total_inventory,
            "rooms_sold": 0,
            "occupancy": 0.0,
            "gst": 0.0,
            "commission": 0.0,
            "receivable": 0.0,
            "receivable_per_night": 0.0,
            "arr": 0.0
        }
    
    # Assign inventory
    assigned, over = assign_inventory_numbers(daily, property_name)
    
    # Extract stats
    stats = extract_stats_from_assigned(assigned, target_date, mob_types)
    total_stats = stats["Total"]
    
    rooms_sold = total_stats["rooms"]
    occupancy = (rooms_sold / total_inventory * 100) if total_inventory > 0 else 0.0
    
    return {
        "rooms_available": total_inventory,
        "rooms_sold": rooms_sold,
        "occupancy": occupancy,
        "gst": total_stats["gst"],
        "commission": total_stats["comm"],
        "receivable": total_stats["value"],  # This is the per-night total
        "receivable_per_night": total_stats["value"],
        "arr": total_stats["arr"]
    }

# ============================================================================
# AGGREGATION
# ============================================================================

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
    st.markdown("View overall daily reports for all TIE Hotels & Resorts properties for the entire month")
    
    # Month and Year selectors
    today = date.today()
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        year = st.selectbox("Year", list(range(today.year-5, today.year+6)), index=5, key="nrd_year")
    
    with col2:
        month = st.selectbox("Month", list(range(1, 13)), index=today.month-1, 
                            format_func=lambda x: calendar.month_name[x], key="nrd_month")
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown("---")
    
    # Generate dates for the month
    num_days = calendar.monthrange(year, month)[1]
    month_dates = [date(year, month, d) for d in range(1, num_days + 1)]
    
    # Only show dates up to today
    month_dates = [d for d in month_dates if d <= today]
    
    if not month_dates:
        st.warning(f"No data available for {calendar.month_name[month]} {year}")
        return
    
    with st.spinner(f"Loading data for {calendar.month_name[month]} {year}..."):
        try:
            supabase = st.session_state.get('supabase_client')
            
            if supabase is None:
                from supabase import create_client
                supabase_url = os.getenv("SUPABASE_URL", "https://oxbrezracnmazucnnqox.supabase.co")
                supabase_key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94YnJlenJhY25tYXp1Y25ucW94Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM3NjUxMTgsImV4cCI6MjA2OTM0MTExOH0.nqBK2ZxntesLY9qYClpoFPVnXOW10KrzF-UI_DKjbKo")
                supabase = create_client(supabase_url, supabase_key)
            
            mob_types = list(mob_mapping.keys())
            
            # Collect all data for the month
            all_month_data = []
            mtd_totals_running = {
                "rooms_available": 0,
                "rooms_sold": 0,
                "gst": 0.0,
                "commission": 0.0,
                "receivable": 0.0,
                "receivable_per_night": 0.0
            }
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for day_idx, target_date in enumerate(month_dates):
                status_text.text(f"Processing {target_date.strftime('%d %b %Y')}...")
                
                property_data = {}
                
                for property_name in PROPERTY_SHORT_NAMES.keys():
                    metrics = calculate_property_metrics_for_day(
                        supabase, 
                        property_name, 
                        target_date,
                        mob_types
                    )
                    property_data[property_name] = metrics
                
                totals = aggregate_totals(property_data)
                df = build_report_dataframe(property_data, totals)
                
                dtd = totals["dtd"]
                
                # Update MTD running totals
                mtd_totals_running["rooms_available"] += dtd["rooms_available"]
                mtd_totals_running["rooms_sold"] += dtd["rooms_sold"]
                mtd_totals_running["gst"] += dtd["gst"]
                mtd_totals_running["commission"] += dtd["commission"]
                mtd_totals_running["receivable"] += dtd["receivable"]
                mtd_totals_running["receivable_per_night"] += dtd["receivable_per_night"]
                
                # Calculate MTD occupancy and ARR
                days_so_far = day_idx + 1
                total_room_days = mtd_totals_running["rooms_available"]
                mtd_occ = (mtd_totals_running["rooms_sold"] / total_room_days * 100) if total_room_days > 0 else 0.0
                mtd_arr = (mtd_totals_running["receivable_per_night"] / mtd_totals_running["rooms_sold"]) if mtd_totals_running["rooms_sold"] > 0 else 0.0
                
                all_month_data.append({
                    "date": target_date,
                    "date_str": target_date.strftime("%d-%b-%Y"),
                    "df": df,
                    "dtd": dtd,
                    "mtd_occ": mtd_occ,
                    "mtd_arr": mtd_arr,
                    "mtd_revenue": mtd_totals_running["receivable_per_night"],
                    "mtd_rooms_sold": mtd_totals_running["rooms_sold"]
                })
                
                progress_bar.progress((day_idx + 1) / len(month_dates))
            
            progress_bar.empty()
            status_text.empty()
            
            st.success(f"✅ Loaded {len(month_dates)} days for {calendar.month_name[month]} {year}")
            
            # Month Summary at the top
            st.subheader(f"📊 Month Summary - {calendar.month_name[month]} {year}")
            
            final_mtd = all_month_data[-1] if all_month_data else None
            
            if final_mtd:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "MTD Rooms Sold",
                        f"{mtd_totals_running['rooms_sold']:,}",
                        f"{final_mtd['mtd_occ']:.1f}% Avg Occ"
                    )
                
                with col2:
                    st.metric("MTD Revenue", f"₹{final_mtd['mtd_revenue']:,.0f}")
                
                with col3:
                    st.metric("MTD Average ARR", f"₹{final_mtd['mtd_arr']:,.0f}")
                
                with col4:
                    st.metric("MTD GST", f"₹{mtd_totals_running['gst']:,.0f}")
            
            st.markdown("---")
            
            # Display each day's report
            for day_data in all_month_data:
                with st.expander(f"📅 {day_data['date_str']} - {day_data['dtd']['rooms_sold']} rooms sold", expanded=False):
                    
                    # Daily metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Rooms Sold",
                            f"{day_data['dtd']['rooms_sold']}/{day_data['dtd']['rooms_available']}",
                            f"{day_data['dtd']['occupancy']:.1f}% Occ"
                        )
                    
                    with col2:
                        st.metric("Revenue", f"₹{day_data['dtd']['receivable']:,.0f}")
                    
                    with col3:
                        st.metric("ARR", f"₹{day_data['dtd']['arr']:,.0f}")
                    
                    with col4:
                        st.metric("GST", f"₹{day_data['dtd']['gst']:,.0f}")
                    
                    st.markdown("**Daily Report:**")
                    
                    def highlight_totals(s):
                        if s.name in ['D.T.D', 'M.T.D']:
                            return ['background-color: #E8F5E9'] * len(s)
                        return [''] * len(s)
                    
                    styled_df = day_data['df'].style.apply(highlight_totals, axis=0)
                    st.dataframe(styled_df, use_container_width=True, height=350)
                    
                    # Download button for this day
                    excel_data = export_to_excel(day_data['df'], day_data['date'])
                    filename = f"TIE_Daily_Report_{day_data['date'].strftime('%Y-%m-%d')}.xlsx"
                    
                    st.download_button(
                        label=f"📥 Download {day_data['date_str']} Excel",
                        data=excel_data,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"download_{day_data['date'].strftime('%Y%m%d')}"
                    )
            
        except Exception as e:
            st.error(f"❌ Error generating reports: {str(e)}")
            logging.error(f"NRD Report Error: {e}", exc_info=True)
