"""app.py — ITIS Platform Flask application (с поддержкой multi-company)."""

from flask import Flask, render_template


def create_app(testing: bool = False) -> Flask:
    app = Flask(__name__)
    app.config["TESTING"] = testing
    app.config["JSON_SORT_KEYS"] = False

    # ── Существующие blueprints ────────────────────────────────────────────
    from routes import itis_bp, bak_bp, ml_bp, export_bp
    for bp in (itis_bp, bak_bp, ml_bp, export_bp):
        app.register_blueprint(bp)

    # ── Новые blueprints для multi-company ────────────────────────────────
    from routes.api_companies import companies_bp
    from routes.export_companies import export_companies_bp
    app.register_blueprint(companies_bp)
    app.register_blueprint(export_companies_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/health")
    def health():
        from flask import jsonify
        return jsonify({"status": "ok", "service": "ITIS Platform"}), 200

    return app


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    create_app().run(host="0.0.0.0", port=port, debug=False)
app = create_app()
