from app import db, Admin, app  # app.pyからdb, Adminモデル, appをインポート
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)

# 新しい管理者アカウントの作成
username = "andy"  # 任意のユーザー名
password = "integral0471"  # 任意のパスワード

# パスワードをハッシュ化
hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

# アプリケーションコンテキスト内でデータベース操作を実行
with app.app_context():
    # 管理者アカウントをデータベースに追加
    admin = Admin(username=username, password=hashed_password)
    db.session.add(admin)
    db.session.commit()
    print(f"管理者アカウント '{username}' を作成しました！")

