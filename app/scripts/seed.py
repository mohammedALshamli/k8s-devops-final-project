"""
Seed script for the Task Tracker app.
Populates the database with 10 sample tasks across all priority levels.
Usage (from the app/ directory): python scripts/seed.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from models import db, Task  # noqa: E402

SAMPLE_TASKS = [
    {"title": "Set up VMware NAT network", "priority": "high", "done": True},
    {"title": "Provision cp1 and w1 VMs", "priority": "high", "done": True},
    {"title": "Configure passwordless SSH", "priority": "high", "done": True},
    {"title": "Write Terraform IaC files", "priority": "medium", "done": True},
    {"title": "Install Ansible on cp1", "priority": "medium", "done": True},
    {"title": "Bootstrap Kubernetes cluster", "priority": "high", "done": True},
    {"title": "Add priority field to Task Tracker", "priority": "medium", "done": True},
    {"title": "Write Dockerfile and docker-compose", "priority": "medium", "done": False},
    {"title": "Set up GitHub Actions CI/CD", "priority": "low", "done": False},
    {"title": "Deploy app to Kubernetes cluster", "priority": "low", "done": False},
]


def seed():
    app = create_app()
    with app.app_context():
        existing = Task.query.count()
        if existing > 0:
            print(f"Database already has {existing} task(s). Skipping seed.")
            return

        for item in SAMPLE_TASKS:
            task = Task(
                title=item["title"],
                priority=item["priority"],
                done=item["done"],
            )
            db.session.add(task)

        db.session.commit()
        print(f"Seeded {len(SAMPLE_TASKS)} tasks successfully.")


if __name__ == "__main__":
    seed()
