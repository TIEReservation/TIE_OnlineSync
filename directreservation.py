import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from supabase import create_client, Client
from inventory import PROPERTY_INVENTORY

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

def load_properties() -> list:
    """Load unique properties from reservations table."""
    try:
        response = supabase.table("reservations").select("property_name").execute()
        properties = sorted(set([row["property_name"] for row in response.data if row["property_name"]]))
        return properties
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []

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

@st.cache_data
def load_reservations_from_supabase():
    """Load all reservations from Supabase."""
    try:
        response = supabase.table("reservations").select("*").execute()
        data = []
        for row in response.data:
            total_pax = safe_int(row.get("no_of_adults", 0)) + safe_int(row.get("no_of_children", 0)) + safe_int(row.get("no_of_infant", 0))
            row["Total Pax"] = total_pax
            row["Booking ID"] = row.get("booking_id", "Unknown")
            row["Property Name"] = row.get("property_name", "")
            row["Guest Name"] = row.get("guest_name", "")
            row["Mobile No"] = row.get("mobile_no", "")
            row["Check In"] = row.get("check_in", "")
            row["Check Out"] = row.get("check_out", "")
            row["Room No"] = row.get("room_no", "")
            row["Room Type"] = row.get("room_type", "")
            row["Plan Status"] = row.get("plan_status", "")
            row["Payment Status"] = row.get("payment_status", "")
            data.append(row)
        return data
    except Exception as e:
        st.error(f"Error loading reservations: {e}")
        return []

def add_reservation_to_supabase(data: dict) -> bool:
    """Add a new reservation to the reservations table."""
    try:
        response = supabase.table("reservations").insert(data).execute()
        return len(response.data) > 0
    except Exception as e:
        st.error(f"Error adding reservation: {e}")
        return False

def update_reservation_in_supabase(booking_id: str, data: dict) -> bool:
    """Update a reservation in the reservations table."""
    try:
        response = supabase.table("reservations").update(data).eq("booking_id", booking_id).execute()
        return len(response.data) > 0
    except Exception as e:
        st.error(f"Error updating reservation {booking_id}: {e}")
        return False

