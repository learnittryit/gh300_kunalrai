import copy

from fastapi.testclient import TestClient
from src.app import app, activities

client = TestClient(app)

BASE_ACTIVITIES = copy.deepcopy(activities)


def reset_activities():
    activities.clear()
    activities.update(copy.deepcopy(BASE_ACTIVITIES))


class TestRootEndpoint:
    def setup_method(self):
        reset_activities()

    def test_root_redirects_to_static_index(self):
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    def setup_method(self):
        reset_activities()

    def test_get_all_activities(self):
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert len(data) == 9

    def test_activity_has_required_fields(self):
        response = client.get("/activities")
        data = response.json()["Chess Club"]
        assert "description" in data
        assert "schedule" in data
        assert "max_participants" in data
        assert "participants" in data
        assert isinstance(data["participants"], list)


class TestSignupEndpoint:
    def setup_method(self):
        reset_activities()

    def test_signup_new_student(self):
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "testuser@mergington.edu"},
        )
        assert response.status_code == 200
        assert "Signed up testuser@mergington.edu for Basketball Team" in response.json()["message"]

        activities_response = client.get("/activities")
        assert "testuser@mergington.edu" in activities_response.json()["Basketball Team"]["participants"]

    def test_signup_duplicate_student(self):
        email = "duplicate@mergington.edu"

        response1 = client.post(
            "/activities/Soccer Club/signup",
            params={"email": email},
        )
        assert response1.status_code == 200

        response2 = client.post(
            "/activities/Soccer Club/signup",
            params={"email": email},
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()

    def test_signup_activity_not_found(self):
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestUnregisterEndpoint:
    def setup_method(self):
        reset_activities()

    def test_unregister_existing_participant(self):
        email = "unregister@mergington.edu"
        signup_response = client.post(
            "/activities/Art Club/signup",
            params={"email": email},
        )
        assert signup_response.status_code == 200

        response = client.delete(
            "/activities/Art Club/participants",
            params={"email": email},
        )
        assert response.status_code == 200
        assert f"Unregistered {email} from Art Club" in response.json()["message"]

        activities_response = client.get("/activities")
        assert email not in activities_response.json()["Art Club"]["participants"]

    def test_unregister_activity_not_found(self):
        response = client.delete(
            "/activities/Nonexistent Club/participants",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_participant_not_found(self):
        response = client.delete(
            "/activities/Drama Club/participants",
            params={"email": "notregistered@mergington.edu"},
        )
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]


class TestIntegrationFlow:
    def setup_method(self):
        reset_activities()

    def test_signup_then_unregister_flow(self):
        email = "integration@mergington.edu"
        activity = "Debate Club"

        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email},
        )
        assert signup_response.status_code == 200

        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]

        unregister_response = client.delete(
            f"/activities/{activity}/participants",
            params={"email": email},
        )
        assert unregister_response.status_code == 200

        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity]["participants"]
