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
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "done": self.done,
        }
