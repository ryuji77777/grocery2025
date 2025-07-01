from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import os
from dotenv import load_dotenv
from menu_items import menu_items

# .envファイルの読み込み
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)


# PostgreSQL接続用の関数
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


# ホーム（買い物リスト）ページ
@app.route('/')
def shopping():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT item FROM groceries;')
    items = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return render_template('shopping.html', items=items)


# メニュー選択・追加食材入力ページ
@app.route('/select', methods=['GET', 'POST'])
def select():
    if request.method == 'POST':
        extra = request.form.get('extra')
        if extra:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('INSERT INTO groceries (item) VALUES (%s);', (extra,))
            conn.commit()
            cur.close()
            conn.close()
        return redirect(url_for('shopping'))
    return render_template('select.html')


if __name__ == '__main__':
    app.run(debug=True)
