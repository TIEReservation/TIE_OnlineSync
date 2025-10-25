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

def show_new_reservation_form():
    """Display the new reservation form with submitted_by default from logged-in user."""
    st.subheader("New Reservation Form")
    
    submitted_by = st.session_state.username if 'username' in st.session_state else "Unknown"
    st.write(f"Submitted By: {submitted_by}")

    with st.form("new_reservation_form"):
        property_name = st.selectbox("Property Name", list(load_property_room_map().keys()))
        room_type = st.selectbox("Room Type", list(load_property_room_map()[property_name].keys()))
        room_no = st.selectbox("Room No", load_property_room_map()[property_name][room_type])
        check_in = st.date_input("Check In", value=date.today())
        check_out = st.date_input("Check Out", value=date.today() + timedelta(days=1))
        no_of_adults = st.number_input("No of Adults", min_value=0, value=1, step=1)
        no_of_children = st.number_input("No of Children", min_value=0, value=0, step=1)
        no_of_infant = st.number_input("No of Infant", min_value=0, value=0, step=1)
        total_pax = no_of_adults + no_of_children + no_of_infant
        st.write(f"Total Pax: {total_pax}")
        guest_name = st.text_input("Guest Name")
        guest_phone = st.text_input("Guest Phone")
        total_tariff = st.number_input("Total Tariff", min_value=0.0, value=0.0, step=100.0)
        advance_amount = st.number_input("Advance Amount", min_value=0.0, value=0.0, step=100.0)
        balance_amount = total_tariff - advance_amount if total_tariff >= advance_amount else 0.0
        st.write(f"Balance Amount: {balance_amount:.2f}")
        advance_mop = st.selectbox("Advance MOP", ["Cash", "UPI", "Card", "Other"])
        if advance_mop == "Other":
            custom_advance_mop = st.text_input("Custom Advance MOP")
        else:
            custom_advance_mop = ""
        balance_mop = st.selectbox("Balance MOP", ["Cash", "UPI", "Card", "Other"])
        if balance_mop == "Other":
            custom_balance_mop = st.text_input("Custom Balance MOP")
        else:
            custom_balance_mop = ""
        mob_value = st.text_input("MOB")
        online_source = st.selectbox("Online Source", ["Booking.com", "Agoda", "Expedia", "Others"])
        if online_source == "Others":
            custom_online_source = st.text_input("Custom Online Source")
        else:
            custom_online_source = ""
        invoice_no = st.text_input("Invoice No")
        enquiry_date = st.date_input("Enquiry Date", value=date.today())
        booking_date = st.date_input("Booking Date", value=date.today())
        breakfast = st.checkbox("Breakfast Included")
        booking_status = st.selectbox("Booking Status", ["Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"])
        payment_status = st.selectbox("Payment Status", ["Not Paid", "Fully Paid", "Partially Paid"])
        remarks = st.text_area("Remarks")
        modified_by = st.session_state.username if 'username' in st.session_state else "Unknown"
        st.write(f"Modified By: {modified_by}")
        modified_comments = st.text_area("Modified Comments")

        if st.form_submit_button("💾 Save Reservation"):
            reservation = {
                "Property Name": property_name,
                "Guest Name": guest_name,
                "Guest Phone": guest_phone,
                "Check In": str(check_in),
                "Check Out": str(check_out),
                "No of Adults": no_of_adults,
                "No of Children": no_of_children,
                "No of Infant": no_of_infant,
                "Total Pax": total_pax,
                "Room No": room_no,
                "Total Tariff": total_tariff,
                "Advance Amount": advance_amount,
                "Balance Amount": balance_amount,
                "Advance MOP": custom_advance_mop if advance_mop == "Other" else advance_mop,
                "Balance MOP": custom_balance_mop if balance_mop == "Other" else balance_mop,
                "MOB": mob_value,
                "Online Source": custom_online_source if online_source == "Others" else online_source,
                "Invoice No": invoice_no,
                "Enquiry Date": str(enquiry_date),
                "Booking Date": str(booking_date),
                "Room Type": room_type,
                "Breakfast": breakfast,
                "Booking Status": booking_status,
                "Submitted By": submitted_by,
                "Modified By": modified_by,
                "Modified Comments": modified_comments,
                "Remarks": remarks,
                "Payment Status": payment_status
            }
            try:
                response = supabase.table("reservations").insert(reservation).execute()
                if response.data:
                    st.session_state.reservations.append(reservation)
                    st.success(f"✅ Reservation saved successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to save reservation.")
            except Exception as e:
                st.error(f"❌ Error saving reservation: {e}")

