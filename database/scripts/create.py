import sqlite3
conn = sqlite3.connect('smartcampus.db')
conn = conn.cursor()

conn.execute('''drop table if exists metrics''')
