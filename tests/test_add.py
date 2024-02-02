import dbm
import unittest
from datetime import datetime, timedelta

from flask import app

from src.automated_clean_code import LeaveRequest, User

# from app import app, db, User, LeaveRequest


class TestLeaveRequests(unittest.TestCase):
    """Test case for LeaveRequest functionality."""

    def setUp(self):
        """Set up the test environment."""
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test_leave_request.db"
        app.config["SECRET_KEY"] = "test_secret_key"
        self.app = app.test_client()
        with app.app_context():
            dbm.create_all()

    def tearDown(self):
        """Tear down the test environment."""
        with app.app_context():
            dbm.session.remove()
            dbm.drop_all()

    def test_overlap_leave_request(self):
        """Test overlapping leave requests for the same user on the same day."""
        # Create a user
        user = User(user_name="test_user", password="test_password")
        dbm.session.add(user)
        dbm.session.commit()

        # Create a leave request for the user
        leave_request = LeaveRequest(
            reason="Vacation",
            date_start=datetime.now(),
            date_end=datetime.now() + timedelta(days=2),
            user_id=user.user_id,
        )
        dbm.session.add(leave_request)
        dbm.session.commit()

        # Attempt to create another leave request for the same user on the same day
        response = self.app.post(
            "/",
            data=dict(
                reason="Another Vacation",
                date_start=leave_request.date_start.strftime("%Y-%m-%d"),
                date_end=leave_request.date_start.strftime("%Y-%m-%d"),
            ),
            follow_redirects=True,
        )

        # Verify that the response contains the expected message
        self.assertIn(b"You have already requested leave for overlapping dates", response.data)


if __name__ == "__main__":
    unittest.main()
