"""
Tests for the Mergington High School Activities API.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset participants to a known state before each test."""
    original = {name: list(data["participants"]) for name, data in activities.items()}
    yield
    for name, participants in original.items():
        activities[name]["participants"] = participants


client = TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_200():
    response = client.get("/activities")
    assert response.status_code == 200


def test_get_activities_returns_dict():
    response = client.get("/activities")
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0


def test_get_activities_contains_expected_fields():
    response = client.get("/activities")
    data = response.json()
    for activity in data.values():
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"},
    )
    assert response.status_code == 200
    assert "newstudent@mergington.edu" in response.json()["message"]


def test_signup_adds_participant():
    email = "addedstudent@mergington.edu"
    client.post("/activities/Chess Club/signup", params={"email": email})
    response = client.get("/activities")
    assert email in response.json()["Chess Club"]["participants"]


def test_signup_unknown_activity_returns_404():
    response = client.post(
        "/activities/Unknown Activity/signup",
        params={"email": "someone@mergington.edu"},
    )
    assert response.status_code == 404


def test_signup_duplicate_returns_400():
    email = "duplicate@mergington.edu"
    client.post("/activities/Chess Club/signup", params={"email": email})
    response = client.post("/activities/Chess Club/signup", params={"email": email})
    assert response.status_code == 400


def test_signup_full_activity_returns_400():
    """Fill an activity to capacity and verify the next signup is rejected."""
    activity_name = "Chess Club"
    activity = activities[activity_name]
    spots = activity["max_participants"] - len(activity["participants"])
    for i in range(spots):
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": f"fill{i}@mergington.edu"},
        )
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "overflow@mergington.edu"},
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_unregister_success():
    email = "michael@mergington.edu"
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": email},
    )
    assert response.status_code == 200
    assert email in response.json()["message"]


def test_unregister_removes_participant():
    email = "michael@mergington.edu"
    client.delete("/activities/Chess Club/signup", params={"email": email})
    response = client.get("/activities")
    assert email not in response.json()["Chess Club"]["participants"]


def test_unregister_unknown_activity_returns_404():
    response = client.delete(
        "/activities/Unknown Activity/signup",
        params={"email": "someone@mergington.edu"},
    )
    assert response.status_code == 404


def test_unregister_not_signed_up_returns_400():
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "notregistered@mergington.edu"},
    )
    assert response.status_code == 400
