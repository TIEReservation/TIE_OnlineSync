
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
    """Show daily status for a selected month."""
    st.markdown("---")
    st.subheader(f"📊 Daily Status - {calendar.month_name[month]} {year}")
    
    # Get calendar for the month
    cal = calendar.monthcalendar(year, month)
    month_start = date(year, month, 1)
    
    # Get last day of month
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)
    
    # Date selector
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        selected_date = st.date_input(
            "Select Date",
            value=month_start,
            min_value=month_start,
            max_value=month_end,
            key=f"date_selector_{year}_{month}"
        )
    
    with col2:
        if st.button("🔄 Refresh Data", key=f"refresh_{year}_{month}"):
            if 'all_reservations' in st.session_state:
                del st.session_state.all_reservations
            st.rerun()
    
    with col3:
        if st.button("📊 Analytics", key=f"analytics_{year}_{month}"):
            st.session_state.show_analytics = True
            st.rerun()
    
    # Show analytics if requested
    if st.session_state.get('show_analytics', False):
        show_inventory_analytics()
        if st.button("← Back to Daily Status"):
            st.session_state.show_analytics = False
            st.rerun()
        return
    
    if selected_date:
        show_daily_property_status(selected_date)

def show_daily_property_status(selected_date):
    """Show property-wise booking status for a selected date."""
    st.subheader(f"🏨 Property Status - {selected_date.strftime('%B %d, %Y')}")
    
    # Load all reservations
    if 'all_reservations' not in st.session_state:
        with st.spinner("Loading reservations..."):
            st.session_state.all_reservations = load_all_reservations()
    
    reservations = st.session_state.all_reservations
    
    # Filter reservations for the selected date (check-in date)
    daily_reservations = [
        res for res in reservations 
        if res["check_in"] == selected_date
    ]
    
    if not daily_reservations:
        st.info(f"No check-ins found for {selected_date.strftime('%B %d, %Y')}")
        return
    
    # Show overall summary
    total_bookings = len(daily_reservations)
    total_revenue = sum(res["total_tariff"] for res in daily_reservations)
    total_advance = sum(res["advance_amount"] for res in daily_reservations)
    total_overbooked = sum(1 for res in daily_reservations if res["inventory_no"] == "Overbooked")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Check-ins", total_bookings)
    with col2:
        st.metric("Total Revenue", f"₹{total_revenue:,.2f}")
    with col3:
        st.metric("Advance Collected", f"₹{total_advance:,.2f}")
    with col4:
        if total_overbooked > 0:
            st.metric("🚨 Total Overbookings", total_overbooked, delta=total_overbooked, delta_color="inverse")
        else:
            st.metric("✅ Overbookings", 0)
    
    # Group by property
    properties = {}
    for res in daily_reservations:
        prop_name = res["property_name"]
        if prop_name not in properties:
            properties[prop_name] = []
        properties[prop_name].append(res)
    
    # Display each property
    for prop_name, prop_reservations in properties.items():
        with st.expander(f"🏨 {prop_name} ({len(prop_reservations)} bookings)", expanded=True):
            show_property_booking_table(prop_name, prop_reservations, selected_date)

