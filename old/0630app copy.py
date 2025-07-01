# app.py
from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from menu_items import menu_items
from menu_categories import menu_categories

# .envファイルの読み込み
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


@app.route('/')
def shopping():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT item, category FROM groceries;')
    rows = cur.fetchall()
    cur.close()
    conn.close()

    items = [{"name": row[0], "category": row[1]} for row in rows]

    return render_template('shopping.html', items=items)


@app.route('/select', methods=['GET', 'POST'])
def select():
    if request.method == 'POST':
        today = datetime.today()
        selected_menus = {}

        for i in range(7):
            menu = request.form.get(f"menu_{i}")
            date_str = (today + timedelta(days=i)).strftime("%m月%d日(") + (today + timedelta(days=i)).strftime("%a").replace('Mon', '月').replace('Tue', '火').replace('Wed', '水').replace('Thu', '木').replace('Fri', '金').replace('Sat', '土').replace('Sun', '日') + ")"
            if menu:
                selected_menus[date_str] = menu

                # 食材をDBに保存
                if menu in menu_items:
                    ingredients = menu_items[menu]
                    conn = get_db_connection()
                    cur = conn.cursor()
                    for item in ingredients:
                        cur.execute(
                            'INSERT INTO groceries (item, category) VALUES (%s, %s);',
                            (item["name"], item["category"])
                        )

                    conn.commit()
                    cur.close()
                    conn.close()

        # 自由入力食材の処理
        extra = request.form.get('extra')
        if extra:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO groceries (item, category) VALUES (%s, %s);',
                (extra, 'othe')
            )

            conn.commit()
            cur.close()
            conn.close()

        print("選ばれたメニュー一覧（辞書）:", selected_menus)
        return redirect(url_for('shopping'))

    # 今日から7日間の日付を生成
    today = datetime.today()
    days = [f"{(today + timedelta(days=i)).month}月{(today + timedelta(days=i)).day}日({(today + timedelta(days=i)).strftime('%a').replace('Mon', '月').replace('Tue', '火').replace('Wed', '水').replace('Thu', '木').replace('Fri', '金').replace('Sat', '土').replace('Sun', '日')})" for i in range(7)]

    return render_template(
        'select.html',
        days=days,
        categories=menu_categories
    )


if __name__ == '__main__':
    app.run(debug=True)
