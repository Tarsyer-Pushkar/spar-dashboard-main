from flask import Blueprint, render_template, session, redirect, url_for

dashboard_bp = Blueprint("dashboard", __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

@dashboard_bp.route("/overview")
@login_required
def overview():
    return render_template("overview.html")

@dashboard_bp.route("/devices")
@login_required
def devices():
    return render_template("heartbeat.html")

@dashboard_bp.route("/heatmap")
@login_required
def heatmap():
    return render_template("heatmap.html")

@dashboard_bp.route("/queue")
@login_required
def queue():
    return render_template("queue.html")
