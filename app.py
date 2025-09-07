from flask import Flask, render_template, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import inspect

from ext import db, login_manager, migrate
from models import User, Role
from auth.routes import auth_bp
from users.routes import users_bp
from admin.routes import admin_bp

app = Flask(__name__)
app.config.update(
    SECRET_KEY="dev-key",
    SQLALCHEMY_DATABASE_URI="sqlite:///app.db",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

db.init_app(app);
login_manager.init_app(app);
migrate.init_app(app, db)
app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(admin_bp)


@login_manager.user_loader
def load_user(uid): return db.session.get(User, int(uid))


@app.get("/")
@login_required
def dashboard():
    users = roles = None
    if current_user.has_role("admin"):
        users = User.query.order_by(User.id.asc()).all()
        roles = Role.query.all()
    return render_template("base.html", users=users, roles=roles)


# 初始化命令：建表 + 种子管理员与角色
@app.cli.command("seed")
def seed():
    db.create_all()
    admin = Role.query.filter_by(name="admin").first() or Role(name="admin", desc="管理员")
    userr = Role.query.filter_by(name="user").first() or Role(name="user", desc="普通用户")
    db.session.add_all([admin, userr]);
    db.session.commit()
    if not User.query.filter_by(username="admin").first():
        u = User(username="admin", email="admin@local")
        u.set_password("Admin123!")
        u.roles.append(admin)
        db.session.add(u);
        db.session.commit()
        print("admin 账户已创建：用户名 admin / 密码 Admin123!")


with app.app_context():
    inspector = inspect(db.engine)
    # 如果没有 users 表，就说明数据库还没初始化
    if not inspector.has_table("users"):
        print("！检测到数据库为空，正在初始化……")
        db.create_all()

        # 创建角色
        admin_role = Role(name="admin", desc="管理员")
        user_role = Role(name="user", desc="普通用户")
        db.session.add_all([admin_role, user_role])
        db.session.commit()

        # 创建默认管理员
        admin = User(username="admin", email="admin@local")
        admin.set_password("Admin123!")
        admin.roles.append(admin_role)
        db.session.add(admin)
        db.session.commit()

        print("！ 初始化完成，默认管理员账号：admin / Admin123!")
    else:
        print("数据库已存在，执行兜底检查…")
        # 兜底：确保角色表里有 admin/user
        admin_role = Role.query.filter_by(name="admin").first()
        user_role = Role.query.filter_by(name="user").first()
        changed = False
        if not admin_role:
            admin_role = Role(name="admin", desc="管理员");
            db.session.add(admin_role);
            changed = True
        if not user_role:
            user_role = Role(name="user", desc="普通用户");
            db.session.add(user_role);
            changed = True
        if changed: db.session.commit()

        # 兜底：确保至少存在一个 admin 账户
        admin_user = User.query.filter_by(username="admin").first()
        if not admin_user:
            admin_user = User(username="admin", email="admin@local")
            admin_user.set_password("Admin123!")
            admin_user.roles.append(admin_role)
            db.session.add(admin_user);
            db.session.commit()
            print("已补种默认管理员：admin / Admin123!")
if __name__ == "__main__":
    app.run(debug=True)
