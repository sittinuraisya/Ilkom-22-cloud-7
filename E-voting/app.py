from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'pollnow-insecure-key'

def init_db():
    conn = sqlite3.connect('pollnow.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, email TEXT UNIQUE)')
    c.execute('CREATE TABLE IF NOT EXISTS polls (id INTEGER PRIMARY KEY, question TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS options (id INTEGER PRIMARY KEY, poll_id INTEGER, text TEXT, votes INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY, poll_id INTEGER, option_id INTEGER, user TEXT, content TEXT)')
    c.execute("SELECT * FROM polls WHERE question = ?", ('Siapa grup K-Pop Gen 3 favoritmu?',))
    if not c.fetchone():
        c.execute("INSERT INTO polls (question) VALUES (?)", ('Siapa grup K-Pop Gen 3 favoritmu?',))
        poll_id = c.lastrowid
        groups = [
            'BTS', 'BLACKPINK', 'TWICE', 'EXO', 'SEVENTEEN',
            'GOT7', 'iKON', 'Red Velvet', 'MAMAMOO', 'WINNER',
            'GFRIEND', 'MONSTA X', 'ASTRO', 'NCT 127', 'NCT Dream',
            'DAY6', 'OH MY GIRL', 'WJSN', 'STRAY KIDS', 'IZ*ONE'
        ]
        for group in groups:
            c.execute("INSERT INTO options (poll_id, text) VALUES (?, ?)", (poll_id, group))
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        if username and email:
            conn = sqlite3.connect('pollnow.db')
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO users (username, email) VALUES (?, ?)", (username, email))
            conn.commit()
            conn.close()
            session['user'] = username
            session['email'] = email
            session.pop('voted', None)
            return redirect('/dashboard')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session or 'email' not in session:
        return redirect('/login')

    conn = sqlite3.connect('pollnow.db')
    c = conn.cursor()
    c.execute("SELECT id FROM polls WHERE question = ?", ('Siapa grup K-Pop Gen 3 favoritmu?',))
    poll_id = c.fetchone()[0]

    c.execute("""
        SELECT option_id FROM comments
        WHERE poll_id = ? AND user = ? AND content = ''
    """, (poll_id, session['email']))
    voted_row = c.fetchone()

    voted = voted_row is not None
    selected_option = voted_row[0] if voted else None

    if request.method == 'POST' and not voted:
        selected_option = request.form.get('option')
        if selected_option:
            c.execute("UPDATE options SET votes = votes + 1 WHERE id = ?", (selected_option,))
            c.execute("INSERT INTO comments (poll_id, option_id, user, content) VALUES (?, ?, ?, ?)",
                      (poll_id, selected_option, session['email'], ''))
            conn.commit()
            voted = True

    c.execute("SELECT id, text, votes FROM options WHERE poll_id = ?", (poll_id,))
    options = c.fetchall()

    c.execute("""
        SELECT o.text, cmt.user, cmt.content
        FROM comments cmt
        JOIN options o ON cmt.option_id = o.id
        WHERE cmt.poll_id = ? AND cmt.content != ''
        ORDER BY cmt.id DESC
    """, (poll_id,))
    comments = c.fetchall()

    conn.close()
    return render_template('dashboard.html',
                           user=session['user'],
                           options=options,
                           comments=comments,
                           voted=voted,
                           poll_id=poll_id)

@app.route('/comment/<int:poll_id>', methods=['POST'])
def comment(poll_id):
    if 'user' not in session:
        return redirect('/login')
    content = request.form.get('content')
    conn = sqlite3.connect('pollnow.db')
    c = conn.cursor()
    c.execute("""
        SELECT option_id FROM comments
        WHERE poll_id = ? AND user = ? AND content = ''
    """, (poll_id, session['email']))
    voted_row = c.fetchone()
    if voted_row:
        option_id = voted_row[0]
        if content:
            c.execute("INSERT INTO comments (poll_id, option_id, user, content) VALUES (?, ?, ?, ?)",
                      (poll_id, option_id, session['email'], content))
            conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.after_request
def disable_security_headers(response):
    response.headers.pop('Content-Security-Policy', None)
    response.headers.pop('X-Frame-Options', None)
    response.headers.pop('X-XSS-Protection', None)
    return response

if __name__ == '__main__':
    app.run(debug=True)
