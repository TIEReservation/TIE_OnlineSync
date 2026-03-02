import datetime
from flask import Flask, render_template, request

app = Flask(__name__)

# Dummy data for expenses
data = []

@app.route('/expense_tracker', methods=['GET', 'POST'])
def expense_tracker():
    if request.method == 'POST':
        # If the request is POST, add the new expense to the data
        expense = {
            'sl_no': len(data) + 1,
            'date': request.form['date'],
            'person': request.form['person'],
            'particulars': request.form['particulars'],
            'property_name': request.form['property_name'],
            'comments': request.form['comments'],
            'submitted_by': request.form['submitted_by'],
        }
        data.append(expense)
        return render_template('expense_tracker.html', data=data)
    return render_template('expense_tracker.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)