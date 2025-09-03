# inventory.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from supabase import create_client, Client

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

# Import functions from directreservation, with embedded implementations to avoid import issues
try:
    from directreservation import load_reservations_from_supabase, load_property_room_map, calculate_days, parse_date as direct_parse_date
except ImportError as e:
    st.warning(f"Import from directreservation failed: {e}. Using embedded implementations.")
    def safe_int(value, default=0):
        """Safely convert value to int, return default if conversion fails."""
        try:
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    def safe_float(value, default=0.0):
        """Safely convert value to float, return default if conversion fails."""
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    def direct_parse_date(dt_str):
        """Parse date string with or without time."""
        if not dt_str or pd.isna(dt_str):
            return None
        try:
            return datetime.strptime(dt_str, "%Y-%m-%d").date()
        except ValueError:
            try:
                return datetime.strptime(dt_str, "%d/%m/%Y").date()
            except ValueError:
                return None

    def calculate_days(check_in, check_out):
        """Calculate the number of days between check-in and check-out dates."""
        if check_in and check_out and check_out >= check_in:
            delta = check_out - check_in
            return max(1, delta.days)
        return 0

    def load_reservations_from_supabase():
        """Load reservations from Supabase, handling potential None values."""
        try:
            response = supabase.table("reservations").select("*").execute()
            reservations = []
            for record in response.data:
                reservation = {
                    "Booking ID": record["booking_id"],
                    "Property Name": record["property_name"] or "",
                    "Room No": record["room_no"] or "",
                    "Guest Name": record["guest_name"] or "",
                    "Mobile No": record["mobile_no"] or "",
                    "No of Adults": safe_int(record["no_of_adults"]),
                    "No of Children": safe_int(record["no_of_children"]),
                    "No of Infants": safe_int(record["no_of_infants"]),
                    "Total Pax": safe_int(record["total_pax"]),
                    "Check In": record["check_in"],
                    "Check Out": record["check_out"],
                    "No of Days": safe_int(record["no_of_days"]),
                    "Tariff": safe_float(record["tariff"]),
                    "Total Tariff": safe_float(record["total_tariff"]),
                    "Advance Amount": safe_float(record["advance_amount"]),
                    "Balance Amount": safe_float(record["balance_amount"]),
                    "Advance MOP": record["advance_mop"] or "",
                    "Balance MOP": record["balance_mop"] or "",
                    "MOB": record["mob"] or "",
                    "Online Source": record["online_source"] or "",
                    "Invoice No": record["invoice_no"] or "",
                    "Enquiry Date": record["enquiry_date"],
                    "Booking Date": record["booking_date"],
                    "Room Type": record["room_type"] or "",
                    "Breakfast": record["breakfast"] or "",
                    "Booking Status": record["booking_status"] or "",
                    "Submitted By": record["submitted_by"] or "",
                    "Modified By": record["modified_by"] or "",
                    "Modified Comments": record["modified_comments"] or "",
                    "Remarks": record["remarks"] or "",
                    "Payment Status": record["payment_status"] or ""
                }
                reservations.append(reservation)
            return reservations
        except Exception as e:
            st.error(f"Error loading reservations: {e}")
            return []

    def load_property_room_map():
        """Loads the property to room type to room numbers mapping."""
        return {
            "Le Poshe Beachview": {
                "Double Room": ["101", "102", "202", "203", "204"],
                "Standard Room": ["201"],
                "Deluex Double Room Seaview": ["301", "302", "303", "304"]
            },
            "La Millionare Resort": {
                "Double Room": ["101", "102", "103", "105"],
                "Deluex Double Room with Balcony": ["205", "304", "305"],
                "Deluex Triple Room with Balcony": ["201", "202", "203", "204", "301", "302", "303"],
                "Deluex Family Room with Balcony": ["206", "207", "208", "306", "307", "308"],
                "Deluex Triple Room": ["402"],
                "Deluex Family Room": ["401"]
            },
            "Le Poshe Luxury": {
                "2BHA Appartment": ["101&102", "101", "102"],
                "2BHA Appartment with Balcony": ["201&202", "201", "202", "301&302", "301", "302", "401&402", "401", "402"],
                "3BHA Appartment": ["203to205", "203", "204", "205", "303to305", "303", "304", "305", "403to405", "403", "404", "405"],
                "Double Room with Private Terrace": ["501"]
            },
            "Le Poshe Suite": {
                "2BHA Appartment": ["601&602", "601", "602", "603", "604", "703", "704"],
                "2BHA Appartment with Balcony": ["701&702", "701", "702"],
                "Double Room with Terrace": ["801"]
            },
            "La Paradise Residency": {
                "Double Room": ["101", "102", "103", "301", "304"],
                "Family Room": ["201", "203"],
                "Triple Room": ["202", "303"]
            },
            "La Paradise Luxury": {
                "3BHA Appartment": ["101to103", "101", "102", "103", "201to203", "201", "202", "203"]
            },
            "La Villa Heritage": {
                "Double Room": ["101", "102", "103"],
                "4BHA Appartment": ["201to203&301", "201", "202", "203", "301"]
            },
            "Le Pondy Beach Side": {
                "Villa": ["101to104", "101", "102", "103", "104"]
            },
            "Le Royce Villa": {
                "Villa": ["101to102&201to202", "101", "102", "201", "202"]
            },
            "La Tamara Luxury": {
                "3BHA": ["101to103", "101", "102", "103", "104to106", "104", "105", "106", "201to203", "201", "202", "203", "204to206", "204", "205", "206", "301to303", "301", "302", "303", "304to306", "304", "305", "306"],
                "4BHA": ["401to404", "401", "402", "403", "404"]
            },
            "La Antilia": {
                "Deluex Suite Room": ["101"],
                "Deluex Double Room": ["203", "204", "303", "304"],
                "Family Room": ["201", "202", "301", "302"],
                "Deluex suite Room with Tarrace": ["404"]
            },
            "La Tamara Suite": {
                "Two Bedroom apartment": ["101&102"],
                "Deluxe Apartment": ["103&104"],
                "Deluxe Double Room": ["203", "204", "205"],
                "Deluxe Triple Room": ["201", "202"],
                "Deluxe Family Room": ["206"]
            },
            "Le Park Resort": {
                "Villa with Swimming Pool View": ["555&666", "555", "666"],
                "Villa with Garden View": ["111&222", "111", "222"],
                "Family Retreate Villa": ["333&444", "333", "444"]
            },
            "Villa Shakti": {
                "2BHA Studio Room": ["101&102"],
                "2BHA with Balcony": ["202&203", "302&303"],
                "Family Suite": ["201"],
                "Family Room": ["301"],
                "Terrace Room": ["401"]
            },
            "Eden Beach Resort": {
                "Double Room": ["101", "102"],
                "Deluex Room": ["103", "202"],
                "Triple Room": ["201"]
            }
        }