def show_property_booking_table(property_name, reservations, selected_date):
    """Show booking table for a specific property."""
    if not reservations:
        st.info("No bookings for this property.")
        return
    
    # Create DataFrame
    df_data = []
    total_tariff = 0
    total_advance = 0
    total_balance = 0
    overbooked_count = 0
    
    for res in reservations:
        is_overbooked = res["inventory_no"] == "Overbooked"
        if is_overbooked:
            overbooked_count += 1
        
        total_tariff += res["total_tariff"]
        total_advance += res["advance_amount"]
        total_balance += res["balance_amount"]
        
        df_data.append({
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
            "Remarks": res["remarks"],
            "Source": res["source"],
            "Total Tariff": res["total_tariff"],
            "Advance": res["advance_amount"],
            "Balance": res["balance_amount"],
            "Overbooked": is_overbooked
        })
    
    if df_data:
        df = pd.DataFrame(df_data)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Bookings", len(df))
        with col2:
            st.metric("Total Revenue", f"₹{total_tariff:,.2f}")
        with col3:
            st.metric("Advance Collected", f"₹{total_advance:,.2f}")
        with col4:
            if overbooked_count > 0:
                st.metric("🚨 Overbookings", overbooked_count, delta=overbooked_count, delta_color="inverse")
            else:
                st.metric("✅ Overbookings", 0)
        
        # Inventory reassignment section
        st.subheader("🔄 Inventory Management")
        
        # Get available inventory numbers for this property
        inventory_map = get_inventory_mapping()
        property_map = inventory_map.get(property_name, {})
        available_inventories = list(property_map.get("room_mapping", {}).keys())
        available_inventories.extend(property_map.get("day_use", []))
        available_inventories.append(property_map.get("no_show", "No Show"))
        available_inventories.append("Overbooked")
        
        # Reassignment interface
        col1, col2, col3 = st.columns(3)
        with col1:
            booking_to_move = st.selectbox("Select Booking to Reassign", df["Booking ID"].tolist(), key=f"move_booking_{property_name}")
        with col2:
            new_inventory = st.selectbox("Assign to Inventory", available_inventories, key=f"new_inventory_{property_name}")
        with col3:
            if st.button("🔄 Reassign", key=f"reassign_{property_name}"):
                # Find the booking
                booking_data = df[df["Booking ID"] == booking_to_move].iloc[0]
                source = booking_data["Source"]
                
                # Check for conflicts
                existing_booking = df[df["Inventory No"] == new_inventory]
                if not existing_booking.empty and new_inventory not in ["Day Use 1", "Day Use 2", "Overbooked", "No Show"]:
                    st.warning(f"⚠️ Inventory {new_inventory} is already assigned to Booking ID: {existing_booking.iloc[0]['Booking ID']}")
                    if st.button("⚠️ Confirm Overbooking", key=f"confirm_overbook_{property_name}"):
                        if update_inventory_assignment(booking_to_move, source, new_inventory):
                            st.success(f"✅ Booking {booking_to_move} reassigned to {new_inventory}")
                            del st.session_state.all_reservations
                            st.rerun()
                else:
                    if update_inventory_assignment(booking_to_move, source, new_inventory):
                        st.success(f"✅ Booking {booking_to_move} reassigned to {new_inventory}")
                        del st.session_state.all_reservations
                        st.rerun()
        
        # Display bookings table with color coding
        st.subheader("📋 Booking Details")
        
        # Create clickable booking IDs
        def make_clickable_booking_id(booking_id, source):
            return f'<a href="#" onclick="editBooking(\'{booking_id}\', \'{source}\')" style="color: #1f77b4; text-decoration: underline;">{booking_id}</a>'
        
        # Style function for overbooked rows
        def highlight_overbooked(row):
            if row["Overbooked"]:
                return ['background-color: #ffebee; color: #c62828; font-weight: bold'] * len(row)
            elif row["Booking Status"] == "Cancelled":
                return ['background-color: #fff3e0; color: #ef6c00'] * len(row)
            elif row["Payment Status"] == "Paid":
                return ['background-color: #e8f5e8; color: #2e7d32'] * len(row)
            return [''] * len(row)
        
        # Prepare display dataframe
        display_df = df[["Inventory No", "Room No", "Booking ID", "Guest Name", "Mobile No", 
                        "Total Pax", "Check-in", "Check-out", "Days", "Booking Status", 
                        "Payment Status", "Total Tariff", "Advance", "Balance", "Remarks"]].copy()
        
        # Add edit links
        for index, row in display_df.iterrows():
            booking_id = row["Booking ID"]
            source = df.loc[index, "Source"]
            if st.button(f"✏️ Edit", key=f"edit_{booking_id}_{property_name}"):
                st.session_state.edit_booking_id = booking_id
                st.session_state.edit_booking_source = source
                st.rerun()
        
        # Apply styling and display
        styled_df = display_df.style.apply(highlight_overbooked, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Show totals
        st.subheader("💰 Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tariff", f"₹{total_tariff:,.2f}")
        with col2:
            st.metric("Total Advance", f"₹{total_advance:,.2f}")
        with col3:
            st.metric("Total Balance", f"₹{total_balance:,.2f}")
        with col4:
            collection_percentage = (total_advance / total_tariff * 100) if total_tariff > 0 else 0
            st.metric("Collection %", f"{collection_percentage:.1f}%")
        
        # Show overbooking details if any
        if overbooked_count > 0:
            st.error("🚨 **OVERBOOKING ALERT**")
            overbooked_df = df[df["Overbooked"] == True]
            st.write(f"⚠️ **{overbooked_count} booking(s) are overbooked and need immediate attention:**")
            
            overbooked_display = overbooked_df[["Booking ID", "Guest Name", "Room No", "Mobile No", "Total Tariff", "Remarks"]].copy()
            st.dataframe(overbooked_display, use_container_width=True)
            
            # Quick fix suggestions
            st.write("**💡 Quick Fix Options:**")
            st.write("- Reassign to available Day Use inventory")
            st.write("- Contact guest to reschedule")
            st.write("- Upgrade to sister property if available")

def show_booking_edit_form(booking_id, source):
    """Show edit form for a selected booking."""
    st.subheader(f"✏️ Edit Booking: {booking_id}")
    
    # Load booking details
    reservations = st.session_state.get('all_reservations', [])
    booking = next((res for res in reservations if res["booking_id"] == booking_id and res["source"] == source), None)
    
    if not booking:
        st.error("Booking not found!")
        return
    
    # Edit form
    with st.form(f"edit_booking_{booking_id}"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_guest_name = st.text_input("Guest Name", value=booking["guest_name"])
            new_mobile_no = st.text_input("Mobile No", value=booking["mobile_no"])
            new_total_pax = st.number_input("Total Pax", value=booking["total_pax"], min_value=1)
            new_room_no = st.text_input("Room No", value=booking["room_no"])
            new_room_type = st.text_input("Room Type", value=booking["room_type"])
        
        with col2:
            new_check_in = st.date_input("Check-in Date", value=booking["check_in"])
            new_check_out = st.date_input("Check-out Date", value=booking["check_out"])
            new_booking_status = st.selectbox("Booking Status", 
                                            ["Confirmed", "Pending", "Cancelled", "No Show"], 
                                            index=["Confirmed", "Pending", "Cancelled", "No Show"].index(booking["booking_status"]) if booking["booking_status"] in ["Confirmed", "Pending", "Cancelled", "No Show"] else 0)
            new_payment_status = st.selectbox("Payment Status", 
                                            ["Paid", "Pending", "Advance Paid", "Not Paid"], 
                                            index=["Paid", "Pending", "Advance Paid", "Not Paid"].index(booking["payment_status"]) if booking["payment_status"] in ["Paid", "Pending", "Advance Paid", "Not Paid"] else 0)
            new_remarks = st.text_area("Remarks", value=booking["remarks"])
        
        # Financial details
        st.subheader("💰 Financial Details")
        col1, col2, col3 = st.columns(3)
        with col1:
            new_total_tariff = st.number_input("Total Tariff", value=float(booking["total_tariff"]), min_value=0.0, step=100.0)
        with col2:
            new_advance = st.number_input("Advance Amount", value=float(booking["advance_amount"]), min_value=0.0, step=100.0)
        with col3:
            new_balance = st.number_input("Balance Amount", value=float(booking["balance_amount"]), min_value=0.0, step=100.0)
        
        # Submit buttons
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)
        with col2:
            cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if submitted:
            # Calculate days
            new_days = (new_check_out - new_check_in).days if new_check_out > new_check_in else 1
            
            # Update booking
            success = update_booking_details(booking_id, source, {
                "guest_name": new_guest_name,
                "mobile_no": new_mobile_no,
                "total_pax": new_total_pax,
                "room_no": new_room_no,
                "room_type": new_room_type,
                "check_in": new_check_in.strftime("%Y-%m-%d"),
                "check_out": new_check_out.strftime("%Y-%m-%d"),
                "no_of_days": new_days,
                "booking_status": new_booking_status,
                "payment_status": new_payment_status,
                "total_tariff": new_total_tariff,
                "advance_amount": new_advance,
                "balance_amount": new_balance,
                "remarks": new_remarks
            })
            
            if success:
                st.success("✅ Booking updated successfully!")
                # Clear cache and return to main view
                if 'all_reservations' in st.session_state:
                    del st.session_state.all_reservations
                if 'edit_booking_id' in st.session_state:
                    del st.session_state.edit_booking_id
                st.rerun()
            else:
                st.error("❌ Failed to update booking. Please try again.")
        
        if cancelled:
            if 'edit_booking_id' in st.session_state:
                del st.session_state.edit_booking_id
            st.rerun()

def update_booking_details(booking_id, source, updates):
    """Update booking details in the database."""
    try:
        table_name = "reservations" if source == "direct" else "online_reservations"
        
        # Map field names for online reservations
        if source == "online":
            field_mapping = {
                "guest_name": "guest_name",
                "mobile_no": "guest_phone",
                "total_pax": "total_pax",
                "room_no": "room_no",
                "room_type": "room_type",
                "check_in": "check_in",
                "check_out": "check_out",
                "booking_status": "booking_status",
                "payment_status": "payment_status",
                "total_tariff": "booking_amount",
                "advance_amount": "total_payment_made",
                "balance_amount": "balance_due",
                "remarks": "remarks"
            }
            mapped_updates = {field_mapping.get(k, k): v for k, v in updates.items() if k in field_mapping}
        else:
            # For direct reservations, map plan_status
            mapped_updates = updates.copy()
            if "booking_status" in mapped_updates:
                mapped_updates["plan_status"] = mapped_updates.pop("booking_status")
        
        response = supabase.table(table_name).update(mapped_updates).eq("booking_id", booking_id).execute()
        return bool(response.data)
    
    except Exception as e:
        st.error(f"Error updating booking: {e}")
        return False

def show_inventory_analytics():
    """Show inventory utilization analytics."""
    st.subheader("📊 Inventory Analytics")
    
    # Date range selector
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=date.today() + timedelta(days=30))
    with col3:
        analysis_type = st.selectbox("Analysis Type", ["Utilization", "Revenue", "Overbookings"])
    
    if start_date > end_date:
        st.error("Start date must be before end date")
        return
    
    # Load reservations
    if 'all_reservations' not in st.session_state:
        st.session_state.all_reservations = load_all_reservations()
    
    reservations = st.session_state.all_reservations
    
    # Filter by date range
    filtered_reservations = [
        res for res in reservations
        if res["check_in"] and start_date <= res["check_in"] <= end_date
    ]
    
    if not filtered_reservations:
        st.info("No reservations found for the selected date range.")
        return
    
    # Create analytics DataFrame
    df = pd.DataFrame(filtered_reservations)
    
    # Property-wise analytics
    if analysis_type == "Utilization":
        show_utilization_analytics(df, start_date, end_date)
    elif analysis_type == "Revenue":
        show_revenue_analytics(df, start_date, end_date)
    else:
        show_overbooking_analytics(df, start_date, end_date)

