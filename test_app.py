import os
import tempfile
import pytest
import json
from app import app, pdf_fileCollections
from bson import ObjectId


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
        'password': 'wrongpassword'  # Use an incorrect password to trigger invalid login
    }

    # Attempt to log in with invalid credentials
    login_response = client.post('/login', json=user_data)
    assert login_response.status_code == 401  # Update the assertion to check for a 401 status code

def test_download_file(client):
    # Create a test PDF file and insert it into the database
    test_pdf_data = b"Test PDF content"
    test_filename = 'test.pdf'
    inserted_id = pdf_fileCollections.insert_one({'filename': test_filename, 'pdf_data': test_pdf_data}).inserted_id

    # Attempt to download the file with the "Accept" header set to request octet-stream response
    response = client.get(f'/download/{str(inserted_id)}', headers={'Accept': 'application/octet-stream'})

    assert response.status_code == 200
    assert response.content_type == 'application/octet-stream'
    assert response.headers['Content-Disposition'] == f'attachment; filename="{test_filename}"'
    assert response.data == test_pdf_data

def test_download_nonexistent_file(client):
    # Attempt to download a nonexistent file
    nonexistent_id = str(ObjectId())
    response = client.get(f'/download/{nonexistent_id}', headers={'Accept': 'application/octet-stream'})

    assert response.status_code == 404
    assert response.data.decode() == 'File not found'

def test_get_all_files(client):
    # Insert some test PDF files into the database
    pdf_files = [
        {'filename': 'file1.pdf', 'pdf_data': b'File 1 content'},
        {'filename': 'file2.pdf', 'pdf_data': b'File 2 content'},
    ]
    pdf_ids = [str(pdf_fileCollections.insert_one(file_data).inserted_id) for file_data in pdf_files]

    # Request to get all files
    response = client.get('/getall')
    data = json.loads(response.data.decode())

    assert response.status_code == 200
    assert len(data) == len(pdf_files)

    # Verify that the response contains information about all inserted files
    for i, file_info in enumerate(data):
        assert 'id' in file_info
        assert file_info['id'] == pdf_ids[i]
        assert 'filename' in file_info
        assert file_info['filename'] == pdf_files[i]['filename']
