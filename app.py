import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase import create_client, Client
from direservations import load_reservations_from_supabase, show_new_reservation_form, show_reservations, show_edit_reservations
from online_reservations import show_online_reservations

# Initialize Supabase client
supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

# Page config
st.set_page_config(
    page_title="TIE Reservation System",
    page_icon="https://github.com/TIEReservation/TIEReservation-System/raw/main/TIE_Logo_Icon.png",
    layout="wide"
)

# Display logo
st.image("https://github.com/TIEReservation/TIEReservation-System/raw/main/TIE_Logo_Icon.png", width=100)

def check_authentication():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.role = None
    if not st.session_state.authenticated:
        st.title("🔐 TIE Reservation System Login")
        st.write("Please select your role and enter the password to access the system.")
        role = st.selectbox("Select Role", ["Management", "ReservationTeam"])
        password = st.text_input("Enter password:", type="password")
        if st.button("🔑 Login"):
            if role == "Management" and password == "TIE2024":
                st.session_state.authenticated = True
                st.session_state.role = "Management"
                st.session_state.reservations = load_reservations_from_supabase()
                st.success("✅ Management login successful! Redirecting...")
                st.rerun()
            elif role == "ReservationTeam" and password == "TIE123":
                st.session_state.authenticated = True
                st.session_state.role = "ReservationTeam"
                st.session_state.reservations = load_reservations_from_supabase()
                st.success("✅ Agent login successful! Redirecting...")
                st.rerun()
            else:
                st.error("❌ Invalid password. Please try again.")
        st.stop()

check_authentication()

if 'reservations' not in st.session_state:
    st.session_state.reservations = []

if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
    st.session_state.edit_index = None

def show_analytics():
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
        filter_status = st.selectbox("Filter by Status", ["All", "Confirmed", "Pending", "Cancelled", "Completed", "No Show"], key="analytics_filter_status")
    with col2:
        filter_check_in_date = st.date_input("Check-in Date", value=None, key="analytics_filter_check_in_date")
    with col3:
        filter_check_out_date = st.date_input("Check-out Date", value=None, key="analytics_filter_check_out_date")
    with col4:
        filter_enquiry_date = st.date_input("Enquiry Date", value=None, key="analytics_filter_enquiry_date")
    with col5:
        filter_booking_date = st.date_input("Booking Date", value=None, key="analytics_filter_booking_date")
    with col6:
        filter_property = st.selectbox("Filter by Property", ["All"] + list(df["Property Name"].unique()), key="analytics_filter_property")

    filtered_df = df.copy()
    if filter_status != "All":
        filtered_df = filtered_df[filtered_df["Plan Status"] == filter_status]
    if filter_check_in_date:
        filtered_df = filtered_df[filtered_df["Check In"] == filter_check_in_date]
    if filter_check_out_date:
        filtered_df = filtered_df[filtered_df["Check Out"] == filter_check_out_date]
    if filter_enquiry_date:
        filtered_df = filtered_df[filtered_df["Enquiry Date"] == filter_enquiry_date]
    if filter_booking_date:
        filtered_df = filtered_df[filtered_df["Booking Date"] == filter_booking_date]
    if filter_property != "All":
        filtered_df = filtered_df[filtered_df["Property Name"] == filter_property]

    if filtered_df.empty:
        st.warning("No reservations match the selected filters.")
        return

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
        total_collected = filtered_df["Advance Amount"].sum() + filtered_df[filtered_df["Plan Status"] == "Completed"]["Balance Amount"].sum()
        st.metric("Total Revenue Collected", f"₹{total_collected:,.2f}")
    with col6:
        balance_pending = filtered_df[filtered_df["Plan Status"] != "Completed"]["Balance Amount"].sum()
        st.metric("Balance Pending", f"₹{balance_pending:,.2f}")

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
        st.plotly_chart(fig_pie, use_container_width=True)
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
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Property-wise Reservation Details")
    properties = filtered_df["Property Name"].unique()
    for property in properties:
        with st.expander(f"{property} Reservations"):
            property_df = filtered_df[filtered_df["Property Name"] == property]
            st.write(f"**Total Reservations**: {len(property_df)}")
            total_revenue = property_df["Total Tariff"].sum()
            st.write(f"**Total Revenue**: ₹{total_revenue:,.2f}")
            total_collected = property_df["Advance Amount"].sum() + property_df[property_df["Plan Status"] == "Completed"]["Balance Amount"].sum()
            st.write(f"**Total Revenue Collected**: ₹{total_collected:,.2f}")
            balance_pending = property_df[property_df["Plan Status"] != "Completed"]["Balance Amount"].sum()
            st.write(f"**Balance Pending**: ₹{balance_pending:,.2f}")
            st.write(f"**Average Tariff**: ₹{property_df['Tariff'].mean():,.2f}" if not property_df.empty else "₹0.00")
            st.write(f"**Average Stay**: {property_df['No of Days'].mean():.1f} days" if not property_df.empty else "0.0 days")
            st.dataframe(
                property_df[["Booking ID", "Guest Name", "Room No", "Check In", "Check Out", "Total Tariff", "Plan Status", "MOB"]],
                use_container_width=True
            )

def main():
    st.title("🏢 TIE Reservation System")
    st.markdown("---")
    st.sidebar.title("Navigation")
    page_options = ["Direct Reservations", "View Reservations", "Edit Reservations", "Online Reservations"]
    if st.session_state.role == "Management":
        page_options.append("Analytics")
    page = st.sidebar.selectbox("Choose a page", page_options)

    if page == "Direct Reservations":
        show_new_reservation_form()
    elif page == "View Reservations":
        show_reservations()
    elif page == "Edit Reservations":
        show_edit_reservations()
    elif page == "Online Reservations":
        show_online_reservations()
    elif page == "Analytics" and st.session_state.role == "Management":
        show_analytics()

if __name__ == "__main__":
    main()
