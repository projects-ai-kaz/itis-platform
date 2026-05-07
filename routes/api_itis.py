"""routes/api_itis.py — REST API для ITIS-калькулятора."""
from flask import Blueprint, request, jsonify
from models.itis import Module, calculate

itis_bp = Blueprint("itis", __name__, url_prefix="/api/itis")


@itis_bp.route("/calculate", methods=["POST"])
def calculate_itis():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Тело запроса должно быть JSON."}), 400
    raw = data.get("modules")
    if not raw or not isinstance(raw, list):
        return jsonify({"error": "Поле 'modules' обязательно и должно быть массивом."}), 400
    try:
        modules = [Module.from_dict(m) for m in raw]
        result = calculate(modules)
    except (KeyError, TypeError) as e:
        return jsonify({"error": f"Неверный формат модуля: {e}"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    return jsonify(result.to_dict()), 200


@itis_bp.route("/validate", methods=["POST"])
def validate_module():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON обязателен."}), 400
    try:
        m = Module.from_dict(data)
        m.validate()
        return jsonify({"valid": True, "itis_i": round(m.itis_i, 4),
                        "efficiency_class": m.efficiency_class}), 200
    except (KeyError, TypeError) as e:
        return jsonify({"valid": False, "error": str(e)}), 400
    except ValueError as e:
        return jsonify({"valid": False, "error": str(e)}), 422


@itis_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "module": "itis"}), 200