def delete_reservation_in_supabase(booking_id: str) -> bool:
    """Delete a reservation from the reservations table."""
    try:
        response = supabase.table("reservations").delete().eq("booking_id", booking_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting reservation {booking_id}: {e}")
        return False

def show_add_reservations():
    """Display add new reservation page."""
    st.title("➕ Add New Reservation")
    
    with st.form("add_reservation_form"):
        # Row 1: Property, Booking Date
        col1, col2 = st.columns(2)
        with col1:
            properties = sorted(load_properties())
            property_name = st.selectbox("Property Name", properties, key="add_property")
        with col2:
            booking_date = st.date_input("Booking Date", value=date.today())

        # Row 2: Guest Name, Mobile No
        col1, col2 = st.columns(2)
        with col1:
            guest_name = st.text_input("Guest Name", key="add_guest_name")
        with col2:
            mobile_no = st.text_input("Mobile Number", key="add_mobile_no")

        # Row 3: Check In, Check Out
        col1, col2 = st.columns(2)
        with col1:
            check_in = st.date_input("Check In", value=date.today(), key="add_check_in")
        with col2:
            check_out = st.date_input("Check Out", value=date.today() + timedelta(days=1), key="add_check_out")

        # Row 4: Room No, Room Type
        col1, col2 = st.columns(2)
        with col1:
            room_options = PROPERTY_INVENTORY.get(property_name, {"all": ["Unknown"]})["all"]
            room_no = st.selectbox("Room No", room_options, key="add_room_no")
        with col2:
            room_type = st.text_input("Room Type", key="add_room_type")

        # Row 5: Number of Adults, Number of Children, Number of Infant
        col1, col2, col3 = st.columns(3)
        with col1:
            no_of_adults = st.number_input("Number of Adults", min_value=0, value=1, key="add_adults")
        with col2:
            no_of_children = st.number_input("Number of Children", min_value=0, value=0, key="add_children")
        with col3:
            no_of_infant = st.number_input("Number of Infant", min_value=0, value=0, key="add_infant")

        # Calculate total pax
        total_pax = no_of_adults + no_of_children + no_of_infant

        # Row 6: Plan, Plan Status, Payment Status
        col1, col2, col3 = st.columns(3)
        with col1:
            plan = st.text_input("Plan", key="add_plan")
        with col2:
            plan_status = st.selectbox("Plan Status", ["Confirmed", "Pending", "Cancelled"], index=0, key="add_plan_status")
        with col3:
            payment_status = st.selectbox("Payment Status", ["Fully Paid", "Partially Paid", "Not Paid"], index=0, key="add_payment_status")

        # Row 7: Total Tariff, Advance Amount, Balance Amount
        col1, col2, col3 = st.columns(3)
        with col1:
            total_tariff = st.number_input("Total Tariff", min_value=0.0, value=0.0, key="add_total_tariff")
        with col2:
            advance_amount = st.number_input("Advance Amount", min_value=0.0, value=0.0, key="add_advance_amount")
        with col3:
            balance_amount = st.number_input("Balance Amount", min_value=0.0, value=0.0, key="add_balance_amount")

        # Row 8: Advance MOP, Balance MOP, Mode of Booking
        col1, col2, col3 = st.columns(3)
        with col1:
            advance_mop = st.text_input("Advance MOP", key="add_advance_mop")
        with col2:
            balance_mop = st.text_input("Balance MOP", key="add_balance_mop")
        with col3:
            mode_of_booking = st.text_input("Mode of Booking", key="add_mode_of_booking")

        # Row 9: Remarks
        remarks = st.text_area("Remarks", key="add_remarks")

        # Row 10: Submitted by, Modified by
        col1, col2 = st.columns(2)
        with col1:
            submitted_by = st.text_input("Submitted by", key="add_submitted_by")
        with col2:
            modified_by = st.text_input("Modified by", key="add_modified_by")

        if st.form_submit_button("➕ Add Reservation", use_container_width=True):
            booking_id = f"DR_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            new_reservation = {
                "booking_id": booking_id,
                "property_name": property_name,
                "booking_date": str(booking_date) if booking_date else None,
                "guest_name": guest_name,
                "mobile_no": mobile_no,
                "check_in": str(check_in) if check_in else None,
                "check_out": str(check_out) if check_out else None,
                "no_of_adults": no_of_adults,
                "no_of_children": no_of_children,
                "no_of_infant": no_of_infant,
                "total_pax": total_pax,
                "room_no": room_no,
                "room_type": room_type,
                "plan": plan,
                "plan_status": plan_status,
                "payment_status": payment_status,
                "total_tariff": total_tariff,
                "advance_amount": advance_amount,
                "balance_amount": balance_amount,
                "advance_mop": advance_mop,
                "balance_mop": balance_mop,
                "mode_of_booking": mode_of_booking,
                "remarks": remarks,
                "submitted_by": submitted_by,
                "modified_by": modified_by
            }
            if add_reservation_to_supabase(new_reservation):
                st.session_state.reservations.append(new_reservation)
                st.success(f"✅ Reservation {booking_id} added successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to add reservation")

