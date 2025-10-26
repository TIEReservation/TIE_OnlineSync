def show_new_reservation_form():
    """Display form to create a new direct reservation."""
    st.header("New Direct Reservation")
    form_key = "new_reservation_form"
    property_room_map = load_property_room_map()
    properties = sorted(property_room_map.keys())
    
    # Property selection OUTSIDE form for dynamic updates
    property_name = st.selectbox("Property Name", properties, key="property_select_outside_form")
    
    # Get room types for selected property and add "Others"
    room_types = list(property_room_map[property_name].keys()) + ["Others"]
    
    with st.form(key=form_key):
        # Row 1: Booking ID
        booking_id = st.text_input("Booking ID", key=f"{form_key}_booking_id")
        
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
            if room_type == "Others":
                room_no = st.text_input("Room No (Enter manually)", key=f"{form_key}_room_no_manual")
            else:
                room_numbers = property_room_map[property_name][room_type]
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
            rate_plans = st.selectbox("Rate Plans", [" ","EP", "CP"], key=f"{form_key}_rate_plans", help="EP: European Plan, CP: Continental Plan")
        with col2:
            booking_source = st.selectbox("Booking Source", BOOKING_SOURCES, key=f"{form_key}_booking_source")
        
        # Row 7: Total Tariff, Advance Payment
        col1, col2 = st.columns(2)
        with col1:
            total_tariff = st.number_input("Total Tariff", min_value=0.0, step=0.01, key=f"{form_key}_total_tariff")
        with col2:
            advance_payment = st.number_input("Advance Payment", min_value=0.0, step=0.01, key=f"{form_key}_advance_payment")
        
        # Row 8: Balance (Auto-calculated), Advance MOP
        col1, col2 = st.columns(2)
        with col1:
            balance = total_tariff - advance_payment
            st.number_input("Balance", value=balance, disabled=True, key=f"{form_key}_balance", help="Auto-calculated: Total Tariff - Advance Payment")
        with col2:
            advance_mop = st.selectbox("Advance MOP", MOP_OPTIONS, key=f"{form_key}_advance_mop", help="Mode of Payment for advance amount")
        
        # Row 9: Balance MOP
        balance_mop = st.selectbox("Balance MOP", MOP_OPTIONS, key=f"{form_key}_balance_mop", help="Mode of Payment for balance amount")
        
        # Row 10: Booking Status, Payment Status
        col1, col2 = st.columns(2)
        with col1:
            booking_status = st.selectbox("Booking Status", ["Pending", "Confirmed", "Cancelled", "Follow-up", "Completed", "No Show"], key=f"{form_key}_booking_status")
        with col2:
            payment_status = st.selectbox("Payment Status", ["Not Paid", "Fully Paid", "Partially Paid"], key=f"{form_key}_payment_status")
        
        # Row 11: Submitted By, Modified By
        col1, col2 = st.columns(2)
        with col1:
            submitted_by = st.text_input("Submitted By", value=st.session_state.get("username", ""), disabled=True, key=f"{form_key}_submitted_by")
        with col2:
            modified_by = st.text_input("Modified By", value="", disabled=True, key=f"{form_key}_modified_by")
        
        # Row 12: Modified Comments, Remarks
        modified_comments = st.text_area("Modified Comments", key=f"{form_key}_modified_comments")
        remarks = st.text_area("Remarks", key=f"{form_key}_remarks")
        
        if st.form_submit_button("Submit Reservation"):
            new_reservation = {
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
                "balance": balance,
                "advance_mop": advance_mop,
                "balance_mop": balance_mop,
                "booking_status": booking_status,
                "payment_status": payment_status,
                "submitted_by": st.session_state.get("username", ""),
                "modified_by": "",
                "modified_comments": modified_comments,
                "remarks": remarks
            }
            try:
                response = supabase.table("reservations").insert(new_reservation).execute()
                if response.data:
                    st.success("✅ Reservation created successfully!")
                    st.session_state.reservations.append({
                        "Property Name": property_name,
                        "Booking ID": booking_id,
                        "Guest Name": guest_name,
                        "Guest Phone": guest_phone,
                        "Check In": str(check_in),
                        "Check Out": str(check_out),
                        "Room No": room_no,
                        "Room Type": room_type,
                        "No of Adults": no_of_adults,
                        "No of Children": no_of_children,
                        "No of Infants": no_of_infants,
                        "Rate Plans": rate_plans,
                        "Booking Source": booking_source,
                        "Total Tariff": total_tariff,
                        "Advance Payment": advance_payment,
                        "Balance": balance,
                        "Advance MOP": advance_mop,
                        "Balance MOP": balance_mop,
                        "Booking Status": booking_status,
                        "Payment Status": payment_status,
                        "Submitted By": st.session_state.get("username", ""),
                        "Modified By": "",
                        "Modified Comments": modified_comments,
                        "Remarks": remarks
                    })
                    st.rerun()
                else:
                    st.error("❌ Failed to create reservation in Supabase.")
            except Exception as e:
                st.error(f"Error creating reservation: {e}")


