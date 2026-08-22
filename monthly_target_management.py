# monthly_target_management.py - Add and manage monthly targets for properties

import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import Client
import json

# Get supabase client from session state or app module
def get_supabase_client() -> Client:
    """Get supabase client"""
    return st.session_state.get("supabase_client")

# List of all properties
ALL_PROPERTIES = [
    "Le Poshe Beachview", "La Millionaire Resort", "Le Poshe Luxury", "Le Poshe Suite",
    "La Paradise Residency", "La Paradise Luxury", "La Villa Heritage", "Le Pondy Beach Side",
    "Le Royce Villa", "La Tamara Luxury", "La Antilia Luxury", "La Tamara Suite",
    "Le Park Resort", "Villa Shakti", "Eden Beach Resort", "La Coromandel Luxury",
    "Le Terra", "Happymates Forest Retreat"
]

def load_monthly_targets(supabase: Client, year: int, month: int) -> dict:
    """Load monthly targets from database for a specific month"""
    try:
        response = supabase.table("monthly_targets").select("*")\
            .eq("year", year)\
            .eq("month", month)\
            .execute()
        
        # Convert to dictionary with property name as key
        targets = {}
        if response.data:
            for record in response.data:
                targets[record["property_name"]] = {
                    "target": record["target"],
                    "id": record.get("id"),
                    "created_at": record.get("created_at"),
                    "updated_at": record.get("updated_at")
                }
        return targets
    except Exception as e:
        st.error(f"Error loading targets: {e}")
        return {}

def add_or_update_target(supabase: Client, property_name: str, year: int, month: int, target: float) -> bool:
    """Add or update a monthly target for a property"""
    try:
        # Check if target already exists
        existing = supabase.table("monthly_targets").select("id").eq("property_name", property_name)\
            .eq("year", year).eq("month", month).execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing
            response = supabase.table("monthly_targets")\
                .update({
                    "target": target,
                    "updated_at": datetime.now().isoformat()
                })\
                .eq("property_name", property_name)\
                .eq("year", year)\
                .eq("month", month)\
                .execute()
        else:
            # Insert new
            response = supabase.table("monthly_targets").insert({
                "property_name": property_name,
                "year": year,
                "month": month,
                "target": target,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }).execute()
        
        return bool(response.data)
    except Exception as e:
        st.error(f"Error saving target for {property_name}: {e}")
        return False

def delete_target(supabase: Client, property_name: str, year: int, month: int) -> bool:
    """Delete a monthly target"""
    try:
        response = supabase.table("monthly_targets").delete()\
            .eq("property_name", property_name)\
            .eq("year", year)\
            .eq("month", month)\
            .execute()
        return True
    except Exception as e:
        st.error(f"Error deleting target: {e}")
        return False

