import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import date

SUPABASE_URL = "https://oxbrezracnmazucnnqox.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94YnJlenJhY25tYXp1Y25ucW94Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM3NjUxMTgsImV4cCI6MjA2OTM0MTExOH0.nqBK2ZxntesLY9qYClpoFPVnXOW10KrzF-UI_DKjbKo"

PROPERTIES = [
    "Le Poshe Beachview", "La Millionaire Resort", "Le Poshe Luxury", "Le Poshe Suite",
    "La Paradise Residency", "La Paradise Luxury", "La Villa Heritage", "Le Pondy Beach Side",
    "Le Royce Villa", "La Tamara Luxury", "La Antilia Luxury", "La Tamara Suite",
    "Le Park Resort", "Villa Shakti", "Eden Beach Resort", "La Coromandel Luxury",
    "Le Terra", "Happymates Forest Retreat", "Other",
]

EXPENSE_CATEGORY_MAP = {
    "Rooms & Housekeeping": [
        "Housekeeping Supplies",
        "Laundry Expenses",
        "Linen & Towels Purchase",
        "Room Amenities (Soap, Shampoo, etc.)",
        "Pest Control",
        "Mattress / Furniture Repairs",
    ],
    "Food & Beverage": [
        "Raw Materials (Vegetables, Meat, Groceries)",
        "Kitchen Supplies",
        "Gas / LPG",
        "Water Cans",
        "Restaurant Consumables",
        "Crockery & Cutlery",
        "Bar Supplies",
    ],
    "Staff & Payroll": [
        "Salaries",
        "Wages (Daily Labour)",
        "Overtime",
        "Staff Food",
        "Staff Uniform",
        "Incentives / Bonus",
        "PF / ESI / Compliance",
    ],
    "Maintenance & Repairs": [
        "Electrical Repairs",
        "Plumbing",
        "AC Service",
        "Generator Maintenance",
        "Lift Maintenance",
        "Carpentry Work",
        "Painting",
        "Civil Work",
    ],
    "Utilities": [
        "Electricity Bill",
        "Water Bill",
        "Internet / WiFi",
        "Cable / TV",
        "Telephone",
        "Sewage Charges",
    ],
    "Sales & Marketing": [
        "Online OTA Commission",
        "Google Ads",
        "Meta Ads",
        "Photography",
        "Branding / Printing",
        "Website Maintenance",
    ],
    "Administrative": [
        "Office Supplies",
        "Stationery",
        "Software Subscription",
        "Accounting Charges",
        "Audit Fees",
        "Legal Fees",
        "Bank Charges",
    ],
    "Transport & Travel": [
        "Fuel",
        "Cab Charges",
        "Staff Travel",
        "Airport Pickup Expenses",
        "Vehicle Maintenance",
    ],
    "Property Specific": [
        "Landscaping / Gardening",
        "Swimming Pool Maintenance",
        "Beach Cleaning",
        "Security Services",
        "CCTV Maintenance",
    ],
    "Guest Experience": [
        "Guest Compensation",
        "Complimentary Items",
        "Event Expenses",
        "Decoration",
        "Entertainment",
    ],
    "Inventory & Purchases": [
        "Furniture Purchase",
        "Equipment Purchase",
        "Kitchen Equipment",
        "Electronics",
        "Generator Purchase",
    ],
    "Miscellaneous": [
        "Miscellaneous Expense",
        "Emergency Expense",
        "Advance Paid",
        "Refund Issued",
        "Other",
    ],
}

ALL_SUBCATEGORIES = [sub for subs in EXPENSE_CATEGORY_MAP.values() for sub in subs]


