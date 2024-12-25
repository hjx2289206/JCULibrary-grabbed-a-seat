from flask import Flask, request, render_template
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import json

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

# 存储用户预约信息的文件
BOOKING_FILE = 'bookings.json'

def load_bookings():
    try:
        with open(BOOKING_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_bookings(bookings):
    with open(BOOKING_FILE, 'w') as f:
        json.dump(bookings, f)

def auto_book_seat():
    bookings = load_bookings()
    for booking in bookings:
        headers['Cookie'] = booking['cookie']
        for sjdId in booking['time_slots']:
            data = {
                'rq': booking['date'],
                'sjdId': sjdId,
                'zwId': booking['seat_id'],
            }
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200:
                print(f"成功预约时间段 {sjdId}")
            else:
                print(f"预约时间段 {sjdId} 失败")
        booking['processed'] = True
    save_bookings(bookings)

scheduler = BackgroundScheduler()
scheduler.add_job(auto_book_seat, 'cron', hour=6, minute=5)  # 每天早上6：05运行
scheduler.start()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        cookie = request.form["cookie"]
        seat_id = request.form["seat_id"]
        date = datetime.now().strftime('%Y-%m-%d')  # 自动获取当前日期
        time_slots = request.form.getlist("time_slots")

        booking = {
            'cookie': cookie,
            'seat_id': seat_id,
            'date': date,
            'time_slots': time_slots,
            'processed': False
        }
        bookings = load_bookings()
        bookings.append(booking)
        save_bookings(bookings)

        return "预约请求已发送"

    # 生成座位信息
    floors = {}
    for floor in range(3, 6):
        floor_name = f'{floor}F'
        floors[floor_name] = []
        for seat_num in range(1, 37 if floor < 5 else 39):
            seat_id = f'{floor_name}Z{seat_num:02d}'
            has_data = seat_num in seat_data.get(floor_name, {}).get('Z', set())
            seat_real_id = seat_data.get(floor_name, {}).get('Z', {}).get(seat_num, seat_id)
            floors[floor_name].append({
                'id': seat_real_id,
                'name': seat_id,
                'has_data': has_data
            })

    return render_template("template.html", floors=floors)

if __name__ == "__main__":
    app.run(debug=True)