# Import online_reservation functions
try:
    from online_reservation import load_online_reservations_from_supabase, parse_date as online_parse_date
except ImportError as e:
    st.warning(f"Import from online_reservation failed: {e}. Using placeholder implementations.")
    def load_online_reservations_from_supabase():
        """Placeholder for loading online reservations."""
        st.error(f"Error loading online reservations: {e}")
        return []
    def online_parse_date(dt_str):
        """Placeholder for parsing online reservation dates."""
        if not dt_str or pd.isna(dt_str):
            return None
        try:
            return datetime.strptime(dt_str, "%Y-%m-%d").date()
        except ValueError:
            try:
                return datetime.strptime(dt_str, "%d/%m/%Y").date()
            except ValueError:
                return None

def parse_room_no(room_no):
    """Parse room number string into a list of individual room numbers."""
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
    """Map room numbers to inventory numbers based on property-specific rules."""
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
    return parse_room_no(room_no)

def sync_inventory_to_supabase():
    """Sync rooms from property_room_map to the inventory table in Supabase."""
    property_map = load_property_room_map()
    try:
        existing = supabase.table("inventory").select("property_name, inventory_no").execute()
        existing_pairs = {(r["property_name"], r["inventory_no"]) for r in existing.data}
        to_insert = []
        for prop, room_types in property_map.items():
            for rooms in room_types.values():
                for room in rooms:
                    if (prop, room) not in existing_pairs:
                        to_insert.append({"property_name": prop, "inventory_no": room})
        if to_insert:
            supabase.table("inventory").insert(to_insert).execute()
            st.success(f"Synced {len(to_insert)} rooms to inventory.")
        else:
            st.info("Inventory table is up-to-date.")
    except Exception as e:
        st.error(f"Error syncing inventory: {e}")