def show_reservations():
    """Display the reservations table with filters."""
    st.subheader("View Reservations")
    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase()
    if not st.session_state.reservations:
        st.info("No reservations available.")
        return
    df = pd.DataFrame(st.session_state.reservations)
   
    st.subheader("Filters")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        start_date = st.date_input("Start Date", value=None, key="filter_start_date")
    with col2:
        end_date = st.date_input("End Date", value=None, key="filter_end_date")
    with col3:
        filter_status = st.selectbox("Filter by Status", ["All", "Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"], key="filter_status")
    with col4:
        filter_property = st.selectbox("Filter by Property", ["All"] + sorted(df["Property Name"].unique()), key="filter_property")
   
    filtered_df = df.copy()
    if start_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["Check In"]) >= pd.to_datetime(start_date)]
    if end_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["Check In"]) <= pd.to_datetime(end_date)]
    if filter_status != "All":
        filtered_df = filtered_df[filtered_df["Booking Status"] == filter_status]
    if filter_property != "All":
        filtered_df = filtered_df[filtered_df["Property Name"] == filter_property]
   
    if filtered_df.empty:
        st.warning("No reservations match the selected filters.")
        return

    st.dataframe(filtered_df)

def show_edit_reservations():
    """Display and edit existing reservations."""
    st.subheader("Edit Reservations")
    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase()
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
        modified_by = st.session_state.username if 'username' in st.session_state else "Unknown"
        st.write(f"Modified By: {modified_by}")

        with st.form("edit_reservation_form"):
            property_name = st.selectbox("Property Name", list(load_property_room_map().keys()), index=list(load_property_room_map().keys()).index(reservation["Property Name"]) if reservation["Property Name"] in load_property_room_map() else 0)
            room_type = st.selectbox("Room Type", list(load_property_room_map().get(property_name, {}).keys()), index=list(load_property_room_map().get(property_name, {}).keys()).index(reservation["Room Type"]) if reservation["Room Type"] in load_property_room_map().get(property_name, {}) else 0)
            room_no = st.selectbox("Room No", load_property_room_map().get(property_name, {}).get(room_type, []), index=load_property_room_map().get(property_name, {}).get(room_type, []).index(reservation["Room No"]) if reservation["Room No"] in load_property_room_map().get(property_name, {}).get(room_type, []) else 0)
            check_in = st.date_input("Check In", value=date.fromisoformat(reservation["Check In"]) if reservation.get("Check In") else date.today())
            check_out = st.date_input("Check Out", value=date.fromisoformat(reservation["Check Out"]) if reservation.get("Check Out") else date.today())
            no_of_adults = st.number_input("No of Adults", min_value=0, value=reservation.get("No of Adults", 1))
            no_of_children = st.number_input("No of Children", min_value=0, value=reservation.get("No of Children", 0))
            no_of_infant = st.number_input("No of Infant", min_value=0, value=reservation.get("No of Infant", 0))
            total_pax = no_of_adults + no_of_children + no_of_infant
            st.write(f"Total Pax: {total_pax}")
            guest_name = st.text_input("Guest Name", value=reservation.get("Guest Name", ""))
            guest_phone = st.text_input("Guest Phone", value=reservation.get("Guest Phone", ""))
            total_tariff = st.number_input("Total Tariff", min_value=0.0, value=reservation.get("Total Tariff", 0.0))
            advance_amount = st.number_input("Advance Amount", min_value=0.0, value=reservation.get("Advance Amount", 0.0))
            balance_amount = total_tariff - advance_amount if total_tariff >= advance_amount else 0.0
            st.write(f"Balance Amount: {balance_amount:.2f}")
            advance_mop = st.selectbox("Advance MOP", ["Cash", "UPI", "Card", "Other"], index=["Cash", "UPI", "Card", "Other"].index(reservation.get("Advance MOP", "Cash")) if reservation.get("Advance MOP") in ["Cash", "UPI", "Card", "Other"] else 0)
            if advance_mop == "Other":
                custom_advance_mop = st.text_input("Custom Advance MOP", value=reservation.get("Advance MOP") if reservation.get("Advance MOP") not in ["Cash", "UPI", "Card"] else "")
            else:
                custom_advance_mop = ""
            balance_mop = st.selectbox("Balance MOP", ["Cash", "UPI", "Card", "Other"], index=["Cash", "UPI", "Card", "Other"].index(reservation.get("Balance MOP", "Cash")) if reservation.get("Balance MOP") in ["Cash", "UPI", "Card", "Other"] else 0)
            if balance_mop == "Other":
                custom_balance_mop = st.text_input("Custom Balance MOP", value=reservation.get("Balance MOP") if reservation.get("Balance MOP") not in ["Cash", "UPI", "Card"] else "")
            else:
                custom_balance_mop = ""
            mob_value = st.text_input("MOB", value=reservation.get("MOB", ""))
            online_source = st.selectbox("Online Source", ["Booking.com", "Agoda", "Expedia", "Others"], index=["Booking.com", "Agoda", "Expedia", "Others"].index(reservation.get("Online Source", "Booking.com")) if reservation.get("Online Source") in ["Booking.com", "Agoda", "Expedia", "Others"] else 0)
            if online_source == "Others":
                custom_online_source = st.text_input("Custom Online Source", value=reservation.get("Online Source") if reservation.get("Online Source") not in ["Booking.com", "Agoda", "Expedia"] else "")
            else:
                custom_online_source = ""
            invoice_no = st.text_input("Invoice No", value=reservation.get("Invoice No", ""))
            enquiry_date = st.date_input("Enquiry Date", value=date.fromisoformat(reservation.get("Enquiry Date", date.today().isoformat())) if reservation.get("Enquiry Date") else date.today())
            booking_date = st.date_input("Booking Date", value=date.fromisoformat(reservation.get("Booking Date", date.today().isoformat())) if reservation.get("Booking Date") else date.today())
            breakfast = st.checkbox("Breakfast Included", value=reservation.get("Breakfast", False))
            booking_status = st.selectbox("Booking Status", ["Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"], index=["Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"].index(reservation.get("Booking Status", "Confirmed")))
            payment_status = st.selectbox("Payment Status", ["Not Paid", "Fully Paid", "Partially Paid"], index=["Not Paid", "Fully Paid", "Partially Paid"].index(reservation.get("Payment Status", "Not Paid")))
            remarks = st.text_area("Remarks", value=reservation.get("Remarks", ""))
            modified_comments = st.text_area("Modified Comments", value=reservation.get("Modified Comments", ""))
            
            if st.form_submit_button("💾 Save Reservation"):
                updated_reservation = {
                    "Property Name": property_name,
                    "Guest Name": guest_name,
                    "Guest Phone": guest_phone,
                    "Check In": str(check_in),
                    "Check Out": str(check_out),
                    "No of Adults": no_of_adults,
                    "No of Children": no_of_children,
                    "No of Infant": no_of_infant,
                    "Total Pax": total_pax,
                    "Room No": room_no,
                    "Total Tariff": total_tariff,
                    "Advance Amount": advance_amount,
                    "Balance Amount": balance_amount,
                    "Advance MOP": custom_advance_mop if advance_mop == "Other" else advance_mop,
                    "Balance MOP": custom_balance_mop if balance_mop == "Other" else balance_mop,
                    "MOB": mob_value,
                    "Online Source": custom_online_source if online_source == "Others" else online_source,
                    "Invoice No": invoice_no,
                    "Enquiry Date": str(enquiry_date),
                    "Booking Date": str(booking_date),
                    "Room Type": room_type,
                    "Breakfast": breakfast,
                    "Booking Status": booking_status,
                    "Modified By": modified_by,
                    "Modified Comments": modified_comments,
                    "Remarks": remarks,
                    "Payment Status": payment_status
                }
                try:
                    response = supabase.table("reservations").update(updated_reservation).eq("Booking ID", reservation["Booking ID"]).execute()
                    if response.data:
                        st.session_state.reservations[edit_index] = {**reservation, **updated_reservation}
                        st.session_state.edit_mode = False
                        st.session_state.edit_index = None
                        st.success(f"✅ Reservation {reservation['Booking ID']} updated successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update reservation.")
                except Exception as e:
                    st.error(f"❌ Error updating reservation: {e}")

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
    col1, col2 = st.columns(2)
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
</DOCUMENT><xaiArtifact artifact_id="a6b5c4d3-e2f1-g0h2-i3j4-k5l6m7n8o9p0" artifact_version_id="q1r2s3t4-u5v6-w7x8-y9z0-a1b2c3d4e5f6" title="directreservation.py" contentType="text/python">
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

