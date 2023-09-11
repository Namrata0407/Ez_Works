import os
import tempfile
import pytest
import json
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_upload_file(client):
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_file:
        temp_file.write(b"Test PDF content")
        temp_file.seek(0)

        # Upload the temporary file
        response = client.post(
            '/addfile',
            data={'file': (temp_file, 'test.pdf')},
            content_type='multipart/form-data'
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert data['message'] == 'Data added successfully'

def test_register_user(client):
    user_data = {
        'email': 'test@example.com',
        'password': 'testpassword'
    }

    response = client.post('/register', json=user_data)
    data = json.loads(response.data.decode())

    assert response.status_code == 200
    assert 'id' in data

def test_login_user(client):
    user_data = {
        'email': 'test@example.com',
        'password': 'testpassword'
    }

    # Register the user first
    register_response = client.post('/register', json=user_data)
    assert register_response.status_code == 200

    # Attempt to log in with the registered user's credentials
    login_response = client.post('/login', json=user_data)
    data = json.loads(login_response.data.decode())

    assert login_response.status_code == 200
    assert 'access_token' in data

def test_invalid_login(client):
    user_data = {
        'email': 'test@example.com',
        'password': 'testpassword'
    }

    # Attempt to log in with invalid credentials
    login_response = client.post('/login', json=user_data)
    assert login_response.status_code == 401
