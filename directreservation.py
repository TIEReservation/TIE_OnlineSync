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
        "Le Poshe Beach view": {
            "Double Room": ["101", "102", "202", "203", "204"],
            "Standard Room": ["201"],
            "Deluex Double Room Seaview": ["301", "302", "303", "304"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Millionaire Resort": {
            "Double Room": ["101", "102", "103", "105"],
            "Deluex Double Room with Balcony": ["205", "304", "305"],
            "Deluex Triple Room with Balcony": ["201", "202", "203", "204", "301", "302", "303"],
            "Deluex Family Room with Balcony": ["206", "207", "208", "306", "307", "308"],
            "Deluex Triple Room": ["402"],
            "Deluex Family Room": ["401"],
            "Day Use" : ["Day Use 1", "Day Use 2", "Day Use 3", "Day Use 5"],
            "No Show" : ["No Show"]
        },
        "Le Poshe Luxury": {
            "2BHA Appartment": ["101&102", "101", "102"],
            "2BHA Appartment with Balcony": ["201&202", "201", "202", "301&302", "301", "302", "401&402", "401", "402"],
            "3BHA Appartment": ["203to205", "203", "204", "205", "303to305", "303", "304", "305", "403to405", "403", "404", "405"],
            "Double Room with Private Terrace": ["501"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "Le Poshe Suite": {
            "2BHA Appartment": ["601&602", "601", "602", "603", "604", "703", "704"],
            "2BHA Appartment with Balcony": ["701&702", "701", "702"],
            "Double Room with Terrace": ["801"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Paradise Residency": {
            "Double Room": ["101", "102", "103", "301", "302", "304"],
            "Family Room": ["201", "203"],
            "Triple Room": ["202", "303"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Paradise Luxury": {
            "3BHA Appartment": ["101to103", "101", "102", "103", "201to203", "201", "202", "203"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Villa Heritage": {
            "Double Room": ["101", "102", "103"],
            "4BHA Appartment": ["201to203&301", "201", "202", "203", "301"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "Le Pondy Beach Side": {
            "Villa": ["101to104", "101", "102", "103", "104"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "Le Royce Villa": {
            "Villa": ["101to102&201to202", "101", "102", "201", "202"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Tamara Luxury": {
            "3BHA": ["101to103", "101", "102", "103", "201to203", "201", "202", "203"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        }
    }

@st.cache_data
def load_reservations_from_supabase():
    """Load all reservations from Supabase without limit."""
    try:
        all_data = []
        offset = 0
        limit = 1000  # Supabase default max rows per request
        while True:
            response = supabase.table("reservations").select("*").range(offset, offset + limit - 1).execute()
            data = response.data if response.data else []
            all_data.extend(data)
            if len(data) < limit:  # If fewer rows than limit, we've reached the end
                break
            offset += limit
        if not all_data:
            st.warning("No reservations found in the database.")
        return all_data
    except Exception as e:
        st.error(f"Error loading reservations: {e}")
        return []

def save_reservation_to_supabase(reservation):
    """Save a new reservation to Supabase."""
    try:
        response = supabase.table("reservations").insert(reservation).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error saving reservation: {e}")
        return None

def update_reservation_in_supabase(booking_id, updated_reservation):
    """Update an existing reservation in Supabase."""
    try:
        response = supabase.table("reservations").update(updated_reservation).eq("Booking ID", booking_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error updating reservation {booking_id}: {e}")
        return None

def delete_reservation_in_supabase(booking_id):
    """Delete a reservation from Supabase."""
    try:
        response = supabase.table("reservations").delete().eq("Booking ID", booking_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error deleting reservation {booking_id}: {e}")
        return False

def display_filtered_analysis(df, start_date, end_date, view_mode=True):
    """Filter and display reservation analysis based on date range."""
    if start_date and end_date:
        df = df[(pd.to_datetime(df["Check In"]).dt.date >= start_date) & (pd.to_datetime(df["Check Out"]).dt.date <= end_date)]
    elif start_date:
        df = df[pd.to_datetime(df["Check In"]).dt.date >= start_date]
    elif end_date:
        df = df[pd.to_datetime(df["Check Out"]).dt.date <= end_date]
    if view_mode:
        st.dataframe(df)
    return df

def show_new_reservation_form():
    """Display form to create a new reservation."""
    st.header("📋 New Reservation Form")
    with st.form("new_reservation_form"):
        col1, col2 = st.columns(2)
        with col1:
            property_name = st.selectbox("Property Name", list(load_property_room_map().keys()))
            room_types = list(load_property_room_map()[property_name].keys())
            room_type = st.selectbox("Room Type", room_types)
            room_numbers = load_property_room_map()[property_name][room_type]
            room_no = st.selectbox("Room Number", room_numbers)
            check_in = st.date_input("Check In", value=date.today())
            check_out = st.date_input("Check Out", value=date.today() + timedelta(days=1))
            no_of_adults = st.number_input("No. of Adults", min_value=0, value=1)
            no_of_children = st.number_input("No. of Children", min_value=0, value=0)
            no_of_infant = st.number_input("No. of Infants", min_value=0, value=0)
            total_pax = no_of_adults + no_of_children + no_of_infant
            st.write(f"Total Pax: {total_pax}")
        with col2:
            guest_name = st.text_input("Guest Name")
            guest_phone = st.text_input("Guest Phone")
            booking_source = st.selectbox("Booking Source", ["Direct", "OTA", "Phone"])
            rate_plan = st.text_input("Rate Plan")
            booking_status = st.selectbox("Booking Status", ["Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"])
            payment_status = st.selectbox("Payment Status", ["Paid", "Pending", "Partial"])
            total_tariff = st.number_input("Total Tariff (₹)", min_value=0.0, value=0.0)
            advance_payment = st.number_input("Advance Payment (₹)", min_value=0.0, value=0.0)
            balance_due = total_tariff - advance_payment
            st.write(f"Balance Due: ₹{balance_due}")
            remarks = st.text_area("Remarks")
            submitted_by = st.text_input("Submitted By", value="Unknown")

        if st.form_submit_button("Save Reservation"):
            new_reservation = {
                "Property Name": property_name,
                "Room Type": room_type,
                "Room No": room_no,
                "Check In": str(check_in),
                "Check Out": str(check_out),
                "No. of Adults": no_of_adults,
                "No. of Children": no_of_children,
                "No. of Infant": no_of_infant,
                "Total Pax": total_pax,
                "Guest Name": guest_name,
                "Guest Phone": guest_phone,
                "Booking Source": booking_source,
                "Rate Plan": rate_plan,
                "Booking Status": booking_status,
                "Payment Status": payment_status,
                "Total Tariff": total_tariff,
                "Advance Payment": advance_payment,
                "Balance Due": balance_due,
                "Remarks": remarks,
                "Submitted By": submitted_by,
                "Booking ID": f"RES{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
            if save_reservation_to_supabase(new_reservation):
                st.session_state.reservations.append(new_reservation)
                st.success(f"✅ Reservation {new_reservation['Booking ID']} saved successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to save reservation")

def show_reservations():
    """Display list of existing reservations."""
    st.header("📋 View Reservations")
    if not st.session_state.reservations:
        st.info("No reservations available.")
        return
    df = pd.DataFrame(st.session_state.reservations)
    st.dataframe(df)

def show_edit_reservations():
    """Display and edit existing reservations."""
    st.header("✏️ Edit Reservations")
    if not st.session_state.reservations:
        st.info("No reservations available to edit.")
        return
    df = pd.DataFrame(st.session_state.reservations)
    selected_booking_id = st.selectbox("Select Booking ID to Edit", df["Booking ID"])
    edit_index = df.index[df["Booking ID"] == selected_booking_id][0]
    if st.button("Edit Reservation"):
        st.session_state.edit_mode = True
        st.session_state.edit_index = edit_index
        st.rerun()

    if st.session_state.edit_mode and st.session_state.edit_index == edit_index:
        reservation = st.session_state.reservations[edit_index]
        with st.form("edit_reservation_form"):
            col1, col2 = st.columns(2)
            with col1:
                property_name = st.selectbox("Property Name", list(load_property_room_map().keys()), index=list(load_property_room_map().keys()).index(reservation["Property Name"]))
                room_types = list(load_property_room_map()[property_name].keys())
                room_type = st.selectbox("Room Type", room_types, index=room_types.index(reservation["Room Type"]))
                room_numbers = load_property_room_map()[property_name][room_type]
                room_no = st.selectbox("Room Number", room_numbers, index=room_numbers.index(reservation["Room No"]))
                check_in = st.date_input("Check In", value=datetime.strptime(reservation["Check In"], "%Y-%m-%d").date())
                check_out = st.date_input("Check Out", value=datetime.strptime(reservation["Check Out"], "%Y-%m-%d").date())
                no_of_adults = st.number_input("No. of Adults", min_value=0, value=reservation["No. of Adults"])
                no_of_children = st.number_input("No. of Children", min_value=0, value=reservation["No. of Children"])
                no_of_infant = st.number_input("No. of Infants", min_value=0, value=reservation["No. of Infant"])
                total_pax = no_of_adults + no_of_children + no_of_infant
                st.write(f"Total Pax: {total_pax}")
            with col2:
                guest_name = st.text_input("Guest Name", value=reservation["Guest Name"])
                guest_phone = st.text_input("Guest Phone", value=reservation["Guest Phone"])
                booking_source = st.selectbox("Booking Source", ["Direct", "OTA", "Phone"], index=["Direct", "OTA", "Phone"].index(reservation["Booking Source"]))
                rate_plan = st.text_input("Rate Plan", value=reservation["Rate Plan"])
                booking_status = st.selectbox("Booking Status", ["Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"], index=["Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"].index(reservation["Booking Status"]))
                payment_status = st.selectbox("Payment Status", ["Paid", "Pending", "Partial"], index=["Paid", "Pending", "Partial"].index(reservation["Payment Status"]))
                total_tariff = st.number_input("Total Tariff (₹)", min_value=0.0, value=reservation["Total Tariff"])
                advance_payment = st.number_input("Advance Payment (₹)", min_value=0.0, value=reservation["Advance Payment"])
                balance_due = total_tariff - advance_payment
                st.write(f"Balance Due: ₹{balance_due}")
                remarks = st.text_area("Remarks", value=reservation["Remarks"])
                modified_by = st.text_input("Modified By", value="Unknown")

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.form_submit_button("Update Reservation"):
                    updated_reservation = {
                        "Property Name": property_name,
                        "Room Type": room_type,
                        "Room No": room_no,
                        "Check In": str(check_in),
                        "Check Out": str(check_out),
                        "No. of Adults": no_of_adults,
                        "No. of Children": no_of_children,
                        "No. of Infant": no_of_infant,
                        "Total Pax": total_pax,
                        "Guest Name": guest_name,
                        "Guest Phone": guest_phone,
                        "Booking Source": booking_source,
                        "Rate Plan": rate_plan,
                        "Booking Status": booking_status,
                        "Payment Status": payment_status,
                        "Total Tariff": total_tariff,
                        "Advance Payment": advance_payment,
                        "Balance Due": balance_due,
                        "Remarks": remarks,
                        "Modified By": modified_by
                    }
                    if update_reservation_in_supabase(reservation["Booking ID"], updated_reservation):
                        st.session_state.reservations[edit_index] = {**reservation, **updated_reservation}
                        st.session_state.edit_mode = False
                        st.session_state.edit_index = None
                        st.success(f"✅ Reservation {reservation['Booking ID']} updated successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update reservation")
            with col_btn2:
                if st.session_state.get('role') == "Management":
                    if st.button("Delete Reservation", use_container_width=True):
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
        filter_status = st.selectbox("Filter by Status", ["All", "Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"], key="analytics_filter_status")
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
