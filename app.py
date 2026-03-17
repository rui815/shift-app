from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt  # パスワードのハッシュ化に使用
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# Flaskアプリケーションの初期化
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shifts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # セッション管理に必要
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# データベースモデル
class UserRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    month = db.Column(db.String(20), nullable=False)  # ここに値が渡される必要がある
    days = db.Column(db.String(200), nullable=False)

class Admin(UserMixin, db.Model):  # 管理者モデル
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# データベースの初期化（アプリケーションコンテキスト内で実行）
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_request():
    # フォームデータを取得
    name = request.form['name']
    month = request.form['month']  # フォームから月を取得
    days = request.form['days']  # 選択された日付を取得

    # 新しい希望休をデータベースに保存
    new_request = UserRequest(name=name, month=month , days=days)
    db.session.add(new_request)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    # 管理者のみが希望休を閲覧可能
    user_requests = UserRequest.query.all()
    return render_template('admin.html', user_requests=user_requests)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and bcrypt.check_password_hash(admin.password, password):
            login_user(admin)
            return redirect(url_for('admin'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)