def show_utilization_analytics(df, start_date, end_date):
    """Show inventory utilization analytics."""
    st.subheader("🏨 Inventory Utilization Analysis")
    
    # Property-wise utilization
    property_stats = []
    inventory_map = get_inventory_mapping()
    
    for prop_name in df["property_name"].unique():
        prop_df = df[df["property_name"] == prop_name]
        prop_mapping = inventory_map.get(prop_name, {})
        total_inventory = len(prop_mapping.get("room_mapping", {}))
        
        # Calculate utilization metrics
        total_bookings = len(prop_df)
        unique_dates = prop_df["check_in"].nunique()
        avg_occupancy = total_bookings / (total_inventory * unique_dates) * 100 if unique_dates > 0 and total_inventory > 0 else 0
        overbooked_count = len(prop_df[prop_df["inventory_no"] == "Overbooked"])
        
        property_stats.append({
            "Property": prop_name,
            "Total Inventory": total_inventory,
            "Total Bookings": total_bookings,
            "Unique Dates": unique_dates,
            "Avg Occupancy %": round(avg_occupancy, 2),
            "Overbookings": overbooked_count,
            "Revenue": prop_df["total_tariff"].sum()
        })
    
    stats_df = pd.DataFrame(property_stats)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Properties", len(stats_df))
    with col2:
        avg_utilization = stats_df["Avg Occupancy %"].mean()
        st.metric("Avg Utilization", f"{avg_utilization:.1f}%")
    with col3:
        total_overbookings = stats_df["Overbookings"].sum()
        st.metric("Total Overbookings", total_overbookings)
    with col4:
        total_revenue = stats_df["Revenue"].sum()
        st.metric("Total Revenue", f"₹{total_revenue:,.2f}")
    
    # Utilization chart
    fig = px.bar(stats_df, x="Property", y="Avg Occupancy %", 
                 title="Property-wise Average Occupancy",
                 color="Avg Occupancy %",
                 color_continuous_scale="RdYlGn")
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed table
    st.dataframe(stats_df, use_container_width=True)
    
    # Daily utilization trend
    daily_stats = df.groupby(["check_in", "property_name"]).agg({
        "booking_id": "count",
        "total_tariff": "sum"
    }).reset_index()
    daily_stats.columns = ["Date", "Property", "Bookings", "Revenue"]
    
    fig2 = px.line(daily_stats, x="Date", y="Bookings", color="Property",
                   title="Daily Booking Trends by Property")
    st.plotly_chart(fig2, use_container_width=True)

