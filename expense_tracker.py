import streamlit as st
from supabase import create_client, Client

# Initialize Supabase client
def init_supabase():
    url = 'your_supabase_url'
    key = 'your_supabase_key'
    return create_client(url, key)

# Function to display the expense tracker
@st.cache_data
def display_expense_tracker():
    supabase = init_supabase()
    
    # Define table structure
    columns = ['Sl No', 'Expense made Date', 'Person who made expense', 'Particulars', 'Property Name', 'Other comments', 'Submitted by']
    expenses = []  # Placeholder for data fetched from Supabase
    
    # Fetch existing data (if any)
    data = supabase.table('expenses').select('*').execute()
    if data['data']:
        expenses = data['data']
    else:
        expenses = []
    
    # Display the editable table
    df = st.data_editor(
        "Expense Tracker",
        data=expenses,
        column_order=columns,
        height=300,
        editor='edit',
        use_container_width=True
    )

    # Save data to Supabase
    if st.button('Save'):  
        for index, row in df.iterrows():
            if row['Sl No'] is None:
                # If Sl No is not present, auto increment it
                row['Sl No'] = len(expenses) + 1
            supabase.table('expenses').upsert(row.to_dict()).execute()
        st.success('Data saved successfully!')

# Check and enforce role-based access control
user_role = 'Management'  # Replace this with actual role from user session
if user_role in ['Management', 'Accounts Team']:
    display_expense_tracker()
else:
    st.warning('You do not have access to view this expense tracker.')