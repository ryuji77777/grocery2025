# init_db.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# 既存のテーブルを削除（開発時のみ。データが消えます）
cur.execute("DROP TABLE IF EXISTS groceries;")

# テーブルを再作成（category カラムを追加）
cur.execute("""
    CREATE TABLE groceries (
        id SERIAL PRIMARY KEY,
        item TEXT NOT NULL,
        category TEXT
    );
""")

conn.commit()
cur.close()
conn.close()

print("✅ groceries テーブルを作成しました（item + category）")
