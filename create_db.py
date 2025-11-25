import sqlite3

# Database file name
db_file = "cars.db"

# Connect (creates file if it doesn't exist)
conn = sqlite3.connect(db_file)
c = conn.cursor()

# Create cars table
c.execute('''
CREATE TABLE IF NOT EXISTS cars (
    car_id TEXT PRIMARY KEY,
    nickname TEXT,
    last4 TEXT,
    owner_name TEXT,
    owner_phone TEXT
)
''')

# Insert two cars
cars = [
    ("car1", "Brezza", "8321", "ROHIT SENMA", "8511758308"),
    ("car2", "Dzire", "3932", "ROHIT SENMA", "8511758308")
]

for car in cars:
    c.execute("INSERT OR REPLACE INTO cars VALUES (?, ?, ?, ?, ?)", car)

conn.commit()
conn.close()

print(f"Database '{db_file}' created with two cars!")
