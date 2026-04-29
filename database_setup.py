import sqlite3

conn = sqlite3.connect("trading_platform.db")
cursor = conn.cursor()

# create users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT,
    password TEXT,
    balance REAL
)
""")

# create admin earnings table
cursor.execute("""
CREATE TABLE IF NOT EXISTS admin_earnings (
    total_fees REAL
)
""")

# insert test user
cursor.execute("INSERT INTO users VALUES ('alexis', '1234', 1000)")

# insert admin earnings row
cursor.execute("INSERT INTO admin_earnings VALUES (0)")

conn.commit()
conn.close()

print("Database ready ✅")