def show_edit_reservations(selected_booking_id=None):
    """Display edit reservations page."""
    st.title("✏️ Edit Reservations")
    
    if st.button("🔄 Refresh Reservations"):
        st.cache_data.clear()
        st.session_state.pop('reservations', None)
        st.success("Cache cleared! Refreshing reservations...")
        st.rerun()

    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase()
    
    if not st.session_state.reservations:
        st.info("No reservations available to edit.")
        return

    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
        st.session_state.edit_index = None

    # Convert reservations to DataFrame for display
    df = pd.DataFrame(st.session_state.reservations)
    columns_to_display = [
        "Booking ID", "Property Name", "Guest Name", "Check In", "Check Out",
        "Room No", "Room Type", "Plan Status", "Payment Status"
    ]
    columns_to_display = [col for col in columns_to_display if col in df.columns]
    st.dataframe(df[columns_to_display], use_container_width=True)

    # Check for query parameter to auto-select a booking
    query_params = st.query_params
    if selected_booking_id or query_params.get("booking_id"):
        booking_id = selected_booking_id or query_params.get("booking_id")
        for idx, reservation in enumerate(st.session_state.reservations):
            if reservation.get("Booking ID") == booking_id:
                st.session_state.edit_mode = True
                st.session_state.edit_index = idx
                break

    if st.session_state.edit_mode and st.session_state.edit_index is not None:
        edit_index = st.session_state.edit_index
        reservation = st.session_state.reservations[edit_index]
        st.subheader(f"Edit Reservation: {reservation['Booking ID']}")
        
        with st.form(f"edit_form_{edit_index}"):
            # Row 1: Property, Booking Date
            col1, col2 = st.columns(2)
            with col1:
                properties = sorted(load_properties())
                property_name = st.selectbox("Property Name", properties, index=properties.index(reservation.get("Property Name", "")) if reservation.get("Property Name") in properties else 0)
            with col2:
                booking_date = st.date_input("Booking Date", value=date.fromisoformat(reservation["Booking Date"]) if reservation.get("Booking Date") else None)

            # Row 2: Guest Name, Mobile No
            col1, col2 = st.columns(2)
            with col1:
                guest_name = st.text_input("Guest Name", value=reservation.get("Guest Name", ""))
            with col2:
                mobile_no = st.text_input("Mobile Number", value=reservation.get("Mobile No", ""))

            # Row 3: Check In, Check Out
            col1, col2 = st.columns(2)
            with col1:
                check_in = st.date_input("Check In", value=date.fromisoformat(reservation["Check In"]) if reservation.get("Check In") else None)
            with col2:
                check_out = st.date_input("Check Out", value=date.fromisoformat(reservation["Check Out"]) if reservation.get("Check Out") else None)

            # Row 4: Room No, Room Type
            col1, col2 = st.columns(2)
            with col1:
                room_options = PROPERTY_INVENTORY.get(property_name, {"all": ["Unknown"]})["all"]
                room_no = st.selectbox("Room No", room_options, index=room_options.index(reservation.get("Room No", "")) if reservation.get("Room No") in room_options else 0)
            with col2:
                room_type = st.text_input("Room Type", value=reservation.get("Room Type", ""))

            # Row 5: Number of Adults, Number of Children, Number of Infant
            col1, col2, col3 = st.columns(3)
            with col1:
                no_of_adults = st.number_input("Number of Adults", min_value=0, value=safe_int(reservation.get("no_of_adults", 0)))
            with col2:
                no_of_children = st.number_input("Number of Children", min_value=0, value=safe_int(reservation.get("no_of_children", 0)))
            with col3:
                no_of_infant = st.number_input("Number of Infant", min_value=0, value=safe_int(reservation.get("no_of_infant", 0)))

            # Calculate total pax
            total_pax = no_of_adults + no_of_children + no_of_infant

            # Row 6: Plan, Plan Status, Payment Status
            col1, col2, col3 = st.columns(3)
            with col1:
                plan = st.text_input("Plan", value=reservation.get("plan", ""))
            with col2:
                plan_status = st.selectbox("Plan Status", ["Confirmed", "Pending", "Cancelled"], index=["Confirmed", "Pending", "Cancelled"].index(reservation.get("Plan Status", "Pending")) if reservation.get("Plan Status") in ["Confirmed", "Pending", "Cancelled"] else 0)
            with col3:
                payment_status = st.selectbox("Payment Status", ["Fully Paid", "Partially Paid", "Not Paid"], index=["Fully Paid", "Partially Paid", "Not Paid"].index(reservation.get("Payment Status", "Not Paid")) if reservation.get("Payment Status") in ["Fully Paid", "Partially Paid", "Not Paid"] else 0)

            # Row 7: Total Tariff, Advance Amount, Balance Amount
            col1, col2, col3 = st.columns(3)
            with col1:
                total_tariff = st.number_input("Total Tariff", min_value=0.0, value=safe_float(reservation.get("total_tariff", 0.0)))
            with col2:
                advance_amount = st.number_input("Advance Amount", min_value=0.0, value=safe_float(reservation.get("advance_amount", 0.0)))
            with col3:
                balance_amount = st.number_input("Balance Amount", min_value=0.0, value=safe_float(reservation.get("balance_amount", 0.0)))

            # Row 8: Advance MOP, Balance MOP, Mode of Booking
            col1, col2, col3 = st.columns(3)
            with col1:
                advance_mop = st.text_input("Advance MOP", value=reservation.get("advance_mop", ""))
            with col2:
                balance_mop = st.text_input("Balance MOP", value=reservation.get("balance_mop", ""))
            with col3:
                mode_of_booking = st.text_input("Mode of Booking", value=reservation.get("mode_of_booking", ""))

            # Row 9: Remarks
            remarks = st.text_area("Remarks", value=reservation.get("remarks", ""))

            # Row 10: Submitted by, Modified by
            col1, col2 = st.columns(2)
            with col1:
                submitted_by = st.text_input("Submitted by", value=reservation.get("submitted_by", ""))
            with col2:
                modified_by = st.text_input("Modified by", value=reservation.get("modified_by", ""))

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.form_submit_button("💾 Update Reservation", use_container_width=True):
                    updated_reservation = {
                        "property_name": property_name,
                        "booking_date": str(booking_date) if booking_date else None,
                        "guest_name": guest_name,
                        "mobile_no": mobile_no,
                        "check_in": str(check_in) if check_in else None,
                        "check_out": str(check_out) if check_out else None,
                        "no_of_adults": no_of_adults,
                        "no_of_children": no_of_children,
                        "no_of_infant": no_of_infant,
                        "total_pax": total_pax,
                        "room_no": room_no,
                        "room_type": room_type,
                        "plan": plan,
                        "plan_status": plan_status,
                        "payment_status": payment_status,
                        "total_tariff": total_tariff,
                        "advance_amount": advance_amount,
                        "balance_amount": balance_amount,
                        "advance_mop": advance_mop,
                        "balance_mop": balance_mop,
                        "mode_of_booking": mode_of_booking,
                        "remarks": remarks,
                        "submitted_by": submitted_by,
                        "modified_by": modified_by
                    }
                    if update_reservation_in_supabase(reservation["Booking ID"], updated_reservation):
                        st.session_state.reservations[edit_index] = {**reservation, **updated_reservation}
                        st.session_state.edit_mode = False
                        st.session_state.edit_index = None
                        st.query_params.clear()
                        st.success(f"✅ Reservation {reservation['Booking ID']} updated successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update reservation")
            with col_btn2:
                if st.session_state.get('role') == "Management":
                    if st.form_submit_button("🗑️ Delete Reservation", use_container_width=True):
                        if delete_reservation_in_supabase(reservation["Booking ID"]):
                            st.session_state.reservations.pop(edit_index)
                            st.session_state.edit_mode = False
                            st.session_state.edit_index = None
                            st.query_params.clear()
                            st.success(f"🗑️ Reservation {reservation['Booking ID']} deleted successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete reservation")

