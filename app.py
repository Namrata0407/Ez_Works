from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_cors import CORS
from bson import ObjectId
import bcrypt
import os


app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'eZ-works'
app.config['JWT_SECRET_KEY'] = 'eZ-works'
jwt = JWTManager(app)

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

mongo_uri = os.environ.get('API_URL')

client = MongoClient(mongo_uri)
db = client['database']
opt_usercollections = db['opt_users']
pdf_fileCollections = db["pdf_fileCollections"]

UPLOAD_FOLDER = 'uploadedFiles'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

from pathlib import Path

def allowed_file(filename):
    return '.' in filename and filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS



# route for file upload

@app.route('/addfile', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file found'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'file is not selected'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Save file to our database
        with open(file_path, 'rb') as pdf_file:
            pdf_data = pdf_file.read()
            pdf_fileCollections.insert_one({'filename': filename, 'pdf_data': pdf_data})

        return jsonify({'message': 'Data added successfully'})

    return jsonify({'error': 'File type is invalid'})


# route for register a OPT user

@app.route('/register', methods=['POST'])
def add_user():
    data = request.get_json()

    password = data['password']
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=5))
    data['password'] = hashed_password.decode('utf-8')

    document = data

    result = opt_usercollections.insert_one(document)

    return jsonify({'id': str(result.inserted_id)})


# route for login a user

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['email']
    password = data['password']

    user = opt_usercollections.find_one({'email': username})

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        access_token = create_access_token(identity=str(user['_id']))
        return jsonify({'access_token': access_token})

    return jsonify({'message': 'Password and username are invalid'}), 401

if __name__ == '__main__':
    app.run()
