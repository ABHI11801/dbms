from flask import Flask, render_template, g, url_for, request, redirect, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'killerbean11801'
DATABASE = os.path.join(os.path.dirname(__file__), 'data.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM login WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Username already exists. Please choose another one.", "warning")
        else:
            cursor.execute("INSERT INTO login (username, password) VALUES (?, ?)", (username, password))
            get_db().commit()
            flash("Signup successful! Please log in.", "success")
            return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM login WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = username 
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password.", "danger")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/index')
def index():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT tableno, status FROM statuss")
    table_statuses = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT DISTINCT tableno FROM table_items")
    occupied_tables = [row[0] for row in cursor.fetchall()]

    for table_no in table_statuses:
        if table_no in occupied_tables:
            if table_statuses[table_no] != 1:
                cursor.execute("UPDATE statuss SET status = 1 WHERE tableno = ?", (table_no,))
        else:
            if table_statuses[table_no] != 0:
                cursor.execute("UPDATE statuss SET status = 0 WHERE tableno = ?", (table_no,))

    db.commit()

    cursor.execute("SELECT tableno, status FROM statuss")
    table_statuses = {row[0]: row[1] for row in cursor.fetchall()}

    return render_template('index.html', table_statuses=table_statuses)

@app.route('/menu')
def menu():
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()
    return render_template('menu.html', items=items)

@app.route('/add_items/<tableno>', methods=['GET', 'POST'])
def add_items(tableno):
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        item_ids = request.form.getlist('item_ids')
        quantities = request.form.getlist('quantities')
        
        for item_id, quantity in zip(item_ids, quantities):
            for _ in range(int(quantity)):
                cursor.execute("INSERT INTO table_items (tableno, item_id) VALUES (?, ?)", (tableno, item_id))
        db.commit()
        
        return redirect(url_for('index'))

    cursor.execute("SELECT * FROM items")
    all_items = cursor.fetchall()

    cursor.execute("""
        SELECT items.id, items.name, items.price, COUNT(table_items.item_id) as count
        FROM items 
        LEFT JOIN table_items ON items.id = table_items.item_id 
        WHERE table_items.tableno = ?
        GROUP BY items.id
    """, (tableno,))
    current_table_items = cursor.fetchall()

    return render_template('add_items.html', tableno=tableno, all_items=all_items, current_table_items=current_table_items)

@app.route('/generate_bill/<tableno>')
def generate_bill(tableno):
    cursor = get_db().cursor()
    cursor.execute("SELECT i.id, i.name, i.price FROM table_items ti JOIN items i ON ti.item_id = i.id WHERE ti.tableno = ?", (tableno,))
    items = cursor.fetchall()
    total = sum(item[2] for item in items)

    return render_template('bill.html', tableno=tableno, items=items, total=total)

@app.route('/bill_paid/<tableno>', methods=['POST'])
def bill_paid(tableno):
    cursor = get_db().cursor()
    cursor.execute("DELETE FROM table_items WHERE tableno = ?", (tableno,))
    get_db().commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)