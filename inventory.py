if daily:
                    is_accounts_team = st.session_state.get('role', '') == "Accounts Team"

                    # ✅ Single table with editable fields for Accounts Team
                    st.subheader("📊 Booking Overview")
                    
                    if is_accounts_team:
                        # Editable table for Accounts Team
                        col_config = {
                            "Inventory No": st.column_config.TextColumn(disabled=True, pinned=True),
                            "Room No": st.column_config.TextColumn(disabled=True, pinned=True),
                            "Booking ID": st.column_config.TextColumn(disabled=True, pinned=True),
                            "Guest Name": st.column_config.TextColumn(disabled=True),
                            "Mobile No": st.column_config.TextColumn(disabled=True),
                            "Total Pax": st.column_config.NumberColumn(disabled=True),
                            "Check In": st.column_config.TextColumn(disabled=True),
                            "Check Out": st.column_config.TextColumn(disabled=True),
                            "Days": st.column_config.NumberColumn(disabled=True),
                            "MOB": st.column_config.TextColumn(disabled=True),
                            "Room Charges": st.column_config.TextColumn(disabled=True),
                            "GST": st.column_config.TextColumn(disabled=True),
                            "TAX": st.column_config.TextColumn(disabled=True),
                            "Total": st.column_config.TextColumn("💰 Total", disabled=True),
                            "Commission": st.column_config.TextColumn(disabled=True),
                            "Hotel Receivable": st.column_config.TextColumn(disabled=True),
                            "Per Night": st.column_config.TextColumn(disabled=True),
                            "Advance": st.column_config.TextColumn("💳 Advance", disabled=True),
                            "Advance Mop": st.column_config.TextColumn(disabled=True),
                            "Balance": st.column_config.TextColumn(disabled=True),
                            "Balance Mop": st.column_config.TextColumn("💵 Balance Mop", disabled=True),
                            "Plan": st.column_config.TextColumn(disabled=True),
                            "Booking Status": st.column_config.TextColumn(disabled=True),
                            "Payment Status": st.column_config.TextColumn(disabled=True),
                            "Submitted by": st.column_config.TextColumn(disabled=True),
                            "Modified by": st.column_config.TextColumn(disabled=True),
                            "Remarks": st.column_config.TextColumn(disabled=True),
                            "Advance Remarks": st.column_config.TextColumn("✏️ Advance Remarks", disabled=False, max_chars=500),
                            "Balance Remarks": st.column_config.TextColumn("✏️ Balance Remarks", disabled=False, max_chars=500),
                            "Accounts Status": st.column_config.SelectboxColumn("✏️ Accounts Status", options=["Pending", "Completed"], disabled=False),
                        }

                        unique_key = f"{prop.replace(' ', '_')}_{day.strftime('%Y%m%d')}"

                        with st.form(key=f"form_{unique_key}"):
                            edited = st.data_editor(
                                display_df,
                                column_config=col_config,
                                hide_index=True,
                                use_container_width=True,
                                num_rows="fixed",
                                key=f"editor_{unique_key}",
                                height=400
                            )
                            
                            submitted = st.form_submit_button("💾 Save Changes", use_container_width=False)

                            if submitted:
                                updates = {}
                                for i in range(len(edited)):
                                    er = edited.iloc[i]
                                    fr = full_df.iloc[i]
                                    
                                    bid = str(er.get("Booking ID", "")).strip()
                                    if not bid:
                                        continue

                                    db_id = str(fr.get("db_id", "")).strip()
                                    btype = str(fr.get("type", "")).strip()

                                    if not db_id or not btype:
                                        continue

                                    update_key = f"{bid}_{i}"
                                    
                                    advance_remarks = str(er.get("Advance Remarks", "") or "").strip()
                                    balance_remarks = str(er.get("Balance Remarks", "") or "").strip()
                                    accounts_status = str(er.get("Accounts Status", "Pending")).strip()
                                    
                                    updates[update_key] = {
                                        "advance_remarks": advance_remarks if advance_remarks else None,
                                        "balance_remarks": balance_remarks if balance_remarks else None,
                                        "accounts_status": accounts_status,
                                        "type": btype,
                                        "db_id": db_id,
                                        "booking_id": bid
                                    }

                                success = error = 0
                                error_details = []
                                processed_bookings = set()

                                for update_key, data in updates.items():
                                    bid = data["booking_id"]
                                    
                                    if bid in processed_bookings:
                                        continue
                                    
                                    processed_bookings.add(bid)
                                    
                                    update_data = {
                                        "advance_remarks": data["advance_remarks"],
                                        "balance_remarks": data["balance_remarks"],
                                        "accounts_status": data["accounts_status"],
                                    }
                                    
                                    update_data = {k: v for k, v in update_data.items() if v is not None}
                                    
                                    logging.info(f"Saving {data['type']} booking {bid} | Key: {data['db_id'] if data['type']=='online' else bid} | Data: {update_data}")

                                    try:
                                        if data["type"] == "online":
                                            res = supabase.table("online_reservations").update(update_data).eq("id", data["db_id"]).execute()
                                        else:
                                            res = supabase.table("reservations").update(update_data).eq("booking_id", bid).execute()

                                        if res.data:
                                            success += 1
                                            logging.info(f"Successfully updated {bid}")
                                        else:
                                            error += 1
                                            error_details.append(f"{bid}: No rows updated")
                                            logging.warning(f"No rows updated for {bid}")
                                    except Exception as e:
                                        error += 1
                                        error_details.append(f"{bid}: {str(e)}")
                                        logging.error(f"Save failed {bid}: {e}")

                                if success:
                                    st.success(f"✅ Saved {success} booking(s)!")
                                    st.cache_data.clear()
                                    st.rerun()
                                if error:
                                    st.error(f"⚠️ {error} failed")
                                    with st.expander("Error Details"):
                                        for msg in error_details:
                                            st.code(msg)
                    else:
                        # Read-only table for non-Accounts Team
                        styled_display = display_df.style.apply(highlight_columns, axis=None)
                        st.dataframe(styled_display, use_container_width=True, height=400, hide_index=True)
