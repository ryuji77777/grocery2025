from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from menu_items import menu_items
from menu_categories import menu_categories

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

    items = [{'name': row[0], 'category': row[1]} for row in rows]  # 辞書に変換
    return render_template('shopping.html', items=items)


@app.route('/select', methods=['GET', 'POST'])
def select():
    if request.method == 'POST':
        action = request.form.get("action")
        today = datetime.today()

        if action == "reset":
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM groceries;")
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('select'))

        if action in ("add", "confirm"):
            selected_menus = {}

            for i in range(7):
                menu = request.form.get(f"menu_{i}")

                print(f"[DEBUG] menu_{i}: {menu}")  # ①

                date_str = (today + timedelta(days=i)).strftime("%m月%d日(") + \
                           (today + timedelta(days=i)).strftime("%a").replace('Mon', '月').replace('Tue', '火') \
                           .replace('Wed', '水').replace('Thu', '木').replace('Fri', '金').replace('Sat', '土') \
                           .replace('Sun', '日') + ")"
                if menu:
                    selected_menus[date_str] = menu

                    if action == "confirm" and menu in menu_items:
                        print(f"[DEBUG] '{menu}' is in menu_items")  # ②
                        ingredients = menu_items[menu]
                        conn = get_db_connection()
                        cur = conn.cursor()
                        for item in ingredients:
                            print(f"[DEBUG] inserting item: {item}")  # ③
                            try:
                                # データベースに挿入
                                cur.execute('INSERT INTO groceries (item, category) VALUES (%s, %s);', 
                                            (item["name"], item["category"]))
                            except Exception as e:
                                print(f"Error inserting item {item['name']} with category {item['category']}: {e}")
                        conn.commit()
                        cur.close()
                        conn.close()

                        # メニューの値を表示して確認　削除★
                        menu = request.form.get(f"menu_{i}")
                        print(menu)

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

            return redirect(url_for('shopping'))

    # GET時
    today = datetime.today()
    days = []
    for i in range(7):
        day = today + timedelta(days=i)
        weekday = day.strftime('%a')
        weekday_jp = weekday.replace('Mon', '月').replace('Tue', '火').replace('Wed', '水') \
                            .replace('Thu', '木').replace('Fri', '金').replace('Sat', '土').replace('Sun', '日')
        days.append(f"{day.month}月{day.day}日（{weekday_jp}）")

    return render_template('select.html', days=days, categories=menu_categories)


if __name__ == '__main__':
    app.run(debug=True)
