# accounts_report.py - Monthly Accounts Report with Property-wise filtering
import streamlit as st
from supabase import create_client, Client
from datetime import date, datetime
import calendar
import pandas as pd
from typing import List, Dict, Optional
import logging

# ────── Logging ──────
logging.basicConfig(filename="accounts_report.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ────── Supabase client ──────
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

# ────── Property synonym mapping ──────
property_mapping = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view",
    "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Le Poshe Beachview": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
    "Le Pondy Beach Side": "Le Pondy Beachside",
    "Le Teera": "Le Terra"
}

def normalize_property(name: str) -> str:
    """Normalize property names using mapping."""
    return property_mapping.get(name.strip(), name.strip())

def safe_float(v, default: float = 0.0) -> float:
    """Safely convert value to float."""
    try:
        return float(v) if v not in [None, "", " "] else default
    except:
        return default

def sanitize_string(v, default: str = "") -> str:
    """Sanitize string values."""
    return str(v).strip() if v is not None else default

# ────────────────────────────────────────────────────────────────────────
# Load bookings with pagination for entire month
# ────────────────────────────────────────────────────────────────────────
def load_all_bookings_for_month(year: int, month: int) -> List[Dict]:
    """Load ALL bookings (both direct and online) for the given month with pagination."""
    try:
        # Calculate month date range
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        
        all_bookings = []
        
        # ───── Load Direct Reservations with pagination ─────
        st.info("Loading direct reservations...")
        page_size = 1000
        start = 0
        
        while True:
            response = supabase.table("reservations")\
                .select("*")\
                .lte("check_in", str(last_day))\
                .gte("check_out", str(first_day))\
                .in_("plan_status", ["Confirmed", "Completed"])\
                .order("check_in", desc=False)\
                .range(start, start + page_size - 1)\
                .execute()
            
            if not response.data:
                break
            
            for record in response.data:
                try:
                    check_in = date.fromisoformat(record["check_in"])
                    check_out = date.fromisoformat(record["check_out"])
                    
                    # Only include bookings that overlap with the selected month
                    if check_out <= first_day or check_in > last_day:
                        continue
                    
                    booking = {
                        "type": "direct",
                        "date": check_in,
                        "property_name": normalize_property(record.get("property_name", "")),
                        "guest_name": sanitize_string(record.get("guest_name")),
                        "booking_id": sanitize_string(record.get("booking_id")),
                        "total_amount": safe_float(record.get("total_tariff")),
                        "advance": safe_float(record.get("advance_amount")),
                        "balance": safe_float(record.get("balance_amount")),
                        "check_in": str(check_in),
                        "check_out": str(check_out),
                        "booking_status": sanitize_string(record.get("plan_status")),
                        "payment_status": sanitize_string(record.get("payment_status")),
                    }
                    
                    # Calculate pending amount
                    booking["pending"] = booking["total_amount"] - booking["advance"] - booking["balance"]
                    
                    all_bookings.append(booking)
                except Exception as e:
                    logging.warning(f"Error processing direct booking: {e}")
                    continue
            
            if len(response.data) < page_size:
                break
            
            start += page_size
        
        # ───── Load Online Reservations with pagination ─────
        st.info("Loading online reservations...")
        start = 0
        
        while True:
            response = supabase.table("online_reservations")\
                .select("*")\
                .lte("check_in", str(last_day))\
                .gte("check_out", str(first_day))\
                .in_("booking_status", ["Confirmed", "Completed"])\
                .order("check_in", desc=False)\
                .range(start, start + page_size - 1)\
                .execute()
            
            if not response.data:
                break
            
            for record in response.data:
                try:
                    check_in = date.fromisoformat(record["check_in"])
                    check_out = date.fromisoformat(record["check_out"])
                    
                    # Only include bookings that overlap with the selected month
                    if check_out <= first_day or check_in > last_day:
                        continue
                    
                    # For online bookings, calculate amounts
                    total_amount = safe_float(record.get("booking_amount"))
                    gst = safe_float(record.get("gst"))
                    tax = safe_float(record.get("ota_tax"))
                    commission = safe_float(record.get("ota_commission"))
                    
                    # Hotel receivable = Total - GST - Tax - Commission
                    receivable = total_amount - gst - tax - commission
                    
                    booking = {
                        "type": "online",
                        "date": check_in,
                        "property_name": normalize_property(record.get("property", "")),
                        "guest_name": sanitize_string(record.get("guest_name")),
                        "booking_id": sanitize_string(record.get("booking_id") or record.get("id")),
                        "total_amount": receivable,  # Use hotel receivable for online bookings
                        "advance": safe_float(record.get("total_payment_made")),
                        "balance": safe_float(record.get("balance_due")),
                        "check_in": str(check_in),
                        "check_out": str(check_out),
                        "booking_status": sanitize_string(record.get("booking_status")),
                        "payment_status": sanitize_string(record.get("payment_status")),
                    }
                    
                    # Calculate pending amount
                    booking["pending"] = booking["total_amount"] - booking["advance"] - booking["balance"]
                    
                    all_bookings.append(booking)
                except Exception as e:
                    logging.warning(f"Error processing online booking: {e}")
                    continue
            
            if len(response.data) < page_size:
                break
            
            start += page_size
        
        logging.info(f"Loaded {len(all_bookings)} total bookings for {year}-{month:02d}")
        return all_bookings
        
    except Exception as e:
        st.error(f"Error loading bookings: {e}")
        logging.error(f"Error loading bookings: {e}")
        return []

