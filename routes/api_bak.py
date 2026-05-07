"""routes/api_bak.py — REST API для БАК-матрицы."""
from flask import Blueprint, request, jsonify
from models.bak import BakMatrix, Goal, BakModule

bak_bp = Blueprint("bak", __name__, url_prefix="/api/bak")


def _parse_matrix(data: dict) -> BakMatrix:
    return BakMatrix.from_dict(data)


@bak_bp.route("/weights", methods=["POST"])
def suggested_weights():
    """Возвращает рекомендованные веса W на основе матрицы покрытия."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON обязателен."}), 400
    try:
        bak = _parse_matrix(data)
        return jsonify({"weights": bak.suggested_weights(),
                        "kpi_summary": bak.kpi_summary()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bak_bp.route("/toggle", methods=["POST"])
def toggle_cell():
    """Переключает ячейку матрицы и возвращает новое состояние."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON обязателен."}), 400
    try:
        gid = int(data["goal_id"])
        mid = int(data["module_id"])
        bak = _parse_matrix(data.get("matrix", {}))
        new_state = bak.toggle(gid, mid)
        return jsonify({"covered": new_state,
                        "weights": bak.suggested_weights(),
                        "kpi_summary": bak.kpi_summary(),
                        "covered_pairs": [list(p) for p in bak.covered]}), 200
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@bak_bp.route("/summary", methods=["POST"])
def matrix_summary():
    """Полный дамп матрицы с весами и KPI."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON обязателен."}), 400
    try:
        bak = _parse_matrix(data)
        return jsonify(bak.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bak_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "module": "bak"}), 200
