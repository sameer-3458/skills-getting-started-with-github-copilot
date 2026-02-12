"""
Tests for the Mergington High School Activities API
"""
import pytest


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activity data"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        activities = response.json()
        
        # Check that we get all 9 activities
        assert len(activities) == 9
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        
    def test_activities_have_required_fields(self, client, reset_activities):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        # Check first activity has all required fields
        chess_club = activities["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        
    def test_activities_have_correct_participant_counts(self, client, reset_activities):
        """Test that activities have the correct initial participant counts"""
        response = client.get("/activities")
        activities = response.json()
        
        assert len(activities["Chess Club"]["participants"]) == 2
        assert len(activities["Programming Class"]["participants"]) == 2
        assert len(activities["Basketball Team"]["participants"]) == 1


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity_success(self, client, reset_activities):
        """Test successfully signing up for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
        
    def test_signup_adds_participant_to_list(self, client, reset_activities):
        """Test that signup actually adds the email to participants"""
        client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
        
        response = client.get("/activities")
        activities = response.json()
        
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
        assert len(activities["Chess Club"]["participants"]) == 3
        
    def test_signup_for_nonexistent_activity(self, client, reset_activities):
        """Test that signup fails for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
        
    def test_signup_duplicate_registration_blocked(self, client, reset_activities):
        """Test that a student cannot register twice for the same activity"""
        # First signup should succeed
        response1 = client.post(
            "/activities/Chess Club/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            "/activities/Chess Club/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
        
    def test_signup_increases_participant_count(self, client, reset_activities):
        """Test that signup increases the participant count"""
        response_before = client.get("/activities")
        count_before = len(response_before.json()["Gym Class"]["participants"])
        
        client.post("/activities/Gym Class/signup?email=newcomer@mergington.edu")
        
        response_after = client.get("/activities")
        count_after = len(response_after.json()["Gym Class"]["participants"])
        
        assert count_after == count_before + 1


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successfully unregistering from an activity"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the email from participants"""
        client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        
        response = client.get("/activities")
        activities = response.json()
        
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
        assert len(activities["Chess Club"]["participants"]) == 1
        
    def test_unregister_from_nonexistent_activity(self, client, reset_activities):
        """Test that unregister fails for non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
        
    def test_unregister_not_registered_student(self, client, reset_activities):
        """Test that unregister fails if student is not registered"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
        
    def test_unregister_decreases_participant_count(self, client, reset_activities):
        """Test that unregister decreases the participant count"""
        response_before = client.get("/activities")
        count_before = len(response_before.json()["Debate Team"]["participants"])
        
        client.delete(
            "/activities/Debate Team/unregister?email=lucas@mergington.edu"
        )
        
        response_after = client.get("/activities")
        count_after = len(response_after.json()["Debate Team"]["participants"])
        
        assert count_after == count_before - 1


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that root path redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestIntegration:
    """Integration tests combining multiple operations"""
    
    def test_signup_then_unregister_workflow(self, client, reset_activities):
        """Test the complete workflow of signing up and then unregistering"""
        email = "integration@mergington.edu"
        activity = "Tennis Club"
        
        # Add participant
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity]["participants"])
        
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        mid_response = client.get("/activities")
        mid_count = len(mid_response.json()[activity]["participants"])
        assert mid_count == initial_count + 1
        assert email in mid_response.json()[activity]["participants"]
        
        # Remove participant
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity]["participants"])
        assert final_count == initial_count
        assert email not in final_response.json()[activity]["participants"]
