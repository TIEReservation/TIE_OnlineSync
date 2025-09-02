import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from supabase import create_client, Client
from utils import safe_int, safe_float
import plotly.express as px
import plotly.graph_objects as go

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

def get_inventory_mapping():
    """Get the inventory mapping rules for all properties."""
    return {
        "Le Poshe Beachview": {
            "room_mapping": {
                "101": ["101"],
                "102": ["102"],
                "201": ["201"],
                "202": ["202"],
                "203": ["203"],
                "204": ["204"],
                "301": ["301"],
                "302": ["302"],
                "303": ["303"],
                "304": ["304"]
            },
            "day_use": ["Day Use 1", "Day Use 2"],
            "no_show": "No Show"
        },
        "La Millionare Resort": {
            "room_mapping": {
                "101": ["101"],
                "102": ["102"],
                "103": ["103"],
                "105": ["105"],
                "201": ["201"],
                "202": ["202"],
                "203": ["203"],
                "204": ["204"],
                "205": ["205"],
                "206": ["206"],
                "207": ["207"],
                "208": ["208"],
                "301": ["301"],
                "302": ["302"],
                "303": ["303"],
                "304": ["304"],
                "305": ["305"],
                "306": ["306"],
                "307": ["307"],
                "308": ["308"],
                "401": ["401"],
                "402": ["402"]
            },
            "day_use": ["day use1", "day use2", "day use3", "day use4"],
            "no_show": "No-Show"
        },
        "Le Poshe Luxury": {
            "room_mapping": {
                "101": ["101&102", "101"],
                "102": ["101&102", "102"],
                "201": ["201&202", "201"],
                "202": ["201&202", "202"],
                "203": ["203to205", "203"],
                "204": ["203to205", "204"],
                "205": ["203to205", "205"],
                "301": ["301&302", "301"],
                "302": ["301&302", "302"],
                "303": ["303to305", "303"],
                "304": ["303to305", "304"],
                "305": ["303to305", "305"],
                "401": ["401&402", "401"],
                "402": ["401&402", "402"],
                "403": ["403to405", "403"],
                "404": ["403to405", "404"],
                "405": ["403to405", "405"],
                "501": ["501"]
            },
            "special_mapping": {
                "D1": "203", "D2": "204", "D3": "205", "D4": "303", "D5": "304"
            },
            "day_use": ["Day Use 1", "Day Use 2"],
            "no_show": "No Show"
        },
        "Le Poshe Suite": {
            "room_mapping": {
                "601": ["601&602", "601"],
                "602": ["601&602", "602"],
                "603": ["603&604", "603"],
                "604": ["603&604", "604"],
                "701": ["701&702", "701"],
                "702": ["701&702", "702"],
                "703": ["703&704", "703"],
                "704": ["703&704", "704"],
                "801": ["801"]
            },
            "day_use": ["Day Use 1", "Day Use 2"],
            "no_show": "No Show"
        },
        "La Paradise Residency": {
            "room_mapping": {
                "101": ["101"],
                "102": ["102"],
                "103": ["103"],
                "201": ["201"],
                "202": ["202"],
                "203": ["203"],
                "301": ["301"],
                "302": ["302"],
                "303": ["303"],
                "304": ["304"]
            },
            "day_use": ["Day Use 1", "Day Use 2"],
            "no_show": "No Show"
        },
        "La Paradise Luxury": {
            "room_mapping": {
                "101": ["sp", "101", "102", "1001", "101to103"],
                "102": ["sp", "101", "102", "1002", "101to103"],
                "103": ["sp", "101", "103", "1003", "101to103"],
                "201": ["sp", "201", "202", "2001", "201to203"],
                "202": ["sp", "201", "202", "2002", "201to203"],
                "203": ["sp", "201", "203", "2003", "201to203"]
            },
            "day_use": ["Day Use 1", "Day Use 2"],
            "no_show": "No Show"
        },
        "La Villa Heritage": {
            "room_mapping": {
                "101": ["EVA", "101", "201", "GF"],
                "102": ["EVA", "102", "201", "GF"],
                "103": ["EVA", "103", "GF"],
                "201": ["EVA", "201", "201to203&301", "202", "FF"],
                "202": ["EVA", "202", "201to203&301", "202A", "FF"],
                "203": ["EVA", "203", "201to203&301", "FF"],
                "301": ["EVA", "301", "201to203&301", "FF"]
            },
            "day_use": ["Day Use 1", "Day Use 2"],
            "no_show": "No Show"
        },
        "Le Pondy Beach Side": {
            "room_mapping": {
                "101": ["101", "102", "201", "202", "Singleroom", "TwoRooms", "ThreeRooms", "11"],
                "102": ["101", "102", "201", "202", "TwoRooms", "ThreeRooms", "11", "203"],
                "201": ["101", "102", "201", "202", "ThreeRooms", "203"],
                "202": ["101", "102", "201", "202", "203"]
            },
            "day_use": ["Day Use 1", "Day Use 2"],
            "no_show": "No Show"
        },
        "Le Royce Villa": {
            "room_mapping": {
                "101": ["101to102&201to202", "101", "201", "301"],
                "102": ["101to102&201to202", "102", "101", "201", "301"],
                "201": ["101to102&201to202", "201", "301"],
                "202": ["101to102&201to202", "202", "301"]
            },
            "day_use": ["Day Use 1", "Day Use 2"],
            "no_show": "No Show"
        },
        "La Tamara Luxury": {
            "room_mapping": {
                "101": ["101", "101to103", "B1"],
                "102": ["102", "101to103", "B1"],
                "103": ["103", "101to103", "B1"],
                "104": ["104", "104to106"],
                "105": ["105", "104to106"],
                "106": ["106", "104to106"],
                "201": ["201", "201to203", "B2"],
                "202": ["202", "201to203", "B2"],
                "203": ["203", "201to203", "B2"],
                "204": ["204", "204to206"],
                "205": ["205", "204to206"],
                "206": ["206", "204to206"],
                "301": ["301", "301to303", "B3"],
                "302": ["302", "301to303", "B3"],
                "303": ["303", "301to303", "B3"],
                "304": ["304", "304to306"],
                "305": ["305", "304to306"],
                "306": ["306", "304to306"],
                "401": ["401", "401to404", "F1"],
                "402": ["402", "401to404", "F1"],
                "403": ["403", "401to404", "F1"],
                "404": ["404", "401to404", "F1"]
            },
            "day_use": ["Day Use 1", "Day Use 2"],
            "no_show": "No Show"
        },
        "La Antilia": {
            "room_mapping": {
                "101": ["101"],
                "201": ["201"],
                "202": ["202"],
                "203": ["203"],
                "204": ["204"],
                "301": ["301"],
                "302": ["302"],
                "303": ["303"],
                "304": ["304"],
                "401": ["401"]
            },
            "day_use": ["Day Use 1", "Day Use 2"],
            "no_show": "No Show"
        },
        "La Tamara Suite": {
            "room_mapping": {
                "101": ["101&102", "101", "A1"],
                "102": ["101&102", "102", "A1"],
                "103": ["103&104", "103", "B1"],
                "104": ["103&104", "104", "B1"],
                "201": ["201"],
                "202": ["202"],
                "203": ["203"],
                "204": ["204"],
                "205": ["205"],
                "206": ["206"]
            },
            "day_use": ["Day Use 1", "Day Use 2"],
            "no_show": "No Show"
        },
        "Le Park Resort": {
            "room_mapping": {
                "111": ["111&222", "111"],
                "222": ["111&222", "222"],
                "333": ["333&444", "333"],
                "444": ["333&444", "444"],
                "555": ["555&666", "555"],
                "666": ["555&666", "666"]
            },
            "day_use": ["Day Use 1", "Day Use 2"],
            "no_show": "No-Show"
        },
        "Villa Shakti": {
            "room_mapping": {
                "101": ["101&102", "102"],
                "102": ["101&102", "102"],
                "201": ["201"],
                "201A": ["201"],
                "202": ["202&203", "202"],
                "203": ["202&203", "202"],
                "301": ["301"],
                "301A": ["301"],
                "302": ["302&303", "302"],
                "303": ["302&303", "302"],
                "401": ["401"]
            },
            "day_use": ["Day Use 1", "Day Use 2"],
            "no_show": "No Show"
        },
        "Eden Beach Resort": {
            "room_mapping": {
                "101": ["101"],
                "102": ["102"],
                "103": ["103"],
                "201": ["201"],
                "202": ["202"]
            },
            "day_use": ["Day Use 1", "Day Use 2"],
            "no_show": "No Show"
        }
    }

