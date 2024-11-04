from flask import Flask, render_template, g, url_for, request, redirect
import sqlite3
import os

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(__file__), 'data.db')

def get_db():
    """Get a database connection."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    """Render the index page with table statuses."""
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM status")
    statuses = cursor.fetchall()
    
    # Create a dictionary to hold table statuses
    table_statuses = {}
    for row in statuses:
        table_no = f"table{row[0]}"
        current_status = row[1]
        table_statuses[table_no] = current_status

    return render_template('index.html', table_statuses=table_statuses)

@app.route('/menu')
def menu():
    """Render the menu page."""
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()
    return render_template('menu.html', items=items)

@app.route('/add_items/<tableno>', methods=['GET', 'POST'])
def add_items(tableno):
    """Add items to the specified table."""
    cursor = get_db().cursor()
    if request.method == 'POST':
        item_ids = request.form.getlist('item_ids')
        
        if item_ids:
            # Insert selected items into the table_items
            for item_id in item_ids:
                cursor.execute("INSERT INTO table_items (tableno, item_id) VALUES (?, ?)", (tableno, item_id))

            # Update table status to Not Free (1)
            cursor.execute("UPDATE status SET status = 1 WHERE tableno = ?", (tableno.split('table')[1],))
            get_db().commit()
            print(f"Status updated for {tableno} to 1")  # Debugging line
            
        return redirect(url_for('index'))

    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()
    return render_template('add_items.html', tableno=tableno, items=items)

@app.route('/generate_bill/<tableno>')
def generate_bill(tableno):
    """Generate the bill for the specified table."""
    cursor = get_db().cursor()
    cursor.execute("SELECT i.id, i.name, i.price FROM table_items ti JOIN items i ON ti.item_id = i.id WHERE ti.tableno = ?", (tableno,))
    items = cursor.fetchall()
    total = sum(item[2] for item in items)

    # Update status to reflect bill generation (2)
    cursor.execute("UPDATE status SET status = 2 WHERE tableno = ?", (tableno.split('table')[1],))
    get_db().commit()
    print(f"Bill generated for {tableno}. Status updated to 2.")  # Debugging line

    return render_template('bill.html', tableno=tableno, items=items, total=total)

@app.route('/bill_paid/<tableno>', methods=['POST'])
def bill_paid(tableno):
    """Process the payment for the bill and reset table items."""
    cursor = get_db().cursor()
    cursor.execute("DELETE FROM table_items WHERE tableno = ?", (tableno,))
    cursor.execute("UPDATE status SET status = 0 WHERE tableno = ?", (tableno.split('table')[1],))  # Set status to Free (0)
    get_db().commit()
    print(f"Bill paid for {tableno}. Status updated to 0.")  # Debugging line
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
