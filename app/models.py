import json
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    priority = db.Column(db.String(10), nullable=False, default="medium")
    done = db.Column(db.Boolean, nullable=False, default=False)

    VALID_PRIORITIES = ("low", "medium", "high")

    def to_dict(self):
        notes = self.description or ""
        tags = []
        due = ""
        rating = 0
        if self.description and self.description.startswith("{"):
            try:
                meta = json.loads(self.description)
                if isinstance(meta, dict):
                    notes = meta.get("notes", "")
                    tags = meta.get("tags", [])
                    due = meta.get("due", "")
                    rating = meta.get("rating", 0)
            except Exception:
                pass
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "notes": notes,
            "tags": tags,
            "due": due,
            "rating": rating,
            "priority": self.priority,
            "done": self.done,
        }