def show_new_reservation_form():
    """Display the new reservation form with submitted_by default from logged-in user."""
    st.subheader("New Reservation Form")
    
    submitted_by = st.session_state.username if 'username' in st.session_state else "Unknown"
    st.write(f"Submitted By: {submitted_by}")

    with st.form("new_reservation_form"):
        # Form fields
        property_name = st.selectbox("Property Name", list(load_property_room_map().keys()))
        room_type = st.selectbox("Room Type", list(load_property_room_map()[property_name].keys()))
        room_no = st.selectbox("Room No", load_property_room_map()[property_name][room_type])
        check_in = st.date_input("Check In", value=date.today())
        check_out = st.date_input("Check Out", value=date.today() + timedelta(days=1))
        no_of_adults = st.number_input("No of Adults", min_value=0, value=1, step=1)
        no_of_children = st.number_input("No of Children", min_value=0, value=0, step=1)
        no_of_infant = st.number_input("No of Infant", min_value=0, value=0, step=1)
        total_pax = no_of_adults + no_of_children + no_of_infant
        st.write(f"Total Pax: {total_pax}")
        guest_name = st.text_input("Guest Name")
        guest_phone = st.text_input("Guest Phone")
        total_tariff = st.number_input("Total Tariff", min_value=0.0, value=0.0, step=100.0)
        advance_amount = st.number_input("Advance Amount", min_value=0.0, value=0.0, step=100.0)
        balance_amount = total_tariff - advance_amount if total_tariff >= advance_amount else 0.0
        st.write(f"Balance Amount: {balance_amount:.2f}")
        advance_mop = st.selectbox("Advance MOP", ["Cash", "UPI", "Card", "Other"])
        if advance_mop == "Other":
            custom_advance_mop = st.text_input("Custom Advance MOP")
        else:
            custom_advance_mop = ""
        balance_mop = st.selectbox("Balance MOP", ["Cash", "UPI", "Card", "Other"])
        if balance_mop == "Other":
            custom_balance_mop = st.text_input("Custom Balance MOP")
        else:
            custom_balance_mop = ""
        mob_value = st.text_input("MOB")
        online_source = st.selectbox("Online Source", ["Booking.com", "Agoda", "Expedia", "Others"])
        if online_source == "Others":
            custom_online_source = st.text_input("Custom Online Source")
        else:
            custom_online_source = ""
        invoice_no = st.text_input("Invoice No")
        enquiry_date = st.date_input("Enquiry Date", value=date.today())
        booking_date = st.date_input("Booking Date", value=date.today())
        breakfast = st.checkbox("Breakfast Included")
        booking_status = st.selectbox("Booking Status", ["Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"])
        payment_status = st.selectbox("Payment Status", ["Not Paid", "Fully Paid", "Partially Paid"])
        remarks = st.text_area("Remarks")
        modified_by = st.session_state.username if 'username' in st.session_state else "Unknown"
        st.write(f"Modified By: {modified_by}")
        modified_comments = st.text_area("Modified Comments")

        if st.form_submit_button("💾 Save Reservation"):
            reservation = {
                "Property Name": property_name,
                "Guest Name": guest_name,
                "Guest Phone": guest_phone,
                "Check In": str(check_in),
                "Check Out": str(check_out),
                "No of Adults": no_of_adults,
                "No of Children": no_of_children,
                "No of Infant": no_of_infant,
                "Total Pax": total_pax,
                "Room No": room_no,
                "Total Tariff": total_tariff,
                "Advance Amount": advance_amount,
                "Balance Amount": balance_amount,
                "Advance MOP": custom_advance_mop if advance_mop == "Other" else advance_mop,
                "Balance MOP": custom_balance_mop if balance_mop == "Other" else balance_mop,
                "MOB": mob_value,
                "Online Source": custom_online_source if online_source == "Others" else online_source,
                "Invoice No": invoice_no,
                "Enquiry Date": str(enquiry_date),
                "Booking Date": str(booking_date),
                "Room Type": room_type,
                "Breakfast": breakfast,
                "Booking Status": booking_status,
                "Submitted By": submitted_by,
                "Modified By": modified_by,
                "Modified Comments": modified_comments,
                "Remarks": remarks,
                "Payment Status": payment_status
            }
            try:
                response = supabase.table("reservations").insert(reservation).execute()
                if response.data:
                    st.session_state.reservations.append(reservation)
                    st.success(f"✅ Reservation saved successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to save reservation.")
            except Exception as e:
                st.error(f"❌ Error saving reservation: {e}")

