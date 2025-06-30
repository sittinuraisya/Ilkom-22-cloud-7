import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL
)""")

c.execute("""CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price REAL,
    image TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
)""")

admin_hash = generate_password_hash('admin')
c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
          ('admin', admin_hash, 'admin'))
c.execute("INSERT INTO products (name, description, price, image) VALUES (?, ?, ?, ?)",
          ('Produk Contoh', 'Deskripsi produk contoh', 12.34, 'default.png'))

conn.commit()
conn.close()
print("DB initialized with admin:admin & sample product.")
