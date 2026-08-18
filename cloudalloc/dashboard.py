from flask import Blueprint, render_template


dashboard = Blueprint("dashboard", __name__)


@dashboard.get("/")
def index():
    return render_template("index.html")

