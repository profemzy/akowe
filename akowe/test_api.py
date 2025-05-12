from flask import Blueprint, jsonify


bp = Blueprint("test_api", __name__, url_prefix="/test_api")


@bp.route("/hello", methods=["GET"])
def hello():
    return jsonify({"message": "Hello, world!"})
