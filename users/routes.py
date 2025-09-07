from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from ext import db

users_bp = Blueprint("users", __name__, url_prefix="/me")

@users_bp.get("/")
@login_required
def profile(): return render_template("profile.html", user=current_user)

@users_bp.post("/update")
@login_required
def update_profile():
    current_user.email = request.form.get("email", current_user.email)
    db.session.commit()
    return redirect(url_for("users.profile"))

@users_bp.post("/change-password")
@login_required
def change_password():
    old = request.form.get("old_password"); new = request.form.get("new_password")
    if not current_user.check_password(old):
        return render_template("profile.html", user=current_user, error="旧密码不正确")
    current_user.set_password(new); db.session.commit()
    return redirect(url_for("users.profile"))
