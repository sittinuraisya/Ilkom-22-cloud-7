from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('index.html', products=products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, "user")',
                     (username, generate_password_hash(password)))
        conn.commit()
        conn.close()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect('/')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if session.get('role') != 'admin':
        return redirect('/login')
    if request.method == 'POST':
        name = request.form['name']
        desc = request.form['description']
        price = request.form['price']
        file = request.files['image']
        filename = secure_filename(file.filename)
        if filename != '':
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = 'default.png'
        conn = get_db_connection()
        conn.execute('INSERT INTO products (name, description, price, image) VALUES (?, ?, ?, ?)',
                     (name, desc, price, filename))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('add_product.html')

@app.route('/order/<int:product_id>')
def order(product_id):
    if 'username' not in session:
        return redirect('/login')
    conn = get_db_connection()
    user = conn.execute('SELECT id FROM users WHERE username=?', (session['username'],)).fetchone()
    conn.execute('INSERT INTO orders (user_id, product_id, quantity) VALUES (?, ?, 1)',
                 (user['id'], product_id))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/admin_orders')
def admin_orders():
    if session.get('role') != 'admin':
        return redirect('/login')
    conn = get_db_connection()
    orders = conn.execute('''
        SELECT o.id, u.username, p.name AS product_name, o.quantity
        FROM orders o
        JOIN users u ON o.user_id = u.id
        JOIN products p ON o.product_id = p.id
    ''').fetchall()
    conn.close()
    return render_template('admin_orders.html', orders=orders)

if __name__ == '__main__':
    app.run(debug=True)