# ────────────────────────────────────────────────────────────────────────
# Create Accounts Report Table
# ────────────────────────────────────────────────────────────────────────
def create_accounts_report(bookings: List[Dict], property_filter: str = "All") -> pd.DataFrame:
    """Create accounts report table with all bookings."""
    
    # Filter by property if not "All"
    if property_filter != "All":
        bookings = [b for b in bookings if b["property_name"] == property_filter]
    
    if not bookings:
        return pd.DataFrame()
    
    # Create DataFrame
    report_data = []
    for booking in bookings:
        report_data.append({
            "Date": booking["date"].strftime("%Y-%m-%d"),
            "Property Name": booking["property_name"],
            "Guest Name": booking["guest_name"],
            "Booking ID": booking["booking_id"],
            "Check In": booking["check_in"],
            "Check Out": booking["check_out"],
            "Total Amount": booking["total_amount"],
            "Advance": booking["advance"],
            "Balance": booking["balance"],
            "Pending": booking["pending"],
            "Booking Status": booking["booking_status"],
            "Payment Status": booking["payment_status"],
            "Type": booking["type"].title()
        })
    
    df = pd.DataFrame(report_data)
    
    # Sort by date and property
    df = df.sort_values(["Date", "Property Name", "Guest Name"])
    
    return df

# ────────────────────────────────────────────────────────────────────────
# Calculate Summary Statistics
# ────────────────────────────────────────────────────────────────────────
def calculate_summary(df: pd.DataFrame) -> Dict:
    """Calculate summary statistics from the report."""
    if df.empty:
        return {
            "Total Bookings": 0,
            "Total Amount": 0.0,
            "Total Advance": 0.0,
            "Total Balance": 0.0,
            "Total Pending": 0.0
        }
    
    return {
        "Total Bookings": len(df),
        "Total Amount": df["Total Amount"].sum(),
        "Total Advance": df["Advance"].sum(),
        "Total Balance": df["Balance"].sum(),
        "Total Pending": df["Pending"].sum()
    }