def show_revenue_analytics(df, start_date, end_date):
    """Show revenue analytics."""
    st.subheader("💰 Revenue Analysis")
    
    # Revenue metrics
    total_revenue = df["total_tariff"].sum()
    total_advance = df["advance_amount"].sum()
    total_balance = df["balance_amount"].sum()
    collection_rate = (total_advance / total_revenue * 100) if total_revenue > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Revenue", f"₹{total_revenue:,.2f}")
    with col2:
        st.metric("Advance Collected", f"₹{total_advance:,.2f}")
    with col3:
        st.metric("Balance Due", f"₹{total_balance:,.2f}")
    with col4:
        st.metric("Collection Rate", f"{collection_rate:.1f}%")
    
    # Property-wise revenue
    prop_revenue = df.groupby("property_name").agg({
        "total_tariff": "sum",
        "advance_amount": "sum",
        "balance_amount": "sum",
        "booking_id": "count"
    }).reset_index()
    prop_revenue.columns = ["Property", "Total Revenue", "Advance", "Balance", "Bookings"]
    prop_revenue["Collection %"] = (prop_revenue["Advance"] / prop_revenue["Total Revenue"] * 100).round(2)
    
    # Revenue by property chart
    fig = px.bar(prop_revenue, x="Property", y="Total Revenue",
                 title="Revenue by Property",
                 color="Collection %",
                 color_continuous_scale="RdYlGn")
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Revenue table
    st.dataframe(prop_revenue, use_container_width=True)
    
    # Daily revenue trend
    daily_revenue = df.groupby("check_in").agg({
        "total_tariff": "sum",
        "advance_amount": "sum",
        "booking_id": "count"
    }).reset_index()
    daily_revenue.columns = ["Date", "Revenue", "Advance", "Bookings"]
    
    fig2 = px.line(daily_revenue, x="Date", y="Revenue",
                   title="Daily Revenue Trend")
    st.plotly_chart(fig2, use_container_width=True)
    
    # Payment status distribution
    payment_dist = df["payment_status"].value_counts()
    fig3 = px.pie(values=payment_dist.values, names=payment_dist.index,
                  title="Payment Status Distribution")
    st.plotly_chart(fig3, use_container_width=True)

