from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import os
import re
from collections import defaultdict
from dotenv import load_dotenv
from datetime import datetime, timedelta
from menu_items import menu_items
from menu_categories import menu_categories

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


def convert_weekday_en_to_jp(weekday_en):
    return weekday_en.replace('Mon', '月').replace('Tue', '火') \
                     .replace('Wed', '水').replace('Thu', '木') \
                     .replace('Fri', '金').replace('Sat', '土') \
                     .replace('Sun', '日')


@app.route('/', methods=['GET', 'POST'])
def shopping():

    if request.method == 'POST':
        checked_items = request.form.getlist('checked_items')
        if checked_items:
            # 表示名から数字を除いて元の名前だけ取得
            cleaned_items = [re.sub(r'\d+$', '', item) for item in checked_items]

            conn = get_db_connection()
            cur = conn.cursor()
            # 重複する item すべてを一括削除
            cur.execute('DELETE FROM groceries WHERE item = ANY(%s);', (cleaned_items,))
            conn.commit()
            cur.close()
            conn.close()

        return redirect(url_for('shopping'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT item, category FROM groceries;')
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # item ごとの個数とカテゴリを集計
    item_counter = defaultdict(lambda: {'count': 0, 'category': ''})
    for name, category in rows:
        item_counter[name]['count'] += 1
        item_counter[name]['category'] = category

    # 表示用に name に数をつける
    items = [
        {
            'name': f"{name}{item_counter[name]['count'] if item_counter[name]['count'] > 1 else ''}",
            'category': item_counter[name]['category']
        }
        for name in item_counter
    ]

    # メニュー表示用の読み込み
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT date_str, menu_name FROM menus ORDER BY date_str;")
    menus = [f"{row[0]}: {row[1]}" for row in cur.fetchall()]
    cur.close()
    conn.close()

    return render_template('shopping.html', items=items, menus=menus)


@app.route('/select', methods=['GET', 'POST'])
def select():
    if request.method == 'POST':
        action = request.form.get("action")
        today = datetime.today()

        if action == "reset":
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM groceries;")
            cur.execute("DELETE FROM menus;")
            conn.commit()
            cur.close()
            conn.close()

            return redirect(url_for('select'))

        if action in ("add", "confirm"):
            today = datetime.today()
            selected_menus = {}

            # 7日分のメニューを収集
            for i in range(7):
                menu_value = request.form.get(f"menu_{i}")
                if not menu_value:
                    continue
                weekday_en = (today + timedelta(days=i)).strftime('%a')
                weekday_jp = convert_weekday_en_to_jp(weekday_en)
                date_str = (today + timedelta(days=i)).strftime("%m月%d日(") + weekday_jp + ")"
                selected_menus[date_str] = menu_value

            # メニューをDBに保存（上書き対応）
            conn = get_db_connection()
            cur = conn.cursor()
            for date_str, menu_value in selected_menus.items():
                cur.execute("""
                    INSERT INTO menus (date_str, menu_name)
                    VALUES (%s, %s)
                    ON CONFLICT (date_str) DO UPDATE SET menu_name = EXCLUDED.menu_name;
                """, (date_str, menu_value))
            conn.commit()
            cur.close()
            conn.close()

            # 必要な食材をDBに追加（全日分まとめて）
            conn = get_db_connection()
            cur = conn.cursor()
            for menu_value in selected_menus.values():
                if menu_value in menu_items:
                    for item in menu_items[menu_value]:
                        try:
                            cur.execute(
                                'INSERT INTO groceries (item, category) VALUES (%s, %s);',
                                (item["name"], item["category"])
                            )
                        except Exception as e:
                            print(f"Error inserting item {item['name']} with category {item['category']}: {e}")
            conn.commit()
            cur.close()
            conn.close()

            # 追加の買い物リスト（extra）処理
            extra = request.form.get('extra')
            if extra:
                split_items = re.split(r'[、,\s\u3000]+', extra.strip())
                conn = get_db_connection()
                cur = conn.cursor()
                for item_name in split_items:
                    if item_name:
                        try:
                            cur.execute(
                                'INSERT INTO groceries (item, category) VALUES (%s, %s);',
                                (item_name, 'othe')
                            )
                        except Exception as e:
                            print(f"Error inserting extra item {item_name}: {e}")
                conn.commit()
                cur.close()
                conn.close()

            return redirect(url_for('shopping'))

    # GET時
    today = datetime.today()
    days = []
    for i in range(7):
        day = today + timedelta(days=i)
        weekday_en = day.strftime('%a')
        weekday_jp = convert_weekday_en_to_jp(weekday_en)
        days.append(f"{day.month}月{day.day}日（{weekday_jp}）")

    return render_template('select.html', days=days, categories=menu_categories)


if __name__ == '__main__':
    app.run(debug=True)
