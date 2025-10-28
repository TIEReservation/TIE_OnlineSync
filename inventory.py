def show_daily_status():
    """Display daily status table with inventory and bookings."""
    st.title("📅 Daily Status")
    if st.button("🔄 Refresh Property List"):
        st.cache_data.clear()
        st.success("Cache cleared! Refreshing properties...")
        st.rerun()
    current_year = date.today().year
    year = st.selectbox("Select Year", list(range(current_year - 5, current_year + 6)), index=5)
    month = st.selectbox("Select Month", list(range(1, 13)), index=date.today().month - 1)
    properties = cached_load_properties()
    if not properties:
        st.info("No properties available.")
        return
    st.subheader("Properties")
    st.markdown(TABLE_CSS, unsafe_allow_html=True)
    for prop in properties:
        with st.expander(f"{prop}"):
            month_dates = generate_month_dates(year, month)
            start_date = month_dates[0]
            end_date = month_dates[-1]
            bookings = cached_load_bookings(prop, start_date, end_date)
            for day in month_dates:
                daily_bookings = filter_bookings_for_day(bookings, day)
                st.subheader(f"{prop} - {day.strftime('%B %d, %Y')}")
                if daily_bookings:
                    daily_bookings, overbookings = assign_inventory_numbers(daily_bookings, prop)
                    df = create_inventory_table(daily_bookings, overbookings, prop)
                    # Remove HTML links from Booking ID column
                    if 'Booking ID' in df.columns:
                        df['Booking ID'] = df['Booking ID'].apply(lambda x: x.split('">')[1].split('</a>')[0] if '">' in str(x) and '</a>' in str(x) else x)
                    tooltip_columns = ['Guest Name', 'Room No', 'Remarks', 'Mobile No', 'MOB', 'Plan', 'Submitted by', 'Modified by']
                    for col in tooltip_columns:
                        if col in df.columns:
                            df[col] = df[col].apply(lambda x: f'<span title="{x}">{x}</span>' if isinstance(x, str) else x)
                    table_html = df.to_html(escape=False, index=False)
                    st.markdown(f'<div class="custom-scrollable-table">{table_html}</div>', unsafe_allow_html=True)
                    
                    # Compute and display statistics
                    dtd_df, mtd_df, summary, mop_df = compute_statistics(bookings, prop, day, month_dates)
                    
                    # Display all 4 reports side by side in 4 columns
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.subheader("MOP Report")
                        st.dataframe(mop_df, use_container_width=True)
                    
                    with col2:
                        st.subheader("D.T.D Statistics")
                        st.dataframe(dtd_df, use_container_width=True)
                    
                    with col3:
                        st.subheader("M.T.D Statistics")
                        st.dataframe(mtd_df, use_container_width=True)
                    
                    with col4:
                        st.subheader("Summary")
                        summary_df = pd.DataFrame([
                            {"Metric": "Rooms Sold", "Value": summary["rooms_sold"]},
                            {"Metric": "Value", "Value": f"{summary['value']:.2f}"},
                            {"Metric": "ARR", "Value": f"{summary['arr']:.2f}"},
                            {"Metric": "Occ%", "Value": f"{summary['occ_percent']:.2f}%"},
                            {"Metric": "Total Pax", "Value": summary["total_pax"]},
                            {"Metric": "Total Inventory", "Value": summary["total_inventory"]},
                            {"Metric": "GST ", "Value": f"{summary['gst']:.2f}"},
                            {"Metric": "Commission", "Value": f"{summary['commission']:.2f}"},
                            {"Metric": "TAX Deduction", "Value": f"{summary['tax_deduction']:.2f}"},
                            {"Metric": "M.T.D Occ %", "Value": f"{summary['mtd_occ_percent']:.2f}%"},
                            {"Metric": "M.T.D Pax", "Value": summary["mtd_pax"]},
                            {"Metric": "M.T.D Rooms", "Value": summary["mtd_rooms"]},
                            {"Metric": "M.T.D GST", "Value": f"{summary['mtd_gst']:.2f}"},
                            {"Metric": "M.T.D Tax Deduc", "Value": f"{summary['mtd_tax_deduction']:.2f}"},
                            {"Metric": "M.T.D Value", "Value": f"{summary['mtd_value']:.2f}"}
                        ])
                        st.dataframe(summary_df, use_container_width=True)
                else:
                    st.info("No active bookings on this day.")
