from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import sqlite3
import hashlib
import time
import requests
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from init_db import init_db  # 导入 init_db 函数
import logging

# 全局调度器实例
scheduler = BackgroundScheduler(
    coalesce=True,  # 合并多次触发的任务
    misfire_grace_time=30,  # 允许任务延迟执行的时间（秒）
)
# 启动调度器
scheduler.start()

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

# 配置logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# 座位数据
seat_data = {
    '3F': {'Z': {
        1: 'EB5736CADE4FFB94E0530B96CE0A6065', 2: 'EB5736CADE66FB94E0530B96CE0A6065',
        3: 'EB5736CADE5AFB94E0530B96CE0A6065', 4: 'EB5736CADE55FB94E0530B96CE0A6065',
        5: 'EB5736CADE63FB94E0530B96CE0A6065', 6: 'EB5736CADE56FB94E0530B96CE0A6065',
        7: 'EB5736CADE5EFB94E0530B96CE0A6065', 8: 'EB5736CADE67FB94E0530B96CE0A6065',
        9: 'EB5736CADE57FB94E0530B96CE0A6065', 10: 'EB5736CADE58FB94E0530B96CE0A6065',
        11: 'EB5736CADE65FB94E0530B96CE0A6065', 12: 'EB5736CADE61FB94E0530B96CE0A6065',
        13: 'EB5736CADE69FB94E0530B96CE0A6065', 14: 'EB5736CADE50FB94E0530B96CE0A6065',
        15: 'EB5736CADE52FB94E0530B96CE0A6065', 16: 'EB5736CADE64FB94E0530B96CE0A6065',
        17: 'EB5736CADE5BFB94E0530B96CE0A6065', 18: 'EB5736CADE6AFB94E0530B96CE0A6065',
        19: 'EB5736CADE5CFB94E0530B96CE0A6065', 20: 'EB5736CADE51FB94E0530B96CE0A6065',
        21: 'EB5736CADE53FB94E0530B96CE0A6065', 22: 'EB5736CADE6BFB94E0530B96CE0A6065',
        23: 'EB5736CADE5DFB94E0530B96CE0A6065', 24: 'EB5736CADE62FB94E0530B96CE0A6065',
        25: 'EB5736CADE54FB94E0530B96CE0A6065', 26: 'EB5736CADE6CFB94E0530B96CE0A6065',
        27: 'EB5736CADE68FB94E0530B96CE0A6065', 28: 'EB5736CADE5FFB94E0530B96CE0A6065',
        29: 'EB5736CADE59FB94E0530B96CE0A6065', 30: 'EB5736CADE60FB94E0530B96CE0A6065',
        31: '5c7f6979a1c8427a8efef36fcfdafe7d', 32: '6848a2eafc854ba983f163124ef68cf0',
        33: '344040c9414a4128bc67e03e128f8136', 34: 'ccc88464ec874dca9efec249884341b4',
        35: '582d803aa9cf4b0f965cd4db62fbe11a', 36: '68d7457fca5b4ed49798bfdb117114ca'
    }},
    '4F': {'Z': {
        1: 'EBD2FE1B50D3A3D0E0530C96CE0AF3C1',  2: 'EBD2FE1B50E6A3D0E0530C96CE0AF3C1',
        3: 'EBD2FE1B50E3A3D0E0530C96CE0AF3C1',  4: 'EBD2FE1B50EAA3D0E0530C96CE0AF3C1',
        5: 'EBD2FE1B50F1A3D0E0530C96CE0AF3C1',  6: 'EBD2FE1B50D7A3D0E0530C96CE0AF3C1',
        7: 'EBD2FE1B50DFA3D0E0530C96CE0AF3C1',  8: 'EBD2FE1B50EBA3D0E0530C96CE0AF3C1',
        9: 'EBD2FE1B50E4A3D0E0530C96CE0AF3C1', 10: 'EBD2FE1B50F2A3D0E0530C96CE0AF3C1',
        11: 'EBD2FE1B50D8A3D0E0530C96CE0AF3C1', 12: 'EBD2FE1B50D4A3D0E0530C96CE0AF3C1',
        13: 'EBD2FE1B50E9A3D0E0530C96CE0AF3C1', 14: 'EBD2FE1B50E2A3D0E0530C96CE0AF3C1',
        15: 'EBD2FE1B50D9A3D0E0530C96CE0AF3C1', 16: 'EBD2FE1B50DDA3D0E0530C96CE0AF3C1',
        17: 'EBD2FE1B50DEA3D0E0530C96CE0AF3C1', 18: 'EBD2FE1B50D0A3D0E0530C96CE0AF3C1',
        19: 'EBD2FE1B50F3A3D0E0530C96CE0AF3C1', 20: 'EBD2FE1B50E0A3D0E0530C96CE0AF3C1',
        21: 'EBD2FE1B50D1A3D0E0530C96CE0AF3C1', 22: 'EBD2FE1B50DAA3D0E0530C96CE0AF3C1',
        23: 'EBD2FE1B50DBA3D0E0530C96CE0AF3C1', 24: 'EBD2FE1B50EDA3D0E0530C96CE0AF3C1',
        25: 'EBD2FE1B50E7A3D0E0530C96CE0AF3C1', 26: 'EBD2FE1B50D5A3D0E0530C96CE0AF3C1',
        27: 'EBD2FE1B50DCA3D0E0530C96CE0AF3C1', 28: 'EBD2FE1B50DEA3D0E0530C96CE0AF3C1',
        29: 'EBD2FE1B50ECA3D0E0530C96CE0AF3C1', 30: 'EBD2FE1B50EEA3D0E0530C96CE0AF3C1',
        31: 'EBD2FE1B50EFA3D0E0530C96CE0AF3C1', 32: 'EBD2FE1B50D6A3D0E0530C96CE0AF3C1',
        33: 'EBD2FE1B50E5A3D0E0530C96CE0AF3C1', 34: 'EBD2FE1B50E1A3D0E0530C96CE0AF3C1',
        35: 'EBD2FE1B50E8A3D0E0530C96CE0AF3C1', 36: 'EBD2FE1B50D2A3D0E0530C96CE0AF3C1'
    }},
    '5F': {'Z': {
        1: 'EBD2FE1B5136A3D0E0530C96CE0AF3C1',  2: 'EBD2FE1B5133A3D0E0530C96CE0AF3C1',
        3: 'EBD2FE1B512EA3D0E0530C96CE0AF3C1',  4: 'EBD2FE1B5122A3D0E0530C96CE0AF3C1',
        5: 'EBD2FE1B5137A3D0E0530C96CE0AF3C1',  6: 'EBD2FE1B5141A3D0E0530C96CE0AF3C1',
        7: 'EBD2FE1B5138A3D0E0530C96CE0AF3C1',  8: 'EBD2FE1B513AA3D0E0530C96CE0AF3C1',
        9: 'EBD2FE1B512FA3D0E0530C96CE0AF3C1', 10: 'EBD2FE1B5144A3D0E0530C96CE0AF3C1',
        11: 'EBD2FE1B5142A3D0E0530C96CE0AF3C1', 12: 'EBD2FE1B513DA3D0E0530C96CE0AF3C1',
        13: 'EBD2FE1B5124A3D0E0530C96CE0AF3C1', 14: 'EBD2FE1B5130A3D0E0530C96CE0AF3C1',
        15: 'EBD2FE1B5140A3D0E0530C96CE0AF3C1', 16: 'EBD2FE1B513EA3D0E0530C96CE0AF3C1',
        17: 'EBD2FE1B5143A3D0E0530C96CE0AF3C1', 18: 'EBD2FE1B5123A3D0E0530C96CE0AF3C1',
        19: 'EBD2FE1B5145A3D0E0530C96CE0AF3C1', 20: 'EBD2FE1B5128A3D0E0530C96CE0AF3C1',
        21: 'EBD2FE1B513CA3D0E0530C96CE0AF3C1', 22: 'EBD2FE1B5131A3D0E0530C96CE0AF3C1',
        23: 'EBD2FE1B5129A3D0E0530C96CE0AF3C1', 24: 'EBD2FE1B5146A3D0E0530C96CE0AF3C1',
        25: 'EBD2FE1B512BA3D0E0530C96CE0AF3C1', 26: 'EBD2FE1B5125A3D0E0530C96CE0AF3C1',
        27: 'EBD2FE1B513FA3D0E0530C96CE0AF3C1', 28: 'EBD2FE1B5126A3D0E0530C96CE0AF3C1',
        29: 'EBD2FE1B512CA3D0E0530C96CE0AF3C1', 30: 'EBD2FE1B5144A3D0E0530C96CE0AF3C1',
        31: 'EBD2FE1B5127A3D0E0530C96CE0AF3C1', 32: 'EBD2FE1B5132A3D0E0530C96CE0AF3C1',
        33: 'EBD2FE1B513BA3D0E0530C96CE0AF3C1', 34: 'EBD2FE1B512AA3D0E0530C96CE0AF3C1',
        35: 'EBD2FE1B5134A3D0E0530C96CE0AF3C1', 36: 'EBD2FE1B5139A3D0E0530C96CE0AF3C1',
        37: 'EBD2FE1B512DA3D0E0530C96CE0AF3C1', 38: 'EBD2FE1B5135A3D0E0530C96CE0AF3C1'
    }}
}