def show_reservations():
    """Display the reservations table with filters."""
    st.subheader("View Reservations")
    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase()
    if not st.session_state.reservations:
        st.info("No reservations available.")
        return
    df = pd.DataFrame(st.session_state.reservations)
   
    st.subheader("Filters")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        start_date = st.date_input("Start Date", value=None, key="filter_start_date")
    with col2:
        end_date = st.date_input("End Date", value=None, key="filter_end_date")
    with col3:
        filter_status = st.selectbox("Filter by Status", ["All", "Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"], key="filter_status")
    with col4:
        filter_property = st.selectbox("Filter by Property", ["All"] + sorted(df["Property Name"].unique()), key="filter_property")
   
    filtered_df = df.copy()
    if start_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["Check In"]) >= pd.to_datetime(start_date)]
    if end_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["Check In"]) <= pd.to_datetime(end_date)]
    if filter_status != "All":
        filtered_df = filtered_df[filtered_df["Booking Status"] == filter_status]
    if filter_property != "All":
        filtered_df = filtered_df[filtered_df["Property Name"] == filter_property]
   
    if filtered_df.empty:
        st.warning("No reservations match the selected filters.")
        return

    st.dataframe(filtered_df)

def show_edit_reservations():
    """Display the edit reservation form with modified_by default from logged-in user."""
    st.subheader("Edit Reservations")
    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase()
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
        modified_by = st.session_state.username if 'username' in st.session_state else "Unknown"
        st.write(f"Modified By: {modified_by}")

        with st.form("edit_reservation_form"):
            property_name = st.selectbox("Property Name", list(load_property_room_map().keys()), index=list(load_property_room_map().keys()).index(reservation["Property Name"]) if reservation["Property Name"] in load_property_room_map() else 0)
            room_type = st.selectbox("Room Type", list(load_property_room_map().get(property_name, {}).keys()), index=list(load_property_room_map().get(property_name, {}).keys()).index(reservation["Room Type"]) if reservation["Room Type"] in load_property_room_map().get(property_name, {}) else 0)
            room_no = st.selectbox("Room No", load_property_room_map().get(property_name, {}).get(room_type, []), index=load_property_room_map().get(property_name, {}).get(room_type, []).index(reservation["Room No"]) if reservation["Room No"] in load_property_room_map().get(property_name, {}).get(room_type, []) else 0)
            check_in = st.date_input("Check In", value=date.fromisoformat(reservation["Check In"]) if reservation.get("Check In") else date.today())
            check_out = st.date_input("Check Out", value=date.fromisoformat(reservation["Check Out"]) if reservation.get("Check Out") else date.today())
            no_of_adults = st.number_input("No of Adults", min_value=0, value=reservation.get("No of Adults", 1))
            no_of_children = st.number_input("No of Children", min_value=0, value=reservation.get("No of Children", 0))
            no_of_infant = st.number_input("No of Infant", min_value=0, value=reservation.get("No of Infant", 0))
            total_pax = no_of_adults + no_of_children + no_of_infant
            st.write(f"Total Pax: {total_pax}")
            guest_name = st.text_input("Guest Name", value=reservation.get("Guest Name", ""))
            guest_phone = st.text_input("Guest Phone", value=reservation.get("Guest Phone", ""))
            total_tariff = st.number_input("Total Tariff", min_value=0.0, value=reservation.get("Total Tariff", 0.0))
            advance_amount = st.number_input("Advance Amount", min_value=0.0, value=reservation.get("Advance Amount", 0.0))
            balance_amount = total_tariff - advance_amount if total_tariff >= advance_amount else 0.0
            st.write(f"Balance Amount: {balance_amount:.2f}")
            advance_mop = st.selectbox("Advance MOP", ["Cash", "UPI", "Card", "Other"], index=["Cash", "UPI", "Card", "Other"].index(reservation.get("Advance MOP", "Cash")) if reservation.get("Advance MOP") in ["Cash", "UPI", "Card", "Other"] else 0)
            if advance_mop == "Other":
                custom_advance_mop = st.text_input("Custom Advance MOP", value=reservation.get("Advance MOP") if reservation.get("Advance MOP") not in ["Cash", "UPI", "Card"] else "")
            else:
                custom_advance_mop = ""
            balance_mop = st.selectbox("Balance MOP", ["Cash", "UPI", "Card", "Other"], index=["Cash", "UPI", "Card", "Other"].index(reservation.get("Balance MOP", "Cash")) if reservation.get("Balance MOP") in ["Cash", "UPI", "Card", "Other"] else 0)
            if balance_mop == "Other":
                custom_balance_mop = st.text_input("Custom Balance MOP", value=reservation.get("Balance MOP") if reservation.get("Balance MOP") not in ["Cash", "UPI", "Card"] else "")
            else:
                custom_balance_mop = ""
            mob_value = st.text_input("MOB", value=reservation.get("MOB", ""))
            online_source = st.selectbox("Online Source", ["Booking.com", "Agoda", "Expedia", "Others"], index=["Booking.com", "Agoda", "Expedia", "Others"].index(reservation.get("Online Source", "Booking.com")) if reservation.get("Online Source") in ["Booking.com", "Agoda", "Expedia", "Others"] else 0)
            if online_source == "Others":
                custom_online_source = st.text_input("Custom Online Source", value=reservation.get("Online Source") if reservation.get("Online Source") not in ["Booking.com", "Agoda", "Expedia"] else "")
            else:
                custom_online_source = ""
            invoice_no = st.text_input("Invoice No", value=reservation.get("Invoice No", ""))
            enquiry_date = st.date_input("Enquiry Date", value=date.fromisoformat(reservation.get("Enquiry Date", date.today().isoformat())) if reservation.get("Enquiry Date") else date.today())
            booking_date = st.date_input("Booking Date", value=date.fromisoformat(reservation.get("Booking Date", date.today().isoformat())) if reservation.get("Booking Date") else date.today())
            breakfast = st.checkbox("Breakfast Included", value=reservation.get("Breakfast", False))
            booking_status = st.selectbox("Booking Status", ["Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"], index=["Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"].index(reservation.get("Booking Status", "Confirmed")))
            payment_status = st.selectbox("Payment Status", ["Not Paid", "Fully Paid", "Partially Paid"], index=["Not Paid", "Fully Paid", "Partially Paid"].index(reservation.get("Payment Status", "Not Paid")))
            remarks = st.text_area("Remarks", value=reservation.get("Remarks", ""))
            modified_comments = st.text_area("Modified Comments", value=reservation.get("Modified Comments", ""))
            
            if st.form_submit_button("💾 Save Reservation"):
                updated_reservation = {
                    "Property Name": property_name,
                    "Guest Name": guest_name,
                    "Guest Phone": guest_phone,
                    "Check In": str(check_in),
                    "Check Out": str(check_out),
                    "No of Adults": no_of_adults,
                    "No of Children": no_of_children,
                    "No of Infant": no_of_infant,
                    "Total Pax": total_pax,
                    "Room No": room_no,
                    "Total Tariff": total_tariff,
                    "Advance Amount": advance_amount,
                    "Balance Amount": balance_amount,
                    "Advance MOP": custom_advance_mop if advance_mop == "Other" else advance_mop,
                    "Balance MOP": custom_balance_mop if balance_mop == "Other" else balance_mop,
                    "MOB": mob_value,
                    "Online Source": custom_online_source if online_source == "Others" else online_source,
                    "Invoice No": invoice_no,
                    "Enquiry Date": str(enquiry_date),
                    "Booking Date": str(booking_date),
                    "Room Type": room_type,
                    "Breakfast": breakfast,
                    "Booking Status": booking_status,
                    "Modified By": modified_by,
                    "Modified Comments": modified_comments,
                    "Remarks": remarks,
                    "Payment Status": payment_status
                }
                try:
                    response = supabase.table("reservations").update(updated_reservation).eq("Booking ID", reservation["Booking ID"]).execute()
                    if response.data:
                        st.session_state.reservations[edit_index] = {**reservation, **updated_reservation}
                        st.session_state.edit_mode = False
                        st.session_state.edit_index = None
                        st.success(f"✅ Reservation {reservation['Booking ID']} updated successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update reservation.")
                except Exception as e:
                    st.error(f"❌ Error updating reservation: {e}")

def show_analytics():
    """Display the analytics dashboard for Management users."""
    if st.session_state.role != "Management":
        st.error("❌ Access Denied: Analytics is available only for Management users.")
        return
    st.header("📊 Analytics Dashboard")
    if not st.session_state.reservations:
        st.info("No reservations available for analysis.")
        return
    df = pd.DataFrame(st.session_state.reservations)
   
    st.subheader("Filters")
    col1, col2 = st.columns(2)
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
</DOCUMENT>
