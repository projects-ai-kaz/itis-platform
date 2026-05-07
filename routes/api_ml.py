"""routes/api_ml.py — REST API для ML-предсказателя."""
from flask import Blueprint, request, jsonify
from models.ml_predictor import PredictInput, predict, FEATURES, FEATURE_KEYS

ml_bp = Blueprint("ml", __name__, url_prefix="/api/ml")


@ml_bp.route("/predict", methods=["POST"])
def ml_predict():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON обязателен."}), 400
    try:
        inp = PredictInput.from_dict(data)
        result = predict(inp)
        return jsonify(result.to_dict()), 200
    except KeyError as e:
        return jsonify({"error": f"Отсутствует признак: {e}"}), 400
    except (TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 422


@ml_bp.route("/features", methods=["GET"])
def feature_info():
    """Список признаков с описаниями и важностью."""
    return jsonify({"features": FEATURES, "keys": FEATURE_KEYS}), 200


@ml_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "module": "ml"}), 200