# ────────────────────────────────────────────────────────────────────────
# Property-wise Summary
# ────────────────────────────────────────────────────────────────────────
def create_property_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create property-wise summary table."""
    if df.empty:
        return pd.DataFrame()
    
    summary = df.groupby("Property Name").agg({
        "Booking ID": "count",
        "Total Amount": "sum",
        "Advance": "sum",
        "Balance": "sum",
        "Pending": "sum"
    }).reset_index()
    
    summary.columns = ["Property Name", "Bookings", "Total Amount", "Advance", "Balance", "Pending"]
    
    # Add totals row
    totals = {
        "Property Name": "TOTAL",
        "Bookings": summary["Bookings"].sum(),
        "Total Amount": summary["Total Amount"].sum(),
        "Advance": summary["Advance"].sum(),
        "Balance": summary["Balance"].sum(),
        "Pending": summary["Pending"].sum()
    }
    
    summary = pd.concat([summary, pd.DataFrame([totals])], ignore_index=True)
    
    return summary

# ────────────────────────────────────────────────────────────────────────
# Main Dashboard
# ────────────────────────────────────────────────────────────────────────
def show_accounts_report():
    """Main dashboard for accounts report."""
    st.set_page_config(page_title="Accounts Report", layout="wide")
    st.title("📊 Monthly Accounts Report")
    
    # Month and Year Selection
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        today = date.today()
        year = st.selectbox("Year", list(range(today.year - 5, today.year + 6)), index=5)
    
    with col2:
        month = st.selectbox("Month", list(range(1, 13)), index=today.month - 1, format_func=lambda x: calendar.month_name[x])
    
    with col3:
        if st.button("🔄 Refresh Data", use_container_width=False):
            st.cache_data.clear()
            st.rerun()
    
    # Load all bookings for the month
    with st.spinner(f"Loading bookings for {calendar.month_name[month]} {year}..."):
        all_bookings = load_all_bookings_for_month(year, month)
    
    if not all_bookings:
        st.warning(f"No bookings found for {calendar.month_name[month]} {year}")
        return
    
    st.success(f"✅ Loaded {len(all_bookings)} bookings")
    
    # Get unique properties
    properties = sorted(list(set(b["property_name"] for b in all_bookings)))
    
    # Property filter
    st.subheader("🏨 Filter by Property")
    property_filter = st.selectbox("Select Property", ["All"] + properties)
    
    # Create report
    df = create_accounts_report(all_bookings, property_filter)
    
    if df.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # Display Summary Statistics
    st.subheader("📈 Summary Statistics")
    summary = calculate_summary(df)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Bookings", summary["Total Bookings"])
    with col2:
        st.metric("Total Amount", f"₹{summary['Total Amount']:,.2f}")
    with col3:
        st.metric("Total Advance", f"₹{summary['Total Advance']:,.2f}")
    with col4:
        st.metric("Total Balance", f"₹{summary['Total Balance']:,.2f}")
    with col5:
        st.metric("Total Pending", f"₹{summary['Total Pending']:,.2f}", 
                 delta=f"{(summary['Total Pending']/summary['Total Amount']*100):.1f}%" if summary['Total Amount'] > 0 else "0%",
                 delta_color="inverse")
    
    # Property-wise Summary
    st.subheader("🏢 Property-wise Summary")
    property_summary = create_property_summary(df)
    
    # Format currency columns
    for col in ["Total Amount", "Advance", "Balance", "Pending"]:
        property_summary[col] = property_summary[col].apply(lambda x: f"₹{x:,.2f}")
    
    st.dataframe(
        property_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Property Name": st.column_config.TextColumn("Property Name", width="medium"),
            "Bookings": st.column_config.NumberColumn("Bookings", width="small"),
            "Total Amount": st.column_config.TextColumn("Total Amount", width="medium"),
            "Advance": st.column_config.TextColumn("Advance", width="medium"),
            "Balance": st.column_config.TextColumn("Balance", width="medium"),
            "Pending": st.column_config.TextColumn("Pending", width="medium"),
        }
    )
    
    # Detailed Report
    st.subheader("📋 Detailed Accounts Report")
    
    # Format currency columns for display
    display_df = df.copy()
    for col in ["Total Amount", "Advance", "Balance", "Pending"]:
        display_df[col] = display_df[col].apply(lambda x: f"₹{x:,.2f}")
    
    # Style function for highlighting
    def highlight_pending(row):
        """Highlight rows with pending amounts."""
        if "Pending" in row.index:
            try:
                pending_val = float(row["Pending"].replace("₹", "").replace(",", ""))
                if pending_val > 0:
                    return ['background-color: #FFE4E1'] * len(row)
            except:
                pass
        return [''] * len(row)
    
    st.dataframe(
        display_df.style.apply(highlight_pending, axis=1),
        use_container_width=True,
        hide_index=True,
        height=600,
        column_config={
            "Date": st.column_config.DateColumn("Date", format="DD-MM-YYYY", width="small"),
            "Property Name": st.column_config.TextColumn("Property Name", width="medium"),
            "Guest Name": st.column_config.TextColumn("Guest Name", width="medium"),
            "Booking ID": st.column_config.TextColumn("Booking ID", width="small"),
            "Check In": st.column_config.TextColumn("Check In", width="small"),
            "Check Out": st.column_config.TextColumn("Check Out", width="small"),
            "Total Amount": st.column_config.TextColumn("Total Amount", width="small"),
            "Advance": st.column_config.TextColumn("Advance", width="small"),
            "Balance": st.column_config.TextColumn("Balance", width="small"),
            "Pending": st.column_config.TextColumn("Pending", width="small"),
            "Booking Status": st.column_config.TextColumn("Status", width="small"),
            "Payment Status": st.column_config.TextColumn("Payment", width="small"),
            "Type": st.column_config.TextColumn("Type", width="small"),
        }
    )
    
    # Export functionality
    st.subheader("📥 Export Report")
    col1, col2 = st.columns(2)
    
    with col1:
        # Export to CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="📄 Download CSV",
            data=csv,
            file_name=f"accounts_report_{year}_{month:02d}_{property_filter.replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Export property summary
        csv_summary = property_summary.to_csv(index=False)
        st.download_button(
            label="📊 Download Property Summary",
            data=csv_summary,
            file_name=f"property_summary_{year}_{month:02d}.csv",
            mime="text/csv",
            use_container_width=True
        )

if __name__ == "__main__":
    show_accounts_report()
