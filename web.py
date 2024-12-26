from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import sqlite3
import hashlib
import requests
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from init_db import init_db  # 导入 init_db 函数

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # 请使用更安全的密钥

DB_FILE = 'bookings.db'

# 配置信息
url = 'https://jcc.educationgroup.cn/tsg/kzwWx/save'
get_seats_url = 'https://jcc.educationgroup.cn/tsg/kzwWx/getZws'
headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 12; HBN-AL80 Build/HUAWEIHBN-AL80; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.103 Mobile Safari/537.36 XWEB/1300199 MMWEBSDK/20241103 MMWEBID/7828 MicroMessenger/8.0.55.2780(0x28003737) WeChat/arm64 Weixin NetType/4G Language/zh_CN ABI/arm64',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
}

# 已有座位数据
seat_data = {
    '3F': {'Z': {
        3: 'EB5736CADE5AFB94E0530B96CE0A6065', 5: 'EB5736CADE63FB94E0530B96CE0A6065',
        6: 'EB5736CADE56FB94E0530B96CE0A6065', 11: 'EB5736CADE65FB94E0530B96CE0A6065',
        15: 'EB5736CADE52FB94E0530B96CE0A6065', 17: 'EB5736CADE5BFB94E0530B96CE0A6065',
        19: 'EB5736CADE5CFB94E0530B96CE0A6065', 26: 'EB5736CADE6CFB94E0530B96CE0A6065',
        27: 'EB5736CADE68FB94E0530B96CE0A6065', 33: '344040c9414a4128bc67e03e128f8136',
        34: 'ccc88464ec874dca9efec249884341b4', 35: '582d803aa9cf4b0f965cd4db62fbe11a'
    }},
    '4F': {'Z': {
        1: 'EBD2FE1B50D3A3D0E0530C96CE0AF3C1', 3: 'EBD2FE1B50E3A3D0E0530C96CE0AF3C1',
        4: 'EBD2FE1B50EAA3D0E0530C96CE0AF3C1', 7: 'EBD2FE1B50DFA3D0E0530C96CE0AF3C1',
        8: 'EBD2FE1B50EBA3D0E0530C96CE0AF3C1', 9: 'EBD2FE1B50E4A3D0E0530C96CE0AF3C1',
        11: 'EBD2FE1B50D8A3D0E0530C96CE0AF3C1', 12: 'EBD2FE1B50D4A3D0E0530C96CE0AF3C1',
        15: 'EBD2FE1B50D9A3D0E0530C96CE0AF3C1', 16: 'EBD2FE1B50DDA3D0E0530C96CE0AF3C1',
        17: 'EBD2FE1B50DEA3D0E0530C96CE0AF3C1', 18: 'EBD2FE1B50D0A3D0E0530C96CE0AF3C1',
        21: 'EBD2FE1B50D1A3D0E0530C96CE0AF3C1', 25: 'EBD2FE1B50E7A3D0E0530C96CE0AF3C1',
        30: 'EBD2FE1B50EEA3D0E0530C96CE0AF3C1', 31: 'EBD2FE1B50EFA3D0E0530C96CE0AF3C1',
        33: 'EBD2FE1B50E5A3D0E0530C96CE0AF3C1'
    }},
    '5F': {'Z': {
        4: 'EBD2FE1B5122A3D0E0530C96CE0AF3C1', 8: 'EBD2FE1B513AA3D0E0530C96CE0AF3C1',
        9: 'EBD2FE1B512FA3D0E0530C96CE0AF3C1', 10: 'EBD2FE1B5144A3D0E0530C96CE0AF3C1',
        12: 'EBD2FE1B513DA3D0E0530C96CE0AF3C1', 14: 'EBD2FE1B512AA3D0E0530C96CE0AF3C1',
        16: 'EBD2FE1B513EA3D0E0530C96CE0AF3C1', 22: 'EBD2FE1B5131A3D0E0530C96CE0AF3C1',
        24: 'EBD2FE1B5146A3D0E0530C96CE0AF3C1', 26: 'EBD2FE1B513BA3D0E0530C96CE0AF3C1',
        28: 'EBD2FE1B5147A3D0E0530C96CE0AF3C1', 30: 'EBD2FE1B5132A3D0E0530C96CE0AF3C1',
        33: 'EBD2FE1B5134A3D0E0530C96CE0AF3C1', 34: 'EBD2FE1B512AA3D0E0530C96CE0AF3C1',
        36: 'EBD2FE1B5139A3D0E0530C96CE0AF3C1', 37: 'EBD2FE1B512DA3D0E0530C96CE0AF3C1'
    }}
}

