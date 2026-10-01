import os
from flask import Flask, jsonify, request, render_template, redirect, url_for

from models import db, Task


def create_app():
    app = Flask(__name__)

    db_url = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.route("/health")
    def health():
        return jsonify(status="ok"), 200

    @app.route("/ready")
    def ready():
        try:
            db.session.execute(db.text("SELECT 1"))
            return jsonify(status="ready"), 200
        except Exception as exc:
            return jsonify(status="not-ready", error=str(exc)), 503

    @app.route("/")
    def index():
        tasks = Task.query.order_by(Task.id).all()
        return render_template("index.html", tasks=tasks, priorities=Task.VALID_PRIORITIES)

    @app.route("/tasks/new", methods=["POST"])
    def create_task_ui():
        title = request.form.get("title", "").strip()
        priority = request.form.get("priority", "medium")
        if priority not in Task.VALID_PRIORITIES:
            priority = "medium"
        if title:
            task = Task(title=title, priority=priority)
            db.session.add(task)
            db.session.commit()
        return redirect(url_for("index"))

    @app.route("/tasks/<int:task_id>/toggle", methods=["POST"])
    def toggle_task_ui(task_id):
        task = Task.query.get_or_404(task_id)
        task.done = not task.done
        db.session.commit()
        return redirect(url_for("index"))

    @app.route("/api/tasks", methods=["GET"])
    def list_tasks():
        tasks = Task.query.order_by(Task.id).all()
        return jsonify([t.to_dict() for t in tasks]), 200

    @app.route("/api/tasks", methods=["POST"])
    def create_task():
        data = request.get_json(silent=True) or {}
        title = data.get("title", "").strip()
        if not title:
            return jsonify(error="title is required"), 400

        priority = data.get("priority", "medium")
        if priority not in Task.VALID_PRIORITIES:
            return jsonify(error="priority must be one of low, medium, high"), 400

        task = Task(
            title=title,
            description=data.get("description"),
            priority=priority,
        )
        db.session.add(task)
        db.session.commit()
        return jsonify(task.to_dict()), 201

    @app.route("/api/tasks/<int:task_id>", methods=["GET"])
    def get_task(task_id):
        task = Task.query.get_or_404(task_id)
        return jsonify(task.to_dict()), 200

    @app.route("/api/tasks/<int:task_id>", methods=["PUT"])
    def update_task(task_id):
        task = Task.query.get_or_404(task_id)
        data = request.get_json(silent=True) or {}

        if "title" in data:
            task.title = data["title"]
        if "description" in data:
            task.description = data["description"]
        if "priority" in data:
            if data["priority"] not in Task.VALID_PRIORITIES:
                return jsonify(error="priority must be one of low, medium, high"), 400
            task.priority = data["priority"]
        if "done" in data:
            task.done = bool(data["done"])

        db.session.commit()
        return jsonify(task.to_dict()), 200

    @app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
    def delete_task(task_id):
        task = Task.query.get_or_404(task_id)
        db.session.delete(task)
        db.session.commit()
        return "", 204

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
