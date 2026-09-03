import os
import sqlite3

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "checker.db")
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

print("Your database is in:", db_path)


cursor.execute("DROP TABLE IF EXISTS logen")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS logen (
        username TEXT UNIQUE,
        password TEXT,
        email TEXT UNIQUE
    )
""")

def add_user(username, password, email):
    cursor.execute("INSERT OR IGNORE INTO logen (username, password, email) VALUES (?, ?, ?)", (username, password, email))

add_user('zak', 'ahmed30', 'zak@gmail.com')
add_user('ahmed', 'ahmed1234', 'ahmed@gmail.com')
add_user('ghina', 'terex123', 'ghina@gmail.com')
add_user('zakk', 'kaxdn', 'zakk@gmail.com')
add_user('rana', 'ranatb', 'rana@gmail.com')
add_user('mohamed', 'mohamed123', 'mohamed@gmail.com')
add_user('sana', 'ahleen', 'sana@gmail.com')

cursor.execute("DELETE FROM logen WHERE username = 'zakk'")

cursor.execute("UPDATE logen SET email = 'ghinatabbara204@gmail.com' WHERE username = 'ghina'")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_grades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        course_name TEXT,
        credits INTEGER,
        grade_points REAL,
        FOREIGN KEY (username) REFERENCES logen (username) ON DELETE CASCADE
    )
""")

connection.commit()
connection.close()
cursor.execute("")