from flask import Blueprint, request, jsonify
from controllers.verify_controller import verify_signature

verify_bp = Blueprint("verify", __name__)

@verify_bp.route("/verify", methods=["POST"])
def verify():
    res, code = verify_signature(request.json)
    return jsonify(res), code