def show_daily_status():
    """Display daily status with room availability and booking density chart."""
    st.title("📅 Daily Status")

    # Sync inventory to ensure all rooms are in the database
    sync_inventory_to_supabase()

    # Show all 12 months in a calendar-like view
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
        year = datetime.now().year  # Dynamic year
        month_map = {m: i+1 for i, m in enumerate(months)}
        month_num = month_map[selected_month]
        month_start = date(year, month_num, 1)
        next_month = month_start + relativedelta(months=1)
        month_end = next_month - relativedelta(days=1)

        # Load reservations
        direct_res = load_reservations_from_supabase()
        online_res = load_online_reservations_from_supabase()
        property_map = load_property_room_map()

        # Generate date range for the month
        date_range = [month_start + timedelta(days=x) for x in range((month_end - month_start).days + 1)]

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

        # Display availability and bookings for each property
        st.subheader(f"Properties for {selected_month} {year}")
        for prop in sorted(property_map.keys()):
            with st.expander(prop):
                property_bookings = [b for b in bookings if b["property"] == prop]
                if not property_bookings:
                    st.info("No bookings for this property in the selected month.")
                    continue

                # Room type filter
                room_types = ["All"] + sorted(property_map[prop].keys())
                selected_room_type = st.selectbox(f"Filter by Room Type for {prop}", room_types, key=f"room_type_{prop}")
                if selected_room_type != "All":
                    property_bookings = [b for b in property_bookings if b["room_type"] == selected_room_type]
                    all_rooms = property_map[prop][selected_room_type]
                else:
                    all_rooms = []
                    for room_type, rooms in property_map[prop].items():
                        for room in rooms:
                            if room not in all_rooms:
                                all_rooms.append(room)
                    all_rooms = sorted(all_rooms)

                # Build availability table
                availability_data = []
                for room in all_rooms:
                    row = {"Room No": room}
                    for d in date_range:
                        status = "Available"
                        for booking in property_bookings:
                            inventory_nos = get_inventory_nos(prop, booking["room_no"], booking["room_type"], booking["booking_status"])
                            if room in inventory_nos and booking["check_in"] <= d < booking["check_out"]:
                                status = booking["booking_id"]
                                break
                        row[d.strftime("%Y-%m-%d")] = status
                    availability_data.append(row)

                st.subheader(f"Room Availability for {prop}")
                df = pd.DataFrame(availability_data)
                st.dataframe(df, use_container_width=True)

                # Booking density chart
                booking_counts = []
                for d in date_range:
                    count = sum(1 for b in property_bookings if b["check_in"] <= d < b["check_out"])
                    booking_counts.append({"Date": d, "Booked Rooms": count})

                st.subheader(f"Booking Density for {prop}")
                df_chart = pd.DataFrame(booking_counts).set_index("Date")
                st.line_chart(df_chart, use_container_width=True)

                # Existing booking table
                table_data = []
                for b in property_bookings:
                    inventory_nos = get_inventory_nos(prop, b["room_no"], b["room_type"], b["booking_status"])
                    inventory_str = ', '.join(inventory_nos)
                    booking_id_html = f'<a href="/{"directreservation" if b["type"] == "direct" else "editOnline"}?booking_id={b["booking_id"]}">{b["booking_id"]}</a>'
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

                st.subheader("Bookings")
                st.markdown(pd.DataFrame(table_data).to_html(escape=False, index=False), unsafe_allow_html=True)