def show_monthly_target_management():
    """Main UI for managing monthly targets"""
    
    # Check if user is Management role
    if st.session_state.role != "Management":
        st.error("Access Denied: Monthly Target Management is available only for Management role.")
        return
    
    st.title("📊 Monthly Target Management")
    st.markdown("Add, edit, or view monthly revenue targets for all properties.")
    
    supabase = get_supabase_client()
    if not supabase:
        st.error("Database connection failed")
        return
    
    # Sidebar: Month and Year Selection
    st.sidebar.markdown("### Select Month & Year")
    current_date = date.today()
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        selected_year = st.number_input(
            "Year", 
            min_value=2020, 
            max_value=2030, 
            value=current_date.year,
            key="target_year"
        )
    with col2:
        selected_month = st.number_input(
            "Month", 
            min_value=1, 
            max_value=12, 
            value=current_date.month,
            key="target_month"
        )
    
    # Load existing targets
    month_name = datetime(selected_year, selected_month, 1).strftime("%B %Y")
    st.subheader(f"Targets for {month_name}")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["Add/Edit Targets", "View Targets", "Bulk Upload"])
    
    # ===== TAB 1: Add/Edit Individual Targets =====
    with tab1:
        st.markdown("#### Add or Edit Target for a Property")
        
        col1, col2 = st.columns(2)
        with col1:
            selected_property = st.selectbox(
                "Select Property",
                options=ALL_PROPERTIES,
                key="edit_property"
            )
        
        # Load current target for this property
        current_targets = load_monthly_targets(supabase, selected_year, selected_month)
        current_value = current_targets.get(selected_property, {}).get("target", 0)
        
        with col2:
            target_amount = st.number_input(
                "Target Amount (₹)",
                min_value=0,
                value=int(current_value) if current_value else 0,
                step=10000,
                key="target_amount"
            )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Save Target", key="save_target_btn"):
                if target_amount > 0:
                    if add_or_update_target(supabase, selected_property, selected_year, selected_month, target_amount):
                        st.success(f"✅ Target saved for {selected_property}: ₹{target_amount:,.0f}")
                        st.rerun()
                else:
                    st.warning("Target amount must be greater than 0")
        
        with col2:
            if current_value > 0:
                if st.button("🗑️ Delete Target", key="delete_target_btn"):
                    if delete_target(supabase, selected_property, selected_year, selected_month):
                        st.success(f"Target deleted for {selected_property}")
                        st.rerun()
        
        with col3:
            if st.button("🔄 Refresh", key="refresh_targets_btn"):
                st.rerun()
    
    # ===== TAB 2: View All Targets =====
    with tab2:
        st.markdown("#### View All Targets for the Selected Month")
        
        current_targets = load_monthly_targets(supabase, selected_year, selected_month)
        
        if current_targets:
            # Create DataFrame for display
            target_data = []
            for prop in sorted(ALL_PROPERTIES):
                if prop in current_targets:
                    target_data.append({
                        "Property Name": prop,
                        "Target (₹)": f"₹{current_targets[prop]['target']:,.0f}",
                        "Updated": current_targets[prop].get('updated_at', 'N/A')[:10]
                    })
                else:
                    target_data.append({
                        "Property Name": prop,
                        "Target (₹)": "Not Set",
                        "Updated": "-"
                    })
            
            df = pd.DataFrame(target_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Summary statistics
            st.markdown("---")
            total_targets = sum(t['target'] for t in current_targets.values())
            properties_with_targets = len(current_targets)
            total_properties = len(ALL_PROPERTIES)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Target Amount", f"₹{total_targets:,.0f}")
            with col2:
                st.metric("Properties Set", f"{properties_with_targets}/{total_properties}")
            with col3:
                st.metric("Properties Missing", f"{total_properties - properties_with_targets}")
            with col4:
                if properties_with_targets > 0:
                    avg_target = total_targets / properties_with_targets
                    st.metric("Average Target", f"₹{avg_target:,.0f}")
            
            # Download button
            st.markdown("---")
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Targets (CSV)",
                data=csv,
                file_name=f"Monthly_Targets_{month_name.replace(' ', '_')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No targets set for this month yet. Use the 'Add/Edit Targets' tab to add targets.")
    
    # ===== TAB 3: Bulk Upload =====
    with tab3:
        st.markdown("#### Bulk Upload Targets from CSV")
        st.info("Upload a CSV file with columns: 'Property Name' and 'Target'. Existing targets will be overwritten.")
        
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv", key="bulk_upload_csv")
        
        if uploaded_file:
            try:
                df_upload = pd.read_csv(uploaded_file)
                
                # Validate CSV structure
                required_columns = ["Property Name", "Target"]
                missing_columns = [col for col in required_columns if col not in df_upload.columns]
                
                if missing_columns:
                    st.error(f"Missing columns: {', '.join(missing_columns)}")
                else:
                    # Show preview
                    st.markdown("**Preview of data to be uploaded:**")
                    st.dataframe(df_upload, use_container_width=True, hide_index=True)
                    
                    if st.button("✅ Confirm and Upload", key="confirm_bulk_upload"):
                        success_count = 0
                        error_count = 0
                        
                        with st.spinner("Uploading targets..."):
                            for idx, row in df_upload.iterrows():
                                prop = row.get("Property Name", "").strip()
                                target = row.get("Target")
                                
                                if not prop or prop not in ALL_PROPERTIES:
                                    error_count += 1
                                    st.warning(f"Row {idx + 1}: Property '{prop}' not found in property list")
                                    continue
                                
                                try:
                                    target_amount = float(target)
                                    if target_amount > 0:
                                        if add_or_update_target(supabase, prop, selected_year, selected_month, target_amount):
                                            success_count += 1
                                        else:
                                            error_count += 1
                                    else:
                                        error_count += 1
                                        st.warning(f"Row {idx + 1}: Target amount must be greater than 0")
                                except ValueError:
                                    error_count += 1
                                    st.warning(f"Row {idx + 1}: Invalid target amount '{target}'")
                        
                        st.success(f"✅ Upload complete! {success_count} targets added/updated.")
                        if error_count > 0:
                            st.warning(f"⚠️ {error_count} rows had errors.")
                        st.rerun()
                        
            except Exception as e:
                st.error(f"Error reading CSV: {e}")

if __name__ == "__main__":
    if "supabase_client" not in st.session_state:
        st.error("This module should be run from the main app")
    else:
        show_monthly_target_management()
