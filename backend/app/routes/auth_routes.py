from flask import Blueprint, request
from app.config import Config

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return {
            "code": 400,
            "message": "用户名和密码不能为空",
            "data": None
        }, 400

    if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
        return {
            "code": 200,
            "message": "登录成功",
            "data": {
                "token": Config.ADMIN_TOKEN,
                "username": username
            }
        }

    return {
        "code": 401,
        "message": "用户名或密码错误",
        "data": None
    }, 401