def assign_inventory_number(property_name, room_no, room_type, booking_status):
    """Assign inventory number based on property mapping rules."""
    inventory_map = get_inventory_mapping()
    property_map = inventory_map.get(property_name, {})
    
    # Handle No Show status
    if booking_status == "No Show":
        return property_map.get("no_show", "No Show")
    
    # Handle Other/UNASSIGNED room types
    if room_type in ["Other", "UNASSIGNED", "", None]:
        day_use_options = property_map.get("day_use", [])
        return day_use_options[0] if day_use_options else "Day Use 1"
    
    # Handle special mappings (like D1-D5 for Le Poshe Luxury)
    if property_name == "Le Poshe Luxury" and room_no in ["D1", "D2", "D3", "D4", "D5"]:
        special_map = property_map.get("special_mapping", {})
        return special_map.get(room_no, "203")  # Default to 203 if not found
    
    # Normal room mapping
    room_mapping = property_map.get("room_mapping", {})
    for inventory_no, room_list in room_mapping.items():
        if room_no in room_list:
            return inventory_no
    
    # If no mapping found, return "Overbooked"
    return "Overbooked"

def load_all_reservations():
    """Load both direct and online reservations."""
    try:
        # Load direct reservations
        direct_response = supabase.table("reservations").select("*").execute()
        direct_reservations = []
        
        for record in direct_response.data:
            reservation = {
                "source": "direct",
                "booking_id": record["booking_id"],
                "property_name": record["property_name"] or "",
                "room_no": record["room_no"] or "",
                "guest_name": record["guest_name"] or "",
                "mobile_no": record["mobile_no"] or "",
                "total_pax": safe_int(record["total_pax"]),
                "check_in": datetime.strptime(record["check_in"], "%Y-%m-%d").date() if record["check_in"] else None,
                "check_out": datetime.strptime(record["check_out"], "%Y-%m-%d").date() if record["check_out"] else None,
                "no_of_days": safe_int(record["no_of_days"]),
                "total_tariff": safe_float(record["total_tariff"]),
                "advance_amount": safe_float(record["advance_amount"]),
                "balance_amount": safe_float(record["balance_amount"]),
                "booking_status": record["plan_status"] or "Pending",
                "payment_status": record.get("payment_status", "Not Paid"),
                "room_type": record["room_type"] or "",
                "remarks": record.get("remarks", ""),
                "inventory_no": record.get("inventory_no", "")
            }
            # Assign inventory if not already assigned
            if not reservation["inventory_no"]:
                reservation["inventory_no"] = assign_inventory_number(
                    reservation["property_name"],
                    reservation["room_no"],
                    reservation["room_type"],
                    reservation["booking_status"]
                )
            direct_reservations.append(reservation)
        
        # Load online reservations
        online_response = supabase.table("online_reservations").select("*").execute()
        online_reservations = []
        
        for record in online_response.data:
            reservation = {
                "source": "online",
                "booking_id": record["booking_id"],
                "property_name": record["property"] or "",
                "room_no": record["room_no"] or "",
                "guest_name": record["guest_name"] or "",
                "mobile_no": record["guest_phone"] or "",
                "total_pax": safe_int(record["total_pax"]),
                "check_in": datetime.strptime(record["check_in"], "%Y-%m-%d").date() if record["check_in"] else None,
                "check_out": datetime.strptime(record["check_out"], "%Y-%m-%d").date() if record["check_out"] else None,
                "no_of_days": (datetime.strptime(record["check_out"], "%Y-%m-%d").date() - datetime.strptime(record["check_in"], "%Y-%m-%d").date()).days if record["check_in"] and record["check_out"] else 0,
                "total_tariff": safe_float(record["booking_amount"]),
                "advance_amount": safe_float(record["total_payment_made"]),
                "balance_amount": safe_float(record["balance_due"]),
                "booking_status": record["booking_status"] or "Pending",
                "payment_status": record.get("payment_status", "Not Paid"),
                "room_type": record["room_type"] or "",
                "remarks": record.get("remarks", ""),
                "inventory_no": ""
            }
            # Assign inventory
            reservation["inventory_no"] = assign_inventory_number(
                reservation["property_name"],
                reservation["room_no"],
                reservation["room_type"],
                reservation["booking_status"]
            )
            online_reservations.append(reservation)
        
        return direct_reservations + online_reservations
    
    except Exception as e:
        st.error(f"Error loading reservations: {e}")
        return []

