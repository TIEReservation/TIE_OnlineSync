import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from supabase import create_client, Client

# ========================================
# INITIALIZATION
# ========================================
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

# Initialize session state
if "reservations" not in st.session_state:
    st.session_state.reservations = []
if "role" not in st.session_state:
    st.session_state.role = "User"  # Change to "Management" for admin
if "username" not in st.session_state:
    st.session_state.username = "User"

# Load reservations on startup
if not st.session_state.reservations:
    st.session_state.reservations = []

# ========================================
# HELPER FUNCTIONS
# ========================================
def load_property_room_map():
    return {
        "Le Poshe Beachview": {
            "Double Room": ["101", "102", "202", "203", "204"],
            "Standard Room": ["201"],
            "Deluex Double Room Seaview": ["301", "302", "303", "304"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Millionaire Resort": {
            "Double Room": ["101", "102", "103", "105"],
            "Deluex Double Room with Balcony": ["205", "304", "305"],
            "Deluex Triple Room with Balcony": ["201", "202", "203", "204", "301", "302", "303"],
            "Deluex Family Room with Balcony": ["206", "207", "208", "306", "307", "308"],
            "Deluex Triple Room": ["402"],
            "Deluex Family Room": ["401"],
            "Day Use": ["Day Use 1", "Day Use 2", "Day Use 3", "Day Use 5"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Le Poshe Luxury": {
            "2BHA Appartment": ["101&102", "101", "102"],
            "2BHA Appartment with Balcony": ["201&202", "201", "202", "301&302", "301", "302", "401&402", "401", "402"],
            "3BHA Appartment": ["203to205", "203", "204", "205", "303to305", "303", "304", "305", "403to405", "403", "404", "405"],
            "Double Room with Private Terrace": ["501"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Le Poshe Suite": {
            "2BHA Appartment": ["601&602", "601", "602", "603", "604", "703", "704"],
            "2BHA Appartment with Balcony": ["701&702", "701", "702"],
            "Double Room with Terrace": ["801"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Paradise Residency": {
            "Double Room": ["101", "102", "103", "301", "304"],
            "Family Room": ["201", "203"],
            "Triple Room": ["202", "303"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Paradise Luxury": {
            "3BHA Appartment": ["101to103", "101", "102", "103", "201to203", "201", "202", "203"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Villa Heritage": {
            "Double Room": ["101", "102", "103"],
            "4BHA Appartment": ["201to203&301", "201", "202", "203", "301"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Le Pondy Beach Side": {
            "Villa": ["101to104", "101", "102", "103", "104"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Le Royce Villa": {
            "Villa": ["101to102&201to202", "101", "102", "202", "202"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Tamara Luxury": {
            "3BHA": ["101to103", "101", "102", "103", "104to106", "104", "105", "106", "201to203", "201", "202", "203", "204to206", "204", "205", "206", "301to303", "301", "302", "303", "304to306", "304", "305", "306"],
            "4BHA": ["401to404", "401", "402", "403", "404"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Antilia": {
            "Deluex Suite Room": ["101"],
            "Deluex Double Room": ["203", "204", "303", "304"],
            "Family Room": ["201", "202", "301", "302"],
            "Deluex suite Room with Tarrace": ["404"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Tamara Suite": {
            "Two Bedroom apartment": ["101&102"],
            "Deluxe Apartment": ["103&104"],
            "Deluxe Double Room": ["203", "204", "205"],
            "Deluxe Triple Room": ["201", "202"],
            "Deluxe Family Room": ["206"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Le Park Resort": {
            "Villa with Swimming Pool View": ["555&666", "555", "666"],
            "Villa with Garden View": ["111&222", "111", "222"],
            "Family Retreate Villa": ["333&444", "333", "444"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Villa Shakti": {
            "2BHA Studio Room": ["101&102"],
            "2BHA with Balcony": ["202&203", "302&303"],
            "Family Suite": ["201"],
            "Family Room": ["301"],
            "Terrace Room": ["401"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Eden Beach Resort": {
            "Double Room": ["101", "102"],
            "Deluex Room": ["103", "202"],
            "Triple Room": ["201"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        }
    }

def generate_booking_id():
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
    if check_in and check_out and check_out >= check_in:
        delta = check_out - check_in
        return max(1, delta.days)
    return 1

def safe_int(value, default=0):
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def update_no_of_days(form_key):
    try:
        check_in = st.session_state.get(f"{form_key}_checkin")
        check_out = st.session_state.get(f"{form_key}_checkout")
        if check_in and check_out:
            st.session_state[f"{form_key}_no_of_days"] = calculate_days(check_in, check_out)
        else:
            st.session_state[f"{form_key}_no_of_days"] = 1
    except:
        st.session_state[f"{form_key}_no_of_days"] = 1

def update_tariff_per_day(form_key):
    try:
        total = st.session_state.get(f"{form_key}_total_tariff", 0.0)
        days = st.session_state.get(f"{form_key}_no_of_days", 1)
        st.session_state[f"{form_key}_tariff_per_day"] = total / max(1, days)
    except:
        st.session_state[f"{form_key}_tariff_per_day"] = 0.0

def load_reservations_from_supabase():
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
            "online_source": updated_reservation["Online Source"],
            "invoice_no": updated_reservation["Invoice No"],
            "enquiry_date": updated_reservation["Enquiry Date"].strftime("%Y-%m-%d") if updated_reservation["Enquiry Date"] else None,
            "booking_date": updated_reservation["Booking Date"].strftime("%Y-%m-%d") if updated_reservation["Booking Date"] else None,
            "room_type": updated_reservation["Room Type"],
            "breakfast": updated_reservation["Breakfast"],
            "plan_status": updated_reservation["Booking Status"],
            "submitted_by": updated_reservation["Submitted By"],
            "modified_by": updated_reservation["Modified By"],
            "modified_comments": updated_reservation["Modified Comments"],
            "remarks": updated_reservation["Remarks"],
            "payment_status": updated_reservation["Payment Status"]
        }
        response = supabase.table("reservations").update(supabase_reservation).eq("booking_id", booking_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error updating reservation: {e}")
        return False

def delete_reservation_in_supabase(booking_id):
    try:
        response = supabase.table("reservations").delete().eq("booking_id", booking_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error deleting reservation: {e}")
        return False

@st.dialog("Reservation Confirmation")
def show_confirmation_dialog(booking_id, is_update=False):
    message = "Reservation Updated!" if is_update else "Reservation Confirmed!"
    st.markdown(f"**{message}**\n\nBooking ID: {booking_id}")
    if st.button("Confirm", use_container_width=True):
        st.rerun()

def display_filtered_analysis(df, start_date=None, end_date=None, view_mode=False):
    filtered_df = df.copy()
    filtered_df = filtered_df[filtered_df["Check In"].notnull()]
    
    if start_date and end_date:
        if end_date < start_date:
            st.error("End date must be on or after start date")
            return filtered_df
        filtered_df = filtered_df[(filtered_df["Check In"] >= start_date) & (filtered_df["Check In"] <= end_date)]
    
    if filtered_df.empty:
        st.warning("No reservations found for the selected filters.")
        return filtered_df
    
    if not view_mode:
        st.subheader("Overall Summary")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Reservations", len(filtered_df))
        with col2:
            total_revenue = filtered_df["Total Tariff"].sum()
            st.metric("Total Revenue", f"₹{total_revenue:,.2f}")
        with col3:
            st.metric("Average Tariff", f"₹{filtered_df['Tariff'].mean():,.2f}" if not filtered_df.empty else "₹0.00")
        with col4:
            st.metric("Average Stay", f"{filtered_df['No of Days'].mean():.1f} days" if not filtered_df.empty else "0.0 days")
        col5, col6 = st.columns(2)
        with col5:
            total_collected = filtered_df["Advance Amount"].sum() + filtered_df[filtered_df["Booking Status"] == "Completed"]["Balance Amount"].sum()
            st.metric("Total Revenue Collected", f"₹{total_collected:,.2f}")
        with col6:
            balance_pending = filtered_df[filtered_df["Booking Status"] != "Completed"]["Balance Amount"].sum()
            st.metric("Balance Pending", f"₹{balance_pending:,.2f}")

        st.subheader("Property-wise Reservation Details")
        for property in sorted(filtered_df["Property Name"].unique()):
            with st.expander(f"{property} Reservations"):
                property_df = filtered_df[filtered_df["Property Name"] == property]
                st.write(f"**Total Reservations**: {len(property_df)}")
                st.write(f"**Total Revenue**: ₹{property_df['Total Tariff'].sum():,.2f}")
                st.write(f"**Total Collected**: ₹{(property_df['Advance Amount'].sum() + property_df[property_df['Booking Status'] == 'Completed']['Balance Amount'].sum()):,.2f}")
                st.write(f"**Balance Pending**: ₹{property_df[property_df['Booking Status'] != 'Completed']['Balance Amount'].sum():,.2f}")
                st.write(f"**Avg Tariff**: ₹{property_df['Tariff'].mean():,.2f}" if not property_df.empty else "₹0.00")
                st.write(f"**Avg Stay**: {property_df['No of Days'].mean():.1f} days" if not property_df.empty else "0.0 days")
                st.dataframe(
                    property_df[["Booking ID", "Guest Name", "Room No", "Check In", "Check Out", "Total Tariff", "Booking Status", "MOB", "Payment Status", "Remarks"]],
                    use_container_width=True
                )
    
    return filtered_df

# ========================================
# FORMS
# ========================================
def show_new_reservation_form():
    st.header("Direct Reservations")
    form_key = "new_reservation"
    property_room_map = load_property_room_map()

    if f"{form_key}_property" not in st.session_state:
        st.session_state[f"{form_key}_property"] = sorted(property_room_map.keys())[0]
    if f"{form_key}_no_of_days" not in st.session_state:
        st.session_state[f"{form_key}_no_of_days"] = 1

    # Row 1
    col1, col2, col3 = st.columns(3)
    with col1:
        property_name = st.selectbox("Property Name", sorted(property_room_map.keys()),
                                    key=f"{form_key}_property",
                                    on_change=lambda: st.session_state.update({f"{form_key}_room_type": ""}))
    with col2:
        guest_name = st.text_input("Guest Name", key=f"{form_key}_guest")
    with col3:
        mobile_no = st.text_input("Mobile No", key=f"{form_key}_mobile")

    # Row 2
    row2_col1, row2_col2, row2_col3, row2_col4 = st.columns(4)
    with row2_col1:
        enquiry_date = st.date_input("Enquiry Date", value=date.today(), key=f"{form_key}_enquiry")
    with row2_col2:
        check_in = st.date_input("Check In", value=date.today(), key=f"{form_key}_checkin",
                                on_change=lambda: update_no_of_days(form_key))
    with row2_col3:
        check_out = st.date_input("Check Out", value=date.today() + timedelta(days=1), key=f"{form_key}_checkout",
                                 on_change=lambda: update_no_of_days(form_key))
    with row2_col4:
        no_of_days = st.session_state[f"{form_key}_no_of_days"]
        st.text_input("No of Days", value=str(no_of_days), disabled=True, key=f"{form_key}_days_display")

    # Row 3
    row3_col1, row3_col2, row3_col3, row3_col4 = st.columns(4)
    with row3_col1:
        adults = st.number_input("Adults", min_value=0, value=1, key=f"{form_key}_adults")
    with row3_col2:
        children = st.number_input("Children", min_value=0, value=0, key=f"{form_key}_children")
    with row3_col3:
        infants = st.number_input("Infants", min_value=0, value=0, key=f"{form_key}_infants")
    with row3_col4:
        breakfast = st.selectbox("Breakfast", ["CP", "EP"], key=f"{form_key}_breakfast")

    # Row 4
    row4_col1, row4_col2, row4_col3, row4_col4 = st.columns(4)
    with row4_col1:
        total_pax = safe_int(adults) + safe_int(children) + safe_int(infants)
        st.text_input("Total Pax", value=str(total_pax), disabled=True)
    with row4_col2:
        mob = st.selectbox("MOB", ["Direct", "Online", "Agent", "Walk-in", "Phone", "Website", "Booking-Drt", "Social Media", "Stay-back", "TIE-Group", "Others"],
                          key=f"{form_key}_mob")
        custom_mob = st.text_input("Custom MOB", key=f"{form_key}_custom_mob") if mob == "Others" else None
    with row4_col3:
        room_types = list(property_room_map[property_name].keys())
        room_type = st.selectbox("Room Type", room_types, key=f"{form_key}_room_type")
    with row4_col4:
        if room_type == "Others":
            room_no = st.text_input("Room No", placeholder="Enter custom", key=f"{form_key}_room_no")
        else:
            suggestions = property_room_map[property_name].get(room_type, [])
            room_no = st.text_input("Room No", placeholder="Enter or pick", key=f"{form_key}_room_no")
            if suggestions:
                st.caption(f"Suggestions: {', '.join(suggestions)}")

    # Row 5
    row5_col1, row5_col2, row5_col3, row5_col4 = st.columns(4)
    with row5_col1:
        total_tariff = st.number_input("Total Tariff", min_value=0.0, step=100.0, key=f"{form_key}_total_tariff",
                                      on_change=lambda: update_tariff_per_day(form_key))
    with row5_col2:
        tariff_per_day = st.session_state.get(f"{form_key}_tariff_per_day", 0.0)
        st.text_input("Tariff (per day)", value=f"₹{tariff_per_day:.2f}", disabled=True)
    with row5_col3:
        advance_amount = st.number_input("Advance", min_value=0.0, step=100.0, key=f"{form_key}_advance")
    with row5_col4:
        advance_mop = st.selectbox("Advance MOP", [" ", "Cash", "Card", "UPI", "Bank Transfer", "ClearTrip", "TIE Management", "Booking.com", "Pending", "Other"],
                                  key=f"{form_key}_advmop")
        custom_advance_mop = st.text_input("Custom MOP", key=f"{form_key}_custom_advmop") if advance_mop == "Other" else None

    # Continue with rest of form (simplified for brevity)
    # ... [rest of your form fields]

    if st.button("Save Reservation", use_container_width=True):
        # Validation and save logic
        pass

# ========================================
# MAIN APP
# ========================================
def main():
    st.set_page_config(page_title="Direct Reservations", layout="wide")
    st.title("Direct Reservation System")

    # Load reservations
    if not st.session_state.reservations:
        with st.spinner("Loading reservations..."):
            st.session_state.reservations = load_reservations_from_supabase()

    # Sidebar
    page = st.sidebar.radio("Navigation", ["New", "View", "Edit", "Analytics"])

    if page == "New":
        show_new_reservation_form()
    elif page == "View":
        show_reservations()
    elif page == "Edit":
        show_edit_reservations()
    elif page == "Analytics":
        show_analytics()

if __name__ == "__main__":
    main()
