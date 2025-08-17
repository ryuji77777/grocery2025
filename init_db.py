import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# 既存のテーブルを削除（開発時のみ。データが消えます）
cur.execute("DROP TABLE IF EXISTS groceries;")
cur.execute("DROP TABLE IF EXISTS menus;")  # 追加

# テーブルを再作成（category カラムを追加）
cur.execute("""
    CREATE TABLE groceries (
        id SERIAL PRIMARY KEY,
        item TEXT NOT NULL,
        category TEXT
    );
""")

cur.execute("""
    CREATE TABLE menus (
        date_str TEXT PRIMARY KEY,
        menu_name TEXT
    );
""")  # 追加

conn.commit()
cur.close()
conn.close()

print("✅ groceries, menus テーブルを作成しました")
