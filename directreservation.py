def show_new_reservation_form():
    """Display form to create a new direct reservation with room types and numbers from load_property_room_map."""
    st.header("New Direct Reservation")
    form_key = "new_reservation_form"
    property_room_map = load_property_room_map()
    properties = sorted(property_room_map.keys())
    
    with st.form(key=form_key):
        # Row 1: Property Name, Booking ID
        col1, col2 = st.columns(2)
        with col1:
            property_name = st.selectbox("Property Name", properties, key=f"{form_key}_property")
        with col2:
            booking_id = st.text_input("Booking ID", key=f"{form_key}_booking_id")
        
        # Debug: Display selected property and room types
        st.write(f"Debug: Selected Property Name = {property_name}")
        room_types = sorted(property_room_map[property_name].keys())
        st.write(f"Debug: Room Types = {room_types}")
        
        # Row 2: Guest Name, Guest Phone
        col1, col2 = st.columns(2)
        with col1:
            guest_name = st.text_input("Guest Name", key=f"{form_key}_guest_name")
        with col2:
            guest_phone = st.text_input("Guest Phone", key=f"{form_key}_guest_phone")
        
        # Row 3: Check In, Check Out
        col1, col2 = st.columns(2)
        with col1:
            check_in = st.date_input("Check In", min_value=date.today(), key=f"{form_key}_check_in")
        with col2:
            check_out = st.date_input("Check Out", min_value=date.today(), key=f"{form_key}_check_out")
        
        # Row 4: Room Type, Room No
        col1, col2 = st.columns(2)
        with col1:
            room_type = st.selectbox("Room Type", room_types, key=f"{form_key}_room_type")
        with col2:
            room_numbers = sorted(property_room_map[property_name][room_type])
            room_no = st.selectbox("Room No", room_numbers, key=f"{form_key}_room_no")
        
        # Row 5: No of Adults, Children, Infants
        col1, col2, col3 = st.columns(3)
        with col1:
            no_of_adults = st.number_input("No of Adults", min_value=0, value=1, step=1, key=f"{form_key}_adults")
        with col2:
            no_of_children = st.number_input("No of Children", min_value=0, value=0, step=1, key=f"{form_key}_children")
        with col3:
            no_of_infants = st.number_input("No of Infants", min_value=0, value=0, step=1, key=f"{form_key}_infants")
        
        # Row 6: Rate Plans, Booking Source
        col1, col2 = st.columns(2)
        with col1:
            rate_plans = st.text_input("Rate Plans", key=f"{form_key}_rate_plans")
        with col2:
            booking_source = st.text_input("Booking Source", key=f"{form_key}_booking_source")
        
        # Row 7: Total Tariff, Advance Payment
        col1, col2 = st.columns(2)
        with col1:
            total_tariff = st.number_input("Total Tariff", min_value=0.0, step=0.01, key=f"{form_key}_total_tariff")
        with col2:
            advance_payment = st.number_input("Advance Payment", min_value=0.0, step=0.01, key=f"{form_key}_advance_payment")
        
        # Row 8: Booking Status, Payment Status
        col1, col2 = st.columns(2)
        with col1:
            booking_status = st.selectbox("Booking Status", ["Pending", "Confirmed", "Cancelled", "Follow-up", "Completed", "No Show"], key=f"{form_key}_booking_status")
        with col2:
            payment_status = st.selectbox("Payment Status", ["Not Paid", "Fully Paid", "Partially Paid"], key=f"{form_key}_payment_status")
        
        # Row 9: Submitted By, Modified By
        col1, col2 = st.columns(2)
        with col1:
            submitted_by = st.text_input("Submitted By", value=st.session_state.get("username", ""), disabled=True, key=f"{form_key}_submitted_by")
        with col2:
            modified_by = st.text_input("Modified By", value="", disabled=True, key=f"{form_key}_modified_by")
        
        # Row 10: Modified Comments, Remarks
        modified_comments = st.text_area("Modified Comments", key=f"{form_key}_modified_comments")
        remarks = st.text_area("Remarks", key=f"{form_key}_remarks")
        
        if st.form_submit_button("✅ Submit Reservation"):
            reservation = {
                "property_name": property_name,
                "booking_id": booking_id,
                "guest_name": guest_name,
                "guest_phone": guest_phone,
                "check_in": str(check_in),
                "check_out": str(check_out),
                "room_no": room_no,
                "room_type": room_type,
                "no_of_adults": no_of_adults,
                "no_of_children": no_of_children,
                "no_of_infants": no_of_infants,
                "rate_plans": rate_plans,
                "booking_source": booking_source,
                "total_tariff": total_tariff,
                "advance_payment": advance_payment,
                "booking_status": booking_status,
                "payment_status": payment_status,
                "submitted_by": st.session_state.get("username", ""),
                "modified_by": "",
                "modified_comments": modified_comments,
                "remarks": remarks
            }
            try:
                response = supabase.table("reservations").insert(reservation).execute()
                if response.data:
                    reservation_transformed = {
                        "Property Name": reservation["property_name"],
                        "Booking ID": reservation["booking_id"],
                        "Guest Name": reservation["guest_name"],
                        "Guest Phone": reservation["guest_phone"],
                        "Check In": reservation["check_in"],
                        "Check Out": reservation["check_out"],
                        "Room No": reservation["room_no"],
                        "Room Type": reservation["room_type"],
                        "No of Adults": reservation["no_of_adults"],
                        "No of Children": reservation["no_of_children"],
                        "No of Infants": reservation["no_of_infants"],
                        "Rate Plans": reservation["rate_plans"],
                        "Booking Source": reservation["booking_source"],
                        "Total Tariff": reservation["total_tariff"],
                        "Advance Payment": reservation["advance_payment"],
                        "Booking Status": reservation["booking_status"],
                        "Payment Status": reservation["payment_status"],
                        "Submitted By": reservation["submitted_by"],
                        "Modified By": reservation["modified_by"],
                        "Modified Comments": reservation["modified_comments"],
                        "Remarks": reservation["remarks"]
                    }
                    st.session_state.reservations = st.session_state.get('reservations', []) + [reservation_transformed]
                    st.success(f"✅ Reservation {booking_id} created successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to create reservation: No data returned from Supabase")
            except Exception as e:
                st.error(f"Error creating reservation: {e}")
