from flask import Flask, request, render_template, jsonify
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3

app = Flask(__name__)

# 配置信息
url = 'https://jcc.educationgroup.cn/tsg/kzwWx/save'
headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 12; HBN-AL80 Build/HUAWEIHBN-AL80; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.103 Mobile Safari/537.36 XWEB/1300199 MMWEBSDK/20241103 MMWEBID/7828 MicroMessenger/8.0.55.2780(0x28003737) WeChat/arm64 Weixin NetType/4G Language/zh_CN ABI/arm64',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
}

# 已有座位数据
seat_data = {
    '3F': {'Z': {
        3: 'EB5736CADE5AFB94E0530B96CE0A6065', 5: 'EB5736CADE63FB94E0530B96CE0A6065',
        11: 'EB5736CADE65FB94E0530B96CE0A6065', 15: 'EB5736CADE52FB94E0530B96CE0A6065',
        19: 'EB5736CADE5CFB94E0530B96CE0A6065', 33: '344040c9414a4128bc67e03e128f8136',
        34: 'ccc88464ec874dca9efec249884341b4'
    }},
    '4F': {'Z': {
        1: 'EBD2FE1B50D3A3D0E0530C96CE0AF3C1', 3: 'EBD2FE1B50E3A3D0E0530C96CE0AF3C1',
        4: 'EBD2FE1B50EAA3D0E0530C96CE0AF3C1', 8: 'EBD2FE1B50EBA3D0E0530C96CE0AF3C1',
        11: 'EBD2FE1B50D8A3D0E0530C96CE0AF3C1', 15: 'EBD2FE1B50D9A3D0E0530C96CE0AF3C1',
        25: 'EBD2FE1B50E7A3D0E0530C96CE0AF3C1', 33: 'EBD2FE1B50E5A3D0E0530C96CE0AF3C1'
    }},
    '5F': {'Z': {
        4: 'EBD2FE1B5122A3D0E0530C96CE0AF3C1', 8: 'EBD2FE1B513AA3D0E0530C96CE0AF3C1',
        10: 'EBD2FE1B5144A3D0E0530C96CE0AF3C1', 12: 'EBD2FE1B513DA3D0E0530C96CE0AF3C1',
        16: 'EBD2FE1B513EA3D0E0530C96CE0AF3C1', 23: 'EBD2FE1B5129A3D0E0530C96CE0AF3C1',
        28: 'EBD2FE1B5147A3D0E0530C96CE0AF3C1', 32: 'EBD2FE1B5132A3D0E0530C96CE0AF3C1',
        35: 'EBD2FE1B5134A3D0E0530C96CE0AF3C1'
    }},
}

# 数据库文件
DB_FILE = 'bookings.db'

# 初始化数据库
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cookie TEXT NOT NULL,
        seat_id TEXT NOT NULL,
        date TEXT NOT NULL,
        time_slots TEXT NOT NULL,
        processed BOOLEAN NOT NULL,
        result TEXT
    )
    ''')
    conn.commit()
    conn.close()

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
            'cookie': row[1],
            'seat_id': row[2],
            'date': row[3],
            'time_slots': row[4].split(','),
            'processed': row[5],
            'result': row[6]
        })
    conn.close()
    return bookings

# 保存预约信息
def save_booking(booking):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO bookings (cookie, seat_id, date, time_slots, processed, result)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (booking['cookie'], booking['seat_id'], booking['date'], ','.join(booking['time_slots']), booking['processed'], booking['result']))
    conn.commit()
    conn.close()

# 更新预约信息
def update_booking(booking):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE bookings
    SET cookie = ?, seat_id = ?, date = ?, time_slots = ?, processed = ?, result = ?
    WHERE id = ?
    ''', (booking['cookie'], booking['seat_id'], booking['date'], ','.join(booking['time_slots']), booking['processed'], booking['result'], booking['id']))
    conn.commit()
    conn.close()

# 删除所有预约信息
def delete_all_bookings():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM bookings')
    conn.commit()
    conn.close()

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
            except Exception as e:
                booking['result'] = f"预约失败: {str(e)}"
            update_booking(booking)
        
        # 清除所有预约记录
        delete_all_bookings()
        
    except Exception as e:
        print(f"自动预约任务失败: {str(e)}")

scheduler = BackgroundScheduler()
scheduler.add_job(auto_book_seat, 'cron', hour=6, minute=5)
scheduler.start()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        try:
            cookie = request.form.get("cookie")
            seat_id = request.form.get("seat_id")
            time_slots = request.form.getlist("time_slots")
            
            if not cookie or not seat_id or not time_slots:
                return "请填写完整信息"
            
            date = datetime.now().strftime('%Y-%m-%d')
            
            # 不立即执行预约，只保存预约记录
            booking = {
                'cookie': cookie,
                'seat_id': seat_id,
                'date': date,
                'time_slots': time_slots,
                'processed': False,
                'result': "预约记录已保存，待自动执行"
            }
            
            save_booking(booking)
            
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

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)