
import sqlite3
conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()
c.execute('''CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password_hash TEXT,
    role TEXT)''')
c.execute('''CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    price REAL,
    image TEXT)''')
c.execute('''CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    quantity INTEGER)''')
from werkzeug.security import generate_password_hash
c.execute("INSERT INTO users (username, password_hash, role) VALUES ('admin', '"+generate_password_hash("admin")+"', 'admin')")
conn.commit()
conn.close()
print("Database initialized.")