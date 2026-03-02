import streamlit as st
import supabase

# Initialize Supabase client
def init_supabase():
    url = "YOUR_SUPABASE_URL"
    key = "YOUR_SUPABASE_KEY"
    return supabase.create_client(url, key)

# Function to show Expense Tracker

def show_expense_tracker():
    st.title('Expense Tracker')
    supabase_client = init_supabase()

    # Fetch expenses from Supabase
    expenses = supabase_client.table('expenses').select('*').execute()
    expense_list = expenses.data if expenses.status_code == 200 else []

    # Editable table to display expenses
    if st.checkbox('Show Expense Tracker'):
        st.subheader('Expense Tracker Table')
        expense_data = []

        for idx, expense in enumerate(expense_list):
            cols = st.columns(6)
            with cols[0]:
                expense_data.append(st.text_input(f'Sl No {idx+1}', value=expense['sl_no'], key=f'sl_no_{idx}'))
            with cols[1]:
                expense_data.append(st.date_input(f'Expense Date {idx+1}', value=expense['expense_date'], key=f'expense_date_{idx}'))
            with cols[2]:
                expense_data.append(st.text_input(f'Person {idx+1}', value=expense['person'], key=f'person_{idx}'))
            with cols[3]:
                expense_data.append(st.text_input(f'Particulars {idx+1}', value=expense['particulars'], key=f'particulars_{idx}'))
            with cols[4]:
                expense_data.append(st.text_input(f'Property {idx+1}', value=expense['property_name'], key=f'property_name_{idx}'))
            with cols[5]:
                expense_data.append(st.text_area(f'Comments {idx+1}', value=expense['comments'], key=f'comments_{idx}'))

        # Submit changes button
        if st.button('Submit Changes'):
            for idx, expense in enumerate(expense_list):
                supabase_client.table('expenses').update({
                    'sl_no': expense_data[idx*6],
                    'expense_date': expense_data[idx*6 + 1],
                    'person': expense_data[idx*6 + 2],
                    'particulars': expense_data[idx*6 + 3],
                    'property_name': expense_data[idx*6 + 4],
                    'comments': expense_data[idx*6 + 5],
                }).eq('id', expense['id']).execute()
            st.success('Expenses updated successfully!')

# Run the function to render the table
show_expense_tracker()