# 哈希密码
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 保存预约信息
def save_booking(booking):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO bookings (user_id, cookie, seat_id, date, time_slots, processed, result)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (booking['user_id'], booking['cookie'], booking['seat_id'], booking['date'], booking['time_slots'], booking['processed'], booking['result']))
    conn.commit()
    conn.close()

# 更新预约信息
def update_booking(booking):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE bookings
    SET user_id = ?, cookie = ?, seat_id = ?, date = ?, time_slots = ?, processed = ?, result = ?
    WHERE id = ?
    ''', (booking['user_id'], booking['cookie'], booking['seat_id'], booking['date'], ','.join(booking['time_slots']), booking['processed'], booking['result'], booking['id']))
    conn.commit()
    conn.close()

# 删除所有预约信息
def delete_all_bookings():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM bookings')
    conn.commit()
    conn.close()

# 发送飞书通知
def send_feishu_notification(webhook_url, message):
    if not webhook_url:
        return True  # 如果Webhook URL为空，则不发送通知，视为成功
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": "抢座位系统通知",
                    "content": [
                        {
                            "tag": "text",
                            "text": message
                        }
                    ]
                }
            }
        }
    }
    response = requests.post(webhook_url, headers=headers, json=data)
    return response.status_code == 200

# 用户注册
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = hash_password(password)

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "用户名已存在，请选择其他用户名"
        finally:
            conn.close()
    return render_template("register.html")

# 用户登录
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = hash_password(password)

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hashed_password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            return redirect(url_for("home"))
        else:
            return "用户名或密码错误"
    return render_template("login.html")

# 用户注销
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))

# 查看预约
@app.route("/my_bookings")
def my_bookings():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_id = session["user_id"]

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    bookings = []
    for row in rows:
        # 将元组转换为字典
        booking_dict = {
            'id': row[0],
            'user_id': row[1],
            'cookie': row[2],
            'seat_id': row[3],
            'date': row[4],
            'time_slots': row[5].split(','),  # 假设时间段是以逗号分隔的字符串
            'processed': row[6],
            'result': row[7]
        }
        # 使用 seat_data 获取座位号
        for floor, seats in seat_data.items():
            if booking_dict['seat_id'] in seats['Z'].values():
                for seat_number, seat_id in seats['Z'].items():
                    if seat_id == booking_dict['seat_id']:
                        booking_dict['seat_name'] = f"{floor}Z{seat_number:02d}"
                        break
        bookings.append(booking_dict)
    conn.close()

    return render_template("my_bookings.html", bookings=bookings)

# 取消预约
@app.route("/cancel_booking/<int:booking_id>")
def cancel_booking(booking_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_id = session["user_id"]

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bookings WHERE id = ? AND user_id = ?", (booking_id, user_id))
    conn.commit()
    conn.close()

    return redirect(url_for("my_bookings"))

# 首页（抢座位）
@app.route("/", methods=["GET", "POST"])
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            user_id = session["user_id"]
            cookie = request.form.get("cookie")
            seat_id = request.form.get("seat_id")
            time_slots = request.form.getlist("time_slots")
            feishu_webhook = request.form.get("feishu_webhook")  # 获取飞书Webhook URL

            if not cookie or not seat_id or not time_slots:
                return "请填写完整信息"

            now = datetime.now()
            if now.hour >= 6:
                date = (now + timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                date = now.strftime('%Y-%m-%d')

            # 发送加入成功通知
            if not send_feishu_notification(feishu_webhook, "加入抢座位系统成功"):
                return "飞书通知发送失败"

            # 不立即执行预约，只保存预约记录
            booking = {
                'user_id': user_id,
                'cookie': cookie,
                'seat_id': seat_id,
                'date': date,
                'time_slots': ','.join(time_slots),
                'processed': False,
                'result': "预约记录已保存，待自动执行",
                'feishu_webhook': feishu_webhook
            }

            save_booking(booking)

            # 发送预约保存成功通知
            if not send_feishu_notification(feishu_webhook, "预约记录已保存，将在明早6:05自动执行"):
                return "飞书通知发送失败"

            return "预约记录已保存，将在明早6:05自动执行"
        except Exception as e:
            return f"预约失败: {str(e)}"

    # 生成座位信息
    floors = {}
    for floor in range(3, 6):
        floor_name = f'{floor}F'
        floors[floor_name] = []
        for seat_num in range(1, 37 if floor < 5 else 39):
            seat_id = f'{floor_name}Z{seat_num:02d}'
            has_data = seat_num in seat_data.get(floor_name, {}).get('Z', {})
            seat_real_id = seat_data.get(floor_name, {}).get('Z', {}).get(seat_num, seat_id)
            floors[floor_name].append({
                'id': seat_real_id,
                'name': seat_id,
                'has_data': has_data
            })

    return render_template("template.html", floors=floors)

# 加载预约信息
def load_bookings():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bookings')
    rows = cursor.fetchall()
    bookings = []
    for row in rows:
        bookings.append({
            'id': row[0],
            'user_id': row[1],
            'cookie': row[2],
            'seat_id': row[3],
            'date': row[4],
            'time_slots': row[5].split(','),
            'processed': row[6],
            'result': row[7]
        })
    conn.close()
    return bookings

# 自动预约任务
def auto_book_seat():
    try:
        bookings = load_bookings()
        for booking in bookings:
            if booking['processed']:
                continue
            try:
                headers['Cookie'] = booking['cookie']
                success_count = 0
                for sjdId in booking['time_slots']:
                    data = {
                        'rq': booking['date'],
                        'sjdId': sjdId,
                        'zwId': booking['seat_id'],
                    }
                    response = requests.post(url, headers=headers, data=data, timeout=10)
                    if response.status_code == 200:
                        success_count += 1
                booking['processed'] = True
                booking['result'] = f"成功预约 {success_count} 个时间段"
                # 发送预约成功通知
                if not send_feishu_notification(booking['feishu_webhook'], booking['result']):
                    print("飞书通知发送失败")
            except Exception as e:
                booking['result'] = f"预约失败: {str(e)}"
            update_booking(booking)

        # 清除所有预约记录
        delete_all_bookings()

    except Exception as e:
        print(f"自动预约任务失败: {str(e)}")

# 定时获取座位数据
def get_seat_data():
    try:
        # 从数据库中查询所有用户的 cookie
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT cookie FROM bookings WHERE processed = 0")
        cookies = [row[0] for row in cursor.fetchall()]
        conn.close()

        # 为每个 cookie 发送请求
        for cookie in cookies:
            # 设置请求头
            headers = {
                'Connection': 'keep-alive',
                'Content-Length': '52',  # 这个值可能需要根据实际的请求体长度动态设置
                'sec-ch-ua-platform': '"Android"',
                'X-Requested-With': 'XMLHttpRequest',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 12; HBN-AL80 Build/HUAWEIHBN-AL80; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.103 Mobile Safari/537.36 XWEB/1300199 MMWEBSDK/20241103 MMWEBID/7828 MicroMessenger/8.0.55.2780(0x28003737) WeChat/arm64 Weixin NetType/4G Language/zh_CN ABI/arm64',
                'Accept': '*/*',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': 'https://jcc.educationgroup.cn',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'Referer': 'https://jcc.educationgroup.cn/tsg/kzwWx/index',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'Cookie': cookie  # 动态设置用户的 cookie
            }
            # 设置请求体
            data = {
                'rq': datetime.now().strftime('%Y-%m-%d'),  # 格式化当前日期
                'sjdId': 'a9596c67c7ab4f5687a0e1a5cb3ae431'  # 固定的时间段 ID
            }
            # 发送请求
            response = requests.post(get_seats_url, headers=headers, data=data, timeout=10)
            if response.status_code == 200:
                print("Seat data retrieved successfully for cookie:", cookie)
            else:
                print(f"Failed to retrieve seat data for cookie {cookie}: {response.status_code}")
    except Exception as e:
        print(f"Error retrieving seat data: {str(e)}")

scheduler = BackgroundScheduler()
scheduler.add_job(auto_book_seat, 'cron', hour=6, minute=5)
scheduler.add_job(get_seat_data, 'interval', minutes=5)  # 每5分钟获取一次座位数据
scheduler.start()

if __name__ == "__main__":
    init_db()
    get_seat_data()  # 初始化任务
    app.run(debug=True, host='0.0.0.0', port=5000)