def show_overbooking_analytics(df, start_date, end_date):
    """Show overbooking analytics."""
    st.subheader("🚨 Overbooking Analysis")
    
    # Overbooking metrics
    total_bookings = len(df)
    overbooked_bookings = len(df[df["inventory_no"] == "Overbooked"])
    overbooking_rate = (overbooked_bookings / total_bookings * 100) if total_bookings > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Bookings", total_bookings)
    with col2:
        st.metric("Overbooked", overbooked_bookings)
    with col3:
        st.metric("Overbooking Rate", f"{overbooking_rate:.2f}%")
    with col4:
        cancelled_bookings = len(df[df["booking_status"] == "Cancelled"])
        st.metric("Cancelled", cancelled_bookings)
    
    if overbooked_bookings == 0:
        st.success("🎉 **Excellent! No overbookings found in the selected period.**")
        return
    
    # Overbooking by property
    overbooked_df = df[df["inventory_no"] == "Overbooked"]
    prop_overbooking = overbooked_df.groupby("property_name").agg({
        "booking_id": "count",
        "total_tariff": "sum"
    }).reset_index()
    prop_overbooking.columns = ["Property", "Overbookings", "Lost Revenue"]
    
    # Overbooking chart
    fig = px.bar(prop_overbooking, x="Property", y="Overbookings",
                 title="Overbookings by Property",
                 color="Lost Revenue",
                 color_continuous_scale="Reds")
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed overbooking table
    st.subheader("📋 Detailed Overbooking List")
    overbooked_display = overbooked_df[["check_in", "property_name", "booking_id", "guest_name", 
                                       "mobile_no", "room_no", "total_tariff", "remarks"]].copy()
    overbooked_display.columns = ["Check-in", "Property", "Booking ID", "Guest", "Mobile", 
                                 "Room No", "Revenue Impact", "Remarks"]
    
    st.dataframe(overbooked_display, use_container_width=True)
    
    # Daily overbooking trend
    daily_overbook = overbooked_df.groupby("check_in").size().reset_index()
    daily_overbook.columns = ["Date", "Overbookings"]
    
    if len(daily_overbook) > 0:
        fig2 = px.line(daily_overbook, x="Date", y="Overbookings",
                       title="Daily Overbooking Trend")
        st.plotly_chart(fig2, use_container_width=True)

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