def show_analytics():
    """Display analytics page with booking statistics."""
    st.title("📊 Analytics")
    
    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase()
    
    if not st.session_state.reservations:
        st.info("No reservations available for analytics.")
        return

    df = pd.DataFrame(st.session_state.reservations)
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        properties = ["All"] + sorted(load_properties())
        selected_property = st.selectbox("Select Property", properties, index=0)
    with col2:
        months = ["All"] + [f"{m:02d}" for m in range(1, 13)]
        selected_month = st.selectbox("Select Month", months, index=0)

    # Filter DataFrame
    filtered_df = df
    if selected_property != "All":
        filtered_df = filtered_df[filtered_df["Property Name"] == selected_property]
    if selected_month != "All":
        filtered_df = filtered_df[filtered_df["Check In"].str.startswith(f"2025-{selected_month}", na=False)]

    if filtered_df.empty:
        st.info("No data available for the selected filters.")
        return

    # Total Bookings
    total_bookings = len(filtered_df)
    st.metric("Total Bookings", total_bookings)

    # Bookings by Status
    status_counts = filtered_df["Plan Status"].value_counts()
    fig_status = px.pie(values=status_counts.values, names=status_counts.index, title="Bookings by Status")
    st.plotly_chart(fig_status, use_container_width=True)

    # Revenue Analysis
    filtered_df["total_tariff"] = filtered_df["total_tariff"].apply(safe_float)
    total_revenue = filtered_df["total_tariff"].sum()
    st.metric("Total Revenue", f"₹{total_revenue:,.2f}")

    # Revenue by Property
    if selected_property == "All":
        revenue_by_property = filtered_df.groupby("Property Name")["total_tariff"].sum()
        fig_revenue = px.bar(x=revenue_by_property.index, y=revenue_by_property.values, title="Revenue by Property")
        st.plotly_chart(fig_revenue, use_container_width=True)

    # Occupancy Rate
    if "Check In" in filtered_df.columns and "Check Out" in filtered_df.columns:
        try:
            filtered_df["Check In"] = pd.to_datetime(filtered_df["Check In"])
            filtered_df["Check Out"] = pd.to_datetime(filtered_df["Check Out"])
            filtered_df["Days"] = (filtered_df["Check Out"] - filtered_df["Check In"]).dt.days
            total_room_nights = filtered_df["Days"].sum()
            if selected_property == "All":
                total_rooms = sum(len(PROPERTY_INVENTORY.get(prop, {"all": []})["all"]) for prop in load_properties())
            else:
                total_rooms = len(PROPERTY_INVENTORY.get(selected_property, {"all": []})["all"])
            days_in_month = 30 if selected_month == "All" else pd.to_datetime(f"2025-{selected_month}-01").days_in_month
            occupancy_rate = (total_room_nights / (total_rooms * days_in_month)) * 100 if total_rooms > 0 and days_in_month > 0 else 0
            st.metric("Occupancy Rate", f"{occupancy_rate:.2f}%")
        except Exception as e:
            st.error(f"Error calculating occupancy rate: {e}")