def update_inventory_assignment(booking_id, source, new_inventory_no):
    """Update inventory assignment for a booking."""
    try:
        table_name = "reservations" if source == "direct" else "online_reservations"
        
        if source == "direct":
            response = supabase.table(table_name).update({"inventory_no": new_inventory_no}).eq("booking_id", booking_id).execute()
        else:
            # For online reservations, we might need to add inventory_no column if it doesn't exist
            response = supabase.table(table_name).update({"inventory_no": new_inventory_no}).eq("booking_id", booking_id).execute()
        
        return bool(response.data)
    except Exception as e:
        st.error(f"Error updating inventory assignment: {e}")
        return False

def show_calendar_navigation():
    """Show year and month calendar navigation."""
    st.title("🏨 Daily Status Dashboard")
    st.markdown("---")
    
    current_year = datetime.now().year
    col1, col2 = st.columns([1, 3])
    
    with col1:
        selected_year = st.selectbox("Year", [current_year - 1, current_year, current_year + 1], index=1)
    
    with col2:
        st.write("### Select Month")
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        
        # Create a 4x3 grid for months
        month_cols = st.columns(4)
        selected_month = None
        
        for i, month in enumerate(months):
            col_index = i % 4
            with month_cols[col_index]:
                if st.button(f"📆 {month}", key=f"month_{i}", use_container_width=True):
                    selected_month = i + 1
                    st.session_state.selected_month = selected_month
                    st.session_state.selected_year = selected_year
    
    # If a month is selected, show daily status
    if hasattr(st.session_state, 'selected_month') and hasattr(st.session_state, 'selected_year'):
        show_monthly_daily_status(st.session_state.selected_year, st.session_state.selected_month)

