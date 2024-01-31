from datetime import datetime
from typing import ByteString
from dateutil.relativedelta import relativedelta
from app import app, db, User, LeaveRequest

@ByteString.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'  # Use a separate test database
    client = app.test_client()

    with app.app_context():
        db.create_all()

    yield client

    with app.app_context():
        db.drop_all()

def test_index_route(client):
    # Test if the index route returns a 200 status code
    response = client.get('/')
    assert response.status_code == 200

def test_login_route(client):
    # Test if the login route returns a 200 status code
    response = client.get('/login')
    assert response.status_code == 200

    # Add more login route tests as needed

def test_register_route(client):
    # Test if the register route returns a 200 status code
    response = client.get('/register')
    assert response.status_code == 200

    # Add more register route tests as needed

def test_logout_route(client):
    # Test if the logout route redirects to /login
    response = client.get('/logout')
    assert response.status_code == 302  # Redirect status code

def test_delete_route(client):
    # Test if the delete route redirects to /login when not logged in
    response = client.get('/delete/1')
    assert response.status_code == 302  # Redirect status code

    # Add more delete route tests as needed

def test_user_model():
    # Test User model functionality
    user = User(user_name='testuser', password='testpassword')
    db.session.add(user)
    db.session.commit()

    assert user.user_id is not None

def test_leave_request_model():
    # Test LeaveRequest model functionality
    user = User(user_name='testuser', password='testpassword')
    db.session.add(user)
    db.session.commit()

    leave_request = LeaveRequest(reason='Vacation', date_start=datetime.now(), date_end=datetime.now(), user_id=user.user_id)
    db.session.add(leave_request)
    db.session.commit()

    assert leave_request.id is not None
