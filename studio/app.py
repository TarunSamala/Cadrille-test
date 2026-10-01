"""Flask application for browsing STL-1 and its retained phase evidence."""

from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request, send_file

from studio.dataset_service import (
    AssetNotFoundError,
    DatasetError,
    DatasetRepository,
    ObjectNotFoundError,
)


def create_app(repo_root: str | Path | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    repository = DatasetRepository(repo_root)
    app.config["DATASET_REPOSITORY"] = repository

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "dataset": "STL-1",
                "objects": len(repository.records),
                "read_only": True,
            }
        )

    @app.get("/api/summary")
    def summary():
        return jsonify(repository.summary())

    @app.get("/api/objects")
    def objects():
        return jsonify({"objects": repository.list_objects(request.args.get("split"))})

    @app.get("/api/objects/<object_id>")
    def object_detail(object_id: str):
        return jsonify(repository.object_detail(object_id))

    @app.get("/api/objects/<object_id>/report")
    def object_report(object_id: str):
        payload = json.dumps(repository.export_object_report(object_id), indent=2)
        return Response(
            payload,
            mimetype="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{object_id}_evidence_report.json"'
            },
        )

    @app.get("/api/objects/<object_id>/assets/<kind>")
    def object_asset(object_id: str, kind: str):
        path = repository.asset_path(object_id, kind, request.args.get("view"))
        as_attachment = kind in {"phase3_stl", "phase3_3mf"}
        return send_file(path, as_attachment=as_attachment, conditional=True)

    @app.get("/api/artifacts/<name>")
    def global_asset(name: str):
        return send_file(repository.global_asset_path(name), conditional=True)

    @app.errorhandler(ObjectNotFoundError)
    @app.errorhandler(AssetNotFoundError)
    def not_found(exc: DatasetError):
        return jsonify({"error": str(exc)}), 404

    @app.errorhandler(DatasetError)
    def bad_request(exc: DatasetError):
        return jsonify({"error": str(exc)}), 400

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host=os.environ.get("IMAGE2CAD_STUDIO_HOST", "127.0.0.1"),
        port=int(os.environ.get("IMAGE2CAD_STUDIO_PORT", "8501")),
        debug=False,
    )

