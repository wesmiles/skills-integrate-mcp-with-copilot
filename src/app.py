"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import json
import os
import sqlite3
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

DB_PATH = current_dir / "activities.db"

DEFAULT_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


def get_db_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db_connection()
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS activities (
            name TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            schedule TEXT NOT NULL,
            max_participants INTEGER NOT NULL,
            participants TEXT NOT NULL DEFAULT '[]'
        )
        """
    )

    existing_count = connection.execute("SELECT COUNT(*) FROM activities").fetchone()[0]
    if existing_count == 0:
        for name, details in DEFAULT_ACTIVITIES.items():
            connection.execute(
                "INSERT INTO activities (name, description, schedule, max_participants, participants) VALUES (?, ?, ?, ?, ?)",
                (
                    name,
                    details["description"],
                    details["schedule"],
                    details["max_participants"],
                    json.dumps(details["participants"]),
                ),
            )

    connection.commit()
    connection.close()


def persist_activity(activity_name: str, activity: dict):
    connection = get_db_connection()
    connection.execute(
        """
        INSERT INTO activities (name, description, schedule, max_participants, participants)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            description = excluded.description,
            schedule = excluded.schedule,
            max_participants = excluded.max_participants,
            participants = excluded.participants
        """,
        (
            activity_name,
            activity["description"],
            activity["schedule"],
            activity["max_participants"],
            json.dumps(activity["participants"]),
        ),
    )
    connection.commit()
    connection.close()


def load_activities():
    connection = get_db_connection()
    rows = connection.execute(
        "SELECT name, description, schedule, max_participants, participants FROM activities"
    ).fetchall()
    connection.close()

    activities = {}
    for row in rows:
        activities[row["name"]] = {
            "description": row["description"],
            "schedule": row["schedule"],
            "max_participants": row["max_participants"],
            "participants": json.loads(row["participants"] or "[]"),
        }
    return activities


init_db()
activities = load_activities()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return load_activities()


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    current_activities = load_activities()

    # Validate activity exists
    if activity_name not in current_activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = current_activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student and persist
    activity["participants"].append(email)
    persist_activity(activity_name, activity)
    global activities
    activities = load_activities()
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    current_activities = load_activities()

    # Validate activity exists
    if activity_name not in current_activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = current_activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student and persist
    activity["participants"].remove(email)
    persist_activity(activity_name, activity)
    global activities
    activities = load_activities()
    return {"message": f"Unregistered {email} from {activity_name}"}
