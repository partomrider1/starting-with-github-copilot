"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirect(self, client):
        """Test that root redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""

    def test_get_activities(self, client):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        
        # Check that expected activities exist
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Basketball" in data
        
    def test_get_activities_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        # Check a specific activity
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        
    def test_get_activities_has_participants(self, client):
        """Test that activities have initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert isinstance(chess_club["participants"], list)
        assert len(chess_club["participants"]) > 0


class TestSignupEndpoint:
    """Tests for signup functionality"""

    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
    def test_signup_reflected_in_activities(self, client):
        """Test that signup is reflected in the activities list"""
        email = "testuser@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Soccer Club/signup?email={email}")
        
        # Check that participant is in the activity
        response = client.get("/activities")
        data = response.json()
        
        assert email in data["Soccer Club"]["participants"]
        
    def test_signup_nonexistent_activity(self, client):
        """Test signup to non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
    def test_signup_already_registered(self, client):
        """Test signup fails if student already registered"""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
        
    def test_signup_multiple_activities(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "versatile@mergington.edu"
        
        # Sign up for multiple activities
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        response2 = client.post(f"/activities/Programming Class/signup?email={email}")
        response3 = client.post(f"/activities/Basketball/signup?email={email}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        
        # Verify in activities
        response = client.get("/activities")
        data = response.json()
        
        assert email in data["Chess Club"]["participants"]
        assert email in data["Programming Class"]["participants"]
        assert email in data["Basketball"]["participants"]


class TestUnregisterEndpoint:
    """Tests for unregister functionality"""

    def test_unregister_success(self, client):
        """Test successful unregister from an activity"""
        email = "testremove@mergington.edu"
        
        # First sign up
        client.post(f"/activities/Science Club/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Science Club/participants?email={email}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        
    def test_unregister_reflected_in_activities(self, client):
        """Test that unregister is reflected in the activities list"""
        email = "testremove2@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Debate Team/signup?email={email}")
        
        # Verify signup
        response = client.get("/activities")
        data = response.json()
        assert email in data["Debate Team"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Debate Team/participants?email={email}")
        
        # Verify removal
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Debate Team"]["participants"]
        
    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Fake Activity/participants?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
    def test_unregister_participant_not_found(self, client):
        """Test unregister when participant not in activity returns 404"""
        response = client.delete(
            "/activities/Art Studio/participants?email=notinthisactivity@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestActivityCount:
    """Tests for activity count and capacity"""

    def test_activity_max_participants(self, client):
        """Test that activities have max_participants"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity in data.items():
            assert "max_participants" in activity
            assert isinstance(activity["max_participants"], int)
            assert activity["max_participants"] > 0
            
    def test_participant_count_within_max(self, client):
        """Test that participant count doesn't exceed max ever"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity in data.items():
            assert len(activity["participants"]) <= activity["max_participants"]