# 时间段数据
time_slot_mapping = {
    "4df8c3dc857e4a39ab11142e132daccf": "07:00 - 10:00",
    "6ba3ccd77482466b82a08e480c4299ee": "10:00 - 12:00",
    "58fc242d7eff41b18f1e795b048f50d4": "12:00 - 14:00",
    "da7bd7e2416246aeb4a35306d75f629b": "14:00 - 16:00",
    "1ead11f7e214444986dbbf877f7de81d": "16:00 - 18:00",
    "a9596c67c7ab4f5687a0e1a5cb3ae431": "18:00 - 22:00"
}

# 哈希密码
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 验证密码
def verify_password(user_id, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users WHERE id = ?', (user_id,))
    stored_password = cursor.fetchone()[0]
    conn.close()
    return hash_password(password) == stored_password

# 保存预约信息
def save_booking(booking):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO bookings (user_id, cookie, seat_id, date, time_slots, processed, result, loop_booking, frequency)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        booking['user_id'], 
        booking['cookie'], 
        booking['seat_id'], 
        booking['date'], 
        booking['time_slots'], 
        booking['processed'], 
        booking['result'], 
        booking['loop_booking'], 
        booking.get('frequency', None)  # 使用频率值，确保在 auto_book 模式下为 None
    ))
    booking_id = cursor.lastrowid
    conn.commit()
    conn.close()
    # 调试输出
    print(f"Saved booking ID: {booking_id}, frequency: {booking.get('frequency', None)}")
    return booking_id

