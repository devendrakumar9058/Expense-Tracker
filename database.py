import sqlite3
import pandas as pd
from datetime import datetime

DATABASE_NAME = 'expenses.db'

def get_connection():
    return sqlite3.connect(DATABASE_NAME)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT)''')
    
    # Salary table
    c.execute('''CREATE TABLE IF NOT EXISTS salary
                 (username TEXT, amount REAL, month TEXT, 
                  PRIMARY KEY (username, month))''')
    
    # Expenses table
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  category TEXT,
                  amount REAL,
                  payment_mode TEXT,
                  date TEXT,
                  description TEXT)''')
    
    conn.commit()
    conn.close()

def add_user(username, hashed_password):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def update_salary(username, amount, month):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO salary VALUES (?, ?, ?)", (username, amount, month))
    conn.commit()
    conn.close()

def get_salary(username, month):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT amount FROM salary WHERE username=? AND month=?", (username, month))
    res = c.fetchone()
    conn.close()
    return res[0] if res else 0.0

def add_expense(username, category, amount, mode, date, desc=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO expenses (username, category, amount, payment_mode, date, description) VALUES (?, ?, ?, ?, ?, ?)",
              (username, category, amount, mode, date, desc))
    conn.commit()
    conn.close()

def get_expenses_df(username):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM expenses WHERE username=?", conn, params=(username,))
    conn.close()
    return df

def get_total_spent(username, month):
    # month format 'YYYY-MM'
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT SUM(amount) FROM expenses WHERE username=? AND date LIKE ?", (username, f"{month}%"))
    res = c.fetchone()
    conn.close()
    return res[0] if res[0] else 0.0

def get_highest_expenditure(username, month):
    # month format 'YYYY-MM'
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT category, amount, date FROM expenses WHERE username=? AND date LIKE ? ORDER BY amount DESC LIMIT 1", 
              (username, f"{month}%"))
    res = c.fetchone()
    conn.close()
    return res if res else None
