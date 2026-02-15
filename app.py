from flask import Flask, render_template
from flask_login import LoginManager
from models import db, User, Product, Comment
import os

app = Flask(__name__)

# 配置 (实际开发中密钥要保密)
app.config['SECRET_KEY'] = '123456'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 自动创建数据库函数
def create_tables():
    with app.app_context():
        db.create_all()
        print(">>> 数据库表已创建成功！(site.db)")

# 路由：首页
@app.route("/")
def home():
    return "<h1>欢迎来到 Flask 校园二手交易平台！</h1><p>环境配置成功，数据库已连接。</p>"

if __name__ == '__main__':
    # 如果数据库文件不存在，就创建它
    if not os.path.exists('site.db'):
        create_tables()
    
    app.run(debug=True)