# init_db.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS groceries (
        id SERIAL PRIMARY KEY,
        item TEXT NOT NULL
    );
""")

conn.commit()
cur.close()
conn.close()

print("✅ テーブル作成完了")
