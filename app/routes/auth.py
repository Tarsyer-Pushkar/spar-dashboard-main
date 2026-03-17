from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import bcrypt
from ..db import get_spar_db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/", methods=["GET", "POST"])
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("dashboard.overview"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        db = get_spar_db()
        user = db.dashboard_users.find_one({"username": username})
        if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
            session["user"] = username
            return redirect(url_for("dashboard.overview"))
        flash("Invalid credentials")
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