def show_monthly_daily_status(year, month):
    """Show daily status for the selected month, listing properties and allowing selection for per-day details."""
    st.subheader(f"Daily Status for {calendar.month_name[month]} {year}")

    # Load reservations if not loaded
    if 'all_reservations' not in st.session_state:
        st.session_state.all_reservations = load_all_reservations()

    reservations = st.session_state.all_reservations

    # Get unique properties
    properties = sorted(set(res["property_name"] for res in reservations if res["property_name"]))

    # Select property
    selected_property = st.selectbox("Select Property", [""] + properties, key="property_select")

    if not selected_property:
        return

    # Get days in month
    _, num_days = calendar.monthrange(year, month)
    days = [f"{day:02d}-{calendar.month_abbr[month]}-{year}" for day in range(1, num_days + 1)]

    selected_day_str = st.selectbox("Select Day", days, key="day_select")
    selected_day = int(selected_day_str.split("-")[0])
    selected_date = date(year, month, selected_day)

    # Filter reservations occupying that date
    filtered = [
        res for res in reservations
        if res["property_name"] == selected_property
        and res["check_in"] and res["check_out"]
        and res["check_in"] <= selected_date < res["check_out"]
    ]

    if not filtered:
        st.info(f"No bookings for {selected_property} on {selected_date.strftime('%d-%b-%Y')}")
        return

    st.subheader(f"Booking Details for {selected_property} on {selected_date.strftime('%d-%b-%Y')}")

    # Display table header
    headers = ["Inventory No", "Room No", "Booking ID", "Guest Name", "Mobile No", "Total Pax", "Check-in", "Check-out", "Days", "Booking Status", "Payment Status", "Remarks"]
    header_cols = st.columns(len(headers))
    for col, header in zip(header_cols, headers):
        col.write(f"**{header}**")

    # Display rows
    for res in sorted(filtered, key=lambda x: str(x.get("inventory_no", ""))):
        row_cols = st.columns(len(headers))
        row_cols[0].write(res.get("inventory_no", ""))
        row_cols[1].write(res.get("room_no", ""))
        with row_cols[2]:
            unique_key = f"edit_{res['booking_id']}_{res['source']}_{selected_date}_{id(res)}"
            if st.button(str(res["booking_id"]), key=unique_key):
                st.session_state.edit_booking_id = res["booking_id"]
                st.session_state.edit_booking_source = res["source"]
                st.rerun()
        row_cols[3].write(res.get("guest_name", ""))
        row_cols[4].write(res.get("mobile_no", ""))
        row_cols[5].write(res.get("total_pax", ""))
        row_cols[6].write(res["check_in"].strftime("%d-%b-%Y") if res["check_in"] else "")
        row_cols[7].write(res["check_out"].strftime("%d-%b-%Y") if res["check_out"] else "")
        row_cols[8].write(res.get("no_of_days", ""))
        row_cols[9].write(res.get("booking_status", ""))
        row_cols[10].write(res.get("payment_status", ""))
        row_cols[11].write(res.get("remarks", ""))

