from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shifts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

ADMIN_PASSWORD = "admin"

# --- データベースモデル ---
class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(20), nullable=False, default="0000") 
    display_order = db.Column(db.Integer, default=0)
    is_double_shift = db.Column(db.Boolean, default=False) # 【追加】昼夜シフト対応フラグ

class ShiftRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)

class ShiftRequestV2(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time_of_day = db.Column(db.String(10), nullable=False) 

class ShiftSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    target_month = db.Column(db.String(7), nullable=False)
    memo = db.Column(db.String(500), nullable=True)

class SystemSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(50), nullable=False)

with app.app_context():
    db.create_all()
    if not SystemSetting.query.filter_by(key='submission_is_open').first():
        db.session.add(SystemSetting(key='submission_is_open', value='true'))
        db.session.commit()

# --- 画面を表示するルート ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/staff_manage')
def staff_manage():
    return render_template('staff_manage.html')

# --- APIエンドポイント ---
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    if data.get('password') == ADMIN_PASSWORD:
        return jsonify({"message": "ログイン成功"}), 200
    return jsonify({"error": "パスワードが違います"}), 401

@app.route('/api/status', methods=['GET'])
def get_status():
    setting = SystemSetting.query.filter_by(key='submission_is_open').first()
    is_open = (setting.value == 'true') if setting else True
    return jsonify({"is_open": is_open}), 200

@app.route('/api/status', methods=['POST'])
def update_status():
    data = request.json
    setting = SystemSetting.query.filter_by(key='submission_is_open').first()
    if setting:
        setting.value = 'true' if data['is_open'] else 'false'
        db.session.commit()
    return jsonify({"message": "設定を更新しました"}), 200

@app.route('/api/staff', methods=['POST'])
def add_staff():
    data = request.json
    max_order = db.session.query(db.func.max(Staff.display_order)).scalar() or 0
    # フラグを受け取って保存
    new_staff = Staff(
        name=data['name'], 
        password=data['password'], 
        display_order=max_order + 1,
        is_double_shift=data.get('is_double_shift', False)
    )
    db.session.add(new_staff)
    db.session.commit()
    return jsonify({"message": "登録しました"}), 201

@app.route('/api/staff', methods=['GET'])
def get_staff():
    staff_list = Staff.query.order_by(Staff.display_order).all()
    return jsonify([{
        "id": s.id, "name": s.name, "password": s.password, "is_double_shift": s.is_double_shift
    } for s in staff_list]), 200

@app.route('/api/staff/reorder', methods=['POST'])
def reorder_staff():
    data = request.json
    for item in data:
        staff = Staff.query.get(item['id'])
        if staff:
            staff.display_order = item['display_order']
    db.session.commit()
    return jsonify({"message": "順番を更新しました"}), 200

@app.route('/api/staff/<int:staff_id>', methods=['DELETE'])
def delete_staff(staff_id):
    staff = Staff.query.get(staff_id)
    if staff:
        ShiftRequest.query.filter_by(staff_id=staff_id).delete()
        ShiftRequestV2.query.filter_by(staff_id=staff_id).delete()
        ShiftSubmission.query.filter_by(staff_id=staff_id).delete()
        db.session.delete(staff)
        db.session.commit()
    return jsonify({"message": "削除しました"}), 200

@app.route('/api/staff/my_shifts', methods=['POST'])
def get_my_shifts():
    data = request.json
    staff_id = data.get('staff_id')
    password = data.get('password')
    target_month = data.get('target_month')

    staff = Staff.query.get(staff_id)
    if not staff or staff.password != password:
        return jsonify({"error": "従業員番号が間違っています。"}), 401

    submission = ShiftSubmission.query.filter_by(staff_id=staff_id, target_month=target_month).first()
    
    if submission:
        requests = ShiftRequestV2.query.filter(ShiftRequestV2.staff_id == staff_id, ShiftRequestV2.date.like(f"{target_month}-%")).all()
        day_offs = [r.date.strftime('%Y-%m-%d') for r in requests if r.time_of_day == 'day']
        night_offs = [r.date.strftime('%Y-%m-%d') for r in requests if r.time_of_day == 'night']
        return jsonify({
            "submitted": True,
            "day_offs": day_offs,
            "night_offs": night_offs,
            "memo": submission.memo or "",
            "is_double_shift": staff.is_double_shift # マイページに情報を渡す
        }), 200
    else:
        return jsonify({
            "submitted": False, 
            "day_offs": [], 
            "night_offs": [], 
            "memo": "", 
            "is_double_shift": staff.is_double_shift
        }), 200

@app.route('/api/shifts', methods=['POST'])
def submit_shift():
    setting = SystemSetting.query.filter_by(key='submission_is_open').first()
    if setting and setting.value == 'false':
        return jsonify({"error": "現在、回答の受付を停止しています。"}), 403

    data = request.json
    staff_id = data['staff_id']
    password = data.get('password', '')
    day_offs = data.get('day_offs', [])
    night_offs = data.get('night_offs', [])
    target_month = data['target_month']
    memo = data.get('memo', '')

    staff = Staff.query.get(staff_id)
    if not staff or staff.password != password:
        return jsonify({"error": "従業員番号が間違っています。"}), 401

    ShiftRequestV2.query.filter(ShiftRequestV2.staff_id == staff_id, ShiftRequestV2.date.like(f"{target_month}-%")).delete(synchronize_session=False)
    ShiftSubmission.query.filter_by(staff_id=staff_id, target_month=target_month).delete()

    submission = ShiftSubmission(staff_id=staff_id, target_month=target_month, memo=memo)
    db.session.add(submission)

    for date_str in day_offs:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        new_request = ShiftRequestV2(staff_id=staff_id, date=date_obj, time_of_day='day')
        db.session.add(new_request)

    for date_str in night_offs:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        new_request = ShiftRequestV2(staff_id=staff_id, date=date_obj, time_of_day='night')
        db.session.add(new_request)
    
    db.session.commit()
    return jsonify({"message": "登録完了"}), 201

@app.route('/api/shifts/<month_str>', methods=['GET'])
def get_shifts(month_str):
    shift_list = [{"staff_name": s.staff_name, "date": s.date.strftime('%Y-%m-%d'), "time_of_day": s.time_of_day} for s in db.session.query(ShiftRequestV2.date, ShiftRequestV2.time_of_day, Staff.name.label('staff_name')).join(Staff).filter(ShiftRequestV2.date.like(f"{month_str}-%")).all()]
    submissions = ShiftSubmission.query.filter_by(target_month=month_str).all()
    submitted_info = []
    for sub in submissions:
        staff_name = Staff.query.get(sub.staff_id).name
        submitted_info.append({
            "name": staff_name,
            "memo": sub.memo or ""
        })

    return jsonify({"shifts": shift_list, "submitted_info": submitted_info}), 200

if __name__ == '__main__':
    app.run(debug=True)