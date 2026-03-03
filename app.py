# Existing imports
import expense_tracker

# Update for the "Expense Tracker" page
@app.route('/expense-tracker')
def expense_tracker_page():
    # Role-based access control
    if 'Management' in session['user_roles'] or 'Accounts Team' in session['user_roles']:
        return render_template('expense_tracker.html')
    else:
        return "Access Denied", 403