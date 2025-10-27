import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from supabase import create_client, Client

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

def load_property_room_map():
    """
    Loads the property to room type to room numbers mapping based on provided data.
    Keys and values are kept as-is from the user's input, including typos and combined rooms.
    Returns a nested dictionary: {"Property": {"Room Type": ["Room No", ...], ...}, ...}
    """
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
            "Villa": ["101to102&201to202", "101", "102", "202", "202"]  # Note: duplicate "202" as per data
        },
        "La Tamara Luxury": {
            "3BHA": ["101to103", "101", "102", "103", "104to106", "104", "105", "106", "201to203", "201", "202", "203", "204to206", "204", "205", "206", "301to303", "301", "302", "303", "304to306", "304", "305", "306"],
            "4BHA": ["401to404", "401", "402", "403", "404"]  # Note: duplicate "404" as per data
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

def generate_booking_id():
    """Generate a unique booking ID by checking existing IDs in Supabase."""
    try:
        today = datetime.now().strftime('%Y%m%d')
        response = supabase.table("reservations").select("booking_id").like("booking_id", f"TIE{today}%").execute()
        existing_ids = [record["booking_id"] for record in response.data]
        sequence = 1
        while f"TIE{today}{sequence:03d}" in existing_ids:
            sequence += 1
        return f"TIE{today}{sequence:03d}"
    except Exception as e:
        st.error(f"Error generating booking ID: {e}")
        return None

def check_duplicate_guest(guest_name, mobile_no, room_no, exclude_booking_id=None, mob=None):
    """Check for duplicate guest based on name, mobile number, and room number, allowing 'Stay-back' if MOB differs."""
    try:
        response = supabase.table("reservations").select("*").execute()
        for reservation in response.data:
            if exclude_booking_id and reservation["booking_id"] == exclude_booking_id:
                continue
            if (reservation["guest_name"].lower() == guest_name.lower() and
                    reservation["mobile_no"] == mobile_no and
                    reservation["room_no"] == room_no):
                if mob == "Stay-back" and reservation["mob"] != "Stay-back":
                    continue
                return True, reservation["booking_id"]
        return False, None
    except Exception as e:
        st.error(f"Error checking duplicate guest: {e}")
        return False, None

def calculate_days(check_in, check_out):
    """Calculate the number of days between check-in and check-out dates."""
    if check_in and check_out and check_out >= check_in:
        delta = check_out - check_in
        return max(1, delta.days)
    return 0

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
                "Check In": datetime.strptime(record["check_in"], "%Y-%m-%d").date() if record["check_in"] else None,
                "Check Out": datetime.strptime(record["check_out"], "%Y-%m-%d").date() if record["check_out"] else None,
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
                "Enquiry Date": datetime.strptime(record["enquiry_date"], "%Y-%m-%d").date() if record["enquiry_date"] else None,
                "Booking Date": datetime.strptime(record["booking_date"], "%Y-%m-%d").date() if record["booking_date"] else None,
                "Room Type": record["room_type"] or "",
                "Breakfast": record["breakfast"] or "",
                "Booking Status": record["plan_status"] or "",
                "Submitted By": record.get("submitted_by", ""),
                "Modified By": record.get("modified_by", ""),
                "Modified Comments": record.get("modified_comments", ""),
                "Remarks": record.get("remarks", ""),
                "Payment Status": record.get("payment_status", "Not Paid")
            }
            reservations.append(reservation)
        return reservations
    except Exception as e:
        st.error(f"Error loading reservations: {e}")
        return []

def save_reservation_to_supabase(reservation):
    """Save a new reservation to Supabase."""
    try:
        supabase_reservation = {
            "booking_id": reservation["Booking ID"],
            "property_name": reservation["Property Name"],
            "room_no": reservation["Room No"],
            "guest_name": reservation["Guest Name"],
            "mobile_no": reservation["Mobile No"],
            "no_of_adults": reservation["No of Adults"],
            "no_of_children": reservation["No of Children"],
            "no_of_infants": reservation["No of Infants"],
            "total_pax": reservation["Total Pax"],
            "check_in": reservation["Check In"].strftime("%Y-%m-%d") if reservation["Check In"] else None,
            "check_out": reservation["Check Out"].strftime("%Y-%m-%d") if reservation["Check Out"] else None,
            "no_of_days": reservation["No of Days"],
            "tariff": reservation["Tariff"],
            "total_tariff": reservation["Total Tariff"],
            "advance_amount": reservation["Advance Amount"],
            "balance_amount": reservation["Balance Amount"],
            "advance_mop": reservation["Advance MOP"],
            "balance_mop": reservation["Balance MOP"],
            "mob": reservation["MOB"],
            "online_source": reservation["Online Source"],
            "invoice_no": reservation["Invoice No"],
            "enquiry_date": reservation["Enquiry Date"].strftime("%Y-%m-%d") if reservation["Enquiry Date"] else None,
            "booking_date": reservation["Booking Date"].strftime("%Y-%m-%d") if reservation["Booking Date"] else None,
            "room_type": reservation["Room Type"],
            "breakfast": reservation["Breakfast"],
            "plan_status": reservation["Booking Status"],
            "submitted_by": reservation["Submitted By"],
            "modified_by": reservation["Modified By"],
            "modified_comments": reservation["Modified Comments"],
            "remarks": reservation["Remarks"],
            "payment_status": reservation["Payment Status"]
        }
        response = supabase.table("reservations").insert(supabase_reservation).execute()
        if response.data:
            st.session_state.reservations = load_reservations_from_supabase()
            return True
        return False
    except Exception as e:
        st.error(f"Error saving reservation: {e}")
        return False

