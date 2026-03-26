from flask import Blueprint, request, jsonify
from controllers.signature_controller import register_signature

bp = Blueprint("signatures", __name__)

@bp.route("/register", methods=["POST"])
def register():
    return jsonify(register_signature(request.json))