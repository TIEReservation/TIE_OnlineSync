# inventory.py
import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from supabase import create_client, Client
from directreservation import load_reservations_from_supabase, load_property_room_map, parse_date as direct_parse_date, calculate_days
from online_reservation import load_online_reservations_from_supabase, parse_date as online_parse_date

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

def parse_room_no(room_no):
    room_no = str(room_no).strip()
    if 'to' in room_no:
        parts = room_no.split('to')
        if len(parts) == 2:
            try:
                start = int(parts[0])
                end = int(parts[1])
                return [str(i) for i in range(start, end + 1)]
            except ValueError:
                return [room_no]
    if '&' in room_no:
        parts = room_no.split('&')
        return [p.strip() for p in parts]
    if ',' in room_no:
        parts = room_no.split(',')
        return [p.strip() for p in parts]
    return [room_no]

def get_inventory_nos(property_name, room_no, room_type, booking_status):
    if booking_status == "No Show":
        return ['No Show']
    if room_type in ["Other", "UNASSIGNED"] or not room_type:
        return ['Day Use 1']

    # Property-specific special mappings
    if property_name == "Le Poshe Luxury":
        if room_no in ['D1', 'D2', 'D3', 'D4', 'D5']:
            map_d = {'D1': '203', 'D2': '204', 'D3': '205', 'D4': '303', 'D5': '305'}
            return [map_d[room_no]]
    elif property_name == "Le Pondy Beach Side":
        if room_no == "Singleroom":
            return ['101']
        elif room_no == "TwoRooms":
            return ['101', '102']
        elif room_no == "ThreeRooms":
            return ['101', '102', '201']
        elif room_no == "11":
            return ['101']
    elif property_name == "La Paradise Luxury":
        if room_no == "sp":
            return ['101']
    elif property_name == "La Villa Heritage":
        if room_no == "EVA":
            return ['101']
    # Add more special cases as needed for other properties

    # Default to parsing the room_no
    return parse_room_no(room_no)

def show_daily_status():
    st.title("📅 Daily Status")

    # Show all 12 months in a calendar-like view (grid of buttons)
    st.subheader("Select Month")
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    cols = st.columns(3)
    selected_month = st.session_state.get('selected_month', None)
    for i, month in enumerate(months):
        with cols[i % 3]:
            if st.button(month):
                st.session_state.selected_month = month
                selected_month = month

    if selected_month:
        year = 2025  # Fixed year as per current date context
        month_map = {m: i+1 for i, m in enumerate(months)}
        month_num = month_map[selected_month]
        month_start = date(year, month_num, 1)
        next_month = month_start + relativedelta(months=1)
        month_end = next_month - relativedelta(days=1)

        # Load reservations
        direct_res = load_reservations_from_supabase()
        online_res = load_online_reservations_from_supabase()

        # Normalize and filter bookings overlapping the month
        bookings = []
        for r in direct_res:
            check_in = r["Check In"] if isinstance(r["Check In"], date) else direct_parse_date(r["Check In"])
            check_out = r["Check Out"] if isinstance(r["Check Out"], date) else direct_parse_date(r["Check Out"])
            if check_in is None or check_out is None or check_out <= month_start or check_in > month_end:
                continue
            bookings.append({
                "type": "direct",
                "property": r["Property Name"],
                "booking_id": r["Booking ID"],
                "guest_name": r["Guest Name"],
                "mobile_no": r["Mobile No"],
                "total_pax": r["Total Pax"],
                "check_in": check_in,
                "check_out": check_out,
                "days": r["No of Days"],
                "booking_status": r["Booking Status"],
                "payment_status": r["Payment Status"],
                "remarks": r["Remarks"],
                "room_no": r["Room No"],
                "room_type": r["Room Type"],
            })
        for r in online_res:
            check_in = online_parse_date(r["check_in"])
            check_out = online_parse_date(r["check_out"])
            if check_in is None or check_out is None or check_out <= month_start or check_in > month_end:
                continue
            bookings.append({
                "type": "online",
                "property": r["property"],
                "booking_id": r["booking_id"],
                "guest_name": r["guest_name"],
                "mobile_no": r["guest_phone"],
                "total_pax": r["total_pax"],
                "check_in": check_in,
                "check_out": check_out,
                "days": calculate_days(check_in, check_out),
                "booking_status": r["booking_status"],
                "payment_status": r["payment_status"],
                "remarks": r["remarks"],
                "room_no": r["room_no"],
                "room_type": r["room_type"],
            })

        # Get all properties
        property_map = load_property_room_map()
        properties = sorted(property_map.keys())

        st.subheader(f"Properties for {selected_month} {year}")
        for prop in properties:
            with st.expander(prop):
                property_bookings = [b for b in bookings if b["property"] == prop]
                if not property_bookings:
                    st.info("No bookings for this property in the selected month.")
                    continue

                table_data = []
                for b in property_bookings:
                    inventory_nos = get_inventory_nos(prop, b["room_no"], b["room_type"], b["booking_status"])
                    inventory_str = ', '.join(inventory_nos)

                    # Make Booking ID a hyperlink based on type
                    if b["type"] == "direct":
                        booking_id_html = f'<a href="/directreservation?booking_id={b["booking_id"]}">{b["booking_id"]}</a>'
                    else:
                        booking_id_html = f'<a href="/editOnline?booking_id={b["booking_id"]}">{b["booking_id"]}</a>'

                    table_data.append({
                        "Inventory No": inventory_str,
                        "Room No": b["room_no"],
                        "Booking ID": booking_id_html,
                        "Guest Name": b["guest_name"],
                        "Mobile No": b["mobile_no"],
                        "Total Pax": b["total_pax"],
                        "Check-in Date": b["check_in"],
                        "Check-out Date": b["check_out"],
                        "Days": b["days"],
                        "Booking Status": b["booking_status"],
                        "Payment Status": b["payment_status"],
                        "Remarks": b["remarks"],
                    })

                df = pd.DataFrame(table_data)
                st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