def update_inventory_assignment(booking_id, source, new_inventory_no):
    """Update inventory assignment for a booking."""
    try:
        table_name = "reservations" if source == "direct" else "online_reservations"
        
        response = supabase.table(table_name).update({"inventory_no": new_inventory_no}).eq("booking_id", booking_id).execute()
        
        return bool(response.data)
    except Exception as e:
        st.error(f"Error updating inventory assignment: {e}")
        return False

def show_inventory_availability_matrix(selected_date):
    """Show inventory availability matrix for a specific date."""
    st.subheader(f"🗓️ Inventory Availability Matrix - {selected_date.strftime('%B %d, %Y')}")
    
    # Load reservations
    if 'all_reservations' not in st.session_state:
        st.session_state.all_reservations = load_all_reservations()
    
    reservations = st.session_state.all_reservations
    
    # Filter for selected date
    date_reservations = [
        res for res in reservations 
        if res["check_in"] and res["check_out"] and res["check_in"] <= selected_date < res["check_out"]
    ]
    
    inventory_map = get_inventory_mapping()
    
    # Create availability matrix
    for prop_name, prop_config in inventory_map.items():
        with st.expander(f"🏨 {prop_name} Availability", expanded=True):
            room_mapping = prop_config.get("room_mapping", {})
            
            # Get occupied inventories
            occupied = set()
            prop_reservations = [res for res in date_reservations if res["property_name"] == prop_name]
            
            for res in prop_reservations:
                if res["inventory_no"] != "Overbooked":
                    occupied.add(res["inventory_no"])
            
            # Create matrix display
            inventory_status = []
            for inventory_no in room_mapping.keys():
                status = "🔴 Occupied" if inventory_no in occupied else "🟢 Available"
                guest_info = ""
                
                if inventory_no in occupied:
                    booking = next((res for res in prop_reservations if res["inventory_no"] == inventory_no), None)
                    if booking:
                        guest_info = f"{booking['guest_name']} ({booking['booking_id']})"
                
                inventory_status.append({
                    "Inventory No": inventory_no,
                    "Status": status,
                    "Guest Info": guest_info
                })
            
            # Display as dataframe
            if inventory_status:
                availability_df = pd.DataFrame(inventory_status)
                st.dataframe(availability_df, use_container_width=True)
            
            # Summary
            total_inventory = len(room_mapping)
            occupied_count = len(occupied)
            available_count = total_inventory - occupied_count
            occupancy_rate = (occupied_count / total_inventory * 100) if total_inventory > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Inventory", total_inventory)
            with col2:
                st.metric("Occupied", occupied_count)
            with col3:
                st.metric("Occupancy Rate", f"{occupancy_rate:.1f}%")