def show_edit_reservations():
    """Display edit direct reservations page."""
    st.title("✏️ Edit Direct Reservations")
    
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

    df = pd.DataFrame(st.session_state.reservations)
    display_columns = ["Property Name", "Booking ID", "Guest Name", "Check In", "Check Out", "Room No", "Room Type", "Booking Status", "Payment Status"]
    st.dataframe(df[display_columns], use_container_width=True)
    
    st.subheader("Select Reservation to Edit")
    booking_id_options = df["Booking ID"].unique()
    selected_booking_id = st.selectbox("Select Booking ID", booking_id_options)
    
    if st.button("✏️ Edit Selected Reservation"):
        edit_index = df[df["Booking ID"] == selected_booking_id].index[0]
        st.session_state.edit_mode = True
        st.session_state.edit_index = edit_index
    
    if st.session_state.edit_mode and st.session_state.edit_index is not None:
        edit_index = st.session_state.edit_index
        reservation = st.session_state.reservations[edit_index]
        
        property_room_map = load_property_room_map()
        properties = sorted(property_room_map.keys())
        
        # Get room types and add "Others"
        room_types = list(property_room_map[reservation["Property Name"]].keys()) if reservation["Property Name"] in property_room_map else []
        room_types.append("Others")
        
        with st.form(key=f"edit_form_{reservation['Booking ID']}"):
            # Row 1: Property Name, Booking ID
            col1, col2 = st.columns(2)
            with col1:
                property_name = st.selectbox("Property Name", properties, index=properties.index(reservation["Property Name"]) if reservation["Property Name"] in properties else 0)
            with col2:
                booking_id = st.text_input("Booking ID", value=reservation["Booking ID"], disabled=True)
            
            # Row 2: Guest Name, Guest Phone
            col1, col2 = st.columns(2)
            with col1:
                guest_name = st.text_input("Guest Name", value=reservation["Guest Name"])
            with col2:
                guest_phone = st.text_input("Guest Phone", value=reservation["Guest Phone"])
            
            # Row 3: Check In, Check Out
            col1, col2 = st.columns(2)
            with col1:
                check_in = st.date_input("Check In", value=date.fromisoformat(reservation["Check In"]) if reservation["Check In"] else date.today())
            with col2:
                check_out = st.date_input("Check Out", value=date.fromisoformat(reservation["Check Out"]) if reservation["Check Out"] else date.today())
            
            # Row 4: Room Type, Room No
            col1, col2 = st.columns(2)
            with col1:
                room_type = st.selectbox("Room Type", room_types, index=room_types.index(reservation["Room Type"]) if reservation["Room Type"] in room_types else 0)
            with col2:
                if room_type == "Others":
                    room_no = st.text_input("Room No (Enter manually)", value=reservation["Room No"])
                else:
                    room_numbers = property_room_map[property_name].get(room_type, [])
                    # If current room number isn't in the list, add it as an option
                    if reservation["Room No"] not in room_numbers:
                        room_numbers = room_numbers + [reservation["Room No"]]
                    room_no = st.selectbox("Room No", room_numbers, index=room_numbers.index(reservation["Room No"]) if reservation["Room No"] in room_numbers else 0)
            
            # Row 5: No of Adults, Children, Infants
            col1, col2, col3 = st.columns(3)
            with col1:
                no_of_adults = st.number_input("No of Adults", min_value=0, value=reservation["No of Adults"])
            with col2:
                no_of_children = st.number_input("No of Children", min_value=0, value=reservation["No of Children"])
            with col3:
                no_of_infants = st.number_input("No of Infants", min_value=0, value=reservation["No of Infants"])
            
            # Row 6: Rate Plans, Booking Source
            col1, col2 = st.columns(2)
            with col1:
                current_rate_plan = reservation.get("Rate Plans", "EP")
                rate_plan_options = ["EP", "CP", "MAP", "AP"]
                rate_plan_index = rate_plan_options.index(current_rate_plan) if current_rate_plan in rate_plan_options else 0
                rate_plans = st.selectbox("Rate Plans", rate_plan_options, index=rate_plan_index, help="EP: European Plan, CP: Continental Plan, MAP: Modified American Plan, AP: American Plan")
            with col2:
                current_source = reservation.get("Booking Source", "")
                source_index = BOOKING_SOURCES.index(current_source) if current_source in BOOKING_SOURCES else 0
                booking_source = st.selectbox("Booking Source", BOOKING_SOURCES, index=source_index)
            
            # Row 7: Total Tariff, Advance Payment
            col1, col2 = st.columns(2)
            with col1:
                total_tariff = st.number_input("Total Tariff", min_value=0.0, value=reservation["Total Tariff"])
            with col2:
                advance_payment = st.number_input("Advance Payment", min_value=0.0, value=reservation["Advance Payment"])
            
            # Row 8: Balance (Auto-calculated), Advance MOP
            col1, col2 = st.columns(2)
            with col1:
                balance = total_tariff - advance_payment
                st.number_input("Balance", value=balance, disabled=True, help="Auto-calculated: Total Tariff - Advance Payment")
            with col2:
                current_advance_mop = reservation.get("Advance MOP", "Not Paid")
                advance_mop_index = MOP_OPTIONS.index(current_advance_mop) if current_advance_mop in MOP_OPTIONS else MOP_OPTIONS.index("Not Paid")
                advance_mop = st.selectbox("Advance MOP", MOP_OPTIONS, index=advance_mop_index, help="Mode of Payment for advance amount")
            
            # Row 9: Balance MOP
            current_balance_mop = reservation.get("Balance MOP", "Not Paid")
            balance_mop_index = MOP_OPTIONS.index(current_balance_mop) if current_balance_mop in MOP_OPTIONS else MOP_OPTIONS.index("Not Paid")
            balance_mop = st.selectbox("Balance MOP", MOP_OPTIONS, index=balance_mop_index, help="Mode of Payment for balance amount")
            
            # Row 10: Booking Status, Payment Status
            col1, col2 = st.columns(2)
            with col1:
                booking_status = st.selectbox("Booking Status", ["Pending", "Confirmed", "Cancelled", "Follow-up", "Completed", "No Show"], index=["Pending", "Confirmed", "Cancelled", "Follow-up", "Completed", "No Show"].index(reservation["Booking Status"]))
            with col2:
                payment_status = st.selectbox("Payment Status", ["Not Paid", "Fully Paid", "Partially Paid"], index=["Not Paid", "Fully Paid", "Partially Paid"].index(reservation["Payment Status"]))
            
            # Row 11: Submitted By, Modified By
            col1, col2 = st.columns(2)
            with col1:
                submitted_by = st.text_input("Submitted By", value=reservation["Submitted By"], disabled=True)
            with col2:
                modified_by = st.text_input("Modified By", value=st.session_state.username, disabled=True)
            
            # Row 12: Modified Comments, Remarks
            modified_comments = st.text_area("Modified Comments", value=reservation["Modified Comments"])
            remarks = st.text_area("Remarks", value=reservation["Remarks"])
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.form_submit_button("💾 Update Reservation", use_container_width=True):
                    updated_reservation = {
                        "property_name": property_name,
                        "booking_id": reservation["Booking ID"],
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
                        "balance": balance,
                        "advance_mop": advance_mop,
                        "balance_mop": balance_mop,
                        "booking_status": booking_status,
                        "payment_status": payment_status,
                        "submitted_by": reservation["Submitted By"],
                        "modified_by": st.session_state.username,
                        "modified_comments": modified_comments,
                        "remarks": remarks
                    }
                    if update_reservation_in_supabase(reservation["Booking ID"], updated_reservation):
                        st.session_state.reservations[edit_index] = {
                            "Property Name": property_name,
                            "Booking ID": reservation["Booking ID"],
                            "Guest Name": guest_name,
                            "Guest Phone": guest_phone,
                            "Check In": str(check_in),
                            "Check Out": str(check_out),
                            "Room No": room_no,
                            "Room Type": room_type,
                            "No of Adults": no_of_adults,
                            "No of Children": no_of_children,
                            "No of Infants": no_of_infants,
                            "Rate Plans": rate_plans,
                            "Booking Source": booking_source,
                            "Total Tariff": total_tariff,
                            "Advance Payment": advance_payment,
                            "Balance": balance,
                            "Advance MOP": advance_mop,
                            "Balance MOP": balance_mop,
                            "Booking Status": booking_status,
                            "Payment Status": payment_status,
                            "Submitted By": reservation["Submitted By"],
                            "Modified By": st.session_state.username,
                            "Modified Comments": modified_comments,
                            "Remarks": remarks
                        }
                        st.session_state.edit_mode = False
                        st.session_state.edit_index = None
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
                            st.success(f"🗑️ Reservation {reservation['Booking ID']} deleted successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete reservation")