# 更新预约信息
def update_booking(booking):
    print(f"更新预约: {booking}")  # 调试输出
    if not booking['time_slots'] or not all(booking['time_slots']):
        print("警告: time_slots 列表为空或包含无效值")
    else:
        print(f"time_slots 列表内容: {booking['time_slots']}")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE bookings
    SET user_id = ?, cookie = ?, seat_id = ?, date = ?, time_slots = ?, processed = ?, result = ?, loop_booking = ?, frequency = ?, last_result = ?
    WHERE id = ?
    ''', (
        booking['user_id'], 
        booking['cookie'], 
        booking['seat_id'], 
        booking['date'], 
        ','.join(booking['time_slots']),  # 确保 time_slots 格式正确
        booking['processed'], 
        booking['result'], 
        booking['loop_booking'], 
        booking['frequency'], 
        booking['last_result'],  # 更新 last_result 字段
        booking['id']
    ))
    conn.commit()
    conn.close()

# 加载预约信息
def load_bookings():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings")
    rows = cursor.fetchall()
    bookings = []
    for row in rows:
        print(f"Raw row data: {row}")  # 调试输出
        bookings.append({
            'id': row[0],
            'user_id': row[1],
            'cookie': row[2],
            'seat_id': row[3],
            'date': row[4],
            'time_slots': row[5].split(','),  # 确保分割时间段ID
            'processed': bool(row[6]),  # 确保 processed 是布尔值
            'result': row[7],
            'loop_booking': bool(row[8]),  # 确保 loop_booking 是布尔值
            'frequency': row[9],  # 直接使用数据库中的值
            'last_result': row[10]  # 添加获取 last_result
        })
        # 调试输出
        print(f"Loaded booking ID: {row[0]}, frequency: {row[9]}")
    conn.close()
    return bookings

# 删除所有预约信息
def delete_all_bookings():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM bookings')
    conn.commit()
    conn.close()

# 格式化结果函数
def format_result_with_time_slots(booking):
    # 将 time_slots 从字符串转换为列表
    time_slots = booking['time_slots'].split(',')

    # 使用映射替换时间段ID为实际时间段
    formatted_time_slots = [time_slot_mapping.get(slot, "Unknown Time Slot") for slot in time_slots]

    # 构建新的 result 字符串
    new_result = "成功预约以下时间段：\n" + "\n".join(formatted_time_slots)

    # 更新 booking 字典中的 result 字段
    booking['result'] = new_result
    return booking

# 更新用户密码
def update_password(user_id, new_password):
    hashed_password = hash_password(new_password)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user_id))
    conn.commit()
    conn.close()

# 更新用户通知设置
def update_notification_settings(user_id, notification_method, feishu_webhook):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 如果通知方式是“无”，删除飞书 Webhook
    if notification_method == 'none':
        cursor.execute('UPDATE users SET notification_method = ?, feishu_webhook = NULL WHERE id = ?', 
                       (notification_method, user_id))
    else:
        cursor.execute('UPDATE users SET notification_method = ?, feishu_webhook = ? WHERE id = ?', 
                       (notification_method, feishu_webhook, user_id))
    
    conn.commit()
    conn.close()

    # 发送加入抢座系统成功通知
    if notification_method == 'feishu' and feishu_webhook:
        send_feishu_notification(feishu_webhook, "加入抢座系统成功")

# 获取用户飞书Webhook地址信息
def get_user_info(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT username, feishu_webhook, notification_method FROM users WHERE id = ?', (user_id,))
    user_info = cursor.fetchone()
    conn.close()
    return user_info

# 账号设置页面
@app.route("/api/user_info", methods=["GET"])
def api_user_info():
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session["user_id"]
    start_time = time.time()
    user_info = get_user_info(user_id)
    end_time = time.time()
    print(f"API 端点查询时间: {end_time - start_time} 秒")

    if not user_info:
        return jsonify({'error': 'User not found'}), 404

    username, feishu_webhook, notification_method = user_info
    return jsonify({
        'username': username,
        'feishu_webhook': feishu_webhook,
        'notification_method': notification_method
    })

@app.route("/account", methods=["GET"])
def account():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    user_info = get_user_info(user_id)
    if not user_info:
        return redirect(url_for("login"))

    username, feishu_webhook, notification_method = user_info  # 确认解包的值和数量匹配
    return render_template("account.html", username=username, feishu_webhook=feishu_webhook, notification_method=notification_method)

@app.route("/update_password", methods=["POST"])
def update_password_route():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    old_password = request.form.get("old_password")
    new_password = request.form.get("new_password")

    # 验证旧密码
    if not verify_password(user_id, old_password):
        return "旧密码错误", 400

    # 更新密码
    update_password(user_id, new_password)
    
    # 让用户重新登录
    return redirect(url_for("logout"))

@app.route("/update_notification_settings", methods=["POST"])
def update_notification_settings_route():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    notification_method = request.form.get("notification_method")
    feishu_webhook = request.form.get("feishu_webhook")

    # 更新通知方式和飞书 Webhook URL
    update_notification_settings(user_id, notification_method, feishu_webhook)
    
    return redirect(url_for("account"))

# 发送飞书通知
def send_feishu_notification(feishu_webhook, message):
    if not feishu_webhook:
        # 如果没有提供飞书 Webhook 地址，直接返回 True 表示成功
        return True

    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        "msg_type": "text",
        "content": {
            "text": message
        }
    }

    # 调试输出
    print(f"发送飞书通知，Webhook: {feishu_webhook}, Message: {message}")

    response = requests.post(feishu_webhook, headers=headers, json=data)
    response.raise_for_status()  # 如果请求失败，这会引发HTTPError
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

# 座位信息
def generate_seat_info():
    floors = {}
    bookings = load_bookings()
    reserved_seats = {booking['seat_id'] for booking in bookings}

    for floor in range(3, 6):
        floor_name = f'{floor}F'
        floors[floor_name] = []
        for seat_num in range(1, 37 if floor < 5 else 39):
            seat_id = f'{floor_name}Z{seat_num:02d}'
            seat_real_id = seat_data.get(floor_name, {}).get('Z', {}).get(seat_num, seat_id)
            has_data = seat_real_id not in reserved_seats  # 判断座位是否可预约

            floors[floor_name].append({
                'id': seat_real_id,
                'name': seat_id,
                'has_data': has_data  # 使用 has_data 字段
            })

    return floors

# 座位状态
@app.route("/get_seat_info", methods=["POST"])
def get_seat_info():
    if "user_id" not in session:
        return jsonify({'message': '未登录'})

    data = request.json
    operation_mode = data.get("operation_mode")
    time_slots = data.get("time_slots", [])

    if not operation_mode:
        return jsonify({'message': '请选择预约模式'})

    # 获取所有预约记录
    bookings = load_bookings()
    reserved_seats = set()

    # 根据预约模式过滤座位
    for booking in bookings:
        if operation_mode == "auto_book":
            # 如果是 6:05 自动预约模式，过滤掉循环预约的座位
            if not booking['loop_booking'] and any(slot in booking['time_slots'] for slot in time_slots):
                reserved_seats.add(booking['seat_id'])
        else:
            # 如果是循环预约模式，不进行过滤
            pass

    # 生成座位信息
    floors = {}
    for floor in range(3, 6):
        floor_name = f'{floor}F'
        floors[floor_name] = []
        for seat_num in range(1, 37 if floor < 5 else 39):
            seat_id = f'{floor_name}Z{seat_num:02d}'
            seat_real_id = seat_data.get(floor_name, {}).get('Z', {}).get(seat_num, seat_id)

            # 判断座位是否可预约
            if operation_mode == "auto_book":
                has_data = seat_real_id not in reserved_seats  # 根据时间段动态判断
            else:
                has_data = True  # 循环预约模式下所有座位都可预约

            floors[floor_name].append({
                'id': seat_real_id,
                'name': seat_id,
                'has_data': has_data
            })

    return jsonify({'floors': floors})

# 用户登录
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # 检查用户名和密码是否为空
        if not username or not password:
            return "缺少用户名或密码", 400

        # 调试信息
        print(f"Username: {username}, Password: {password}")

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
            'time_slots': row[5].split(',') if row[5] else [],  # 确保空字符串返回空列表
            'processed': row[6] == 1,  # 仅当值为 1 时返回 True
            'result': row[7],
            'loop_booking': row[8] == 1,  # 仅当值为 1 时返回 True
            'frequency': row[9]  # 直接使用数据库中的值
        }
        # 默认座位号
        booking_dict['seat_name'] = "未知座位"
        # 使用 seat_data 获取座位号
        for floor, seats in seat_data.items():
            if booking_dict['seat_id'] in seats['Z'].values():
                for seat_number, seat_id in seats['Z'].items():
                    if seat_id == booking_dict['seat_id']:
                        booking_dict['seat_name'] = f"{floor}Z{seat_number:02d}"
                        break
        # 调试输出
        print(f"Booking: {booking_dict}")
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

    # 获取用户信息
    user_info = get_user_info(user_id)
    if user_info:
        _, feishu_webhook, _ = user_info

    # 删除预约记录
    cursor.execute("DELETE FROM bookings WHERE id = ? AND user_id = ?", (booking_id, user_id))
    conn.commit()
    conn.close()

    # 停止调度器任务
    job_id = f"booking_{booking_id}"
    try:
        scheduler.remove_job(job_id)
        print(f"任务 {job_id} 已取消")
    except Exception as e:
        print(f"无法取消任务 {job_id}：{e}")

    # 发送飞书通知，告知用户已取消预约
    if feishu_webhook:
        send_feishu_notification(feishu_webhook, "预约已取消")

    return redirect(url_for("my_bookings"))

# 删除已完成的预约
@app.route("/delete_completed_booking/<int:booking_id>")
def delete_completed_booking(booking_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 检查预约是否已完成
    cursor.execute("SELECT processed FROM bookings WHERE id = ? AND user_id = ?", (booking_id, user_id))
    result = cursor.fetchone()

    if result and result[0]:  # 如果 processed 为 True
        # 删除预约记录
        cursor.execute("DELETE FROM bookings WHERE id = ? AND user_id = ?", (booking_id, user_id))
        conn.commit()
        conn.close()
        return redirect(url_for("my_bookings"))
    else:
        conn.close()
        return "无法删除未完成的预约", 400

# 首页（抢座位）
@app.route("/", methods=["GET", "POST"])
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            user_id = session["user_id"]
            user_info = get_user_info(user_id)
            if not user_info:
                return jsonify({'message': '用户信息不存在'})

            # 调试输出
            print(f"用户信息: {user_info}")

            # 确保正确解包 user_info 返回的值
            username, feishu_webhook, notification_method = user_info

            cookie = request.form.get("cookie")
            seat_id = request.form.get("seat_id")
            time_slots = request.form.getlist("time_slots")
            operation_mode = request.form.get("operation_mode")
            frequency = 10  # 默认每10秒查询一次

            # 调试输出
            print(f"表单提交数据: cookie={cookie}, seat_id={seat_id}, time_slots={time_slots}, operation_mode={operation_mode}")

            if not cookie or not seat_id or not time_slots:
                return jsonify({'message': '请填写完整信息'})

            now = datetime.now()

            # 根据操作方式设置日期
            if operation_mode == "auto_book":
                if now.hour >= 6:
                    date = (now + timedelta(days=1)).strftime('%Y-%m-%d')
                else:
                    date = now.strftime('%Y-%m-%d')
                frequency = None  # 自动预约模式下没有频率
            else:
                # 循环预约使用今天的日期
                date = now.strftime('%Y-%m-%d')
                frequency = 10  # 确保在循环预约模式下频率为10

            # 转换时间段 ID 列表为字符串
            time_slots_str = ','.join(time_slots)

            booking = {
                'user_id': user_id,
                'cookie': cookie,
                'seat_id': seat_id,
                'date': date,
                'time_slots': time_slots_str,
                'processed': False,
                'result': "预约记录已保存，待自动执行" if operation_mode == "auto_book" else None,
                'loop_booking': operation_mode != "auto_book",
                'frequency': frequency,
                'feishu_webhook': feishu_webhook  # 确保在 booking 中存储 feishu_webhook
            }

            booking_id = save_booking(booking)
            print(f"预约记录已保存，ID: {booking_id}")

            if operation_mode == "auto_book":
                # 调试输出
                print(f"调用飞书通知，Webhook: {feishu_webhook}, Message: 预约记录已保存，将在明早6:05自动执行")

                if not send_feishu_notification(feishu_webhook, "预约记录已保存，将在明早6:05自动执行"):
                    return jsonify({'message': '飞书通知发送失败'})

                return jsonify({'message': '预约记录已保存，将在明早6:05自动执行'})
            else:
                booking['id'] = booking_id
                print(f"循环预约记录已保存，ID: {booking_id}")

                # 创建一个唯一的 job_id
                job_id = f"booking_{booking_id}"

                # 添加调度器任务，定期执行预约任务
                scheduler.add_job(lambda: auto_book_seat_single(booking, job_id), 'interval', seconds=frequency, id=job_id)

                # 调试输出
                print(f"调用飞书通知，Webhook: {feishu_webhook}, Message: 预约信息已保存，将每10秒查询一次座位信息")

                if not send_feishu_notification(feishu_webhook, "预约信息已保存，将每10秒查询一次座位信息"):
                    return jsonify({'message': '飞书通知发送失败'})

                print(f"循环预约任务已启动，Job ID: {job_id}")
                return jsonify({'message': '预约信息已保存，将每10秒查询一次座位信息'})
        except Exception as e:
            print(f"处理预约请求时出错: {str(e)}")
            return jsonify({'message': f'预约失败: {str(e)}'})

    # 生成座位信息
    floors = generate_seat_info()

    return render_template("template.html", floors=floors)

# 自动预约任务
def get_current_seats(cookie, sjdId):
    headers = {
        'Connection': 'keep-alive',
        'Content-Length': '52',
        'sec-ch-ua-platform': '"Android"',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 12; HBN-AL80 Build/HUAWEIHBN-AL80; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.103 Mobile Safari/537.36 XWEB/1300199 MMWEBSDK/20241103 MMWEBID/7828 MicroMessenger/8.0.55.2780(0x28003737) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64',
        'Accept': '*/*',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://jcc.educationgroup.cn',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://jcc.educationgroup.cn/tsg/kzwWx/index',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cookie': cookie
    }
    data = {
        'rq': datetime.now().strftime('%Y-%m-%d'),
        'sjdId': sjdId
    }
    response = requests.post(get_seats_url, headers=headers, data=data, timeout=10)
    if response.status_code == 200:
        try:
            current_seats = response.json()
            print(f"获取到座位数据: {current_seats}")
            return current_seats.get('data', [])
        except ValueError:
            print("解析座位数据时出错")
            return []
    else:
        print("获取当前座位数据失败")
        return []

def filter_zones(seats_data):
    filtered_data = {
        '3F(Z区)': [],
        '4F(Z区)': [],
        '5F(Z区)': []
    }
    for area in seats_data:
        room_name = area.get('roomName', '')
        if "3F(Z区)" in room_name:
            filtered_data['3F(Z区)'].extend(area.get('zwList', []))
        elif "4F(Z区)" in room_name:
            filtered_data['4F(Z区)'].extend(area.get('zwList', []))
        elif "5F(Z区)" in room_name:
            filtered_data['5F(Z区)'].extend(area.get('zwList', []))
    return filtered_data

# 辅助函数，用于检查消息是否重复
def should_send_notification(last_message, current_message):
    return current_message != last_message

def auto_book_seat_single(booking, job_id):
    try:
        print(f"开始处理预约任务: {booking['id']}")

        # 确保 time_slots 是列表
        if isinstance(booking['time_slots'], str):
            time_slots = booking['time_slots'].split(',')
        elif isinstance(booking['time_slots'], list):
            time_slots = booking['time_slots']
        else:
            raise ValueError("time_slots 必须是字符串或列表")

        print(f"解析后的时间段: {time_slots}")
        booking['time_slots'] = time_slots  # 保存解析后的列表

        # 从数据库中获取用户信息
        user_info = get_user_info(booking['user_id'])
        if not user_info:
            raise ValueError("用户信息不存在")

        _, feishu_webhook, _ = user_info
        booking['feishu_webhook'] = feishu_webhook

        # 设置请求头
        headers = {
            'Connection': 'keep-alive',
            'sec-ch-ua-platform': '"Android"',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 12; HBN-AL80 Build/HUAWEIHBN-AL80; wv) AppleWebKit/537.36 (KHTML, Gecko) Version/4.0 Chrome/130.0.6723.103 Mobile Safari/537.36 XWEB/1300199 MMWEBSDK/20241103 MMWEBID/7828 MicroMessenger/8.0.55.2780(0x28003737) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64',
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://jcc.educationgroup.cn',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://jcc.educationgroup.cn/tsg/kzwWx/index',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cookie': booking['cookie']
        }

        # 获取当前座位数据
        available_seats = {}
        assigned_slots = []
        failure_details = []
        seat_code_map = {}
        seat_floor_map = {}
        all_slots_success = True

        for sjdId in time_slots:
            current_seats_data = get_current_seats(booking['cookie'], sjdId)
            filtered_seats_data = filter_zones(current_seats_data)

            # 分析座位数据
            for floor, seats in filtered_seats_data.items():
                for seat in seats:
                    seat_code_map[seat['id']] = seat['zwCode']
                    seat_floor_map[seat['id']] = floor
                    if seat['id'] == booking['seat_id']:
                        if booking['seat_id'] not in available_seats:
                            available_seats[booking['seat_id']] = []
                        available_seats[booking['seat_id']].append(sjdId)
                    elif sjdId not in available_seats.get(seat['id'], []):
                        available_seats[seat['id']] = available_seats.get(seat['id'], [])
                        available_seats[seat['id']].append(sjdId)

        print(f"可用座位数据: {available_seats}")

        # 预约逻辑
        for sjdId in list(time_slots):  # 创建时间段列表的副本
            if sjdId in available_seats.get(booking['seat_id'], []):
                data = {
                    'rq': booking['date'],
                    'sjdId': sjdId,
                    'zwId': booking['seat_id'],
                }
                response = requests.post(url, headers=headers, data=data, timeout=10)
                if response.status_code == 200:
                    assigned_slots.append((sjdId, booking['seat_id']))
                    if sjdId in booking['time_slots']:  # 检查时间段是否存在于列表中
                        booking['time_slots'].remove(sjdId)  # 移除已预约的时间段
                else:
                    all_slots_success = False
                    failure_details.append((sjdId, booking['seat_id'], response.status_code))
            else:
                all_slots_success = False
                for seat_id, slots in available_seats.items():
                    if sjdId in slots:
                        data = {
                            'rq': booking['date'],
                            'sjdId': sjdId,
                            'zwId': seat_id,
                        }
                        response = requests.post(url, headers=headers, data=data, timeout=10)
                        if response.status_code == 200:
                            assigned_slots.append((sjdId, seat_id))
                            if sjdId in booking['time_slots']:  # 检查时间段是否存在于列表中
                                booking['time_slots'].remove(sjdId)  # 移除已预约的时间段
                            break
                        else:
                            failure_details.append((sjdId, seat_id, response.status_code))
                else:
                    floor_zones = next((key for key, seats in filtered_seats_data.items() if booking['seat_id'] in [seat['id'] for seat in seats]), None)
                    if floor_zones:
                        for seat in filtered_seats_data[floor_zones]:
                            if sjdId in available_seats.get(seat['id'], []):
                                data = {
                                    'rq': booking['date'],
                                    'sjdId': sjdId,
                                    'zwId': seat['id'],
                                }
                                response = requests.post(url, headers=headers, data=data, timeout=10)
                                if response.status_code == 200:
                                    assigned_slots.append((sjdId, seat['id']))
                                    if sjdId in booking['time_slots']:  # 检查时间段是否存在于列表中
                                        booking['time_slots'].remove(sjdId)  # 移除已预约的时间段
                                    break
                                else:
                                    failure_details.append((sjdId, seat['id'], response.status_code))

        # 结果消息转换时间段ID
        assigned_slots_formatted = [f"成功预约 座位号: {seat_code_map[seat_id]} ({seat_floor_map[seat_id]}), 时间段: {time_slot_mapping.get(sjdId, 'Unknown Time Slot')}" for sjdId, seat_id in assigned_slots]
        failure_details_formatted = [f"预约失败 座位号: {seat_code_map[seat_id]} ({seat_floor_map[seat_id]}), 时间段: {time_slot_mapping.get(sjdId, 'Unknown Time Slot')}, 错误代码: {status_code}" for sjdId, seat_id, status_code in failure_details]

        # 输出结果
        result_message = ""
        if assigned_slots_formatted:
            result_message += "\n".join(assigned_slots_formatted)
            if not all_slots_success:
                result_message += "\n所选座位已被占用，自动更改为其他座位。"
        if failure_details_formatted:
            result_message += "\n".join(failure_details_formatted)

        # 检查是否需要发送飞书通知
        if result_message:
            if should_send_notification(booking.get('last_result', ''), result_message):
                print(f"预约结果: {result_message}")
                booking['result'] = result_message
                booking['processed'] = True
                booking['last_result'] = result_message  # 更新最后消息状态
                update_booking(booking)  # 更新数据库中的预约信息
                send_feishu_notification(booking['feishu_webhook'], booking['result'])  # 发送飞书通知
            else:
                print("消息未发生变化，不发送飞书通知。")

        # 检查所有时间段是否已成功预约
        if not booking['time_slots']:
            print(f"所有时间段成功预约，停止任务 {job_id}")
            try:
                scheduler.remove_job(job_id)
            except Exception as e:
                print(f"无法移除任务 {job_id}: {e}")
            update_booking(booking)  # 更新数据库中的状态

    except Exception as e:
        error_message = f"预约失败: {str(e)}"
        print(f"处理预约任务时出错: {error_message}")
        booking['result'] = error_message
        booking['processed'] = True
        booking['last_result'] = error_message  # 更新最后消息状态
        if 'time_slots' not in booking:  # 确保 time_slots 存在
            booking['time_slots'] = []
        update_booking(booking)
        send_feishu_notification(booking['feishu_webhook'], booking['result'])  # 发送飞书通知

def auto_book_seat():
    try:
        # 加载所有未处理的预约记录
        bookings = load_bookings()
        for booking in bookings:
            if booking['processed']:
                continue  # 如果预约已处理，跳过

            # 生成唯一的 job_id
            job_id = f"booking_{booking['id']}"

            # 检查是否已经存在相同 job_id 的任务
            if scheduler.get_job(job_id):
                print(f"任务 {job_id} 已存在，跳过")
                continue

            # 添加调度器任务，10秒后执行
            scheduler.add_job(
                lambda: auto_book_seat_single(booking, job_id),
                'date',
                run_date=datetime.now() + timedelta(seconds=2),  # 2秒后执行
                id=job_id
            )
            print(f"任务 {job_id} 已添加")

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

# 清除已完成预约的记录
def clear_completed_bookings():
    """
    清除所有时间段都预约成功的记录（time_slots 为空的记录）
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # 删除 time_slots 为空的记录
        cursor.execute('DELETE FROM bookings WHERE time_slots = ""')
        conn.commit()
        print(f"已清除 {cursor.rowcount} 条已完成预约的记录")
    except sqlite3.Error as e:
        print(f"清除预约记录时出错: {e}")
    finally:
        conn.close()

# 添加任务到调度器
scheduler.add_job(auto_book_seat, 'cron', hour=6, minute=1, second=30)  # 每天早上 6:01:30 执行
scheduler.add_job(get_seat_data, 'interval', minutes=5)  # 每 5 分钟获取一次座位数据
scheduler.add_job(clear_completed_bookings, 'cron', hour=18, minute=30)  # 每天 18:30 清除已完成预约的记录

if __name__ == "__main__":
    init_db()
    get_seat_data()  # 初始化任务
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)