def update_reservation_in_supabase(booking_id, updated_reservation):
    """Update an existing reservation in Supabase."""
    try:
        supabase_reservation = {
            "booking_id": updated_reservation["Booking ID"],
            "property_name": updated_reservation["Property Name"],
            "room_no": updated_reservation["Room No"],
            "guest_name": updated_reservation["Guest Name"],
            "mobile_no": updated_reservation["Mobile No"],
            "no_of_adults": updated_reservation["No of Adults"],
            "no_of_children": updated_reservation["No of Children"],
            "no_of_infants": updated_reservation["No of Infants"],
            "total_pax": updated_reservation["Total Pax"],
            "check_in": updated_reservation["Check In"].strftime("%Y-%m-%d") if updated_reservation["Check In"] else None,
            "check_out": updated_reservation["Check Out"].strftime("%Y-%m-%d") if updated_reservation["Check Out"] else None,
            "no_of_days": updated_reservation["No of Days"],
            "tariff": updated_reservation["Tariff"],
            "total_tariff": updated_reservation["Total Tariff"],
            "advance_amount": updated_reservation["Advance Amount"],
            "balance_amount": updated_reservation["Balance Amount"],
            "advance_mop": updated_reservation["Advance MOP"],
            "balance_mop": updated_reservation["Balance MOP"],
            "mob": updated_reservation["MOB"],
            "online_sour...(truncated 27913 characters)...o_index, key=f"{form_key}_room")

        # Row 5: Total Tariff, Tariff (per day), Advance Amount, Advance MOP
        row5_col1, row5_col2, row5_col3, row5_col4 = st.columns(4)
        with row5_col1:
            total_tariff = st.number_input("Total Tariff", min_value=0.0, value=reservation["Total Tariff"], step=100.0, key=f"{form_key}_total_tariff")
        with row5_col2:
            tariff = total_tariff / max(1, no_of_days)
            st.text_input("Tariff (per day)", value=f"₹{tariff:.2f}", disabled=True, key=f"{form_key}_tariff", help="Total Tariff ÷ No of Days")
        with row5_col3:
            advance_amount = st.number_input("Advance Amount", min_value=0.0, value=reservation["Advance Amount"], step=100.0, key=f"{form_key}_advance")
        with row5_col4:
            advance_mop_options = ["Cash", "Card", "UPI", "Bank Transfer", "ClearTrip", "TIE Management", "Booking.com", "Pending", "Other"]
            advance_mop_index = advance_mop_options.index(reservation["Advance MOP"]) if reservation["Advance MOP"] in advance_mop_options else len(advance_mop_options) - 1
            advance_mop = st.selectbox("Advance MOP", advance_mop_options, index=advance_mop_index, key=f"{form_key}_advmop")
            if advance_mop == "Other":
                custom_advance_mop = st.text_input("Custom Advance MOP", value=reservation["Advance MOP"] if advance_mop_index == len(advance_mop_options) - 1 else "", key=f"{form_key}_custom_advmop")
            else:
                custom_advance_mop = None

        # Row 6: Balance Amount, Balance MOP
        row6_col1, row6_col2 = st.columns(2)
        with row6_col1:
            balance_amount = max(0, total_tariff - safe_float(advance_amount))
            st.text_input("Balance Amount", value=f"₹{balance_amount:.2f}", disabled=True, key=f"{form_key}_balance_amount", help="Total Tariff - Advance Amount")
        with row6_col2:
            balance_mop_options = ["Pending", "Cash", "Card", "UPI", "Bank Transfer", "Other"]
            balance_mop_index = balance_mop_options.index(reservation["Balance MOP"]) if reservation["Balance MOP"] in balance_mop_options else 0
            balance_mop = st.selectbox("Balance MOP", balance_mop_options, index=balance_mop_index, key=f"{form_key}_balmop")
            if balance_mop == "Other":
                custom_balance_mop = st.text_input("Custom Balance MOP", value=reservation["Balance MOP"] if balance_mop_index == len(balance_mop_options) - 1 else "", key=f"{form_key}_custom_balmop")
            else:
                custom_balance_mop = None

        # Row 7: Booking Date, Invoice No, Booking Status
        row7_col1, row7_col2, row7_col3 = st.columns(3)
        with row7_col1:
            booking_date = st.date_input("Booking Date", value=reservation["Booking Date"], key=f"{form_key}_booking")
        with row7_col2:
            invoice_no = st.text_input("Invoice No", value=reservation["Invoice No"], key=f"{form_key}_invoice")
        with row7_col3:
            booking_status_options = ["Confirmed", "Pending", "Cancelled", "Completed", "No Show"]
            booking_status_index = booking_status_options.index(reservation["Booking Status"]) if reservation["Booking Status"] in booking_status_options else 1
            booking_status = st.selectbox("Booking Status", booking_status_options, index=booking_status_index, key=f"{form_key}_status")

        # Row 8: Remarks
        row8_col1, = st.columns(1)
        with row8_col1:
            remarks = st.text_area("Remarks", value=reservation["Remarks"], key=f"{form_key}_remarks")

        # Row 9: Payment Status, Submitted By
        row9_col1, row9_col2 = st.columns(2)
        with row9_col1:
            payment_status_options = ["Fully Paid", "Partially Paid", "Not Paid"]
            payment_status_index = payment_status_options.index(reservation["Payment Status"]) if reservation["Payment Status"] in payment_status_options else 2
            payment_status = st.selectbox("Payment Status", payment_status_options, index=payment_status_index, key=f"{form_key}_payment_status")
        with row9_col2:
            submitted_by = st.text_input("Submitted By", value=reservation["Submitted By"], key=f"{form_key}_submitted_by", disabled=True)

        # Online Source (conditionally shown when MOB is Online)
        if mob == "Online":
            row10_col1, = st.columns(1)
            with row10_col1:
                online_source_options = ["Booking.com", "Agoda Prepaid", "Agoda Booking.com", "Expedia", "MMT", "Cleartrip", "Others"]
                online_source_index = online_source_options.index(reservation["Online Source"]) if reservation["Online Source"] in online_source_options else len(online_source_options) - 1
                online_source = st.selectbox("Online Source", online_source_options, index=online_source_index, key=f"{form_key}_online_source")
                if online_source == "Others":
                    custom_online_source = st.text_input("Custom Online Source", value=reservation["Online Source"] if online_source_index == len(online_source_options) - 1 else "", key=f"{form_key}_custom_online_source")
                else:
                    custom_online_source = None
        else:
            online_source = None
            custom_online_source = None

        # Row 10: Modified By, Modified Comments
        row10_col1, row10_col2 = st.columns(2)
        with row10_col1:
            modified_by = st.text_input("Modified By", value=st.session_state.get("username", ""), key=f"{form_key}_modified_by", disabled=True)
        with row10_col2:
            modified_comments = st.text_area("Modified Comments", value=reservation["Modified Comments"], key=f"{form_key}_modified_comments")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submitted = st.form_submit_button("💾 Save Reservation", use_container_width=True)
            if submitted:
                if not all([property_name, room_no, guest_name, mobile_no]):
                    st.error("❌ Please fill in all required fields")
                elif check_out < check_in:
                    st.error("❌ Check-out date must be on or after check-in")
                elif no_of_days < 0:
                    st.error("❌ Number of days cannot be negative")
                else:
                    mob_value = custom_mob if mob == "Others" else mob
                    is_duplicate, existing_booking_id = check_duplicate_guest(guest_name, mobile_no, room_no, exclude_booking_id=reservation["Booking ID"], mob=mob_value)
                    if is_duplicate:
                        st.error(f"❌ Guest already exists! Booking ID: {existing_booking_id}")
                    else:
                        updated_reservation = {
                            "Property Name": property_name,
                            "Room No": room_no,
                            "Guest Name": guest_name,
                            "Mobile No": mobile_no,
                            "No of Adults": safe_int(adults),
                            "No of Children": safe_int(children),
                            "No of Infants": safe_int(infants),
                            "Total Pax": total_pax,
                            "Check In": check_in,
                            "Check Out": check_out,
                            "No of Days": no_of_days,
                            "Tariff": safe_float(tariff),
                            "Total Tariff": safe_float(total_tariff),
                            "Advance Amount": safe_float(advance_amount),
                            "Balance Amount": balance_amount,
                            "Advance MOP": custom_advance_mop if advance_mop == "Other" else advance_mop,
                            "Balance MOP": custom_balance_mop if balance_mop == "Other" else balance_mop,
                            "MOB": mob_value,
                            "Online Source": custom_online_source if online_source == "Others" else online_source,
                            "Invoice No": invoice_no,
                            "Enquiry Date": enquiry_date,
                            "Booking Date": booking_date,
                            "Booking ID": reservation["Booking ID"],
                            "Room Type": custom_room_type if room_type == "Other" else room_type,
                            "Breakfast": breakfast,
                            "Booking Status": booking_status,
                            "Submitted By": reservation["Submitted By"],
                            "Modified By": st.session_state.get("username", ""),
                            "Modified Comments": modified_comments,
                            "Remarks": remarks,
                            "Payment Status": payment_status
                        }
                        if update_reservation_in_supabase(reservation["Booking ID"], updated_reservation):
                            st.session_state.reservations[edit_index] = updated_reservation
                            st.session_state.edit_mode = False
                            st.session_state.edit_index = None
                            st.success(f"✅ Reservation {reservation['Booking ID']} updated successfully!")
                            show_confirmation_dialog(reservation["Booking ID"], is_update=True)
                        else:
                            st.error("❌ Failed to update reservation")
        with col_btn2:
            if st.session_state.role == "Management":
                deleted = st.form_submit_button("🗑️ Delete Reservation", use_container_width=True)
                if deleted:
                    if delete_reservation_in_supabase(reservation["Booking ID"]):
                        st.session_state.reservations.pop(edit_index)
                        st.session_state.edit_mode = False
                        st.session_state.edit_index = None
                        st.success(f"🗑️ Reservation {reservation['Booking ID']} deleted successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete reservation")
    except Exception as e:
        st.error(f"Error rendering edit form: {e}")

def show_analytics():
    """Display analytics dashboard for Management users."""
    if st.session_state.role != "Management":
        st.error("❌ Access Denied: Analytics is available only for Management users.")
        return

    st.header("📊 Analytics Dashboard")
    if not st.session_state.reservations:
        st.info("No reservations available for analysis.")
        return

    df = pd.DataFrame(st.session_state.reservations)
    
    st.subheader("Filters")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        start_date = st.date_input("Start Date", value=None, key="analytics_filter_start_date", help="Filter by Check In date range (optional)")
    with col2:
        end_date = st.date_input("End Date", value=None, key="analytics_filter_end_date", help="Filter by Check In date range (optional)")
    with col3:
        filter_status = st.selectbox("Filter by Status", ["All", "Confirmed", "Pending", "Cancelled", "Completed", "No Show"], key="analytics_filter_status")
    with col4:
        filter_check_in_date = st.date_input("Check-in Date", value=None, key="analytics_filter_check_in_date")
    with col5:
        filter_check_out_date = st.date_input("Check-out Date", value=None, key="analytics_filter_check_out_date")
    with col6:
        filter_property = st.selectbox("Filter by Property", ["All"] + sorted(df["Property Name"].unique()), key="analytics_filter_property")

    filtered_df = display_filtered_analysis(df, start_date, end_date, view_mode=False)
    
    if filter_status != "All":
        filtered_df = filtered_df[filtered_df["Booking Status"] == filter_status]
    if filter_check_in_date:
        filtered_df = filtered_df[filtered_df["Check In"] == filter_check_in_date]
    if filter_check_out_date:
        filtered_df = filtered_df[filtered_df["Check Out"] == filter_check_out_date]
    if filter_property != "All":
        filtered_df = filtered_df[filtered_df["Property Name"] == filter_property]

    if filtered_df.empty:
        st.warning("No reservations match the selected filters.")
        return

    st.subheader("Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        property_counts = filtered_df["Property Name"].value_counts().reset_index()
        property_counts.columns = ["Property Name", "Reservation Count"]
        fig_pie = px.pie(
            property_counts,
            values="Reservation Count",
            names="Property Name",
            title="Reservation Distribution by Property",
            height=400
        )
        st.plotly_chart(fig_pie, use_container_width=True, key="analytics_pie_chart")
    with col2:
        revenue_by_property = filtered_df.groupby("Property Name")["Total Tariff"].sum().reset_index()
        fig_bar = px.bar(
            revenue_by_property,
            x="Property Name",
            y="Total Tariff",
            title="Total Revenue by Property",
            height=400,
            labels={"Total Tariff": "Revenue (₹)"}
        )
        st.plotly_chart(fig_bar, use_container_width=True, key="analytics_bar_chart")
