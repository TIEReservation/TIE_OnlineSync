import pandas as pd

# Define the columns for the expense tracker
columns = ['Expense made Date', 'Person who made expense', 'Particulars', 'Property Name', 'Other comments if any', 'Submitted by']

# Create an empty DataFrame with the specified columns
expense_tracker = pd.DataFrame(columns=columns)

# Save the DataFrame to an Excel file
expense_tracker.to_excel('expense_tracker.xlsx', index=False)