def main():
    """Main function for inventory management."""
    st.set_page_config(
        page_title="Hotel Inventory Dashboard",
        page_icon="🏨",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Check if editing a booking
    if hasattr(st.session_state, 'edit_booking_id'):
        show_booking_edit_form(st.session_state.edit_booking_id, st.session_state.edit_booking_source)
        return
    
    # Main dashboard
    show_calendar_navigation()
    
    # Add availability matrix option
    if hasattr(st.session_state, 'selected_month') and hasattr(st.session_state, 'selected_year'):
        st.markdown("---")
        if st.button("🗓️ Show Availability Matrix"):
            st.session_state.show_availability = True
            st.rerun()
        
        if st.session_state.get('show_availability', False):
            # Date selector for availability
            month_start = date(st.session_state.selected_year, st.session_state.selected_month, 1)
            if st.session_state.selected_month == 12:
                month_end = date(st.session_state.selected_year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(st.session_state.selected_year, st.session_state.selected_month + 1, 1) - timedelta(days=1)
            
            availability_date = st.date_input(
                "Select Date for Availability Matrix",
                value=date.today() if month_start <= date.today() <= month_end else month_start,
                min_value=month_start,
                max_value=month_end,
                key="availability_date"
            )
            
            show_inventory_availability_matrix(availability_date)
            
            if st.button("← Back to Daily Status"):
                st.session_state.show_availability = False
                st.rerun()

# Additional utility functions for integration

def get_property_inventory_summary(property_name, target_date):
    """Get inventory summary for a specific property and date."""
    if 'all_reservations' not in st.session_state:
        st.session_state.all_reservations = load_all_reservations()
    
    reservations = st.session_state.all_reservations
    
    # Filter reservations for the property and date
    prop_reservations = [
        res for res in reservations
        if res["property_name"] == property_name and res["check_in"] == target_date
    ]
    
    inventory_map = get_inventory_mapping()
    prop_config = inventory_map.get(property_name, {})
    total_inventory = len(prop_config.get("room_mapping", {}))
    
    return {
        "total_inventory": total_inventory,
        "total_bookings": len(prop_reservations),
        "overbooked": len([res for res in prop_reservations if res["inventory_no"] == "Overbooked"]),
        "revenue": sum(res["total_tariff"] for res in prop_reservations),
        "advance": sum(res["advance_amount"] for res in prop_reservations),
        "balance": sum(res["balance_amount"] for res in prop_reservations)
    }

def get_available_inventory_for_property(property_name, target_date):
    """Get available inventory slots for a property on a specific date."""
    if 'all_reservations' not in st.session_state:
        st.session_state.all_reservations = load_all_reservations()
    
    reservations = st.session_state.all_reservations
    inventory_map = get_inventory_mapping()
    prop_config = inventory_map.get(property_name, {})
    
    # Get all inventory numbers for the property
    all_inventory = list(prop_config.get("room_mapping", {}).keys())
    
    # Get occupied inventory for the date range
    occupied_inventory = set()
    for res in reservations:
        if (res["property_name"] == property_name and 
            res["check_in"] and res["check_out"] and
            res["check_in"] <= target_date < res["check_out"] and
            res["inventory_no"] not in ["Overbooked", "Day Use 1", "Day Use 2", "No Show"]):
            occupied_inventory.add(res["inventory_no"])
    
    # Return available inventory
    available_inventory = [inv for inv in all_inventory if inv not in occupied_inventory]
    return available_inventory

def export_daily_report(selected_date):
    """Export daily report to CSV."""
    if 'all_reservations' not in st.session_state:
        return None
    
    reservations = st.session_state.all_reservations
    
    # Filter for selected date
    daily_reservations = [
        res for res in reservations 
        if res["check_in"] == selected_date
    ]
    
    if not daily_reservations:
        return None
    
    # Create export DataFrame
    export_data = []
    for res in daily_reservations:
        export_data.append({
            "Date": selected_date.strftime("%Y-%m-%d"),
            "Property": res["property_name"],
            "Inventory No": res["inventory_no"],
            "Room No": res["room_no"],
            "Booking ID": res["booking_id"],
            "Guest Name": res["guest_name"],
            "Mobile No": res["mobile_no"],
            "Total Pax": res["total_pax"],
            "Check-in": res["check_in"].strftime("%Y-%m-%d") if res["check_in"] else "",
            "Check-out": res["check_out"].strftime("%Y-%m-%d") if res["check_out"] else "",
            "Days": res["no_of_days"],
            "Booking Status": res["booking_status"],
            "Payment Status": res["payment_status"],
            "Total Tariff": res["total_tariff"],
            "Advance": res["advance_amount"],
            "Balance": res["balance_amount"],
            "Source": res["source"],
            "Remarks": res["remarks"]
        })
    
    return pd.DataFrame(export_data)

if __name__ == "__main__":
    main()
