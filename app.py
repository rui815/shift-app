from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
# データベースの設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shifts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- データベースモデル ---

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    requests = db.relationship('ShiftRequest', backref='staff', lazy=True)

class ShiftRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    date = db.Column(db.Date, nullable=False) # 'YYYY-MM-DD' 形式
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# データベースの初期化
with app.app_context():
    db.create_all()

# --- APIエンドポイント（フロントエンドと通信する窓口） ---

# 1. スタッフを登録するAPI
@app.route('/api/staff', methods=['POST'])
def add_staff():
    data = request.json
    new_staff = Staff(name=data['name'])
    db.session.add(new_staff)
    db.session.commit()
    return jsonify({"message": f"{data['name']}さんを登録しました！"}), 201

# 2. スタッフ一覧を取得するAPI
@app.route('/api/staff', methods=['GET'])
def get_staff():
    staff_list = Staff.query.all()
    # JSONで返せる形（辞書のリスト）に変換
    result = [{"id": s.id, "name": s.name} for s in staff_list]
    return jsonify(result), 200

# 3. 希望休を提出するAPI
@app.route('/api/shifts', methods=['POST'])
def submit_shift():
    data = request.json
    staff_id = data['staff_id']
    dates = data['dates'] # ["2024-05-01", "2024-05-05"] のようなリストを想定

    for date_str in dates:
        # 文字列を日付データに変換
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        new_request = ShiftRequest(staff_id=staff_id, date=date_obj)
        db.session.add(new_request)
    
    db.session.commit()
    return jsonify({"message": "希望休を登録しました！"}), 201

# 4. 指定した月の希望休一覧を取得するAPI (例: /api/shifts/2024-05)
@app.route('/api/shifts/<month_str>', methods=['GET'])
def get_shifts(month_str):
    # 月の最初と最後の日付範囲を作って検索する処理が必要ですが、
    # 今回はシンプルに「指定した文字（例：2024-05）で始まる日付」を検索します
    shifts = ShiftRequest.query.filter(ShiftRequest.date.like(f"{month_str}-%")).all()
    
    result = []
    for shift in shifts:
        result.append({
            "id": shift.id,
            "staff_name": shift.staff.name, # リレーションを使ってスタッフ名を取得
            "date": shift.date.strftime('%Y-%m-%d')
        })
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(debug=True)



