import json

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from ext import db
from models import User, Role, ResetToken, LoginLog

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def require_admin():
    return current_user.is_authenticated and current_user.has_role("admin")

def _wants_json():
    # 前端 fetch 会带这个头；也兼容 Accept: application/json
    return request.headers.get("X-Requested-With") == "XMLHttpRequest" or \
           request.accept_mimetypes.best == "application/json"

@admin_bp.before_request
def guard():
    if not require_admin():
        from flask import abort
        abort(403)


@admin_bp.get("/users")
def users_list():
    return render_template("admin_users.html",
                           users=User.query.all(),
                           roles=Role.query.all())


@admin_bp.post("/users/create")
def create_user():
    username = (request.form.get("username") or "").strip()
    email = (request.form.get("email") or "").strip()
    pwd = (request.form.get("password") or "Init123!").strip()

    if not username or not email:
        payload = {"ok": False, "message": "用户名和邮箱必填"}
        return (jsonify(payload), 400) if _wants_json() else redirect(url_for("admin.users_list"))

    # 唯一性校验
    exists = User.query.filter(or_(User.username == username, User.email == email)).first()
    if exists:
        payload = {"ok": False, "message": "用户名或邮箱已存在"}
        return (jsonify(payload), 409) if _wants_json() else redirect(url_for("admin.users_list"))

    u = User(username=username, email=email)
    u.set_password(pwd)

    # 默认给普通角色
    role_user = Role.query.filter_by(name="user").first()
    if role_user:
        u.roles.append(role_user)

    db.session.add(u)
    db.session.commit()

    payload = {
        "ok": True,
        "message": f"User {u.username} created",
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "roles": [r.name for r in u.roles],  # ← 返回字符串列表
    }
    return jsonify(payload) if _wants_json() else redirect(url_for("admin.users_list"))


@admin_bp.post("/users/<int:uid>/grant")
def grant(uid):
    u = db.session.get(User, uid)
    r = Role.query.filter_by(name=request.form["role"]).first()
    if not u or not r:
        payload = {"ok": False, "message": "User not found"}
        return (jsonify(payload), 400) if _wants_json() else redirect(url_for("admin.users_list"))
    if u and r and not u.has_role(r.name):
        u.roles.append(r);db.session.commit()

    payload = {"ok": True, "message": f"已授予 {u.username} 角色 {r.name}",
               "id": u.id, "roles": [x.name for x in u.roles]}
    return jsonify(payload) if _wants_json() else redirect(url_for("admin.users_list"))


@admin_bp.post("/users/<int:uid>/revoke")
def revoke(uid):
    u = db.session.get(User, uid)
    r = Role.query.filter_by(name=request.form["role"]).first()
    if not u or not r:
        payload = {"ok": False, "message": "用户或角色不存在"}
        return (jsonify(payload), 400) if _wants_json() else redirect(url_for("admin.users_list"))

        # 不能撤销自己 & 不能撤掉系统最后一个 admin
    if u == current_user:
        payload = {"ok": False, "message": "不能撤销自己的权限"}
        return (jsonify(payload), 400) if _wants_json() else redirect(url_for("admin.users_list"))

    if r.name == "admin" and u.has_role("admin"):
        admin_count = User.query.join(User.roles).filter(Role.name == "admin").count()
        if admin_count <= 1:
            payload = {"ok": False, "message": "系统至少保留一名管理员"}
            return (jsonify(payload), 400) if _wants_json() else redirect(url_for("admin.users_list"))

    u.roles = [x for x in u.roles if x.id != r.id]
    db.session.commit()
    payload = {"ok": True, "message": f"已撤销 {u.username} 的 {r.name}",
               "id": u.id, "roles": [x.name for x in u.roles]}
    return jsonify(payload) if _wants_json() else redirect(url_for("admin.users_list"))


@admin_bp.post("/users/<int:uid>/delete")
def delete(uid):
    u = db.session.get(User, uid)
    if not u:
        payload = {"ok": False, "message": "用户不存在"}
        return (jsonify(payload), 400) if _wants_json() else redirect(url_for("admin.users_list"))

    if u == current_user:
        payload = {"ok": False, "message": "不能删除自己"}
        return (jsonify(payload), 400) if _wants_json() else redirect(url_for("admin.users_list"))

    if u.has_role("admin"):
        admin_count = User.query.join(User.roles).filter(Role.name == "admin").count()
        if admin_count <= 1:
            payload = {"ok": False, "message": "系统至少保留一名管理员"}
            return (jsonify(payload), 400) if _wants_json() else redirect(url_for("admin.users_list"))

    username = u.username
    u.roles.clear()
    ResetToken.query.filter_by(user_id=uid).delete()
    LoginLog.query.filter_by(user_id=uid).delete()
    db.session.delete(u);
    db.session.commit()

    payload = {"ok": True, "message": f"已删除用户 {username}", "id": uid}
    return jsonify(payload) if _wants_json() else redirect(url_for("admin.users_list"))


@admin_bp.post("/users/<int:uid>/reset-password")
def reset(uid):
    u = db.session.get(User, uid)
    if not u:
        payload = {"ok": False, "message": "用户不存在"}
        return (jsonify(payload), 400) if _wants_json() else redirect(url_for("admin.users_list"))

    new_pwd = request.form.get("new_password", "").strip()
    if not new_pwd:
        payload = {"ok": False, "message": "新密码不能为空"}
        return (jsonify(payload), 400) if _wants_json() else redirect(url_for("admin.users_list"))

    u.set_password(new_pwd); db.session.commit()
    payload = {"ok": True, "message": f"已重置 {u.username} 的密码", "id": u.id}
    return jsonify(payload) if _wants_json() else redirect(url_for("admin.users_list"))