@st.cache_resource
def get_expense_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def display_expense_tracker():
    supabase = get_expense_supabase()

    st.header("Expense Tracker")
    st.markdown("---")

    st.subheader("Add New Expense")
    with st.form("add_expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            expense_date        = st.date_input("Expense Date", value=date.today())
            person              = st.text_input("Person Who Made Expense")
            particulars         = st.text_input("Particulars")
            expense_group       = st.selectbox("Expense Category", list(EXPENSE_CATEGORY_MAP.keys()))
            expense_subcategory = st.selectbox("Sub-Category", EXPENSE_CATEGORY_MAP[expense_group])
        with col2:
            property_name  = st.selectbox("Property Name", PROPERTIES)
            amount         = st.number_input("Amount (Rs.)", min_value=0.0, format="%.2f")
            other_comments = st.text_area("Other Comments", height=120)

        submitted_by = st.text_input("Submitted By", value=st.session_state.get("username", ""))

        submit = st.form_submit_button("Add Expense")
        if submit:
            if not person or not particulars:
                st.error("Please fill in at least 'Person' and 'Particulars'.")
            else:
                new_row = {
                    "expense_date":        str(expense_date),
                    "person":              person,
                    "particulars":         particulars,
                    "expense_category":    expense_group,
                    "expense_subcategory": expense_subcategory,
                    "property_name":       property_name,
                    "amount":              amount,
                    "other_comments":      other_comments,
                    "submitted_by":        submitted_by,
                }
                try:
                    supabase.table("expenses").insert(new_row).execute()
                    st.success("Expense added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save expense: {e}")

    st.markdown("---")

    st.subheader("All Expenses")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        filter_property = st.selectbox("Filter by Property", ["All"] + PROPERTIES, key="filter_property")
    with col2:
        filter_group = st.selectbox("Filter by Category", ["All"] + list(EXPENSE_CATEGORY_MAP.keys()), key="filter_group")
    with col3:
        sub_options = ["All"] + (EXPENSE_CATEGORY_MAP[filter_group] if filter_group != "All" else ALL_SUBCATEGORIES)
        filter_sub = st.selectbox("Filter by Sub-Category", sub_options, key="filter_sub")
    with col4:
        filter_from = st.date_input("From Date", value=date(date.today().year, date.today().month, 1), key="filter_from")
    with col5:
        filter_to = st.date_input("To Date", value=date.today(), key="filter_to")

    try:
        result = supabase.table("expenses").select("*").order("expense_date", desc=True).execute()
        data   = result.data if result.data else []

        if data:
            df = pd.DataFrame(data)
            df["expense_date"] = pd.to_datetime(df["expense_date"]).dt.date

            df = df[(df["expense_date"] >= filter_from) & (df["expense_date"] <= filter_to)]
            if filter_property != "All":
                df = df[df["property_name"] == filter_property]
            if filter_group != "All" and "expense_category" in df.columns:
                df = df[df["expense_category"] == filter_group]
            if filter_sub != "All" and "expense_subcategory" in df.columns:
                df = df[df["expense_subcategory"] == filter_sub]

            display_cols = [
                "id", "expense_date", "person", "particulars",
                "expense_category", "expense_subcategory",
                "property_name", "amount", "other_comments", "submitted_by",
            ]
            display_cols = [c for c in display_cols if c in df.columns]
            df = df[display_cols]

            total = df["amount"].sum() if "amount" in df.columns else 0
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Expenses (filtered)", f"Rs. {total:,.2f}")
            m2.metric("No. of Records", len(df))
            if "expense_subcategory" in df.columns and not df.empty:
                top_sub = df.groupby("expense_subcategory")["amount"].sum().idxmax()
                m3.metric("Top Sub-Category", top_sub)

            st.dataframe(df, use_container_width=True, hide_index=True)

            if "expense_subcategory" in df.columns and not df.empty:
                with st.expander("Category-wise Summary"):
                    cat_summary = (
                        df.groupby(["expense_category", "expense_subcategory"])["amount"]
                        .sum()
                        .reset_index()
                        .rename(columns={
                            "expense_category":    "Category",
                            "expense_subcategory": "Sub-Category",
                            "amount":              "Total Amount (Rs.)",
                        })
                        .sort_values("Total Amount (Rs.)", ascending=False)
                    )
                    st.dataframe(cat_summary, use_container_width=True, hide_index=True)
                    st.bar_chart(cat_summary.set_index("Sub-Category")["Total Amount (Rs.)"])

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download as CSV", csv, "expenses.csv", "text/csv")

        else:
            st.info("No expenses found. Add your first expense above!")

    except Exception as e:
        st.error(f"Failed to load expenses: {e}")

    st.markdown("---")

    if st.session_state.get("role") in ["Management", "Admin"]:
        st.subheader("Delete an Expense")
        try:
            result = supabase.table("expenses").select(
                "id, expense_date, person, particulars, expense_category, expense_subcategory, amount"
            ).order("expense_date", desc=True).execute()
            deletable = result.data if result.data else []
            if deletable:
                options = {
                    f"#{r['id']} | {r['expense_date']} | {r.get('expense_category','')}: {r.get('expense_subcategory','')} | {r['person']} | Rs.{r['amount']}": r["id"]
                    for r in deletable
                }
                selected_label = st.selectbox("Select Expense to Delete", list(options.keys()))
                if st.button("Delete Selected Expense"):
                    expense_id = options[selected_label]
                    supabase.table("expenses").delete().eq("id", expense_id).execute()
                    st.success("Expense deleted.")
                    st.rerun()
        except Exception as e:
            st.error(f"Could not load expenses for deletion: {e}")
