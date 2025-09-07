from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user
from ext import db
from models import User, LoginLog

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.get("/login")
def login(): return render_template("auth_login.html")


@auth_bp.post("/login")
def login_post():
    username = request.form.get("username");
    password = request.form.get("password")
    u = User.query.filter_by(username=username).first()
    ok = bool(u and u.is_active and u.check_password(password))
    db.session.add(LoginLog(user_id=u.id if u else None,
                            status="success" if ok else "fail",
                            ip=request.remote_addr, ua=request.headers.get("User-Agent")))
    db.session.commit()
    if not ok:
        return render_template("auth_login.html", error="用户名或密码错误")
    login_user(u, remember=True)
    u.last_login_at = datetime.utcnow();
    db.session.commit()
    return redirect(url_for("dashboard"))


@auth_bp.post("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
