import pytest
from fastapi.testclient import TestClient
from src.app import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def clear_activities_after_test():
    yield
    # Reset the activities database after each test
    from src.app import activities
    for activity in activities.values():
        activity["participants"] = activity["participants"][:2]  # Keep only the first two original participants

def test_root_redirects_to_static(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"

def test_get_activities(client):
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    assert isinstance(activities, dict)
    assert "Chess Club" in activities
    assert "Programming Class" in activities

def test_signup_for_activity_success(client):
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}

    # Verify the student was actually added
    activities = client.get("/activities").json()
    assert email in activities[activity_name]["participants"]

def test_signup_for_activity_already_registered(client):
    activity_name = "Programming Class"
    email = "emma@mergington.edu"  # This email is already registered in the test data
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up"}

def test_signup_for_nonexistent_activity(client):
    response = client.post("/activities/NonexistentClub/signup?email=test@mergington.edu")
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}

def test_remove_participant_success(client):
    activity_name = "Gym Class"
    email = "john@mergington.edu"  # This email exists in test data
    response = client.delete(f"/activities/{activity_name}/participant/{email}")
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}

    # Verify the student was actually removed
    activities = client.get("/activities").json()
    assert email not in activities[activity_name]["participants"]

def test_remove_participant_not_registered(client):
    activity_name = "Chess Club"
    email = "notregistered@mergington.edu"
    response = client.delete(f"/activities/{activity_name}/participant/{email}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}

def test_remove_participant_nonexistent_activity(client):
    response = client.delete("/activities/NonexistentClub/participant/test@mergington.edu")
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}