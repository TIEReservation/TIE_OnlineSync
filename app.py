def show_edit_form(edit_index):
    st.markdown("---")
    st.subheader("✏️ Edit Reservation")
    
    # Get current reservation data
    current_reservation = st.session_state.reservations[edit_index]
    
    # Display current booking ID for reference
    st.info(f"Editing Booking ID: {current_reservation['Booking ID']}")
    
    with st.form("edit_reservation_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            property_options = [
                "Eden Beach Resort",
                "La Paradise Luxury",
                "La Villa Heritage",
                "Le Pondy Beach Side",
                "Le Royce Villa",
                "Le Poshe Luxury",
                "Le Poshe Suite",
                "La Paradise Residency",
                "La Tamara Luxury",
                "Le Poshe Beachview",
                "La Antilia",
                "La Tamara Suite",
                "La Millionare Resort",
                "Le Park Resort"
            ]
            current_property = current_reservation["Property Name"]
            if current_property not in property_options:
                property_options.append(current_property)
            property_name = st.selectbox("Property Name", property_options, 
                                       index=property_options.index(current_property))
            room_no = st.text_input("Room No", value=current_reservation["Room No"])
            guest_name = st.text_input("Guest Name", value=current_reservation["Guest Name"])
            mobile_no = st.text_input("Mobile No", value=current_reservation["Mobile No"])
            
        with col2:
            adults = st.number_input("No of Adults", min_value=0, value=current_reservation["No of Adults"])
            children = st.number_input("No of Children", min_value=0, value=current_reservation["No of Children"])
            infants = st.number_input("No of Infants", min_value=0, value=current_reservation["No of Infants"])
            total_pax = adults + children + infants
            st.text_input("Total Pax", value=str(total_pax), disabled=True)
            
        with col3:
            check_in = st.date_input("Check In", value=current_reservation["Check In"])
            check_out = st.date_input("Check Out", value=current_reservation["Check Out"])
            no_of_days = calculate_days(check_in, check_out)
            st.text_input("No of Days", value=str(max(0, no_of_days)), disabled=True)
            
            # Fixed Room Type options to match the original form
            room_type_options = ["Double", "Triple", "Family", "1BHK", "2BHK", "3BHK", "4BHK", "Superior Villa"]
            current_room_type = current_reservation["Room Type"]
            if current_room_type not in room_type_options:
                room_type_options.append(current_room_type)
            room_type = st.selectbox("Room Type", room_type_options, 
                                   index=room_type_options.index(current_room_type))
        
        col4, col5 = st.columns(2)
        
        with col4:
            tariff = st.number_input("Tariff (per day)", min_value=0.0, value=current_reservation["Tariff"], step=100.0)
            total_tariff = tariff * max(0, no_of_days)
            st.text_input("Total Tariff", value=f"₹{total_tariff:.2f}", disabled=True)
            
            # Fixed MOP options to match the original form
            advance_mop_options = ["Cash", "Card", "UPI", "Bank Transfer", "Agoda", "MMT", "Airbnb", "Expedia", "Staflexi", "Website"]
            current_advance_mop = current_reservation["Advance MOP"]
            if current_advance_mop not in advance_mop_options:
                advance_mop_options.append(current_advance_mop)
            advance_mop = st.selectbox("Advance MOP", advance_mop_options, 
                                     index=advance_mop_options.index(current_advance_mop))
            
            balance_mop_options = ["Cash", "Card", "UPI", "Bank Transfer", "Agoda", "MMT", "Airbnb", "Expedia", "Stayflexi", "Website", "Pending"]
            current_balance_mop = current_reservation["Balance MOP"]
            if current_balance_mop not in balance_mop_options:
                balance_mop_options.append(current_balance_mop)
            balance_mop = st.selectbox("Balance MOP", balance_mop_options, 
                                     index=balance_mop_options.index(current_balance_mop))
            
        with col5:
            advance_amount = st.number_input("Advance Amount", min_value=0.0, value=current_reservation["Advance Amount"], step=100.0)
            balance_amount = max(0, total_tariff - advance_amount)
            st.text_input("Balance Amount", value=f"₹{balance_amount:.2f}", disabled=True)
            mob = st.text_input("MOB (Mode of Booking)", value=current_reservation["MOB"])
            invoice_no = st.text_input("Invoice No", value=current_reservation["Invoice No"])
        
        col6, col7 = st.columns(2)
        
        with col6:
            enquiry_date = st.date_input("Enquiry Date", value=current_reservation["Enquiry Date"])
            booking_date = st.date_input("Booking Date", value=current_reservation["Booking Date"])
            booking_source_options = ["Direct", "Online", "Agent", "Walk-in", "Phone"]
            current_booking_source = current_reservation["Booking Source"]
            if current_booking_source not in booking_source_options:
                booking_source_options.append(current_booking_source)
            booking_source = st.selectbox("Booking Source", booking_source_options, 
                                        index=booking_source_options.index(current_booking_source))
            
        with col7:
            # Fixed Breakfast options to match the original form
            breakfast_options = ["CP", "EP"]
            current_breakfast = current_reservation["Breakfast"]
            if current_breakfast not in breakfast_options:
                breakfast_options.append(current_breakfast)
            breakfast = st.selectbox("Breakfast", breakfast_options, 
                                   index=breakfast_options.index(current_breakfast))
            
            # Fixed Plan Status options to match the original form
            plan_status_options = ["Confirmed", "Pending", "Cancelled", "Completed", "No Show"]
            current_plan_status = current_reservation["Plan Status"]
            if current_plan_status not in plan_status_options:
                plan_status_options.append(current_plan_status)
            plan_status = st.selectbox("Plan Status", plan_status_options, 
                                     index=plan_status_options.index(current_plan_status))
        
        # Form buttons - Made more prominent
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        
        with col_btn1:
            update_submitted = st.form_submit_button("✅ Update Reservation", 
                                                    use_container_width=True, 
                                                    type="primary")
        
        with col_btn2:
            cancel_edit = st.form_submit_button("❌ Cancel Edit", 
                                              use_container_width=True)
        
        with col_btn3:
            # Optional: Add a delete button if needed
            delete_reservation = st.form_submit_button("🗑️ Delete Reservation", 
                                                     use_container_width=True,
                                                     type="secondary")
        
        # Handle form submissions
        if cancel_edit:
            st.session_state.edit_mode = False
            st.session_state.edit_index = None
            st.rerun()
        
        if delete_reservation:
            # Add confirmation dialog
            if st.session_state.get('confirm_delete', False):
                # Delete the reservation
                st.session_state.reservations.pop(edit_index)
                st.success(f"✅ Reservation {current_reservation['Booking ID']} deleted successfully!")
                st.session_state.edit_mode = False
                st.session_state.edit_index = None
                st.session_state.confirm_delete = False
                st.rerun()
            else:
                st.session_state.confirm_delete = True
                st.error("⚠️ Click 'Delete Reservation' again to confirm deletion!")
        
        if update_submitted:
            # Reset delete confirmation
            st.session_state.confirm_delete = False
            
            # Validation checks
            if not all([property_name, room_no, guest_name, mobile_no]):
                st.error("❌ Please fill in all required fields (Property Name, Room No, Guest Name, Mobile No)")
            elif check_out <= check_in:
                st.error("❌ Check-out date must be after check-in date")
            else:
                # Check for duplicate guest (excluding current reservation)
                is_duplicate, existing_booking_id = check_duplicate_guest(guest_name, mobile_no, room_no, exclude_index=edit_index)
                
                if is_duplicate:
                    st.error(f"❌ Guest '{guest_name}' with mobile '{mobile_no}' in room '{room_no}' already exists! Existing Booking ID: {existing_booking_id}")
                else:
                    # Calculate final values
                    no_of_days = calculate_days(check_in, check_out)
                    total_tariff = tariff * max(0, no_of_days)
                    balance_amount = max(0, total_tariff - advance_amount)
                    
                    # Update reservation record
                    updated_reservation = {
                        "Property Name": property_name,
                        "Room No": room_no,
                        "Guest Name": guest_name,
                        "Mobile No": mobile_no,
                        "No of Adults": adults,
                        "No of Children": children,
                        "No of Infants": infants,
                        "Total Pax": total_pax,
                        "Check In": check_in,
                        "Check Out": check_out,
                        "No of Days": no_of_days,
                        "Tariff": tariff,
                        "Total Tariff": total_tariff,
                        "Advance Amount": advance_amount,
                        "Balance Amount": balance_amount,
                        "Advance MOP": advance_mop,
                        "Balance MOP": balance_mop,
                        "MOB": mob,
                        "Invoice No": invoice_no,
                        "Enquiry Date": enquiry_date,
                        "Booking Date": booking_date,
                        "Booking ID": current_reservation["Booking ID"],  # Keep original booking ID
                        "Booking Source": booking_source,
                        "Room Type": room_type,
                        "Breakfast": breakfast,
                        "Plan Status": plan_status
                    }
                    
                    # Update the reservation in session state
                    st.session_state.reservations[edit_index] = updated_reservation
                    
                    st.success(f"✅ Reservation updated successfully! Booking ID: {current_reservation['Booking ID']}")
                    st.balloons()
                    
                    # Reset edit mode
                    st.session_state.edit_mode = False
                    st.session_state.edit_index = None
                    st.rerun()
